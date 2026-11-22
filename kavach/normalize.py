"""Text cleaning ("normalisation") that undoes the tricks scammers use to get past filters.

normalize(text) returns the cleaned text plus a map from every cleaned character back to the
character it came from in the original. The map lets us highlight suspicious words in the
message exactly as the user received it, even after we changed the letters.

Tricks handled:
  * fancy Unicode letters (fullwidth, bold maths letters...)  -> NFKC folding
  * lookalike letters from other alphabets (Cyrillic "а", Greek "ο")  -> Latin letters
  * invisible characters (zero-width space, joiners, soft hyphen)  -> removed
  * digits/symbols inside words ("L0TT3RY", "w!nner", "fr€e")  -> letters
  * letters spaced out or dotted ("K Y C", "K.Y.C", "l-o-t-t-e-r-y")  -> joined
  * repeated letters ("urgentttt")  -> at most two
  * everything lowercased, runs of whitespace collapsed
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

ZERO_WIDTH = {"​", "‌", "‍", "⁠", "﻿", "­", "᠎", "⁡", "⁢", "⁣"}

# Lookalike characters from other alphabets that render (almost) like Latin letters.
HOMOGLYPHS = {
    # Cyrillic
    "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p", "с": "c",
    "т": "t", "у": "y", "х": "x", "ѕ": "s", "і": "i", "ї": "i", "ј": "j", "һ": "h", "ԁ": "d", "ԛ": "q",
    "ԝ": "w", "ɡ": "g", "ո": "n", "ս": "u",
    # Greek
    "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p", "τ": "t",
    "υ": "u", "χ": "x", "ω": "w", "ϲ": "c",
    # Latin variants
    "ı": "i", "ł": "l", "ø": "o", "ß": "ss", "ƅ": "b", "ɑ": "a", "ʀ": "r", "ɪ": "i", "ɴ": "n", "ᴏ": "o",
}

# Symbols that stand in for letters when they sit inside a word ("L0TT3RY", "w!nner", "$BI").
LEET = {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s",
        "!": "i", "|": "l", "€": "e", "£": "l"}

SEPARATORS = " .-_*·•"


@dataclass
class Normalized:
    original: str
    text: str                       # cleaned text
    origin: list[int]               # origin[i] = index in `original` of cleaned char i
    tricks: dict[str, int] = field(default_factory=dict)  # trick name -> how many times it was undone

    def span_to_original(self, start: int, end: int) -> tuple[int, int]:
        """Map a [start, end) span of the cleaned text back onto the original message."""
        if not self.origin or start >= end:
            return 0, 0
        end = min(end, len(self.origin))
        return self.origin[start], self.origin[end - 1] + 1

    @property
    def disguised(self) -> bool:
        return any(self.tricks.get(k) for k in ("lookalike letters", "invisible characters",
                                                "symbols inside words", "spaced-out letters"))


def _is_letter(ch: str) -> bool:
    return ch.isalpha()


def normalize(text: str) -> Normalized:
    tricks: dict[str, int] = {}

    def count(name: str, n: int = 1) -> None:
        tricks[name] = tricks.get(name, 0) + n

    # Pass 1: per-character folding. Each output char remembers its origin index.
    chars: list[str] = []
    origin: list[int] = []
    for i, ch in enumerate(text):
        if ch in ZERO_WIDTH:
            count("invisible characters")
            continue
        folded = unicodedata.normalize("NFKC", ch)
        if folded != ch and not ch.isspace() and folded.strip():
            count("fancy unicode letters")
        for f in folded:
            low = f.lower()
            if low in HOMOGLYPHS:
                count("lookalike letters")
                low = HOMOGLYPHS[low]
            for out in low:
                chars.append(" " if out.isspace() else out)
                origin.append(i)

    # Pass 2: leetspeak inside words. A symbol is replaced only when the "word" around it has
    # at least two real letters and the symbol touches a letter, so "Rs 500" or "9876543210"
    # stay untouched while "l0tt3ry" and "w!nner" are fixed.
    s = "".join(chars)
    out = list(s)
    for m in re.finditer(r"[^\s]+", s):
        word = m.group()
        letters = sum(c.isalpha() for c in word)
        leet = sum(c in LEET for c in word)
        # need real letters to outnumber the symbols, so "XX1234", "10am" and "Rs.500" stay as they are
        if letters < 2 or letters < leet or re.search(r"\d{3,}", word) or re.fullmatch(r"[\d.,:/₹+-]+", word):
            continue
        if re.fullmatch(r"\W*(rs\.?|inr|₹)?[\d.,]+(am|pm|st|nd|rd|th|gb|mb|kb|kg|km|ml|hrs?|mins?|days?|k|l|g|x|cr|lakh|lac)?\W*",
                        word):
            continue  # times, amounts and units such as "10am", "2gb", "rs.500", "5lakh"
        if re.match(r"(https?://|www\.)", word) or re.fullmatch(r"[\w.\-]+@[a-z]{3,}(\.[a-z]{2,})*", word.rstrip(".,!?")):
            continue  # don't rewrite links, e-mail addresses or UPI IDs
        for j, c in enumerate(word):
            if c in LEET:
                prev_l = j > 0 and (word[j - 1].isalpha() or word[j - 1] in LEET and j > 1 and word[j - 2].isalpha())
                next_l = j + 1 < len(word) and word[j + 1].isalpha()
                if c in "!.$" and not (prev_l and next_l) and not (c == "$" and next_l and j == 0):
                    continue  # "hello!" or "$5" are normal
                if prev_l or next_l:
                    out[m.start() + j] = LEET[c]
                    count("symbols inside words")
    s = "".join(out)

    # Pass 3: join spaced-out / dotted single letters: "k y c", "k.y.c", "l-o-t-t-e-r-y".
    keep = [True] * len(s)
    for m in re.finditer(r"(?<![a-z])[a-z](?:[ .\-_*·•][a-z]){2,}(?![a-z])", s):
        seg = m.group()
        if seg.count(".") == len(seg) // 2 and len(seg) <= 5:
            # "u.s." style abbreviations are normal; only count it as a trick for 3+ letters
            pass
        for j, c in enumerate(seg):
            if c in SEPARATORS:
                keep[m.start() + j] = False
        count("spaced-out letters")
    s2, o2 = [], []
    for c, o, k in zip(s, origin, keep):
        if k:
            s2.append(c)
            o2.append(o)

    # Pass 4: squash 3+ repeated letters and runs of spaces.
    s3, o3 = [], []
    for c, o in zip(s2, o2):
        if c == " " and s3 and s3[-1] == " ":
            continue
        if c.isalpha() and len(s3) >= 2 and s3[-1] == c and s3[-2] == c:
            count("stretched letters")
            continue
        s3.append(c)
        o3.append(o)
    # trim
    while s3 and s3[0] == " ":
        s3.pop(0)
        o3.pop(0)
    while s3 and s3[-1] == " ":
        s3.pop()
        o3.pop()
    return Normalized(text, "".join(s3), o3, tricks)


def clean(text: str) -> str:
    """Just the cleaned string (used by the model's vectoriser)."""
    return normalize(text).text
