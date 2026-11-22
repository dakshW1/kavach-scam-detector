"""Scam Diary: an OPTIONAL history kept only on this computer.

Privacy rules (enforced here, checked by tests/test_privacy.py):
  * OFF by default; nothing is written until the user switches it on
  * only the lesson is stored: date, verdict, category, red-flag names, brands, link domains and a
    MASKED snippet (see redact.py); never the full message, numbers, codes or clickable links
  * stored in one local SQLite file (local_data/diary.db, git-ignored), never sent anywhere
  * the user can delete one entry, delete everything, or auto-delete entries older than N days
"""
from __future__ import annotations

import io
import json
import sqlite3
from contextlib import contextmanager
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from .redact import redact

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "local_data"
DB_PATH = DATA_DIR / "diary.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
DEFAULTS = {"diary_enabled": False, "auto_delete_days": 0}


# ------------------------------------------------------------------ settings
def settings(path: Path = SETTINGS_PATH) -> dict:
    try:
        return {**DEFAULTS, **json.loads(path.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save_settings(values: dict, path: Path = SETTINGS_PATH) -> None:
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


def add(result, path: Path = DB_PATH) -> int | None:
    """Save the lesson from one checked message. Does nothing unless the diary is enabled."""
    if not is_enabled() or result.verdict == "SAFE":
        return None
    snippet = redact(result.text)
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."
    domains = sorted({lf.registered.replace(".", "[.]") for lf in result.links if lf.verdict != "official"})
    with _db(path) as con:
        cur = con.execute(
            "INSERT INTO entries (ts, verdict, category, family, confidence, flags, brands, link_domains, snippet) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), result.verdict, result.category, result.family,
             round(result.p_scam, 3), json.dumps(sorted({f.label for f in result.red_flags})),
             json.dumps(result.brands), json.dumps(domains), snippet))
        return cur.lastrowid


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
        "total": len(rows),
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
