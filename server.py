"""Kavach web server: the Kavach engine behind a small local API + the website in web/dist.

Run:  python server.py      ->  open http://127.0.0.1:8000

Privacy: the network guard is switched on before anything else, the server listens only on
127.0.0.1 (other devices cannot reach it), and the website's fonts and libraries are bundled
in web/dist, so the browser does not need the internet either.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from kavach import netguard  # noqa: E402

netguard.enable()

import json  # noqa: E402

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from kavach import diary, intel, report  # noqa: E402
from kavach.detector import analyze, get_model  # noqa: E402
from kavach.library import FAMILIES, RECOVERY_COMMON, REPORT_ONLY  # noqa: E402
from kavach.tricks import TRICKS, disguise  # noqa: E402

app = FastAPI(title="Kavach", docs_url=None, redoc_url=None)
get_model()  # load once at start-up

MAX_LEN = 5000


class Msg(BaseModel):
    text: str = Field(..., max_length=MAX_LEN)
    sender: str = Field("", max_length=60)
    save: bool = True


class ReportIn(Msg):
    received: str = ""
    channel: str = "SMS"
    lost_money: bool = False
    amount_lost: str = ""
    transaction_ref: str = ""
    notes: str = Field("", max_length=2000)
    format: str = "pdf"


class Batch(BaseModel):
    messages: list[str] = Field(..., max_length=2000)


class DisguiseIn(BaseModel):
    text: str = Field(..., max_length=MAX_LEN)
    tricks: list[str] = []
    seed: int = 1


class SettingsIn(BaseModel):
    diary_enabled: bool | None = None
    auto_delete_days: int | None = None


def result_json(res, saved_id=None) -> dict:
    fam = res.family_info
    return {
        "text": res.text, "cleaned": res.cleaned, "tricks": {k: v for k, v in res.tricks.items() if v},
        "verdict": res.verdict, "p_scam": res.p_scam, "confidence": res.confidence,
        "confidence_text": report.pct(res.confidence), "category": res.category, "category_probs": res.category_probs,
        "unfamiliar": res.unfamiliar, "family": res.family, "family_info": fam,
        "flags": [{"rule": f.rule, "label": f.label, "reason": f.reason, "severity": f.severity,
                   "start": f.start, "end": f.end, "text": f.text} for f in res.flags],
        "links": [{"url": l.url, "defanged": l.defanged, "start": l.start, "end": l.end, "host": l.host,
                   "registered": l.registered, "verdict": l.verdict, "issues": l.issues, "notes": l.notes}
                  for l in res.links],
        "brands": res.brands, "top_words": [{"word": w, "weight": v} for w, v in res.top_words],
        "advice": res.advice, "recovery": RECOVERY_COMMON, "report_only": REPORT_ONLY,
        "sender_note": res.sender_note, "safety_net": res.safety_net, "ms": res.ms, "saved_to_diary": saved_id,
    }


@app.post("/api/analyze")
def api_analyze(m: Msg):
    if not m.text.strip():
        raise HTTPException(400, "Paste a message first.")
    res = analyze(m.text, m.sender)
    saved = diary.add(res) if m.save else None
    return result_json(res, saved)


@app.post("/api/report")
def api_report(r: ReportIn):
    res = analyze(r.text, r.sender)
    det = report.ReportDetails(sender=r.sender, received=r.received, channel=r.channel, lost_money=r.lost_money,
                               amount_lost=r.amount_lost, transaction_ref=r.transaction_ref, notes=r.notes)
    rep = report.build(res, det)
    if r.format == "summary":
        return {"summary": report.complaint_summary(rep), "report_id": rep["report_id"], "sha256": rep["sha256"]}
    if r.format == "txt":
        return Response(report.text_report(rep), media_type="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{report.filename(rep, "txt")}"'})
    return Response(report.pdf_report(rep), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{report.filename(rep, "pdf")}"'})


@app.get("/api/privacy")
def api_privacy():
    return {"guard": netguard.self_test(), "blocked": len(netguard.blocked_attempts),
            "diary": diary.is_enabled(), "intel_used": bool(netguard.allowed_log), "intel_hosts": sorted(set(netguard.allowed_log))}


@app.get("/api/diary")
def api_diary():
    rows = diary.entries()
    st = diary.stats(rows)
    return {"settings": diary.settings(), "entries": rows,
            "stats": {k: (dict(v.most_common()) if hasattr(v, "most_common") else v) for k, v in st.items()}}


@app.post("/api/diary/settings")
def api_diary_settings(s: SettingsIn):
    diary.save_settings({k: v for k, v in s.model_dump().items() if v is not None})
    return diary.settings()


@app.delete("/api/diary/{entry_id}")
def api_diary_delete(entry_id: int):
    diary.delete(entry_id)
    return {"ok": True}


@app.delete("/api/diary")
def api_diary_delete_all():
    diary.delete_all()
    return {"ok": True}


@app.get("/api/diary/alert")
def api_alert(days: int = 7):
    a = diary.family_alert(diary.entries(), days)
    return {"en": a["en"], "hi": a["hi"]}


@app.get("/api/diary/alert.png")
def api_alert_png(days: int = 7):
    a = diary.family_alert(diary.entries(), days)
    return Response(diary.alert_card_png(a["en"] or "No scams logged yet."), media_type="image/png")


@app.get("/api/library")
def api_library():
    return {"families": FAMILIES, "recovery": RECOVERY_COMMON, "report_only": REPORT_ONLY}


@app.post("/api/intel/preview")
def api_intel_preview(m: Msg):
    res = analyze(m.text, m.sender)
    return {"query": intel.build_query(res), "available": res.verdict != "SAFE"}


@app.post("/api/intel/search")
def api_intel_search(m: Msg):
    """The query is rebuilt here from the analysis, so only scam type + brand can ever be sent."""
    res = analyze(m.text, m.sender)
    if res.verdict == "SAFE":
        raise HTTPException(400, "Only available for SCAM or SUSPICIOUS results.")
    r = intel.search(intel.build_query(res))
    return {"query": r.query, "error": r.error, "fetched_at": r.fetched_at, "last_30": r.last_30, "cities": r.cities,
            "amounts": list(dict.fromkeys(r.amounts)),
            "articles": [{"title": a["title"], "source": a["source"],
                          "date": a["date"].strftime("%d %b %Y") if a["date"] else ""} for a in r.articles[:10]],
            "total": len(r.articles)}


@app.post("/api/batch")
def api_batch(b: Batch):
    out = []
    for m in b.messages[:2000]:
        if not m.strip():
            continue
        r = analyze(m[:MAX_LEN])
        out.append({"verdict": r.verdict, "confidence": r.confidence, "category": r.category or "",
                    "signs": [f.label for f in r.red_flags[:3]], "message": m})
    return {"rows": out}


@app.get("/api/tricks")
def api_tricks():
    return TRICKS


@app.post("/api/disguise")
def api_disguise(d: DisguiseIn):
    return {"text": disguise(d.text, d.tricks, d.seed)}


@app.get("/api/metrics")
def api_metrics():
    p = ROOT / "results" / "metrics.json"
    if not p.exists():
        raise HTTPException(404, "Run scripts/evaluate.py first.")
    return JSONResponse(json.loads(p.read_text(encoding="utf-8")))


@app.get("/api/reliability.png")
def api_reliability():
    return FileResponse(ROOT / "results" / "reliability.png")


DIST = ROOT / "web" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="site")


if __name__ == "__main__":
    import uvicorn
    print("Kavach is running offline at  http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
