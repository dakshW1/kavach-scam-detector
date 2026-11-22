"""Main page: paste a message -> verdict, highlights, links, advice, evidence report, scam guide, online intel."""
from __future__ import annotations

import html

import streamlit as st

from kavach import diary, intel, report
from kavach.detector import analyze
from kavach.library import FAMILIES, RECOVERY_COMMON, REPORT_ONLY
from ui.components import flag_list, highlighted_message, legend, link_cards, verdict_banner

EXAMPLES = {
    "Fake SBI KYC": ("Dear customer, your SBI account will be blocked today. Update your KYC immediately at "
                     "https://onlinesbi.sbi.secure-login.top/kyc or call 9876543210.", "9876543210"),
    "Hinglish bijli scare": ("Aapka bijli connection aaj raat 9:30 baje kat jayega kyunki pichle mahine ka bill update "
                             "nahi hua. Turant officer ko call karein 8123456790", ""),
    "Disguised lottery": ("C0NGR@TS!! Y0u w0n ₹25,00,000 in the K.B.C lucky dr@w. Pay ₹4,999 pr0cessing fee to claim. "
                          "WhatsApp 9123456780", ""),
    "Task job": ("Part time job! Earn Rs 3000 per day by liking YouTube videos from home. Join now t.me/earnfast24", ""),
    "Genuine OTP": ("482913 is your OTP for txn of Rs 2,499 at Amazon. Valid for 10 mins. Do not share it with anyone. -SBI",
                    "AX-SBIINB-S"),
    "Genuine debit alert": ("Rs.500.00 debited from A/c XX1234 on 22-11-26 to VPA swiggy@icici (UPI Ref No 412345678901). "
                            "Not you? Call 18001234567 to block. -HDFC Bank", "VM-HDFCBK-S"),
}


def _set_example(name):
    st.session_state["msg"], st.session_state["sender"] = EXAMPLES[name]
    st.session_state.pop("result", None)


def page():
    st.title("🛡️ Kavach – is this message a scam?")
    st.caption("Paste an SMS or WhatsApp message. Everything is checked **on this computer** – nothing is sent anywhere.")

    with st.container(border=True):
        st.text_area("Message", key="msg", height=130, placeholder="Paste the message here…",
                     label_visibility="collapsed")
        c1, c2, c3 = st.columns([2, 1.2, 1])
        c1.text_input("Sender (optional)", key="sender", placeholder="e.g. AX-SBIINB-S or 98765 43210",
                      help="The number or sender ID the message came from. A bank message from a personal mobile number is a red flag.")
        c2.selectbox("Received on", ["SMS", "WhatsApp", "Email", "Other"], key="channel")
        c3.write("")
        c3.write("")
        go = c3.button("Check message", type="primary", width="stretch")
        st.caption("Try an example:")
        cols = st.columns(len(EXAMPLES))
        for col, name in zip(cols, EXAMPLES):
            col.button(name, on_click=_set_example, args=(name,), width="stretch")

    if go:
        if not st.session_state.get("msg", "").strip():
            st.warning("Paste a message first.")
            return
        res = analyze(st.session_state["msg"], st.session_state.get("sender", ""))
        st.session_state["result"] = res
        st.session_state.pop("intel", None)
        st.session_state["saved_id"] = diary.add(res)
    res = st.session_state.get("result")
    if not res:
        _empty_state()
        return
    show_result(res)


def _empty_state():
    st.markdown("#### What Kavach checks")
    a, b, c = st.columns(3)
    a.markdown("**🔍 Tricks & tactics**  \nOTP requests, threats, urgency, prizes, fees, fake jobs, 'digital arrest'… in English, Hinglish and Hindi.")
    b.markdown("**🔗 Links – without opening them**  \nFake bank domains, lookalikes (hdfcbnak.com), short links, .apk files.")
    c.markdown("**🕵️ Disguised text**  \nUndoes L0TT3RY, K.Y.C, lookalike letters and invisible characters before checking.")


