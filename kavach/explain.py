"""Explains why a message looks GENUINE (the other half of explainability).

A scam verdict is explained by red flags. A safe verdict is explained by three things:
  1. what kind of genuine message it looks like (bank alert, OTP, delivery code, chat...) and the genuine signs found
  2. the scam checks it passed – only the checks that matter for THAT kind of message: a bank alert is checked for
     OTP requests, KYC links and account-block threats, a delivery message for redelivery fees and "parcel held"
     stories, a personal chat for "new number" emergencies and money requests
  3. what to stay careful about anyway, because "looks genuine" is never a guarantee
"""
from __future__ import annotations

S, D = {"asks_secret"}, {"asks_details"}
MONEY = {"fee", "money_demand", "collect_request"}
MOBILE = {"personal_mobile", "sender_mobile"}

# kind -> list of (red-flag rules that would fail the check, text shown when the check is passed)
DOMAIN_CHECKS = {
    "bank": [
        (S | D, "Does not ask for your OTP, PIN, CVV, card or bank details"),
        ({"kyc"}, "Does not ask you to update KYC through a link or a phone call"),
        ({"threat"}, "Does not threaten to block or freeze your account"),
        (MONEY, "Does not ask you to pay, transfer money or approve a request"),
        ({"urgency"}, "No pressure to act within minutes or hours"),
        ({"remote_app"}, "Does not ask you to install an app or share your screen"),
        (MOBILE, "Gives no personal mobile number to call – only an official helpline, if any"),
    ],
    "otp": [
        (S, "Does not ask you to share, forward or read out the code"),
        (MOBILE, "Gives no mobile number for you to call back"),
        ({"urgency", "threat"}, "No threat or deadline pushing you to hand the code over"),
        ({"remote_app"}, "Does not ask you to install an app"),
    ],
    "delivery": [
        (MONEY, "Does not ask for a redelivery, customs or address-update fee"),
        ({"parcel"}, "No 'parcel held / address incomplete' story"),
        (D, "Does not ask for your bank, card or personal details"),
        ({"authority"}, "No customs or police threat about the parcel"),
    ],
    "offer": [
        (MONEY, "Does not ask you to pay a fee or tax to get the reward"),
        (S | D, "Does not ask for your card, bank or personal details"),
        ({"prize", "money_bait"}, "No big cash prize from a draw you never entered"),
        ({"urgency"}, "No pressure to claim it within minutes"),
    ],
    "notice": [
        ({"disconnection", "threat"}, "No threat to cut the service tonight unless you call or pay"),
        (MONEY, "Does not ask you to pay through a link or to a person"),
        (MOBILE, "Gives no personal mobile number of an 'officer' to call"),
        ({"urgency"}, "No pressure to act within minutes"),
    ],
    "awareness": [
        (S | D, "Does not ask you for any code or personal details"),
        (MONEY, "Does not ask you to pay anything"),
        (MOBILE, "Points to official helplines, not a personal mobile number"),
    ],
    "service": [
        ({"kyc"}, "Does not ask you to update KYC through a link or a call"),
        (S | D, "Does not ask for your OTP, PIN or bank details"),
        (MONEY, "Does not ask you to pay through a link or to a person"),
        ({"threat", "urgency"}, "No threat or deadline"),
    ],
    "chat": [
        ({"family_emergency"}, "No 'new number / lost phone / stuck somewhere' emergency story"),
        ({"money_demand", "collect_request", "donation_request"}, "No urgent request to send money to an account or UPI ID"),
        (S, "Does not ask for a code you received"),
        ({"chain_forward"}, "Not a chain forward asking you to share it with many people"),
        ({"pressure_secrecy"}, "Does not ask you to keep it secret from family"),
    ],
    "general": [
        (S | D, "Does not ask you for an OTP, PIN, password, card or bank details"),
        (MONEY | {"donation_request"}, "Does not ask you to pay, transfer, deposit or approve a request"),
        ({"threat", "disconnection", "authority", "shame_threat", "pressure_secrecy"}, "No threat to block an account, cut a service or arrest you"),
        ({"urgency"}, "No pressure to act within minutes or hours"),
        ({"prize", "loan_bait", "job_bait", "invest_bait", "money_bait", "refund"}, "No prize, loan, job, investment or refund offer to lure you"),
        ({"remote_app"}, "Does not ask you to install an app or share your screen"),
    ],
}
LINK_DOMAINS = {"bank", "otp", "delivery", "offer", "notice", "service", "general", "awareness"}
DISGUISE_DOMAINS = {"bank", "otp", "offer", "service", "general"}

