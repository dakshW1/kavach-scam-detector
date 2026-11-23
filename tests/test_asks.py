"""'This message wants you to …' must name the real ask and never invent one."""
from kavach.asks import wants
from kavach.detector import analyze


def items(text, sender=""):
    return wants(analyze(text, sender))["items"]


def test_lottery_names_the_fee_not_the_prize():
    got = items("C0NGR@TS!! Y0u w0n ₹25,00,000 in the K.B.C lucky dr@w. Pay ₹4,999 pr0cessing fee to claim. WhatsApp 9123456780")
    assert got[0] == "pay ₹4,999"
    assert "WhatsApp 9123456780" in got


def test_kyc_scam_lists_link_and_number():
    got = items("Dear customer, your SBI account will be blocked today. Update your KYC immediately at "
                "https://onlinesbi.sbi.secure-login.top/kyc or call 9876543210.", "9876543210")
    assert "open onlinesbi.sbi.secure-login.top/kyc" in got and "call 9876543210" in got


def test_genuine_otp_asks_for_nothing():
    w = wants(analyze("482913 is your OTP for txn of Rs 2,499 at Amazon. Valid for 10 mins. Do not share it with anyone. -SBI",
                      "AX-SBIINB-S"))
    assert w["nothing"] and w["items"][0].startswith("nothing")


def test_friend_chat_asks_for_nothing():
    w = wants(analyze("Bhai kal ka plan pakka? 7 baje station pe milte hain, tickets maine book kar di"))
    assert w["nothing"]


def test_hindi_wording():
    w = wants(analyze("Hello sir, I am in the army, posted at the border so cannot visit the flat. I will pay the advance by UPI, "
                      "please accept the request I send"), "hi")
    assert "UPI" in w["items"][0] and "मंज़ूर" in w["items"][0]