def show_result(res):
    verdict_banner(res)
    if res.safety_net:
        st.info(res.safety_net)
    if st.session_state.get("saved_id"):
        st.caption("📔 Saved to your Scam Diary (masked – no numbers, codes or clickable links).")

    left, right = st.columns([1.35, 1])
    with left:
        st.markdown("##### The message, with suspicious parts marked")
        st.markdown(highlighted_message(res), unsafe_allow_html=True)
        legend()
        if res.cleaned != res.text.lower().strip() and res.tricks:
            with st.expander("🕵️ Disguise tricks found – what Kavach actually read"):
                st.code(res.cleaned, language=None)
                st.write(", ".join(f"**{k}** ×{v}" for k, v in res.tricks.items() if v))
        if res.links:
            st.markdown("##### 🔗 Links (inspected, never opened)")
            link_cards(res)
    with right:
        st.markdown(f"##### Why? ({len(res.red_flags)} warning signs, {len(res.good_signs)} reassuring)")
        if res.flags:
            flag_list(res)
        else:
            st.write("No specific warning signs or reassuring signs were found; the verdict comes from the model's reading of the wording.")
        if res.sender_note:
            st.caption(f"Sender: {res.sender_note}")

    tabs = st.tabs(["✅ What to do", "📄 Report this scam", "📚 How this scam works", "🌐 Is it happening to others?", "🔬 Under the hood"])
    with tabs[0]:
        _what_to_do(res)
    with tabs[1]:
        _report(res)
    with tabs[2]:
        _guide(res)
    with tabs[3]:
        _intel(res)
    with tabs[4]:
        _under_the_hood(res)


def _what_to_do(res):
    if res.verdict == "SAFE":
        st.success("This message looks genuine. Still: never share OTPs, PINs or passwords, and make payments only in official apps.")
        return
    a, b = st.columns(2)
    with a:
        st.markdown("**If you have NOT paid or shared anything**")
        for s in REPORT_ONLY:
            st.markdown(f"- {s}")
    with b:
        st.markdown("**If you already paid, clicked or shared a code**")
        for i, s in enumerate(RECOVERY_COMMON, 1):
            st.markdown(f"{i}. {s}")
    st.markdown("**How to protect yourself from this type**")
    for s in res.advice.get("protect", []):
        st.markdown(f"- {s}")


def _report(res):
    st.markdown("Create an **evidence report** to attach to a complaint (cybercrime.gov.in, your bank, Chakshu). "
                "It is made on this computer, kept in memory, and saved only if you download it.")
    with st.form("report_form"):
        c1, c2, c3 = st.columns(3)
        sender = c1.text_input("Sender number / ID", value=st.session_state.get("sender", ""))
        received = c2.text_input("Received on (date & time)", placeholder="e.g. 23 Nov 2026, 10:15 AM")
        channel = c3.selectbox("Channel", ["SMS", "WhatsApp", "Email", "Other"],
                               index=["SMS", "WhatsApp", "Email", "Other"].index(st.session_state.get("channel", "SMS")))
        lost = st.checkbox("I lost money because of this message")
        c4, c5 = st.columns(2)
        amount = c4.text_input("Amount lost (if any)")
        ref = c5.text_input("Transaction / UPI reference (if any)")
        notes = st.text_area("Anything else (what happened, when you noticed)", height=70)
        made = st.form_submit_button("Create report", type="primary")
    if made:
        det = report.ReportDetails(sender=sender, received=received, channel=channel, lost_money=lost,
                                   amount_lost=amount, transaction_ref=ref, notes=notes)
        st.session_state["report"] = report.build(res, det)
    rep = st.session_state.get("report")
    if rep and rep["sha256"] == report.fingerprint(res.text):
        if rep["details"].lost_money:
            st.error("💸 Money lost: call **1930** now – the first hours matter most. Then file at cybercrime.gov.in with this report.")
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ Download PDF report", report.pdf_report(rep), file_name=report.filename(rep, "pdf"),
                           mime="application/pdf", width="stretch")
        d2.download_button("⬇️ Download text report", report.text_report(rep), file_name=report.filename(rep, "txt"),
                           mime="text/plain", width="stretch")
        st.markdown("**Short description – copy this into the complaint form's 'incident details' box:**")
        st.code(report.complaint_summary(rep), language=None, wrap_lines=True)
        with st.expander("Preview the full report"):
            st.code(report.text_report(rep), language=None, wrap_lines=True)


