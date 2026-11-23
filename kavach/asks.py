""""This message wants you to: ..." – the actions a message asks for, in a few plain words.

Built only from what the detector already found (red-flag and good-sign rules, links, phone numbers, amounts),
so it runs offline in under a millisecond and never invents anything that is not in the message.
"""
from __future__ import annotations

import re

from .links import phone_numbers
from .report import AMOUNT_RE

PAY_WORDS = re.compile(r"\b(pay|paying|payment|fee|charges?|deposit|transfer|send|lend|bhej\w*|jama|donate|advance|clearance)\b", re.I)
SMALL_AMOUNT = re.compile(r"(?i)\b\d+\s?k\b")
APP_NAMES = re.compile(r"(?i)\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid|[\w-]+\.apk)\b")
WHATSAPP = re.compile(r"(?i)whats\s?app")
GROUP = re.compile(r"(?i)\b(add you|join (our |my |the )?(group|channel)|telegram group|whatsapp group)\b")
STOCKS = re.compile(r"(?i)\b(stocks?|trading|shares?|crypto|ipo|returns?|profit)\b")

HI = {
    "share an OTP, PIN or password": "OTP, PIN या पासवर्ड बताना",
    "send your personal or bank details": "अपनी निजी या बैंक जानकारी भेजना",
    "update KYC through the message": "मैसेज से KYC अपडेट करना",
    "approve a UPI request (that takes money out)": "UPI रिक्वेस्ट मंज़ूर करना (इससे पैसा कटता है)",
    "install {app}": "{app} इंस्टॉल करना",
    "install an app": "एक ऐप इंस्टॉल करना",
    "pay {amt}": "{amt} भुगतान करना",
    "pay money": "पैसे भेजना",
    "pay {amt} through the official app or website": "{amt} आधिकारिक ऐप या वेबसाइट से भरना",
    "pay through the official app or website": "आधिकारिक ऐप या वेबसाइट से भुगतान करना",
    "open {site}": "{site} खोलना",
    "open {site} (official site)": "{site} खोलना (आधिकारिक साइट)",
    "WhatsApp {num}": "{num} पर WhatsApp करना",
    "call {num}": "{num} पर कॉल करना",
    "call {num} only if it was not you": "{num} पर कॉल – सिर्फ़ तब जब यह आपने नहीं किया",
    "forward it to others": "इसे दूसरों को फ़ॉरवर्ड करना",
    "keep it secret": "इसे किसी को न बताना",
    "invest for 'sure' returns": "'पक्के' मुनाफ़े के लिए पैसा लगाना",
    "join their group": "उनके ग्रुप से जुड़ना",
    "claim a prize": "इनाम का दावा करना",
    "take an instant loan": "तुरंत लोन लेना",
    "take a paid online task": "पैसे वाला ऑनलाइन टास्क करना",
    "act now ('{t}')": "तुरंत कुछ करना ('{t}')",
    "show the code to the delivery agent in person": "कोड सिर्फ़ सामने खड़े डिलीवरी एजेंट को दिखाना",
    "nothing – it gives you a code for something you started": "कुछ नहीं – यह आपके शुरू किए काम का कोड है",
    "nothing – it only reports a transaction": "कुछ नहीं – यह सिर्फ़ एक लेन-देन की सूचना है",
    "nothing – it only informs you": "कुछ नहीं – यह सिर्फ़ सूचना है",
    "nothing involving money, codes or links": "पैसे, कोड या लिंक से जुड़ा कुछ नहीं",
}


def _t(key: str, lang: str, **kw) -> str:
    return (HI.get(key, key) if lang == "hi" else key).format(**kw)


def _amounts(text: str) -> list[tuple[int, str]]:
    found = [(m.start(), m.group(0).strip()) for m in AMOUNT_RE.finditer(text)]
    found += [(m.start(), "₹" + m.group(0).strip()) for m in SMALL_AMOUNT.finditer(text)]
    return sorted(found)


