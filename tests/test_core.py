"""Behaviour tests for the cleaner, rules, link inspector, detector and report."""
import pytest

from kavach import report
from kavach.detector import analyze
from kavach.links import find_links
from kavach.normalize import normalize
from kavach.redact import redact
from kavach.rules import find_flags


# ---------------- text cleaner
@pytest.mark.parametrize("raw,clean", [
    ("L0TT3RY w1nn3r", "lottery winner"),
    ("Update your K.Y.C now", "update your kyc now"),
    ("Yоur SВI ассount", "your sbi account"),          # Cyrillic lookalikes
    ("bl​ocked", "blocked"),                        # zero-width space
    ("Rs.500 debited from XX1234 at 10am", "rs.500 debited from xx1234 at 10am"),  # numbers untouched
])
def test_normalize(raw, clean):
    assert normalize(raw).text == clean


def test_highlight_spans_map_back_to_the_original():
    text = "Your K.Y.C is pending"
    n = normalize(text)
    i = n.text.index("kyc")
    a, b = n.span_to_original(i, i + 3)
    assert text[a:b] == "K.Y.C"


# ---------------- link inspector
@pytest.mark.parametrize("text,verdict", [
    ("Update at http://sbi-kyc-update.xyz", "dangerous"),
    ("Login at https://onlinesbi.sbi.secure-login.top", "dangerous"),
    ("Visit www.hdfcbnak.com", "dangerous"),
    ("Click bit.ly/3xYz", "suspicious"),
    ("Track https://amzn.in/d/abc", "official"),
    ("Login onlinesbi.sbi", "official"),
    ("Pay at http://10.0.0.1/pay", "dangerous"),
])
def test_links(text, verdict):
    (f,) = find_links(text, ["SBI"] if "sbi" in text.lower() else [])
    assert f.verdict == verdict


def test_amount_is_not_a_link():
    assert find_links("Rs.500.00 debited. Avl bal Rs.1200.50") == []


# ---------------- rules
def rules(text):
    return {f.rule for f in find_flags(text)[0]}


def test_otp_request_vs_genuine_otp():
    assert "asks_secret" in rules("Please share the OTP you received with our executive")
    genuine = rules("482913 is your OTP. Do not share it with anyone. -SBI")
    assert "asks_secret" not in genuine and "otp_dont_share" in genuine


def test_negation_turns_advice_into_a_good_sign():
    assert "remote_app" not in rules("Police advisory: never install screen sharing apps")
    assert "fee" not in rules("Do not pay extra to the delivery person")


def test_hinglish_and_hindi():
    assert {"threat", "disconnection"} <= rules("Aapka bijli connection aaj raat 9:30 baje kat jayega")
    assert "asks_secret" in rules("अनब्लॉक करने के लिए अपना ओटीपी हमें भेजें")


def test_family_emergency_needs_story_and_money():
    assert "family_emergency" in rules("Hi Dad, I lost my phone. Can you send 8000 to this UPI?")
    assert "family_emergency" not in rules("Bhai mera naya number save kar le")


# ---------------- detector
@pytest.mark.parametrize("text,verdict,category", [
    ("Congratulations! You won Rs 25 lakh in KBC lottery. Pay Rs 4999 processing fee to claim. Call 9123456789",
     "SCAM", "Lottery/Prize"),
    ("Instant personal loan of Rs 5 lakh approved, no documents, no CIBIL. Pay Rs 999 file charge.", "SCAM", "Loan/Credit"),
    ("Part time job! Earn Rs 3000 per day by liking YouTube videos. Join t.me/earnfast", "SCAM", "Job/Investment"),
    ("482913 is your OTP for txn of Rs 2,499 at Amazon. Valid for 10 mins. Do not share it with anyone. -SBI", "SAFE", None),
    ("Rs.500.00 debited from A/c XX1234 on 22-11-26 to VPA swiggy@icici (UPI Ref No 412345678901). Not you? Call 18001234567",
     "SAFE", None),
])
def test_detector(text, verdict, category):
    r = analyze(text)
    assert r.verdict == verdict
    assert r.category == category
    assert 0.5 <= r.confidence <= 1


def test_disguised_scam_is_still_caught():
    assert analyze("C0NGR@TS!! Y0u w0n ₹25,00,000 in K.B.C lucky dr@w. P@y ₹4,999 fee").verdict != "SAFE"


def test_personal_sender_raises_suspicion_for_bank_message():
    r = analyze("SBI: your account needs verification, call us", sender="9876543210")
    assert any(f.rule == "sender_mobile" for f in r.flags)


# ---------------- privacy helpers and report
def test_redact_masks_private_details():
    out = redact("Dear Rahul, OTP 482913, call 9876543210, pay rahul9@ybl, card 4111 1111 1111 1111, http://x.xyz")
    for s in ("Rahul", "482913", "9876543210", "rahul9@ybl", "4111"):
        assert s not in out
    assert "hxxp://x[.]xyz" in out


def test_report_contains_evidence_and_fingerprint():
    msg = "Dear customer, your SBI account will be blocked. Update KYC at http://sbi-kyc-update.xyz"
    rep = report.build(analyze(msg), report.ReportDetails(sender="9876543210", lost_money=True, amount_lost="Rs 5,000"))
    txt = report.text_report(rep)
    assert report.fingerprint(msg) in txt and "1930" in txt and "NOT an official SBI domain" in txt
    assert report.pdf_report(rep)[:4] == b"%PDF"
    assert "Rs 5,000" in report.complaint_summary(rep)
