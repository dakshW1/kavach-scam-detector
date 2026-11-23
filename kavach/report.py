"""Evidence report: turns an analysis into a document the user can attach to a complaint.

Two outputs, both made on this computer:
  * plain text  - a short "incident description" to paste into cybercrime.gov.in, plus the full report
  * PDF         - the same content, laid out for printing or attaching

What investigators need first is the MONEY TRAIL (where the money went or was asked to go): UPI IDs,
bank account + IFSC, phone numbers, links, amount, transaction reference (UTR) and time. Kavach pulls
these out of the message automatically and puts them in their own section.

The report contains the original message (the authorities need it). It is created only when the user
asks, kept in memory, and saved only where the user chooses; it is never stored by the app.
"""
from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass, fields
from datetime import datetime
from pathlib import Path

from .links import OFFICIAL, defang, phone_numbers

VERSION = "Kavach 2.0"
BANKS = {"SBI", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Bank", "PNB", "Bank of Baroda", "Canara Bank",
         "Union Bank", "Yes Bank", "IndusInd Bank", "Paytm", "PhonePe", "Google Pay", "CRED"}


@dataclass
class ReportDetails:
    sender: str = ""
    received: str = ""          # when the message arrived, as the user typed it
    channel: str = "SMS"        # SMS / WhatsApp / Email / Call / Other
    lost_money: bool = False
    amount_lost: str = ""
    transaction_ref: str = ""   # UTR / RRN / UPI reference of the victim's payment
    debit_time: str = ""        # when the money left the account
    victim_bank: str = ""       # the bank / app the victim paid from
    beneficiary: str = ""       # UPI ID / account the victim paid to, if known
    customer: str = ""          # filled in by a bank / police officer helping a customer (optional)
    customer_account: str = ""  # last digits only
    officer: str = ""           # officer name and branch / station (optional)
    notes: str = ""

    def __post_init__(self):
        # typed-in fields must not be able to forge new lines or sections in the report
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, str):
                limit = 2000 if f.name == "notes" else 120
                v = re.sub(r"[\r\n\t\x00-\x1f]+", " ", v).strip()[:limit]
                setattr(self, f.name, v)
        if re.fullmatch(r"[\d,]+(\.\d{1,2})?", self.amount_lost or ""):
            self.amount_lost = "Rs " + self.amount_lost   # "4500" -> "Rs 4500"


def pct(p: float) -> str:
    """Confidence as text; never claims 100%."""
    return ">99%" if p >= 0.995 else "<1%" if p < 0.005 else f"{p:.0%}"


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ money trail
UPI_RE = re.compile(r"\b[\w.\-]{2,}@(?:[a-z]{2,}bank|ok[a-z]+|ybl|ibl|axl|apl|paytm|upi|icici|sbi|hdfc|kotak|yesbank|"
                    r"airtel|jio|fbl|abfspay|freecharge|pingpay|[a-z]{3,})\b", re.I)
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
ACCOUNT_RE = re.compile(r"(?i)(?:a/?c|acct|account)(?:\s*(?:no\.?|number|num))?[\s:.#-]*(\d[\d\s-]{7,20}\d)")
AMOUNT_RE = re.compile(r"(?i)(?:rs\.?|inr|₹)\s?\d[\d,]*(?:\.\d{1,2})?(?:\s?(?:lakh|lac|crore|cr))?|\b\d+\s?(?:lakh|lac|crore)\b")


def money_trail(text: str, links: list) -> dict:
    """Everything in the message that tells investigators where money was asked to go or whom to trace."""
    emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", text, re.I))
    upis = [u for u in dict.fromkeys(UPI_RE.findall(text)) if not any(u in e for e in emails)]
    accounts = []
    for m in ACCOUNT_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(1))
        if 9 <= len(digits) <= 18:
            accounts.append(digits)
    phones = [(n, k) for _, _, n, k in phone_numbers(text)]
    return {
        "upi_ids": upis,
        "accounts": list(dict.fromkeys(accounts)),
        "ifsc": list(dict.fromkeys(IFSC_RE.findall(text))),
        "phones": list(dict.fromkeys(phones)),
        "emails": sorted(emails),
        "amounts": list(dict.fromkeys(a.strip() for a in AMOUNT_RE.findall(text)))[:5],
        "links": [(defang(l.url), l.registered.replace(".", "[.]"), l.verdict) for l in links],
    }


def scam_name(result) -> str:
    fam = (result.family_info or {}).get("title")
    if fam and result.family != "unknown":
        return fam
    if result.category and result.category != "Other":
        return f"{result.category} fraud"
    return "fraud / phishing"