# genuine-message type, decided by the good signs found (first match wins)
TYPES = [
    ({"handover_code"}, "delivery", "a delivery or ride code", "It gives YOU a code to show the delivery agent or driver in person, and asks for nothing else."),
    ({"masked_account", "transaction_ref"}, "bank", "a bank transaction alert", "It reports a transaction with a masked account number and a reference, and asks you for nothing."),
    ({"otp_dont_share", "valid_for"}, "otp", "a one-time password (OTP) message", "It gives you a code for something you started yourself and warns you not to share it."),
    ({"awareness"}, "awareness", "a fraud-awareness message", "It warns about fraud and points to official channels without asking you for anything."),
    ({"visit_branch"}, "service", "a service reminder from an organisation", "It sends you to the branch or the official app instead of a link or a phone number."),
    ({"planned_notice"}, "notice", "a service or maintenance notice", "It informs you of a scheduled event with a date and time, and asks for nothing."),
    ({"shop_offer"}, "offer", "an ordinary shopping offer", "It is a normal discount or reward and asks for no payment or personal details."),
    ({"link_official"}, "general", "a message with an official link", "Its link goes to the organisation's real website."),
    ({"not_you_report"}, "bank", "a bank or service alert", "It tells you how to report it through an official helpline if something is wrong."),
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
CHAT_CAUTION = "If this person later asks for money or a code, call them on the number you already know before doing anything."
GENERAL = ["Kavach reads the text only. If someone calls or messages you about this, do not share any code, PIN or password.",
           "A genuine-looking message can still be copied by scammers later – always check unexpected requests through official channels."]


def explain_genuine(result) -> dict:
    """Why a message looks genuine. Useful for SAFE results (and as 'what looks normal' for SUSPICIOUS ones)."""
    rules = {f.rule for f in result.flags}
    good = [f for f in result.flags if f.is_good]
    good_ids = {f.rule for f in good}

    domain, kind, kind_why = "chat", "an ordinary personal message", "It does not ask you for money, codes, personal details or urgent action."
    for ids, dom, name, why in TYPES:
        if ids & good_ids:
            domain, kind, kind_why = dom, name, why
            break
    official = [l.official_brand for l in result.links if l.verdict == "official" and l.official_brand]
    if kind == "a message with an official link" and official:
        kind = f"a message from {official[0]} with its official link"
    elif not good and (result.brands or result.links):
        domain, kind = "general", (f"a message mentioning {result.brands[0]}" if result.brands else "an ordinary message with a link")

    checks = list(DOMAIN_CHECKS[domain])
    if domain in DISGUISE_DOMAINS:
        checks.append(({"disguised"}, "Written normally – no disguised letters or hidden characters"))
    passed = [text for bad, text in checks if not (bad & rules)]
    n_checks = len(checks)
    links = result.links
    if domain in LINK_DOMAINS or links:
        n_checks += 1
        if not links:
            passed.append("Contains no links to click")
        elif all(l.verdict == "official" for l in links):
            names = ", ".join(sorted({l.registered for l in links}))
            passed.append(f"Every link goes to an official website ({names})")
    if result.sender_note:
        n_checks += 1
        if "registered business sender" in result.sender_note:
            passed.append("Sent from a registered business sender ID (TRAI format)")

    cautions = list(dict.fromkeys(CAUTION[f.rule] for f in good if f.rule in CAUTION))[:2]
    if domain == "chat":
        cautions.append(CHAT_CAUTION)
    cautions += GENERAL[: 2 if not cautions else 1]
    return {
        "summary": f"This looks like {kind}. {kind_why}",
        "kind": kind,
        "domain": domain,
        "good_signs": [{"label": f.label, "text": f.text, "reason": f.reason} for f in good],
        "passed": passed,
        "n_checks": n_checks,
        "cautions": cautions,
    }
