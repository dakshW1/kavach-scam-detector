"""Evidence report: turns an analysis into a document the user can attach to a complaint.

Two outputs, both made on this computer:
  * plain text  - short "incident description" to paste into cybercrime.gov.in, plus the full report
  * PDF         - the same content, laid out for printing or attaching

The report contains the original message (the authorities need it). It is created only when the
user asks, kept in memory, and saved only where the user chooses; it is never stored by the app.
The SHA-256 fingerprint lets anyone check later that the message text was not changed.
"""
from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .links import OFFICIAL, defang, phone_numbers

VERSION = "Kavach 1.0"


@dataclass
class ReportDetails:
    sender: str = ""
    received: str = ""          # when the message arrived, as the user typed it
    channel: str = "SMS"        # SMS / WhatsApp / Email / Other
    lost_money: bool = False
    amount_lost: str = ""
    transaction_ref: str = ""
    notes: str = ""


def pct(p: float) -> str:
    """Confidence as text; never claims 100%."""
    return ">99%" if p >= 0.995 else "<1%" if p < 0.005 else f"{p:.0%}"


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def where_to_report(result, details: ReportDetails) -> list[str]:
    steps = []
    if details.lost_money:
        steps.append("URGENT - money was lost: call 1930 (National Cyber Crime Helpline) right away; reporting in the "
                     "first hours gives the best chance of freezing the money.")
        steps.append("File a complaint at https://cybercrime.gov.in -> 'Report Cyber Crime' -> 'Financial Fraud'. "
                     "Attach this report and your bank statement.")
        steps.append("Call your bank on the number printed on your card / passbook and block cards, UPI and net banking.")
    else:
        steps.append("Report the message on Sanchar Saathi -> Chakshu (https://sancharsaathi.gov.in) so the sender "
                     "number can be checked and blocked.")
        steps.append("You can also report it at https://cybercrime.gov.in (or call 1930 if anything was paid or shared).")
    if any(b in OFFICIAL for b in result.brands):
        b = next(b for b in result.brands if b in OFFICIAL)
        steps.append(f"Inform {b} through its official website ({OFFICIAL[b][0]}) or the number on your card; "
                     "banks track phishing that uses their name.")
    steps.append("Block the sender and delete the message after saving this report.")
    return steps


def build(result, details: ReportDetails | None = None) -> dict:
    """Collect everything once; text_report() and pdf_report() only lay it out."""
    details = details or ReportDetails()
    now = datetime.now()
    evidence = []
    for f in result.red_flags:
        if f.rule.startswith("link_"):
            continue  # links get their own section
        quote = f'"{f.text.strip()}"' if f.text.strip() else ""
        evidence.append({"title": f.label, "quote": quote, "why": f.reason, "severity": f.severity})
    links = []
    for lf in result.links:
        links.append({"as_written": defang(lf.url), "real_domain": lf.registered.replace(".", "[.]"),
                      "verdict": lf.verdict, "issues": lf.issues, "notes": lf.notes})
    phones = [(n, k) for _, _, n, k in phone_numbers(result.text)]
    return {
        "generated": now.strftime("%d %b %Y, %I:%M %p"),
        "report_id": f"KV-{now.strftime('%Y%m%d-%H%M%S')}-{fingerprint(result.text)[:6].upper()}",
        "verdict": result.verdict, "confidence": result.confidence, "p_scam": result.p_scam,
        "category": result.category or "-", "family": (result.family_info or {}).get("title", "-"),
        "message": result.text, "sha256": fingerprint(result.text), "details": details,
        "evidence": evidence, "links": links, "phones": phones, "brands": result.brands,
        "good_signs": [f.label for f in result.good_signs], "tricks": {k: v for k, v in result.tricks.items() if v},
        "steps": where_to_report(result, details),
    }


