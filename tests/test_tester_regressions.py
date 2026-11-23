"""Regression tests for the problems five persona testers found in v1 (see data/tester_set.py).
Each test is one general behaviour, checked with wording that differs from the tester's message."""
import pytest

from kavach.detector import analyze
from kavach.links import find_links, brands_in, phone_numbers
from kavach.normalize import normalize
from kavach.rules import find_flags


def rules(text):
    return {f.rule for f in find_flags(text)[0]}


def good(text):
    return {f.rule for f in find_flags(text)[0] if f.is_good}


# ---- false alarms on genuine messages
@pytest.mark.parametrize("msg", [
    "Dunzo: your order is nearby. Give OTP 6612 to the delivery partner at the door.",
    "Ola: your ride PIN is 3390, tell it to the driver after you board.",
    "Dear UPI user A/C X9911 debited by 120.0 on date 14Feb26 trf to SWIGGY Refno 512398700011. If not u? call 1800111109. -SBI",
])
def test_genuine_otp_and_bank_formats_are_safe(msg):
    assert analyze(msg).verdict == "SAFE"


def test_compact_dates_are_not_disguised_text():
    assert normalize("debited on 23Nov26 and 05Dec15").tricks.get("symbols inside words", 0) == 0
    assert normalize("y0ur acc0unt").text == "your account"          # real leetspeak still decoded


def test_ordinary_amounts_are_not_money_offers():
    assert "money_bait" not in rules("Rs 1,250 debited from A/c XX1234. Not you? Call 18001234")
    assert "money_bait" in rules("You won Rs 25,00,000 in the lucky draw")


def test_shop_offer_and_awareness_are_reassuring():
    assert "prize" not in rules("Congrats! You won a 30% off coupon. Use code SAVE30 on your next order.")
    assert "awareness" in good("Beware of fraudsters asking for OTP. We never call for it. Report at 1930.")


# ---- scams that slipped through
@pytest.mark.parametrize("msg", [
    "Kindly tell me the 4 digit number you got on SMS so I can unblock your card.",
    "Please send me the code that came on your phone, I typed your number by mistake.",
])
def test_code_requests_without_the_word_otp(msg):
    assert "asks_secret" in rules(msg)
    assert analyze(msg).verdict != "SAFE"


def test_do_not_tell_family_is_isolation_not_reassurance():
    f = rules("Stay on the video call and do not tell your family. Transfer Rs 50,000 now.")
    assert "pressure_secrecy" in f and "money_demand" in f and "otp_dont_share" not in f


@pytest.mark.parametrize("url,verdict", [
    ("https://sites.google.com/view/hdfc-points", "dangerous"),
    ("https://kyc-update.blogspot.com", "dangerous"),
    ("https://pan-link.netlify.app", "dangerous"),
])
def test_free_hosted_pages_are_never_official(url, verdict):
    text = f"Your bank account will be blocked. Update at {url}"
    (f,) = find_links(text, brands_in(text))
    assert f.verdict == verdict and f.official_brand is None


def test_friend_form_link_is_only_suspicious():
    (f,) = find_links("Fill this form for the picnic list: https://forms.gle/abc12")
    assert f.verdict == "suspicious"


def test_government_lookalike_domains():
    for host in ("epfo-gov.in", "pmkisan-gov.co", "parivahan.gov.in.fine-pay.top"):
        (f,) = find_links(f"Pay now at https://{host}/x")
        assert f.verdict == "dangerous", host
    (f,) = find_links("Pay at https://echallan.parivahan.gov.in")
    assert f.verdict == "official"


def test_family_emergency_variants_and_shame_threats():
    assert "family_emergency" in rules("Appa my phone got stolen, using a friend's mobile. Send 4000 to this UPI.")
    assert "family_emergency" in rules("Stuck at the airport and lost my wallet, please transfer 7000 to my friend's account")
    assert "shame_threat" in rules("Pay today or we will message all your contacts that you are a defaulter")


def test_chain_forwards_and_donations_are_not_safe():
    assert analyze("Donate Rs 251 for the temple festival to UPI templefund@ybl and share with 11 groups").verdict != "SAFE"
    assert analyze("Forward this to 15 contacts or your account will be charged from Monday. Forwarded as received.").verdict != "SAFE"


def test_short_messages_are_not_near_certain():
    r = analyze("Call me now")
    assert r.confidence <= 0.85


def test_category_follows_a_proven_scam_type():
    r = analyze("This is CBI. You are under digital arrest. Stay on the video call and pay a security deposit of Rs 90,000.")
    assert r.family == "digital_arrest" and r.category == "Other"


def test_international_numbers_are_extracted():
    assert any(k == "international" for *_, k in phone_numbers("WhatsApp our HR on +852 9123 4567"))


def test_sender_newlines_cannot_forge_report_lines():
    from kavach import report
    r = analyze("Your SBI KYC expired, update at sbi-kyc.in", sender="98765\nVERIFIED SENDER")
    rep = report.build(r, report.ReportDetails(sender="98765\nVERIFIED SENDER"))
    assert "\nVERIFIED" not in report.text_report(rep)


# ---- round 2 testers (shopkeeper, student, bank helpdesk, jury, accessibility)
@pytest.mark.parametrize("msg", [
    "Bhai advance bhejne ke liye QR scan karo aur PIN dalo, paisa aa jayega",
    "PhonePe pe request bheja hai, approve kar do, payment aa jayega",
    "QR कोड स्कैन करें और अपना UPI PIN डालें",
])
def test_receive_money_tricks_in_hinglish_and_hindi(msg):
    assert "collect_request" in rules(msg) and analyze(msg).verdict == "SCAM"


def test_unreadable_script_is_never_safe():
    r = analyze("നിങ്ങളുടെ അക്കൗണ്ട് ഇന്ന് ബ്ലോക്ക് ചെയ്യും. ഉടൻ വിളിക്കുക")
    assert r.verdict != "SAFE" and r.confidence <= 0.6 and any(f.rule == "unreadable_script" for f in r.flags)


def test_unknown_link_to_cancel_or_verify_is_not_safe():
    assert analyze("Rs 1 debited for mandate setup. If not you, click http://mandate-stop.in to cancel").verdict != "SAFE"


def test_pay_or_be_barred_and_buy_first_scams():
    assert "fee" in rules("Pay Rs 300 at http://x-portal.in today or you will be barred from the exam")
    assert "fee" in rules("Buy any one product from our store first and you will get 40% commission")


def test_genuine_no_fee_notice_delivery_and_branch_reminder():
    assert "no_fee" in good("Interview on Friday. No fee is charged at any stage.")
    assert "order_update" in good("Your order has been shipped and is out for delivery today")
    f = rules("Your KYC is due. Please visit your nearest branch with ID proof.")
    assert "visit_branch" in f and "kyc" not in f


def test_postal_pin_code_is_not_a_secret():
    assert "asks_secret" not in rules("Please share your address with PIN code for the courier")