def where_to_report(result, details: ReportDetails) -> list[str]:
    steps = []
    if result.family == "digital_arrest":
        steps.append("If you are on a call or video call with them right now: hang up. There is no 'digital arrest' in "
                     "Indian law. Call 1930 or 112 immediately.")
    if details.lost_money:
        steps.append("URGENT – money was lost: call 1930 (National Cyber Crime Helpline) right away. Reporting in the first "
                     "hours (the 'golden hour') gives the best chance of the money being frozen.")
        steps.append("File a complaint at https://cybercrime.gov.in -> 'Report Cyber Crime' -> 'Financial Fraud'. "
                     "Give the amount, the transaction reference (UTR) and the beneficiary UPI ID / account from this report.")
        steps.append("Call your bank on the number printed on your card or passbook and ask them to block cards, UPI and "
                     "net banking and to raise a fraud dispute for the transaction.")
    else:
        steps.append("Report the message on Sanchar Saathi -> Chakshu (https://sancharsaathi.gov.in), which is meant for "
                     "suspected fraud calls, SMS and WhatsApp messages.")
        steps.append("You can also report it at https://cybercrime.gov.in, or call 1930 if you paid or shared anything.")
    named = [b for b in result.brands if b in OFFICIAL]
    if named:
        b = named[0]
        if b in BANKS:
            steps.append(f"Inform {b} through its official website ({OFFICIAL[b][0]}) or the number on your card, so it "
                         "can act on phishing that uses its name.")
        else:
            steps.append(f"You can tell {b} about the misuse of its name through its official website ({OFFICIAL[b][0]}).")
    steps.append("Do NOT delete the original message or the caller's number: investigators may need them on your phone. "
                 "Take screenshots, then block the sender.")
    steps.append("For unwanted promotional (not fraud) SMS, use 1909 or your operator's DND service instead.")
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
    links = [{"as_written": defang(lf.url), "real_domain": lf.registered.replace(".", "[.]"), "verdict": lf.verdict,
              "issues": lf.issues, "notes": lf.notes} for lf in result.links]
    return {
        "generated": now.strftime("%d %b %Y, %I:%M %p"),
        "report_id": f"KV-{now.strftime('%Y%m%d-%H%M%S')}-{fingerprint(result.text)[:6].upper()}",
        "verdict": result.verdict, "confidence": result.confidence, "p_scam": result.p_scam,
        "category": result.category or "-", "family": scam_name(result),
        "message": result.text, "sha256": fingerprint(result.text), "details": details,
        "evidence": evidence, "links": links, "trail": money_trail(result.text, result.links), "brands": result.brands,
        "good_signs": [f.label for f in result.good_signs], "tricks": {k: v for k, v in result.tricks.items() if v},
        "steps": where_to_report(result, details),
    }


def _trail_lines(rep: dict) -> list[str]:
    t, d = rep["trail"], rep["details"]
    out = []
    if d.lost_money:
        out.append(f"Amount lost: {d.amount_lost or 'not given'}")
        out.append(f"Transaction reference (UTR / UPI ref): {d.transaction_ref or 'not given'}")
        out.append(f"Debited at: {d.debit_time or 'not given'}   From bank/app: {d.victim_bank or 'not given'}")
        if d.beneficiary:
            out.append(f"Paid to (as given by victim): {d.beneficiary}")
    if t["upi_ids"]:
        out.append("UPI ID(s) in the message: " + ", ".join(t["upi_ids"]))
    if t["accounts"]:
        out.append("Bank account number(s) in the message: " + ", ".join(t["accounts"]))
    if t["ifsc"]:
        out.append("IFSC code(s) in the message: " + ", ".join(t["ifsc"]))
    if t["phones"]:
        out.append("Phone number(s) in the message: " + ", ".join(f"{n} ({k})" for n, k in t["phones"]))
    if t["emails"]:
        out.append("E-mail address(es) in the message: " + ", ".join(t["emails"]))
    if t["amounts"]:
        out.append("Amounts mentioned in the message: " + ", ".join(t["amounts"]))
    if t["links"]:
        out.append("Links (made unclickable – do not open): " + ", ".join(f"{a} [{v}]" for a, _, v in t["links"]))
    return out or ["No UPI ID, account, phone number or link found in the message."]


