"""Scam Diary page: opt-in local history, dashboard, and family alerts."""
from __future__ import annotations

import html

import matplotlib
import streamlit as st

from kavach import diary
from kavach.report import pct

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _bar(counter, title, color="#2a6fdb", horizontal=True):
    items = counter.most_common(8) if hasattr(counter, "most_common") else list(counter.items())
    if not items:
        return None
    labels, vals = zip(*items)
    fig, ax = plt.subplots(figsize=(5, 0.45 * len(items) + 0.9 if horizontal else 2.6), dpi=130)
    if horizontal:
        ax.barh(list(labels)[::-1], list(vals)[::-1], color=color)
        ax.set_xlabel("messages")
    else:
        ax.bar(labels, vals, color=color)
        ax.set_ylabel("messages")
    ax.set_title(title, fontsize=10, loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x" if horizontal else "y", alpha=.25)
    fig.tight_layout()
    return fig


def page():
    st.title("📔 Scam Diary")
    st.caption("An optional history of the scams aimed at you – kept **only on this computer**, with private details masked.")
    cfg = diary.settings()
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        on = c1.toggle("Keep a scam diary on this computer", value=cfg["diary_enabled"],
                       help="Off by default. When on, each SCAM/SUSPICIOUS result is saved in masked form.")
        days = c2.selectbox("Auto-delete entries older than", [0, 7, 30, 90],
                            index=[0, 7, 30, 90].index(cfg.get("auto_delete_days", 0)),
                            format_func=lambda d: "never" if d == 0 else f"{d} days")
        if on != cfg["diary_enabled"] or days != cfg.get("auto_delete_days", 0):
            diary.save_settings({"diary_enabled": on, "auto_delete_days": days})
            st.rerun()
        st.markdown(
            "<div class='kv-muted'><b>Saved:</b> date, verdict, category, warning-sign names, brands, link domains and a "
            "masked snippet. <b>Never saved:</b> the full message, phone numbers, OTPs, account/card numbers, UPI IDs, "
            "names or clickable links. File: <code>local_data/diary.db</code> (never uploaded).</div>",
            unsafe_allow_html=True)

    rows = diary.entries()
    if not rows:
        st.info("Your diary is empty." + ("" if on else " Switch it on above, then check messages on the main page."))
        return

    st_ = diary.stats(rows)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Scam messages logged", st_["total"])
    m2.metric("Marked SCAM", st_["scam"])
    m3.metric("Marked suspicious", st_["suspicious"])
    m4.metric("Most common type", st_["by_category"].most_common(1)[0][0])

    a, b = st.columns(2)
    with a:
        fig = _bar(st_["by_category"], "Scams aimed at you, by type", "#c0392b")
        if fig:
            st.pyplot(fig)
        fig = _bar(st_["by_flag"], "Tricks used on you most", "#d68910")
        if fig:
            st.pyplot(fig)
    with b:
        if st_["by_week"]:
            fig = _bar(st_["by_week"], "Scam messages per week (week starting)", "#2a6fdb", horizontal=False)
            st.pyplot(fig)
        fig = _bar(st_["by_brand"], "Brands / authorities impersonated", "#7d3c98")
        if fig:
            st.pyplot(fig)

    st.markdown("### 👨‍👩‍👧 Warn your family and friends")
    st.caption("Creates a short warning with the scam patterns only – no personal details. Kavach never sends it; you copy or download it and share it yourself.")
    period = st.radio("Include", [7, 30, 3650], horizontal=True,
                      format_func=lambda d: {7: "last 7 days", 30: "last 30 days", 3650: "everything"}[d])
    alert = diary.family_alert(rows, period)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**English**")
        st.code(alert["en"], language=None, wrap_lines=True)
    with c2:
        st.markdown("**हिन्दी**")
        st.code(alert["hi"], language=None, wrap_lines=True)
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇️ Alert card (image)", diary.alert_card_png(alert["en"]), "scam_alert.png", "image/png",
                       width="stretch")
    d2.download_button("⬇️ Alert text (both languages)", alert["en"] + "\n\n" + alert["hi"], "scam_alert.txt",
                       "text/plain", width="stretch")
    with d3.popover("Preview card", width="stretch"):
        st.image(diary.alert_card_png(alert["en"]))

    st.markdown("### Entries")
    for r in rows:
        with st.container(border=True):
            c1, c2 = st.columns([6, 1])
            icon = "🚨" if r["verdict"] == "SCAM" else "⚠️"
            c1.markdown(f"{icon} **{html.escape(r['category'] or 'Other')}** · {r['ts'].replace('T', ' ')} · "
                        f"scam probability {pct(r['confidence'])}")
            c1.markdown(f"<span class='kv-muted'>{html.escape(r['snippet'])}</span>", unsafe_allow_html=True)
            if r["flags"]:
                c1.caption("Signs: " + ", ".join(r["flags"]))
            if c2.button("Delete", key=f"del_{r['id']}"):
                diary.delete(r["id"])
                st.rerun()
    with st.expander("🗑️ Delete everything"):
        sure = st.checkbox("Yes, permanently delete all diary entries from this computer")
        if st.button("Delete all entries", disabled=not sure, type="primary"):
            diary.delete_all()
            st.success("All diary entries deleted.")
            st.rerun()
