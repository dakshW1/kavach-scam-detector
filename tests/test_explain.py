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
    assert "ordinary message" in g["summary"] and "Contains no links to click" in g["passed"]


def test_failed_checks_are_not_listed_as_passed():
    g = explain_genuine(analyze("Urgent: your account will be blocked today, share the OTP"))
    assert not any("OTP, PIN" in p for p in g["passed"]) and not any("pressure" in p for p in g["passed"])