def complaint_summary(rep: dict) -> str:
    """A short paragraph for the 'incident details' box of a complaint form. Money facts come first."""
    d: ReportDetails = rep["details"]
    t = rep["trail"]
    parts = []
    if d.lost_money:
        money = f"I lost {d.amount_lost or 'money (amount to be confirmed)'}"
        if d.debit_time:
            money += f" on {d.debit_time}"
        if d.victim_bank:
            money += f" from my {d.victim_bank} account"
        if d.transaction_ref:
            money += f", transaction reference (UTR) {d.transaction_ref}"
        if d.beneficiary:
            money += f", paid to {d.beneficiary}"
        parts.append(money + ".")
    parts.append(f"The fraud started with a suspected '{rep['family']}' message"
                 + (f" received on {d.channel}" if d.channel else "") + (f" from {d.sender}" if d.sender else "")
                 + (f" on {d.received}" if d.received else "") + ".")
    if rep["brands"]:
        parts.append(f"The message pretends to be from {', '.join(rep['brands'][:3])}.")
    if t["upi_ids"] or t["accounts"]:
        parts.append("It gives these payment details: " + ", ".join(t["upi_ids"] + t["accounts"] + t["ifsc"]) + ".")
    mobiles = [n for n, k in t["phones"] if k in ("mobile", "international")]
    if mobiles:
        parts.append("Contact number(s) given in the message: " + ", ".join(mobiles) + ".")
    bad_links = [l for l in rep["links"] if l["verdict"] in ("dangerous", "suspicious")]
    if bad_links:
        parts.append("It contains the link(s) " + ", ".join(l["as_written"] for l in bad_links)
                     + ", which are not official websites of the organisation named.")
    tactics = [e["title"] for e in rep["evidence"] if e["severity"] in ("high", "medium")]
    if tactics:
        parts.append("Warning signs: " + "; ".join(dict.fromkeys(tactics)) + ".")
    if d.customer or d.officer:
        parts.append("Reported" + (f" by {d.customer}" if d.customer else "")
                     + (f" (account ending {d.customer_account})" if d.customer_account else "")
                     + (f", assisted by {d.officer}" if d.officer else "") + ".")
    if not d.lost_money:
        parts.append("I did not make any payment or share any codes.")
    parts.append(f'Message text: "{rep["message"]}"')
    return " ".join(parts)


