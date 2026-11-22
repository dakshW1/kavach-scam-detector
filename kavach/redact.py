"""Masks private details before anything is saved in the Scam Diary or shared as a family alert.

Kept:    the scam's wording, amounts, brand names (that is the lesson)
Masked:  phone numbers, OTP/codes, account/card/Aadhaar/PAN numbers, UPI IDs, e-mails, names after a greeting
Broken:  links are 'defanged' (hxxp://sbi-kyc[.]xyz) so nobody can tap them by accident
"""
from __future__ import annotations

import re

from .links import URL_RE, defang

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}(?:\.[a-z]{2,})?", re.I)
PATTERNS = [
    ("upi", re.compile(r"\b[\w.\-]{2,}@[a-z]{3,}\b", re.I), "[upi-id]"),
    ("pan", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[PAN]"),
    ("card", re.compile(r"\b(?:\d[\s-]?){13,19}\b"), "[card/account no.]"),
    ("aadhaar", re.compile(r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b"), "[aadhaar]"),
    ("masked_acct", re.compile(r"(?i)\b(x{1,}|\*{2,})\d{3,4}\b"), "XX****"),
]
PHONE = re.compile(r"(?<![\w*])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
CODE = re.compile(r"(?<![\w₹.,])\d{4,8}(?![\w,.]?\d)")
GREETING_NAME = re.compile(r"(?i)\b(dear|hi|hello|hey|namaste)\s+(?!customer|user|sir|madam|consumer|winner|grahak|member)([A-Z][a-z]+)")


def _mask_phone(m: re.Match) -> str:
    d = re.sub(r"\D", "", m.group())[-10:]
    return d[:2] + "X" * (len(d) - 4) + d[-2:]


def redact(text: str) -> str:
    out = EMAIL.sub("[email]", text)          # e-mails before links ("gmail.com" is not a link)
    links: list[str] = []

    def keep_link(m: re.Match) -> str:
        links.append(defang(m.group()))
        return f"\x00{len(links) - 1}\x00"

    out = URL_RE.sub(keep_link, out)
    for _, rx, rep in PATTERNS:
        out = rx.sub(rep, out)
    out = PHONE.sub(_mask_phone, out)
    out = CODE.sub("[code]", out)              # OTPs and short codes (amounts like 4,999 are kept)
    out = GREETING_NAME.sub(lambda m: f"{m.group(1)} [name]", out)
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], out)
