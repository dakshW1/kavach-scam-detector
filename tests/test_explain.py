"""Why-it-looks-genuine explanations for SAFE results."""
from kavach.detector import analyze
from kavach.explain import explain_genuine


def test_bank_alert_is_explained_as_genuine():
    r = analyze("Rs.500.00 debited from A/c XX1234 on 22-11-26 (UPI Ref No 412345678901). Not you? Call 18001234567. -HDFC Bank",
                sender="VM-HDFCBK-S")
    g = explain_genuine(r)
    assert r.verdict == "SAFE" and "bank transaction alert" in g["summary"]
    assert any("OTP, PIN" in p for p in g["passed"]) and any("registered business sender" in p for p in g["passed"])
    assert len(g["passed"]) <= g["n_checks"]
    assert any("number printed on your card" in c for c in g["cautions"])


def test_delivery_code_and_plain_chat():
    assert "delivery or ride code" in explain_genuine(analyze("Share OTP 5521 with the delivery agent at your door. -Zepto"))["summary"]
    g = explain_genuine(analyze("Kal milte hai college me, notes le aana"))
    assert g["domain"] == "chat" and "ordinary personal message" in g["summary"]
    assert any("new number" in p for p in g["passed"]) and not any("KYC" in p for p in g["passed"])


def test_checks_match_the_message_domain():
    bank = explain_genuine(analyze("Rs 900 debited from A/c XX4411. UPI Ref 512300011122. Not you? Call 18001234 -SBI"))
    assert bank["domain"] == "bank" and any("KYC" in p for p in bank["passed"])
    assert not any("chain forward" in p for p in bank["passed"])
    offer = explain_genuine(analyze("You won a 30% off coupon. Use code SAVE30 on your next order."))
    assert offer["domain"] == "offer" and len(offer["passed"]) == offer["n_checks"]


def test_failed_checks_are_not_listed_as_passed():
    g = explain_genuine(analyze("Urgent: your account will be blocked today, share the OTP"))
    assert not any("OTP, PIN" in p for p in g["passed"]) and not any("pressure" in p for p in g["passed"])