def text_report(rep: dict) -> str:
    d: ReportDetails = rep["details"]
    L = ["SCAM MESSAGE EVIDENCE REPORT", "=" * 60, f"Generated: {rep['generated']}    Tool: {VERSION} (offline)", ""]
    sections = []
    who = []
    if d.customer:
        who.append(f"Customer   : {d.customer}" + (f" (account ending {d.customer_account})" if d.customer_account else ""))
    if d.officer:
        who.append(f"Assisted by: {d.officer}")
    sections.append(("SUMMARY", who + [f"Assessment : {rep['verdict']} ({pct(rep['confidence'])} confidence)",
                                 f"Scam type  : {rep['family']}", f"Category   : {rep['category']}"]))
    msg = [f"Channel    : {d.channel or '-'}", f"Sender     : {d.sender or '(not provided)'}",
           f"Received   : {d.received or '(not provided)'}", "Original message (exactly as received):"]
    msg += ["  | " + ln for ln in rep["message"].splitlines() or [""]]
    sections.append(("MESSAGE", msg))
    sections.append(("MONEY TRAIL – details to trace", _trail_lines(rep)))
    ev = []
    for i, e in enumerate(rep["evidence"], 1):
        ev.append(f"{i}. {e['title']} {e['quote']}")
        ev.append(f"   {e['why']}")
    sections.append(("WARNING SIGNS", ev or ["(no text-based warning signs; see links)"]))
    lk = []
    for i, l in enumerate(rep["links"], 1):
        lk.append(f"{i}. {l['as_written']} -> real website: {l['real_domain']} [{l['verdict'].upper()}]")
        lk += [f"   - {x}" for x in l["issues"] + l["notes"]]
    if lk:
        sections.append(("LINKS (made unclickable; NOT opened by the tool)", lk))
    if rep["tricks"]:
        sections.append(("DISGUISE TRICKS FOUND", [", ".join(f"{k} ({v}x)" for k, v in rep["tricks"].items())]))
    if d.notes:
        sections.append(("VICTIM'S NOTES", [d.notes]))
    sections.append(("WHERE TO REPORT", [f"{i}. {s}" for i, s in enumerate(rep["steps"], 1)]))
    sections.append(("SHORT DESCRIPTION FOR COMPLAINT FORMS", [complaint_summary(rep)]))
    for n, (title, lines) in enumerate(sections, 1):
        L.append(f"{n}. {title}")
        L += ["   " + ln for ln in lines]
        L.append("")
    L += ["-" * 60,
          "This is an automated analysis by an offline tool, made to support a complaint. It is not a legal finding. "
          "The tool did not open any link and cannot see where a shortened link leads.",
          f"Reference code: {rep['report_id']} · SHA-256 of the message text: {rep['sha256']} "
          "(lets anyone check later that the message was not changed)."]
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
    h1 = ParagraphStyle("h1", parent=base, fontSize=16, leading=20, textColor=colors.HexColor("#9a2e3a"))
    h2 = ParagraphStyle("h2", parent=base, fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=3,
                        textColor=colors.HexColor("#1f3b63"))
    box = ParagraphStyle("m", parent=base, backColor=colors.HexColor("#f4f4f4"), borderPadding=6,
                         borderColor=colors.HexColor("#dddddd"), borderWidth=0.5, leftIndent=4, rightIndent=4)
    trail_box = ParagraphStyle("t", parent=box, backColor=colors.HexColor("#fff6e5"), borderColor=colors.HexColor("#e2c48a"))
    d: ReportDetails = rep["details"]
    story = [Paragraph("Scam Message Evidence Report", h1),
             Paragraph(esc(f"Generated {rep['generated']} · {VERSION}, offline analysis"), small), Spacer(1, 6)]
    verdict_color = {"SCAM": "#9a2e3a", "SUSPICIOUS": "#a8771e", "SAFE": "#2f6b4f"}[rep["verdict"]]
    summary = [["Assessment", Paragraph(f'<font color="{verdict_color}"><b>{rep["verdict"]}</b></font> '
                                        f'({pct(rep["confidence"])} confidence)', base)],
               ["Scam type", Paragraph(esc(rep["family"]), base)],
               ["Channel / sender", Paragraph(esc(f"{d.channel or '-'} / {d.sender or 'not provided'}"), base)],
               ["Received", Paragraph(esc(d.received or "not provided"), base)]]
    t = Table(summary, colWidths=[35 * mm, 135 * mm])
    t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), font), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                           ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
                           ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#dddddd")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Paragraph("Original message (exactly as received)", h2),
              Paragraph(esc(rep["message"]).replace("\n", "<br/>"), box),
              Paragraph("Money trail – details to trace", h2),
              Paragraph("<br/>".join(esc(x) for x in _trail_lines(rep)), trail_box),
              Paragraph("Warning signs", h2)]
    for i, e in enumerate(rep["evidence"], 1):
        story.append(Paragraph(f"<b>{i}. {esc(e['title'])}</b> {esc(e['quote'])}", base))
        story.append(Paragraph(esc(e["why"]), small))
        story.append(Spacer(1, 3))
    if rep["links"]:
        story.append(Paragraph("Links in the message (made unclickable; not opened)", h2))
        for l in rep["links"]:
            c = {"dangerous": "#9a2e3a", "suspicious": "#a8771e", "official": "#2f6b4f"}.get(l["verdict"], "#555555")
            story.append(Paragraph(f"<b>{esc(l['as_written'])}</b> -&gt; real website <b>{esc(l['real_domain'])}</b> "
                                   f'<font color="{c}">[{l["verdict"].upper()}]</font>', base))
            for x in l["issues"] + l["notes"]:
                story.append(Paragraph("• " + esc(x), small))
            story.append(Spacer(1, 3))
    if d.notes:
        story += [Paragraph("Victim's notes", h2), Paragraph(esc(d.notes), base)]
    story.append(Paragraph("Where to report", h2))
    for i, s in enumerate(rep["steps"], 1):
        story.append(Paragraph(esc(f"{i}. {s}"), base))
    story += [Paragraph("Short description for complaint forms", h2), Paragraph(esc(complaint_summary(rep)), base),
              Spacer(1, 12),
              Paragraph("Automated analysis by an offline tool, made to support a complaint; not a legal finding. The tool "
                        "did not open any link and cannot see where a shortened link leads.", small),
              Paragraph(esc(f"Reference code {rep['report_id']} · SHA-256 of the message text: {rep['sha256']}"), small)]
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm,
                      bottomMargin=16 * mm, title="Scam evidence report", author=VERSION).build(story)
    return buf.getvalue()


def filename(rep: dict, ext: str) -> str:
    return re.sub(r"[^\w-]", "_", rep["report_id"]) + "." + ext


def slip_text(rep: dict) -> str:
    """One-page customer slip: verdict, 3 reasons, what to do now – for printing at a bank or police desk."""
    d: ReportDetails = rep["details"]
    reasons = [e["title"] for e in rep["evidence"]][:3]
    L = ["KAVACH – SCAM MESSAGE CHECK", "=" * 44,
         f"Date: {rep['generated']}" + (f"    Customer: {d.customer}" if d.customer else ""), "",
         f"RESULT: {rep['verdict']}  –  {rep['family']}", ""]
    if reasons:
        L.append("Why:")
        L += [f"  {i}. {r}" for i, r in enumerate(reasons, 1)]
        L.append("")
    L += ["What to do now:",
          "  - Do NOT click the link, call back, pay or share any OTP / PIN.",
          "  - Lost money? Call 1930 immediately (first hours matter most).",
          "  - Report at cybercrime.gov.in, or Sanchar Saathi -> Chakshu if no money was lost.",
          "  - Keep the original message; do not delete it.", ""]
    if d.officer:
        L.append(f"Checked by: {d.officer}")
    L += ["", "Stamp / signature: ______________________", "",
          f"Ref: {rep['report_id']}  (offline analysis, not a legal finding)"]
    return "\n".join(L)
