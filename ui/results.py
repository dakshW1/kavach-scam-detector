"""Results & privacy page: how well Kavach works (from results/metrics.json) and how to verify it is offline."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from kavach import netguard

ROOT = Path(__file__).resolve().parent.parent


def _pct(x):
    return "–" if x is None else f"{x:.1%}"


def page():
    st.title("📊 Results & privacy")
    path = ROOT / "results" / "metrics.json"
    if not path.exists():
        st.warning("Run `python scripts/evaluate.py` to create the results.")
        return
    m = json.loads(path.read_text(encoding="utf-8"))

    st.markdown("### How well does it work?")
    st.caption("All numbers are on messages the model never saw during training. "
               "**Final test** = 72 hand-written messages written before tuning and never used to improve the model.")
    rows = []
    names = {"final": "Final test (hand-written, untouched)", "challenge": "Challenge set (hand-written)",
             "test": "Held-out templates + UCI messages"}
    for k in ("final", "challenge", "test"):
        s = m[k]
        rows.append({"Test set": names[k], "Messages": s["n"], "Accuracy": _pct(s["accuracy"]),
                     "Scams caught (SCAM or SUSPICIOUS)": _pct(s["caught_scam_or_suspicious"]),
                     "Precision": _pct(s["precision"]), "Recall": _pct(s["recall"]),
                     "Genuine wrongly marked SCAM": _pct(s["safe_marked_scam"]),
                     "Genuine marked SUSPICIOUS": _pct(s["safe_marked_suspicious"]),
                     "Category accuracy": _pct(s.get("category_accuracy")), "ms / message": f"{s['ms_per_message']:.0f}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    a, b = st.columns([1, 1])
    with a:
        st.markdown("#### Can you trust the confidence %?")
        img = ROOT / "results" / "reliability.png"
        if img.exists():
            st.image(str(img))
        cal = m["calibration_all"]
        st.caption(f"Each dot groups messages by the confidence Kavach gave; a dot on the dashed line means "
                   f"'when it says 80%, it is right about 80% of the time'. Expected calibration error "
                   f"{cal['ece']:.3f} (0 = perfect), Brier score {cal['brier']:.3f}.")
    with b:
        st.markdown("#### False alarms on real messages")
        fa = []
        for k in ("final", "challenge", "test"):
            for kind, v in m[k].get("false_alarms_by_kind", {}).items():
                fa.append({"Set": k, "Type": kind.replace("_", " "), "n": v["n"], "marked SCAM": _pct(v["marked_scam"]),
                           "marked SUSPICIOUS": _pct(v["marked_suspicious"])})
        if fa:
            st.dataframe(pd.DataFrame(fa), hide_index=True, width="stretch")
        rob = m.get("robustness", {})
        if rob:
            st.markdown("#### Disguised messages")
            st.markdown(f"Test scams caught: **{_pct(rob['caught_original'])}** as written, "
                        f"**{_pct(rob['caught_disguised'])}** after random disguise tricks ({rob['n']} messages).")
            wc = rob.get("without_cleaner")
            if wc:
                st.markdown(f"Same model **without** the text cleaner: {_pct(wc['caught_original'])} → "
                            f"**{_pct(wc['caught_disguised'])}** on disguised copies.")
        kinds = m["final"].get("caught_by_kind")
        if kinds:
            st.markdown("#### Final test: scams caught by language")
            st.markdown(" · ".join(f"{k}: **{_pct(v['caught'])}** ({v['n']})" for k, v in kinds.items()))

    with st.expander("Where it still goes wrong (final + challenge sets)"):
        for k in ("final", "challenge"):
            for x in m[k].get("mistakes", []):
                st.markdown(f"- `{k}` true **{x['label']}** {('(' + x['category'] + ')') if x['category'] else ''} → "
                            f"said **{x['verdict']}** {('(' + str(x['pred_category']) + ')') if x['pred_category'] else ''}, "
                            f"p={x['p_scam']}: {x['text'][:140]}")

    st.markdown("### 🔒 Privacy: how to verify it is offline")
    ok = netguard.self_test()
    if ok:
        st.success("Live check just now: an outgoing connection to the internet was **refused** by Kavach's network guard.")
    else:
        st.error("Live check: the network guard is not active.")
    st.markdown("""
1. **Turn off Wi-Fi** (or unplug the network) and use the app – every feature except the optional news search works.
2. **Network guard in code:** `kavach/netguard.py` replaces Python's socket functions at start-up; any connection to a
   non-local address raises an error. The sidebar shows how many attempts were blocked.
3. **Automated proof:** `pytest tests/test_privacy.py` analyses messages, writes the diary and builds reports with the
   guard on and asserts that **zero** outgoing connections were made, and that the diary file contains no phone numbers,
   OTPs or clickable links.
4. **Streamlit settings:** `.streamlit/config.toml` turns off usage statistics and makes the app listen only on
   `127.0.0.1`, so other devices on the network cannot open it.
5. **The model is a local 1 MB file** (`models/kavach.joblib`); no cloud AI or API is used.
6. **The only online feature** (news search) is off until you click it, shows the exact words first, sends only the
   scam type and brand name, and talks to a single host.""")
    st.markdown("### Data used")
    st.markdown("""
- **UCI SMS Spam Collection** (Almeida & Hidalgo, CC BY 4.0): 2,500 genuine personal messages and the prize/claim spam
  (as Lottery/Prize scams). Other UCI spam (marketing, ringtones) was left out because it is spam, not fraud.
- **Indian messages generated from hand-written templates** in English, Hinglish and Hindi (banks, OTPs, deliveries,
  bills, chats and 5 scam categories), based on public warnings from RBI, banks, the cyber-crime portal and news reports.
  The train/test split is **by template**, so test messages never share a template with training messages.
- **Two hand-written test sets** (challenge 101, final 72) with different wording, never used for training.""")
    st.markdown("### Limitations")
    st.markdown("""
- Much of the Indian training data is template-generated: real scams are more varied, so real-world accuracy will be
  lower than the held-out template score. The hand-written test sets are the more realistic estimate.
- Text only: no voice calls, images or screenshots.
- A brand-new style of scam may come out as SUSPICIOUS or "Other" – by design, not a crash.
- Kavach cannot see where a shortened link leads (that would require opening it).""")
