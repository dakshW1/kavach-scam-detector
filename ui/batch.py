"""Batch check: many messages at once (one per line, or a CSV with a 'text'/'message' column)."""
from __future__ import annotations

import csv
import io

import pandas as pd
import streamlit as st

from kavach.detector import analyze


def _read(upload) -> list[str]:
    raw = upload.getvalue().decode("utf-8", errors="replace")
    if upload.name.lower().endswith(".csv"):
        rows = list(csv.DictReader(io.StringIO(raw)))
        if rows:
            key = next((k for k in rows[0] if k and k.strip().lower() in ("text", "message", "sms", "body")), None)
            if key:
                return [r[key] for r in rows if (r.get(key) or "").strip()]
        return [ln for ln in raw.splitlines()[1:] if ln.strip()]
    return [ln for ln in raw.splitlines() if ln.strip()]


def page():
    st.title("📋 Batch check")
    st.caption("Check many messages at once – for example an exported SMS backup. Processed on this computer only.")
    up = st.file_uploader("Upload a .txt (one message per line) or .csv (column named 'text' or 'message')",
                          type=["txt", "csv"])
    pasted = st.text_area("…or paste several messages, one per line", height=120)
    msgs = _read(up) if up else [ln for ln in pasted.splitlines() if ln.strip()]
    if not msgs:
        return
    if len(msgs) > 2000:
        st.warning("Only the first 2,000 messages are checked.")
        msgs = msgs[:2000]
    if not st.button(f"Check {len(msgs)} messages", type="primary"):
        return
    rows, bar = [], st.progress(0.0)
    for i, m in enumerate(msgs):
        r = analyze(m)
        rows.append({"verdict": r.verdict, "confidence": round(r.confidence, 3), "category": r.category or "",
                     "top warning signs": "; ".join(f.label for f in r.red_flags[:3]), "message": m})
        bar.progress((i + 1) / len(msgs))
    df = pd.DataFrame(rows)
    a, b, c = st.columns(3)
    a.metric("SCAM", int((df.verdict == "SCAM").sum()))
    b.metric("SUSPICIOUS", int((df.verdict == "SUSPICIOUS").sum()))
    c.metric("SAFE", int((df.verdict == "SAFE").sum()))
    order = {"SCAM": 0, "SUSPICIOUS": 1, "SAFE": 2}
    df = df.sort_values(by="verdict", key=lambda s: s.map(order), kind="stable")
    st.dataframe(df, width="stretch", hide_index=True,
                 column_config={"confidence": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)})
    st.download_button("⬇️ Download results (CSV)", df.to_csv(index=False).encode("utf-8"), "kavach_results.csv", "text/csv")
