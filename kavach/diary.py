"""Scam Diary: an OPTIONAL history kept only on this computer.

Privacy rules (enforced here, checked by tests/test_privacy.py):
  * OFF by default; nothing is written until the user switches it on
  * only the lesson is stored: date, verdict, category, red-flag names, brands, link domains and a
    MASKED snippet (see redact.py); never the full message, numbers, codes or clickable links
  * stored in one local SQLite file (local_data/diary.db, git-ignored), never sent anywhere
  * the user can delete one entry, delete everything, or auto-delete entries older than N days
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from .normalize import normalize
from .redact import redact

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "local_data"
DB_PATH = DATA_DIR / "diary.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
DEFAULTS = {"diary_enabled": False, "auto_delete_days": 0}


# ------------------------------------------------------------------ settings
def settings(path: Path | None = None) -> dict:
    path = path or SETTINGS_PATH
    try:
        return {**DEFAULTS, **json.loads(path.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save_settings(values: dict, path: Path | None = None) -> None:
    path = path or SETTINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**settings(path), **values}, indent=2), encoding="utf-8")


def is_enabled() -> bool:
    return bool(settings().get("diary_enabled"))


# ------------------------------------------------------------------ storage
@contextmanager
def _db(path: Path = DB_PATH):
    """Open, commit and always CLOSE the connection (so the file can be deleted on Windows)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        _init(con)
        yield con
        con.commit()
    finally:
        con.close()


def _init(con: sqlite3.Connection) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, verdict TEXT, category TEXT, family TEXT,
        confidence REAL, flags TEXT, brands TEXT, link_domains TEXT, snippet TEXT)""")
    cols = {r[1] for r in con.execute("PRAGMA table_info(entries)")}
    for col, decl in (("times_seen", "INTEGER DEFAULT 1"), ("last_seen", "TEXT"), ("fp", "TEXT")):
        if col not in cols:  # older diary files: add the new columns in place
            con.execute(f"ALTER TABLE entries ADD COLUMN {col} {decl}")


# ------------------------------------------------------------------ "already checked" (repeat detection)
# Two ways to recognise a message seen before, without ever storing the message itself:
#  * SAME:    a keyed fingerprint (HMAC-SHA256) of the cleaned text. One-way: the message cannot be read back from it.
#  * SIMILAR: the masked snippet (numbers, codes, links already removed) compared with earlier snippets, so the same scam
#             sent again with a different phone number, link or amount is recognised too.
# With the diary OFF, a short in-memory list (lost when the app closes) still lets Kavach say "you checked this
# earlier in this session". Nothing is written to disk in that case.
SIMILAR_MIN = 0.85
_SESSION: list[dict] = []
_SESSION_SALT = os.urandom(16)


def _salt() -> bytes:
    """Per-installation key for diary fingerprints (created on first use, stored next to the diary)."""
    s = settings()
    if not s.get("fp_salt"):
        save_settings({"fp_salt": secrets.token_hex(16)})
        s = settings()
    return bytes.fromhex(s["fp_salt"])


def _fp(text: str, salt: bytes) -> str:
    return hmac.new(salt, normalize(text).text.encode("utf-8"), hashlib.sha256).hexdigest()


def _snippet(text: str) -> str:
    s = redact(text)
    return s[:277] + "..." if len(s) > 280 else s


def _shape(snippet: str) -> str:
    """Comparable form of a masked snippet: lowercase words, placeholders and digits collapsed."""
    s = normalize(snippet).text
    s = re.sub(r"hxxps?://\S+|\S+\[\.\]\S+", " LINK ", s)
    s = re.sub(r"\d[\d,.]*", "0", s)
    return re.sub(r"\s+", " ", s).strip()


def similarity(a: str, b: str) -> float:
    a, b = _shape(a), _shape(b)
    if not a or not b:
        return 0.0
    wa, wb = set(a.split()), set(b.split())
    if len(wa & wb) / max(1, len(wa | wb)) < 0.4:   # cheap filter before the exact comparison
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def lookup(result, path: Path = DB_PATH) -> dict | None:
    """Has this message (or a very similar one) been checked before? Call BEFORE add()/remember()."""
    snip = _snippet(result.text)
    best = None
    if path.exists():
        fp = _fp(result.text, _salt())
        for e in entries(path):
            if e.get("fp") == fp:
                return {"match": "same", "similarity": 1.0, "source": "diary", "ts": e["ts"], "last_seen": e.get("last_seen") or e["ts"],
                        "times_seen": e.get("times_seen") or 1, "verdict": e["verdict"], "category": e["category"],
                        "snippet": e["snippet"], "id": e["id"]}
            sim = similarity(snip, e["snippet"])
            if sim >= SIMILAR_MIN and (not best or sim > best["similarity"]):
                best = {"match": "similar", "similarity": round(sim, 2), "source": "diary", "ts": e["ts"],
                        "last_seen": e.get("last_seen") or e["ts"], "times_seen": e.get("times_seen") or 1,
                        "verdict": e["verdict"], "category": e["category"], "snippet": e["snippet"], "id": e["id"]}
    sfp = _fp(result.text, _SESSION_SALT)
    for e in reversed(_SESSION):
        if e["fp"] == sfp:
            return {"match": "same", "similarity": 1.0, "source": "session", "ts": e["ts"], "last_seen": e["ts"],
                    "times_seen": e["n"], "verdict": e["verdict"], "category": e["category"], "snippet": e["snippet"], "id": None}
        if not best:
            sim = similarity(snip, e["snippet"])
            if sim >= SIMILAR_MIN:
                best = {"match": "similar", "similarity": round(sim, 2), "source": "session", "ts": e["ts"], "last_seen": e["ts"],
                        "times_seen": e["n"], "verdict": e["verdict"], "category": e["category"], "snippet": e["snippet"], "id": None}
    return best


def remember(result) -> None:
    """In-memory only: lets Kavach recognise repeats during this session even when the diary is off."""
    sfp = _fp(result.text, _SESSION_SALT)
    for e in _SESSION:
        if e["fp"] == sfp:
            e["n"] += 1
            return
    _SESSION.append({"fp": sfp, "snippet": _snippet(result.text), "verdict": result.verdict, "category": result.category,
                     "ts": datetime.now().isoformat(timespec="seconds"), "n": 1})
    del _SESSION[:-200]


def add(result, path: Path = DB_PATH, previous: dict | None = None) -> dict | None:
    """Save the lesson from one checked message. Does nothing unless the diary is enabled.
    The same or a very similar message is NOT stored twice: the existing entry's count goes up instead."""
    if not is_enabled() or result.verdict == "SAFE":
        return None
    now = datetime.now().isoformat(timespec="seconds")
    if previous and previous.get("source") == "diary" and previous.get("id"):
        with _db(path) as con:
            con.execute("UPDATE entries SET times_seen = COALESCE(times_seen, 1) + 1, last_seen = ? WHERE id = ?",
                        (now, previous["id"]))
            n = con.execute("SELECT times_seen FROM entries WHERE id = ?", (previous["id"],)).fetchone()[0]
        return {"id": previous["id"], "updated": True, "times_seen": n}
    domains = sorted({lf.registered.replace(".", "[.]") for lf in result.links if lf.verdict != "official"})
    with _db(path) as con:
        cur = con.execute(
            "INSERT INTO entries (ts, verdict, category, family, confidence, flags, brands, link_domains, snippet, "
            "times_seen, last_seen, fp) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (now, result.verdict, result.category, result.family,
             round(result.p_scam, 3), json.dumps(sorted({f.label for f in result.red_flags})),
             json.dumps(result.brands), json.dumps(domains), _snippet(result.text), 1, now, _fp(result.text, _salt())))
        return {"id": cur.lastrowid, "updated": False, "times_seen": 1}


