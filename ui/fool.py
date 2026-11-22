"""'Try to fool it' page: disguise a scam and watch Kavach still read it."""
from __future__ import annotations

import random
import re

import streamlit as st

from kavach.detector import analyze
from kavach.report import pct
from ui.components import highlighted_message

CHALLENGES = [
    "Your SBI account will be blocked today. Update KYC now at sbi-kyc-update.xyz",
    "Congratulations! You won Rs 25 lakh in the KBC lottery. Pay Rs 5000 processing fee to claim.",
    "Instant loan approved, no documents needed. Pay Rs 999 file charge to receive the money.",
    "Earn Rs 3000 daily by liking YouTube videos. Join our Telegram group.",
]
LEET = {"o": "0", "i": "1", "e": "3", "a": "@", "s": "$"}
HOMO = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "i": "і"}


def disguise(text: str, how: list[str], seed: int) -> str:
    rng = random.Random(seed)
    words = text.split(" ")
    idx = [i for i, w in enumerate(words) if re.fullmatch(r"[A-Za-z]{3,}[.,!]?", w)]
    rng.shuffle(idx)
    for i in idx[: max(2, len(idx) // 2)]:
        w = words[i]
        t = rng.choice(how)
        if t == "Numbers for letters (L0TT3RY)":
            w = "".join(LEET.get(c.lower(), c) for c in w)
        elif t == "Spaced letters (K.Y.C)":
            w = ".".join(w.upper())
        elif t == "Lookalike letters from other alphabets":
            w = "".join(HOMO.get(c, c) for c in w)
        elif t == "Invisible characters":
            w = "​".join(w)
        words[i] = w
    return " ".join(words)


def page():
    st.title("🧪 Try to fool it")
    st.caption("Scammers disguise words so filters miss them. Disguise a scam here and see whether Kavach still catches it.")
    base = st.selectbox("Start from a scam", CHALLENGES + ["(type your own below)"])
    own = st.text_input("Or type your own scam message") if base.startswith("(") else ""
    text = own or (base if not base.startswith("(") else "")
    how = st.multiselect("Disguise tricks", ["Numbers for letters (L0TT3RY)", "Spaced letters (K.Y.C)",
                                             "Lookalike letters from other alphabets", "Invisible characters"],
                         default=["Numbers for letters (L0TT3RY)", "Lookalike letters from other alphabets"])
    seed = st.session_state.setdefault("fool_seed", 1)
    if st.button("🎲 Disguise it differently"):
        st.session_state["fool_seed"] = seed + 1
        seed += 1
    if not text:
        return
    fooled = disguise(text, how, seed) if how else text
    edited = st.text_area("Disguised message (you can edit it further)", fooled, key=f"fooled_{seed}_{hash(text)}_{len(how)}")
    a, b = st.columns(2)
    for col, label, msg in ((a, "Original", text), (b, "Disguised", edited)):
        r = analyze(msg)
        with col:
            color = {"SCAM": "🚨", "SUSPICIOUS": "⚠️", "SAFE": "✅"}[r.verdict]
            st.markdown(f"#### {label}: {color} {r.verdict} ({pct(r.confidence)})")
            st.markdown(highlighted_message(r), unsafe_allow_html=True)
            if label == "Disguised":
                st.markdown("**What Kavach read after cleaning:**")
                st.code(r.cleaned, language=None, wrap_lines=True)
                tricks = {k: v for k, v in r.tricks.items() if v}
                if tricks:
                    st.caption("Undone: " + ", ".join(f"{k} ×{v}" for k, v in tricks.items()))
    st.info("Why it works: before checking, Kavach cleans the text – lookalike letters become normal letters, "
            "numbers inside words become letters, dots between single letters are removed and invisible characters "
            "are deleted. The disguise itself is also a red flag: genuine companies never write like this.")