def complaint_summary(rep: dict) -> str:
    """A short paragraph for the 'incident details' box of a complaint form."""
    d: ReportDetails = rep["details"]
    parts = [f"I received a suspected {rep['category']} fraud message"
             + (f" on {d.channel}" if d.channel else "") + (f" from {d.sender}" if d.sender else "")
             + (f" on {d.received}" if d.received else "") + "."]
    if rep["brands"]:
        parts.append(f"The message pretends to be from {', '.join(rep['brands'])}.")
    bad_links = [l for l in rep["links"] if l["verdict"] in ("dangerous", "suspicious")]
    if bad_links:
        parts.append("It contains the link(s) " + ", ".join(l["as_written"] for l in bad_links)
                     + ", which are not official websites of the organisation named.")
    tactics = [e["title"].lower() for e in rep["evidence"] if e["severity"] in ("high", "medium")]
    if tactics:
        parts.append("Warning signs: " + "; ".join(dict.fromkeys(tactics)) + ".")
    mobiles = [n for n, k in rep["phones"] if k == "mobile"]
    if mobiles:
        parts.append("Contact number(s) given in the message: " + ", ".join(mobiles) + ".")
    if d.lost_money:
        parts.append(f"I lost money: {d.amount_lost or 'amount to be confirmed'}"
                     + (f", transaction reference {d.transaction_ref}" if d.transaction_ref else "") + ".")
    else:
        parts.append("I did not make any payment or share any codes.")
    parts.append(f'Message text: "{rep["message"]}"')
    return " ".join(parts)


def text_report(rep: dict) -> str:
    d: ReportDetails = rep["details"]
    L = ["SCAM MESSAGE EVIDENCE REPORT", "=" * 60,
         f"Report ID: {rep['report_id']}    Generated: {rep['generated']}    Tool: {VERSION} (offline)", "",
         "1. SUMMARY", f"   Assessment : {rep['verdict']} ({pct(rep['confidence'])} confidence)",
         f"   Category   : {rep['category']}", f"   Scam type  : {rep['family']}", "",
         "2. MESSAGE DETAILS",
         f"   Channel    : {d.channel or '-'}", f"   Sender     : {d.sender or '(not provided)'}",
         f"   Received   : {d.received or '(not provided)'}", "   Original message (exactly as received):",
         *["     | " + ln for ln in rep["message"].splitlines() or [""]],
         f"   SHA-256 fingerprint of the message: {rep['sha256']}", ""]
    L.append("3. EVIDENCE")
    for i, e in enumerate(rep["evidence"], 1):
        L.append(f"   3.{i} {e['title']} {e['quote']}")
        L.append(f"        {e['why']}")
    if not rep["evidence"]:
        L.append("   (no text-based warning signs; see links below)")
    L.append("")
    L.append("4. LINKS IN THE MESSAGE (made unclickable; NOT opened by the tool)")
    for i, l in enumerate(rep["links"], 1):
        L.append(f"   4.{i} {l['as_written']}  ->  real domain: {l['real_domain']}  [{l['verdict'].upper()}]")
        for x in l["issues"] + l["notes"]:
            L.append(f"        - {x}")
    if not rep["links"]:
        L.append("   (none)")
    L.append("")
    L.append("5. PHONE NUMBERS IN THE MESSAGE")
    L += [f"   - {n} ({k})" for n, k in rep["phones"]] or ["   (none)"]
    if rep["tricks"]:
        L += ["", "6. DISGUISE TRICKS FOUND", "   " + ", ".join(f"{k} ({v}x)" for k, v in rep["tricks"].items())]
    if d.lost_money or d.notes:
        L += ["", "7. VICTIM'S NOTES"]
        if d.lost_money:
            L.append(f"   Money lost: {d.amount_lost or '-'}   Transaction reference: {d.transaction_ref or '-'}")
        if d.notes:
            L.append(f"   {d.notes}")
    L += ["", "WHERE TO REPORT", *[f"   {i}. {s}" for i, s in enumerate(rep["steps"], 1)], "",
          "SHORT DESCRIPTION FOR COMPLAINT FORMS", "   " + complaint_summary(rep), "",
          "DISCLAIMER: This is an automated analysis by an offline tool, made to support a complaint. It is not a "
          "legal finding. The tool cannot see where a shortened link really leads, and it did not open any link."]
    return "\n".join(L)