def _pay_amount(text: str) -> str | None:
    """The amount the message asks you to pay: the one closest to a pay/fee word (not the prize it dangles)."""
    amts, words = _amounts(text), [m.start() for m in PAY_WORDS.finditer(text)]
    if not amts:
        return None
    if not words:
        return amts[0][1] if len(amts) == 1 else None
    return min(amts, key=lambda a: min(abs(a[0] - w) for w in words))[1]


def wants(result, lang: str = "en") -> dict:
    """{'items': [...], 'nothing': bool}. Items are short verb phrases; at most four, most serious first."""
    rules = {f.rule for f in result.flags}
    text = result.text
    t = lambda key, **kw: _t(key, lang, **kw)  # noqa: E731
    items: list[str] = []
    add = lambda s: s not in items and items.append(s)  # noqa: E731
    scammy = result.verdict != "SAFE"

    if "asks_secret" in rules:
        add(t("share an OTP, PIN or password"))
    if "collect_request" in rules:
        add(t("approve a UPI request (that takes money out)"))
    if "remote_app" in rules:
        app = APP_NAMES.search(text)
        add(t("install {app}", app=app.group(0)) if app else t("install an app"))
    if "asks_details" in rules:
        add(t("send your personal or bank details"))
    if "kyc" in rules:
        add(t("update KYC through the message"))

    asks_pay = bool(rules & {"fee", "money_demand", "donation_request"}) or (bool(PAY_WORDS.search(text)) and bool(_amounts(text)))
    if asks_pay:
        amt = _pay_amount(text)
        if scammy:
            add(t("pay {amt}", amt=amt) if amt else t("pay money"))
        elif re.search(r"(?i)\bpay\b", text):
            add(t("pay {amt} through the official app or website", amt=amt) if amt else t("pay through the official app or website"))

    for link in result.links:
        site = re.sub(r"(?i)^https?://(www\.)?", "", link.url).rstrip("/")
        site = site if len(site) <= 42 else site[:40] + "…"
        add(t("open {site} (official site)", site=link.registered) if link.verdict == "official" else t("open {site}", site=site))

    for _, _, num, kind in phone_numbers(text):
        if kind == "tollfree" and "not_you_report" in rules:
            add(t("call {num} only if it was not you", num=num))
        elif scammy or kind == "mobile":
            add(t("WhatsApp {num}", num=num) if WHATSAPP.search(text) else t("call {num}", num=num))

    if scammy:
        if GROUP.search(text):
            add(t("join their group"))
        if "job_bait" in rules and STOCKS.search(text):
            rules = (rules - {"job_bait"}) | {"invest_bait"}   # a "stock tips group" is an investment pitch, not a job
        for rule, key in (("invest_bait", "invest for 'sure' returns"), ("prize", "claim a prize"),
                          ("loan_bait", "take an instant loan"), ("job_bait", "take a paid online task"),
                          ("chain_forward", "forward it to others"), ("pressure_secrecy", "keep it secret")):
            if rule in rules:
                add(t(key))
        urgent = next((f for f in result.flags if f.rule == "urgency" and f.text.strip()), None)
        if urgent and len(items) < 4:
            add(t("act now ('{t}')", t=urgent.text.strip()[:30]))
    elif "handover_code" in rules:
        items.insert(0, t("show the code to the delivery agent in person"))

    items = items[:4]
    if items:
        return {"items": items, "nothing": False}
    # nothing asked: say why, in the words of the message type
    if rules & {"otp_dont_share", "valid_for"}:
        key = "nothing – it gives you a code for something you started"
    elif rules & {"masked_account", "transaction_ref"}:
        key = "nothing – it only reports a transaction"
    elif rules & {"order_update", "planned_notice", "awareness", "event_result"}:
        key = "nothing – it only informs you"
    else:
        key = "nothing involving money, codes or links"
    return {"items": [t(key)], "nothing": True}

