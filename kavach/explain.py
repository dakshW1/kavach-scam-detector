"""Explains why a message looks GENUINE (the other half of explainability).

A scam verdict is explained by red flags. A safe verdict is explained by three things:
  1. what kind of genuine message it looks like (bank alert, OTP, delivery code...) and the genuine signs found
  2. the scam checks it passed: everything Kavach looked for and did NOT find
  3. what to stay careful about anyway, because "looks genuine" is never a guarantee
"""
from __future__ import annotations

# (check id, red-flag rules that would fail it, text when passed)
CHECKS = [
    ("secret", {"asks_secret", "asks_details"}, "Does not ask you for an OTP, PIN, password, card or bank details"),
    ("money", {"fee", "money_demand", "collect_request", "donation_request"}, "Does not ask you to pay, transfer, deposit or approve a request"),
    ("threat", {"threat", "disconnection", "authority", "shame_threat", "pressure_secrecy"}, "No threat to block an account, cut a service or arrest you"),
    ("urgency", {"urgency"}, "No pressure to act within minutes or hours"),
    ("bait", {"prize", "loan_bait", "job_bait", "invest_bait", "money_bait", "refund"}, "No prize, loan, job, investment or refund offer to lure you"),
    ("app", {"remote_app"}, "Does not ask you to install an app or share your screen"),
    ("story", {"family_emergency", "chain_forward", "parcel"}, "No emergency story, chain forward or parcel trap"),
    ("disguise", {"disguised"}, "Written normally – no disguised letters or hidden characters"),
]

# genuine-message type, decided by the good signs found (first match wins)
TYPES = [
    ({"handover_code"}, "a delivery or ride code", "It gives YOU a code to show the delivery agent or driver in person, and asks for nothing else."),
    ({"masked_account", "transaction_ref"}, "a bank transaction alert", "It reports a transaction with a masked account number and a reference, and asks you for nothing."),
    ({"otp_dont_share", "valid_for"}, "a one-time password (OTP) message", "It gives you a code for something you started yourself and warns you not to share it."),
    ({"awareness"}, "a fraud-awareness message", "It warns about fraud and points to official channels without asking you for anything."),
    ({"visit_branch"}, "a service reminder from an organisation", "It sends you to the branch or the official app instead of a link or a phone number."),
    ({"planned_notice"}, "a service or maintenance notice", "It informs you of a scheduled event with a date and time, and asks for nothing."),
    ({"shop_offer"}, "an ordinary shopping offer", "It is a normal discount or reward and asks for no payment or personal details."),
    ({"link_official"}, "a message with an official link", "Its link goes to the organisation's real website."),
    ({"not_you_report"}, "a bank or service alert", "It tells you how to report it through an official helpline if something is wrong."),
]

CAUTION = {
    "handover_code": "Share this code only with the person who is physically delivering to you or driving you – never over a phone call or chat.",
    "masked_account": "If you did not make this transaction, call the number printed on your card or passbook – not a number from any message.",
    "transaction_ref": "Check the amount and reference in your bank's official app before assuming it is correct.",
    "otp_dont_share": "Use this OTP only if YOU just started the login or payment. If anyone calls asking for it, it is a scam.",
    "valid_for": "If you did not request this code, someone may be trying to use your account – do not share it, and change your password.",
    "link_official": "Even with an official link, it is safest to open the official app or type the website yourself.",
    "shop_offer": "Use offers only inside the official app or website; ignore copies of the offer that ask for payment or details.",
    "awareness": "Real awareness messages never ask you to click a link or call a mobile number to 'verify'.",
}
GENERAL = ["Kavach reads the text only. If someone calls or messages you about this, do not share any code, PIN or password.",
           "A genuine-looking message can still be copied by scammers later – always check unexpected requests through official channels."]


def explain_genuine(result) -> dict:
    """Why a message looks genuine. Useful for SAFE results (and as 'what looks normal' for SUSPICIOUS ones)."""
    rules = {f.rule for f in result.flags}
    good = [f for f in result.flags if f.is_good]
    good_ids = {f.rule for f in good}

    kind, kind_why = "an ordinary message", "It does not ask you for money, codes, personal details or urgent action."
    for ids, name, why in TYPES:
        if ids & good_ids:
            kind, kind_why = name, why
            break
    official = [l.official_brand for l in result.links if l.verdict == "official" and l.official_brand]
    if kind == "a message with an official link" and official:
        kind = f"a message from {official[0]} with its official link"
    elif not good and result.brands:
        kind = f"a message mentioning {result.brands[0]}"

    passed = [text for cid, bad, text in CHECKS if not (bad & rules)]
    links = result.links
    if not links:
        passed.append("Contains no links to click")
    elif all(l.verdict == "official" for l in links):
        names = ", ".join(sorted({l.registered for l in links}))
        passed.append(f"Every link goes to an official website ({names})")
    if result.sender_note and "registered business sender" in result.sender_note:
        passed.append("Sent from a registered business sender ID (TRAI format)")

    cautions = [CAUTION[g] for g in [f.rule for f in good] if g in CAUTION]
    cautions = list(dict.fromkeys(cautions))[:2] + GENERAL[: 2 if not cautions else 1]
    summary = f"This looks like {kind}. {kind_why}"
    return {
        "summary": summary,
        "kind": kind,
        "good_signs": [{"label": f.label, "text": f.text, "reason": f.reason} for f in good],
        "passed": passed,
        "n_checks": len(CHECKS) + 1 + (1 if result.sender_note else 0),  # + links check (+ sender check if a sender was given)
        "cautions": cautions,
    }