# ------------------------------------------------------------------ PDF
def _font() -> str:
    """Register a Unicode font (Devanagari + ₹) if the system has one; fall back to Helvetica."""
    from reportlab import rl_config
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    try:
        import uharfbuzz  # noqa: F401  (enables correct Hindi letter shaping)
        rl_config.shaping = 1
    except Exception:
        pass
    candidates = [
        (Path("C:/Windows/Fonts/Nirmala.ttc"), 0), (Path("C:/Windows/Fonts/Nirmala.ttf"), None),
        (Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"), None),
        (Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"), None),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), None),
    ]
    for path, idx in candidates:
        if path.exists():
            try:
                kw = {"subfontIndex": idx} if idx is not None else {}
                pdfmetrics.registerFont(TTFont("KavachUni", str(path), **kw))
                return "KavachUni"
            except Exception:
                continue
    return "Helvetica"


def pdf_report(rep: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    font = _font()

    def esc(s: str) -> str:
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if font == "Helvetica":
            s = s.replace("₹", "Rs.").encode("latin-1", "replace").decode("latin-1")
        return s

    base = ParagraphStyle("b", fontName=font, fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=base, fontSize=8, leading=10.5, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=base, fontSize=16, leading=20, textColor=colors.HexColor("#b03a2e"))
    h2 = ParagraphStyle("h2", parent=base, fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=3,
                        textColor=colors.HexColor("#1f3b63"))
    mono = ParagraphStyle("m", parent=base, backColor=colors.HexColor("#f4f4f4"), borderPadding=6,
                          borderColor=colors.HexColor("#dddddd"), borderWidth=0.5, leftIndent=4, rightIndent=4)
    d: ReportDetails = rep["details"]
    story = [Paragraph("Scam Message Evidence Report", h1),
             Paragraph(esc(f"Report ID {rep['report_id']} · generated {rep['generated']} · {VERSION}, offline analysis"), small),
             Spacer(1, 6)]
    verdict_color = {"SCAM": "#c0392b", "SUSPICIOUS": "#d68910", "SAFE": "#1e8449"}[rep["verdict"]]
    summary = [["Assessment", Paragraph(f'<font color="{verdict_color}"><b>{rep["verdict"]}</b></font> '
                                        f'({pct(rep["confidence"])} confidence)', base)],
               ["Category", Paragraph(esc(rep["category"]), base)], ["Scam type", Paragraph(esc(rep["family"]), base)],
               ["Channel / sender", Paragraph(esc(f"{d.channel or '-'} / {d.sender or 'not provided'}"), base)],
               ["Received", Paragraph(esc(d.received or "not provided"), base)]]
    t = Table(summary, colWidths=[35 * mm, 135 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                           ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#dddddd")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Paragraph("Original message (exactly as received)", h2),
              Paragraph(esc(rep["message"]).replace("\n", "<br/>"), mono), Spacer(1, 3),
              Paragraph(esc(f"SHA-256 fingerprint: {rep['sha256']}"), small),
              Paragraph("Evidence", h2)]
    for i, e in enumerate(rep["evidence"], 1):
        story.append(Paragraph(f"<b>{i}. {esc(e['title'])}</b> {esc(e['quote'])}", base))
        story.append(Paragraph(esc(e["why"]), small))
        story.append(Spacer(1, 3))
    if rep["links"]:
        story.append(Paragraph("Links in the message (made unclickable; not opened)", h2))
        for l in rep["links"]:
            c = {"dangerous": "#c0392b", "suspicious": "#d68910", "official": "#1e8449"}.get(l["verdict"], "#555555")
            story.append(Paragraph(f"<b>{esc(l['as_written'])}</b> -&gt; real domain <b>{esc(l['real_domain'])}</b> "
                                   f'<font color="{c}">[{l["verdict"].upper()}]</font>', base))
            for x in l["issues"] + l["notes"]:
                story.append(Paragraph("• " + esc(x), small))
            story.append(Spacer(1, 3))
    if rep["phones"]:
        story.append(Paragraph("Phone numbers in the message", h2))
        story.append(Paragraph(esc(", ".join(f"{n} ({k})" for n, k in rep["phones"])), base))
    if d.lost_money or d.notes:
        story.append(Paragraph("Victim's notes", h2))
        if d.lost_money:
            story.append(Paragraph(esc(f"Money lost: {d.amount_lost or '-'} · Transaction reference: {d.transaction_ref or '-'}"), base))
        if d.notes:
            story.append(Paragraph(esc(d.notes), base))
    story.append(Paragraph("Where to report", h2))
    for i, s in enumerate(rep["steps"], 1):
        story.append(Paragraph(esc(f"{i}. {s}"), base))
    story += [Paragraph("Short description for complaint forms", h2), Paragraph(esc(complaint_summary(rep)), base),
              Spacer(1, 10),
              Paragraph("Disclaimer: automated analysis by an offline tool, made to support a complaint; not a legal "
                        "finding. The tool did not open any link and cannot see where a shortened link leads.", small)]
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                      bottomMargin=16 * mm, title="Scam evidence report", author=VERSION).build(story)
    return buf.getvalue()


def filename(rep: dict, ext: str) -> str:
    return re.sub(r"[^\w-]", "_", rep["report_id"]) + "." + ext
