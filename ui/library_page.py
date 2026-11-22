"""Scam Library page: every scam family, fully offline."""
from __future__ import annotations

import streamlit as st

from kavach.library import FAMILIES, RECOVERY_COMMON, REPORT_ONLY

ORDER = ["KYC/Bank", "Lottery/Prize", "Loan/Credit", "Job/Investment", "Other"]


def page():
    st.title("📚 Scam Library")
    st.caption("How common scams in India work, the warning signs, and what to do. Stored in the app – works with no internet.")
    with st.container(border=True):
        a, b = st.columns(2)
        with a:
            st.markdown("**☎️ Lost money? Act in the golden hour**")
            for i, s in enumerate(RECOVERY_COMMON, 1):
                st.markdown(f"{i}. {s}")
        with b:
            st.markdown("**🛑 Got a scam message but didn't pay?**")
            for s in REPORT_ONLY:
                st.markdown(f"- {s}")
    q = st.text_input("Search the library", placeholder="e.g. electricity, loan, parcel, OTP")
    for cat in ORDER:
        fams = [(k, f) for k, f in FAMILIES.items() if f["category"] == cat and k != "unknown"]
        if q:
            ql = q.lower()
            fams = [(k, f) for k, f in fams if ql in (f["title"] + " ".join(f["how"] + f["signs"] + f["protect"])).lower()]
        if not fams:
            continue
        st.markdown(f"### {cat}")
        for k, f in fams:
            with st.expander(f"{f['icon']} {f['title']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**How it works**")
                    for i, s in enumerate(f["how"], 1):
                        st.markdown(f"{i}. {s}")
                with c2:
                    st.markdown("**Warning signs**")
                    for s in f["signs"]:
                        st.markdown(f"- {s}")
                    st.markdown("**Protect yourself**")
                    for s in f["protect"]:
                        st.markdown(f"- {s}")
    st.caption("Sources: public advice from RBI, the National Cyber Crime Reporting Portal (cybercrime.gov.in), "
               "the Department of Telecommunications (Sanchar Saathi / Chakshu) and bank fraud-awareness pages.")