def _guide(res):
    fam = res.family_info or FAMILIES["unknown"]
    if res.verdict == "SAFE":
        st.info("No scam detected. Browse every scam type in the **Scam Library** page.")
        return
    st.markdown(f"### {fam['icon']} {fam['title']}")
    a, b = st.columns(2)
    with a:
        st.markdown("**How it works**")
        for i, s in enumerate(fam["how"], 1):
            st.markdown(f"{i}. {s}")
        st.markdown("**Warning signs**")
        for s in fam["signs"]:
            st.markdown(f"- {s}")
    with b:
        st.markdown("**Protect yourself**")
        for s in fam["protect"]:
            st.markdown(f"- {s}")
        st.markdown("**If you were tricked – recovery steps**")
        for i, s in enumerate(RECOVERY_COMMON, 1):
            st.markdown(f"{i}. {s}")
    st.caption("From the offline Scam Library – works without internet.")


def _intel(res):
    st.markdown("**Optional.** Search recent news to see if this type of scam is being reported. "
                "This is the **only** feature that uses the internet, and only when you click the button.")
    if res.verdict == "SAFE":
        st.info("Available when a message is marked SCAM or SUSPICIOUS.")
        return
    q = intel.build_query(res)
    st.markdown("Only these words will be sent to the news search (news.google.com):")
    st.code(q, language=None)
    st.caption("❌ Not sent: your message, phone numbers, links, names or anything about you.")
    agree = st.checkbox("I understand – send only these words", key=f"intel_ok_{hash(res.text)}")
    if st.button("🌐 Send this search", disabled=not agree):
        with st.spinner("Searching recent news…"):
            st.session_state["intel"] = intel.search(q)
    r = st.session_state.get("intel")
    if not r:
        return
    if r.error:
        st.warning(r.error)
        return
    if not r.articles:
        st.info("No recent news found for this scam type. That does not mean it is safe.")
        return
    m1, m2, m3 = st.columns(3)
    m1.metric("News reports (last 120 days)", len(r.articles))
    m2.metric("In the last 30 days", r.last_30)
    m3.metric("Cities mentioned", len(r.cities))
    if r.cities:
        st.markdown("**Where it was reported:** " + ", ".join(f"{c} ({n})" for c, n in r.cities))
    if r.amounts:
        st.markdown("**Amounts mentioned in headlines:** " + ", ".join(dict.fromkeys(r.amounts)))
    st.markdown("**Latest reports**")
    for a in r.articles[:8]:
        d = a["date"].strftime("%d %b %Y") if a["date"] else ""
        st.markdown(f"- {html.escape(a['title'])} – *{html.escape(a['source'])}*, {d}")
    st.caption(f"Fetched {r.fetched_at}. Headlines are shown as text (links not opened). Summary made on this computer; "
               "no AI service was used. How the scam works and recovery steps are in the 'How this scam works' tab.")


def _under_the_hood(res):
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Scam probability (calibrated):** {res.p_scam:.3f}")
        st.markdown(f"**Checked in:** {res.ms:.0f} ms, fully offline")
        st.markdown("**Category probabilities**")
        for c, p in sorted(res.category_probs.items(), key=lambda kv: -kv[1]):
            st.progress(min(1.0, p), text=f"{c}: {p:.0%}")
    with b:
        st.markdown("**Words that pushed the model** (from its learned weights)")
        for w, v in res.top_words:
            arrow = "🔺 scam" if v > 0 else "🔻 safe"
            st.markdown(f"- `{w}` {arrow} ({v:+.2f})")
        st.markdown("**Text after cleaning**")
        st.code(res.cleaned, language=None)
