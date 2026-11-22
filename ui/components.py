"""Shared UI pieces: CSS, verdict banner, highlighted message, link cards."""
from __future__ import annotations

import html

import streamlit as st

from kavach.report import pct

CSS = """
<style>
:root { --scam:#c0392b; --susp:#d68910; --safe:#1e8449; --ink:#1c2833; --muted:#5d6d7e; }
.block-container { padding-top: 2rem; max-width: 1100px; }
.kv-verdict { border-radius: 14px; padding: 18px 22px; color: white; margin: 6px 0 14px 0; }
.kv-verdict h2 { color: white; margin: 0; font-size: 1.9rem; letter-spacing: .5px; }
.kv-verdict p { margin: 4px 0 0 0; opacity: .95; font-size: 1.02rem; }
.kv-SCAM { background: linear-gradient(135deg,#c0392b,#922b21); }
.kv-SUSPICIOUS { background: linear-gradient(135deg,#e67e22,#b9770e); }
.kv-SAFE { background: linear-gradient(135deg,#239b56,#1d6f42); }
.kv-msg { font-size: 1.08rem; line-height: 2.0; padding: 16px 18px; border: 1px solid #e5e8e8; border-radius: 12px;
          background: #fbfcfc; white-space: pre-wrap; word-break: break-word; color: var(--ink); }
.kv-msg mark { padding: 2px 3px; border-radius: 4px; cursor: help; color: inherit; }
.kv-msg mark.high { background: #f5b7b1; border-bottom: 2px solid var(--scam); }
.kv-msg mark.medium { background: #fad7a0; border-bottom: 2px solid var(--susp); }
.kv-msg mark.low { background: #fcf3cf; border-bottom: 2px dashed #b7950b; }
.kv-msg mark.good { background: #abebc6; border-bottom: 2px solid var(--safe); }
.kv-msg sup { font-size: .68rem; font-weight: 700; color: var(--muted); margin-left: 1px; }
.kv-legend span { display:inline-block; margin-right: 12px; font-size: .82rem; color: var(--muted); }
.kv-legend i { display:inline-block; width: 12px; height: 12px; border-radius: 3px; margin-right: 4px; vertical-align: -1px; }
.kv-flag { border-left: 4px solid #ccc; padding: 6px 12px; margin: 6px 0; background: #fdfefe; border-radius: 0 8px 8px 0; }
.kv-flag.high { border-color: var(--scam); } .kv-flag.medium { border-color: var(--susp); }
.kv-flag.low { border-color: #b7950b; } .kv-flag.good { border-color: var(--safe); }
.kv-flag b { color: var(--ink); } .kv-flag small { color: var(--muted); }
.kv-link { border: 1px solid #e5e8e8; border-radius: 10px; padding: 10px 14px; margin: 8px 0; }
.kv-link code { font-size: .95rem; }
.kv-pill { display:inline-block; padding: 1px 9px; border-radius: 99px; font-size: .75rem; font-weight: 700; color: white; }
.kv-pill.dangerous { background: var(--scam); } .kv-pill.suspicious { background: var(--susp); }
.kv-pill.official { background: var(--safe); } .kv-pill.unknown { background: #7f8c8d; }
.kv-privacy { font-size: .86rem; line-height: 1.6; }
.kv-muted { color: var(--muted); font-size: .9rem; }
</style>
"""

VERDICT_TEXT = {
    "SCAM": ("🚨 SCAM", "This message shows clear signs of fraud. Do not click, call back, pay or share anything."),
    "SUSPICIOUS": ("⚠️ SUSPICIOUS – be careful", "Some warning signs. Verify through an official channel before you act."),
    "SAFE": ("✅ Looks SAFE", "No strong scam signs found. Still never share OTPs or PINs with anyone."),
}


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def verdict_banner(res) -> None:
    title, sub = VERDICT_TEXT[res.verdict]
    cat = ""
    if res.verdict != "SAFE":
        cat = f" · Category: <b>{html.escape(res.category or 'Other')}</b>"
        if res.unfamiliar:
            cat += " (does not closely match a known type)"
    st.markdown(
        f'<div class="kv-verdict kv-{res.verdict}"><h2>{title}</h2>'
        f"<p>Confidence <b>{pct(res.confidence)}</b>{cat}</p><p>{sub}</p></div>",
        unsafe_allow_html=True)


def highlighted_message(res) -> str:
    """The original message with each flagged span marked; numbers point to the reasons list."""
    text = res.text
    spans = []
    for i, f in enumerate(res.flags, 1):
        if f.end > f.start:
            spans.append((f.start, f.end, f.severity, f.reason, i))
    # drop overlaps, keeping the most severe (flags are already sorted by severity)
    chosen = []
    for s in spans:
        if all(s[1] <= c[0] or s[0] >= c[1] for c in chosen):
            chosen.append(s)
    chosen.sort()
    out, pos = [], 0
    for a, b, sev, reason, n in chosen:
        out.append(html.escape(text[pos:a]))
        out.append(f'<mark class="{sev}" title="{html.escape(reason)}">{html.escape(text[a:b])}</mark><sup>{n}</sup>')
        pos = b
    out.append(html.escape(text[pos:]))
    return '<div class="kv-msg">' + "".join(out) + "</div>"


def legend() -> None:
    st.markdown(
        '<div class="kv-legend"><span><i style="background:#f5b7b1"></i>serious red flag</span>'
        '<span><i style="background:#fad7a0"></i>warning sign</span><span><i style="background:#fcf3cf"></i>minor sign</span>'
        '<span><i style="background:#abebc6"></i>reassuring sign</span><span>hover a highlight for the reason</span></div>',
        unsafe_allow_html=True)


def flag_list(res) -> None:
    for i, f in enumerate(res.flags, 1):
        icon = {"high": "🔴", "medium": "🟠", "low": "🟡", "good": "🟢"}[f.severity]
        quote = f' <small>“{html.escape(f.text[:80])}”</small>' if f.text.strip() else ""
        st.markdown(f'<div class="kv-flag {f.severity}">{icon} <b>{i}. {html.escape(f.label)}</b>{quote}<br>'
                    f"<small>{html.escape(f.reason)}</small></div>", unsafe_allow_html=True)


def link_cards(res) -> None:
    for lf in res.links:
        items = "".join(f"<li>{html.escape(x)}</li>" for x in lf.issues + lf.notes)
        st.markdown(
            f'<div class="kv-link"><span class="kv-pill {lf.verdict}">{lf.verdict.upper()}</span> '
            f"<code>{html.escape(lf.defanged)}</code><br>"
            f'<span class="kv-muted">Real website (decided by the end of the address): '
            f"<b>{html.escape(lf.registered)}</b></span><ul>{items}</ul></div>",
            unsafe_allow_html=True)
