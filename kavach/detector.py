"""analyze(message) -> everything the app shows: verdict, category, confidence, highlights, links, advice."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from functools import lru_cache

from .library import FAMILIES, advice, family_for
from .links import LinkFinding
from .model import CATEGORIES, MODEL_PATH, KavachModel
from .normalize import normalize
from .rules import RULE_IDS, Flag, find_flags, flag_vector

SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "good": 3}
# a request for money ("lend me 5k", "send Rs 2000", "paise bhej") – used with the secrecy flag
MONEY_ASK = re.compile(r"\b(lend|borrow|send|transfer|pay|bhej|de do|udhaar|loan)\b.{0,40}(\brs\.?|₹|\b\d+\s?k\b|\b\d{3,}\b|money|paise|paisa|rupees)"
                       r"|(\brs\.?|₹|\b\d+\s?k\b|money|paise|paisa).{0,30}\b(lend|send|transfer|bhej|de do|udhaar)\b", re.I)
STRONG_FAMILIES = {"digital_arrest", "remote_access", "family_emergency", "donation", "upi_collect", "electricity",
                   "parcel_customs", "pension_ppo", "account_takeover", "hoax_forward"}


@dataclass
class Result:
    text: str
    cleaned: str
    tricks: dict
    verdict: str                 # SCAM / SUSPICIOUS / SAFE
    p_scam: float                # calibrated probability that it is a scam
    confidence: float            # how sure we are of the verdict shown (0-1)
    category: str | None
    category_probs: dict
    unfamiliar: bool             # scam that does not closely match any known category
    family: str | None
    flags: list[Flag]
    links: list[LinkFinding]
    brands: list[str]
    top_words: list[tuple[str, float]]
    advice: dict
    sender_note: str | None = None
    safety_net: str | None = None
    ms: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def red_flags(self) -> list[Flag]:
        return [f for f in self.flags if not f.is_good]

    @property
    def good_signs(self) -> list[Flag]:
        return [f for f in self.flags if f.is_good]

    @property
    def family_info(self) -> dict | None:
        return FAMILIES.get(self.family) if self.family else None


@lru_cache(maxsize=1)
def get_model() -> KavachModel:
    return KavachModel.load(MODEL_PATH)


ORG_CLAIM = re.compile(r"\b(bank|customer care|customer service|department|officer|support team|helpdesk|help desk|kyc|"
                       r"executive|government|police|courier|electricity board|verification desk|account|card)\b")


def _sender_check(sender: str, brands: list[str], cleaned: str = "") -> tuple[Flag | None, str | None]:
    s = re.sub(r"[\r\n\t]+", " ", sender).strip()[:60]
    if not s:
        return None, None
    digits = re.sub(r"\D", "", s)
    if re.fullmatch(r"(\+?91)?[6-9]\d{9}", re.sub(r"[\s-]", "", s)):
        claim = brands[0] if brands else (ORG_CLAIM.search(cleaned).group(0) if ORG_CLAIM.search(cleaned) else None)
        if claim:
            who = claim if brands else f"an organisation (it mentions '{claim}')"
            return (Flag("sender_mobile", "Sent from a personal number",
                         f"The message claims to be from {who} but was sent from an ordinary mobile number ({s}). "
                         "Banks and companies send SMS from registered sender IDs like 'AX-SBIINB-S'.", "high"),
                    "Personal mobile number")
        return None, "Personal mobile number"
    if re.fullmatch(r"[A-Z]{2}-[A-Z0-9]{3,9}(-[SPTG])?", s.upper()):
        return (None, "Looks like a registered business sender ID (TRAI format, e.g. 'AX-SBIINB-S'). This is a good "
                      "sign but not proof: always check the content too.")
    if len(digits) > 10:
        return (Flag("sender_international", "International / unusual number",
                     f"The sender ({s}) is not a normal Indian mobile or business sender ID.", "medium"), "Unusual sender")
    return None, None


def analyze(text: str, sender: str = "", model: KavachModel | None = None) -> Result:
    t0 = time.perf_counter()
    model = model or get_model()
    norm = normalize(text)
    flags, links, brands = find_flags(text, norm)
    sflag, sender_note = _sender_check(sender, brands, norm.text)
    if sflag:
        flags.append(sflag)

    import numpy as np
    from scipy import sparse
    v = flag_vector(flags, brands)
    R = sparse.csr_matrix(np.array([[v[r] for r in RULE_IDS]], dtype=float))
    X = model.feats.transform([text], R)
    p = float(model.scam_proba([text], X)[0])
    if sflag and sflag.severity == "high":
        p = max(p, min(0.95, p + 0.25))  # a "bank" message from a personal number is a strong extra signal

    verdict = "SCAM" if p >= model.t_scam else "SAFE" if p < model.t_safe else "SUSPICIOUS"
    safety_net = None
    high = [f for f in flags if f.severity == "high"]
    rule_ids = {f.rule for f in flags}
    if verdict == "SAFE" and len({f.rule for f in high}) >= 2 and not any(f.is_good for f in flags):
        verdict = "SUSPICIOUS"
        safety_net = "The model leaned towards safe, but two or more serious red flags were found, so we ask you to be careful."
    elif verdict == "SAFE" and rule_ids & {"chain_forward", "donation_request"}:
        verdict = "SUSPICIOUS"
        safety_net = ("This looks like a chain forward or a donation appeal. It may not be a bank scam, but do not forward it "
                      "or pay until you have checked it with the organisation directly.")
    elif verdict == "SAFE" and rule_ids & {"asks_secret", "family_emergency", "collect_request", "remote_app", "fee", "link_action"} \
            and not rule_ids & {"otp_dont_share", "handover_code", "awareness"}:
        verdict = "SUSPICIOUS"
        safety_net = "The wording looks ordinary, but it asks for something scammers ask for, so please verify before you act."
    elif verdict == "SAFE" and "pressure_secrecy" in rule_ids and MONEY_ASK.search(norm.text):
        verdict = "SUSPICIOUS"
        safety_net = ("It asks for money and tells you to keep it secret. Even if it seems to come from someone you know, "
                      "call them on their old number before you send anything.")
    if "unreadable_script" in rule_ids and verdict == "SAFE":
        verdict = "SUSPICIOUS"
        safety_net = ("Kavach cannot read most of this message's language, so it cannot call it safe. Ask someone who reads it, "
                      "and never share an OTP or PIN, or pay, because of a message you cannot fully understand.")

    cats = model.category_proba([text], X)[0]
    cat_probs = {c: float(cats[list(model.category.classes_).index(c)]) for c in CATEGORIES}
    n_words = len(norm.text.split())
    category, unfamiliar, family = None, False, None
    if verdict != "SAFE":
        category = max(cat_probs, key=cat_probs.get)
        specific = rule_ids & {"kyc", "prize", "loan_bait", "job_bait", "invest_bait", "fee", "threat", "asks_secret"}
        if cat_probs[category] < model.other_min or (n_words < 8 and not specific):
            unfamiliar = True  # too little evidence to name a category: say so instead of guessing "Lottery"
            category = "Other"
        family = family_for(category, rule_ids, norm.text)
        if unfamiliar and family in ("unknown", None):
            family = "unknown"
        if "unreadable_script" in rule_ids:
            category, unfamiliar, family = "Other", True, "unknown"   # cannot name a scam type in a language we cannot read
        elif family in STRONG_FAMILIES and cat_probs.get(category, 0) < 0.6:
            # the model is unsure of the category, but a rule proved the scam type (e.g. digital arrest): use the type's category
            category, unfamiliar = FAMILIES[family]["category"], False

    conf = p if verdict == "SCAM" else (1 - p) if verdict == "SAFE" else max(p, 1 - p)
    if n_words < 8 and len([f for f in flags if f.severity in ("high", "good")]) == 0:
        conf = min(conf, 0.85)  # a very short message without clear signs cannot support a near-certain verdict
    if "unreadable_script" in rule_ids:
        conf = min(conf, 0.6)   # the model did not understand most of the text
    flags.sort(key=lambda f: (SEV_ORDER.get(f.severity, 9), f.start))
    words = []
    for name, w in model.contributions(X[0]):
        kind, _, tok = name.partition(":")
        if kind == "word" and len(words) < 8:
            words.append((tok, w))
    return Result(text=text, cleaned=norm.text, tricks=norm.tricks, verdict=verdict, p_scam=p, confidence=conf,
                  category=category, category_probs=cat_probs, unfamiliar=unfamiliar, family=family, flags=flags,
                  links=links, brands=brands, top_words=words, advice=advice(family or "unknown", verdict),
                  sender_note=sender_note, safety_net=safety_net, ms=(time.perf_counter() - t0) * 1000)