def entries(path: Path = DB_PATH) -> list[dict]:
    purge_old(path=path)
    if not path.exists():
        return []
    with _db(path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM entries ORDER BY ts DESC").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        for k in ("flags", "brands", "link_domains"):
            d[k] = json.loads(d[k] or "[]")
        out.append(d)
    return out


def delete(entry_id: int, path: Path = DB_PATH) -> None:
    with _db(path) as con:
        con.execute("DELETE FROM entries WHERE id = ?", (entry_id,))


def delete_all(path: Path = DB_PATH) -> None:
    """Erase every entry and the file itself."""
    if path.exists():
        with _db(path) as con:
            con.execute("DELETE FROM entries")
        try:
            path.unlink()
        except OSError:
            pass


def purge_old(days: int | None = None, path: Path = DB_PATH) -> int:
    days = settings().get("auto_delete_days", 0) if days is None else days
    if not days or not path.exists():
        return 0
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    with _db(path) as con:
        return con.execute("DELETE FROM entries WHERE ts < ?", (cutoff,)).rowcount


# ------------------------------------------------------------------ dashboard numbers
def stats(rows: list[dict]) -> dict:
    weeks = Counter()
    for r in rows:
        d = datetime.fromisoformat(r["ts"])
        weeks[(d - timedelta(days=d.weekday())).date()] += 1
    return {
        "total": len(rows),                                              # different scam messages
        "received": sum((r.get("times_seen") or 1) for r in rows),      # including repeats
        "repeats": sum(1 for r in rows if (r.get("times_seen") or 1) > 1),
        "scam": sum(r["verdict"] == "SCAM" for r in rows),
        "suspicious": sum(r["verdict"] == "SUSPICIOUS" for r in rows),
        "by_category": Counter(r["category"] or "Other" for r in rows),
        "by_flag": Counter(f for r in rows for f in r["flags"]),
        "by_brand": Counter(b for r in rows for b in r["brands"]),
        "by_week": {k.strftime("%d %b"): v for k, v in sorted(weeks.items())},
    }


# ------------------------------------------------------------------ family alert
CAT_EN = {"KYC/Bank": "fake bank / KYC", "Lottery/Prize": "fake lottery / prize", "Loan/Credit": "fake loan",
          "Job/Investment": "fake job / investment", "Other": "other scam"}
CAT_HI = {"KYC/Bank": "नकली बैंक / KYC", "Lottery/Prize": "नकली लॉटरी / इनाम", "Loan/Credit": "नकली लोन",
          "Job/Investment": "नकली नौकरी / निवेश", "Other": "दूसरे धोखाधड़ी"}
TIP_EN = {"KYC/Bank": "Banks never ask for KYC, OTP or PIN through SMS links or calls.",
          "Lottery/Prize": "Real prizes never ask you to pay a fee first.",
          "Loan/Credit": "Never pay a 'processing fee' before a loan; borrow only from RBI-registered lenders.",
          "Job/Investment": "Real jobs never ask you to pay, and no investment guarantees profit.",
          "Other": "Police, courts and companies never demand money or codes over SMS, WhatsApp or video call."}
TIP_HI = {"KYC/Bank": "बैंक कभी SMS लिंक या कॉल से KYC, OTP या PIN नहीं माँगते।",
          "Lottery/Prize": "असली इनाम के लिए कभी पहले पैसे नहीं देने पड़ते।",
          "Loan/Credit": "लोन से पहले कभी 'प्रोसेसिंग फीस' न दें।",
          "Job/Investment": "असली नौकरी में पैसे नहीं माँगे जाते, और कोई निवेश पक्का मुनाफ़ा नहीं देता।",
          "Other": "पुलिस या कंपनियाँ कभी SMS, WhatsApp या वीडियो कॉल पर पैसे या कोड नहीं माँगतीं।"}


def family_alert(rows: list[dict], days: int = 7) -> dict:
    """A short warning for family WhatsApp groups. Contains no personal data: only scam patterns."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = [r for r in rows if datetime.fromisoformat(r["ts"]) >= cutoff] or rows
    st = stats(recent)
    period_en = "this week" if days <= 7 else f"in the last {days} days"
    period_hi = "इस हफ़्ते" if days <= 7 else f"पिछले {days} दिनों में"
    if not recent:
        return {"en": "", "hi": ""}
    top = st["by_category"].most_common(3)
    brands = [b for b, _ in st["by_brand"].most_common(2)]
    tricks = [f for f, _ in st["by_flag"].most_common(3)]
    lines_en = [f"⚠️ Scam alert from Kavach: {period_en} I received {st['total']} scam message(s)."]
    lines_en += [f"• {n} × {CAT_EN.get(c, c)}" for c, n in top]
    if brands:
        lines_en.append(f"They pretended to be: {', '.join(brands)}.")
    if tricks:
        lines_en.append(f"Tricks used: {', '.join(t.lower() for t in tricks)}.")
    lines_en.append(TIP_EN.get(top[0][0], TIP_EN["Other"]))
    lines_en.append("Never share OTP/PIN. If money is lost, call 1930 immediately or report at cybercrime.gov.in.")
    lines_hi = [f"⚠️ Kavach स्कैम अलर्ट: {period_hi} मुझे {st['total']} धोखाधड़ी वाले मैसेज आए।"]
    lines_hi += [f"• {n} × {CAT_HI.get(c, c)}" for c, n in top]
    if brands:
        lines_hi.append(f"ये {', '.join(brands)} के नाम से आए थे।")
    lines_hi.append(TIP_HI.get(top[0][0], TIP_HI["Other"]))
    lines_hi.append("OTP/PIN कभी किसी से साझा न करें। पैसे गए हों तो तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर शिकायत करें।")
    return {"en": "\n".join(lines_en), "hi": "\n".join(lines_hi), "stats": st}


def alert_card_png(text_en: str) -> bytes:
    """Render the English alert as a shareable image card (PNG bytes)."""
    import textwrap

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lines = []
    for para in text_en.replace("⚠️ ", "").split("\n"):
        lines += textwrap.wrap(para, 52) or [""]
    h = 1.6 + 0.32 * len(lines)
    fig = plt.figure(figsize=(6, h), dpi=160)
    fig.patch.set_facecolor("#fff8e7")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 1 - 0.9 / h), 1, 0.9 / h, color="#c0392b", transform=ax.transAxes))
    ax.text(0.05, 1 - 0.45 / h, "SCAM ALERT", color="white", fontsize=18, fontweight="bold", va="center",
            transform=ax.transAxes)
    ax.text(0.95, 1 - 0.45 / h, "shared from Kavach (offline)", color="#ffe1dc", fontsize=8, va="center",
            ha="right", transform=ax.transAxes)
    y = 1 - 1.15 / h
    for ln in lines:
        ax.text(0.05, y, ln, fontsize=10, color="#222", va="top", transform=ax.transAxes)
        y -= 0.32 / h
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()
