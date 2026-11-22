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


def _sender_check(sender: str, brands: list[str]) -> tuple[Flag | None, str | None]:
    s = sender.strip()
    if not s:
        return None, None
    digits = re.sub(r"\D", "", s)
    if re.fullmatch(r"(\+?91)?[6-9]\d{9}", re.sub(r"[\s-]", "", s)):
        if brands:
            return (Flag("sender_mobile", "Sent from a personal number",
                         f"The message claims to be from {brands[0]} but was sent from an ordinary mobile number ({s}). "
                         "Banks and companies send SMS from registered sender IDs like 'AX-SBIINB'.", "high"),
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
    sflag, sender_note = _sender_check(sender, brands)
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
    if verdict == "SAFE" and len({f.rule for f in high}) >= 2 and not any(f.is_good for f in flags):
        verdict = "SUSPICIOUS"
        safety_net = "The model leaned towards safe, but two or more serious red flags were found, so we ask you to be careful."

    cats = model.category_proba([text], X)[0]
    cat_probs = {c: float(cats[list(model.category.classes_).index(c)]) for c in CATEGORIES}
    category, unfamiliar, family = None, False, None
    if verdict != "SAFE":
        category = max(cat_probs, key=cat_probs.get)
        if cat_probs[category] < model.other_min:
            unfamiliar = True
            category = "Other"
        family = family_for(category, {f.rule for f in flags}, norm.text)
        if unfamiliar:
            family = "unknown"

    conf = p if verdict == "SCAM" else (1 - p) if verdict == "SAFE" else max(p, 1 - p)
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
