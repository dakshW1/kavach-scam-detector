"""Disguise tricks used by the 'Try to fool it' page (the same tricks scammers use)."""
from __future__ import annotations

import random
import re

LEET = {"o": "0", "i": "1", "e": "3", "a": "@", "s": "$"}
HOMO = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "i": "і"}
TRICKS = {
    "leet": "Numbers for letters (L0TT3RY)",
    "spaced": "Spaced letters (K.Y.C)",
    "homoglyph": "Lookalike letters from other alphabets",
    "invisible": "Invisible characters",
}


def disguise(text: str, how: list[str], seed: int = 1) -> str:
    """Disguise about half of the words with the chosen tricks (keys of TRICKS)."""
    how = [h for h in how if h in TRICKS] or ["leet"]
    rng = random.Random(seed)
    words = text.split(" ")
    idx = [i for i, w in enumerate(words) if re.fullmatch(r"[A-Za-z]{3,}[.,!]?", w)]
    rng.shuffle(idx)
    for i in idx[: max(2, len(idx) // 2)]:
        w = words[i]
        t = rng.choice(how)
        if t == "leet":
            w = "".join(LEET.get(c.lower(), c) for c in w)
        elif t == "spaced":
            w = ".".join(w.upper())
        elif t == "homoglyph":
            w = "".join(HOMO.get(c, c) for c in w)
        elif t == "invisible":
            w = "​".join(w)
        words[i] = w
    return " ".join(words)
