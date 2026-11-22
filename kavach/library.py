"""Offline Scam Library: how each common scam works, warning signs, protection and recovery steps.

Written from public advice by RBI, the National Cyber Crime Reporting Portal (cybercrime.gov.in),
the Department of Telecommunications (Sanchar Saathi / Chakshu) and bank fraud-awareness pages.
Everything is stored in this file, so it works with no internet.
"""
from __future__ import annotations

RECOVERY_COMMON = [
    "Call **1930** (National Cyber Crime Helpline) immediately. The first hours (the 'golden hour') matter most: the faster you report, the better the chance the money can be frozen before it is moved.",
    "Call your bank on the number printed on your card or passbook (not a number from the message) and block your card, UPI and net banking.",
    "File a complaint at **cybercrime.gov.in** (choose 'Report Financial Fraud'). Keep the complaint number.",
    "Save evidence: screenshots of the message, sender number, links, transaction IDs and UPI IDs. Kavach's evidence report collects most of this for you.",
    "Change passwords and UPI PIN if you shared them, and log out of all devices.",
]

REPORT_ONLY = [
    "Do not reply, call back, or click the link.",
    "Report the message on **Sanchar Saathi -> Chakshu** (sancharsaathi.gov.in) so the number can be investigated and blocked.",
    "Block the sender on your phone / WhatsApp.",
    "If the message used a bank's name, you can also forward it to the bank's official fraud-reporting address listed on its website.",
]

FAMILIES: dict[str, dict] = {
    "kyc_bank": {
        "title": "Fake KYC / bank account block", "category": "KYC/Bank", "icon": "🏦",
        "how": ["You get a message that looks like it is from your bank: 'KYC expired', 'account will be blocked today'.",
                "It has a link to a fake bank page, or a mobile number of a fake 'bank officer'.",
                "The fake page asks for your customer ID, password, card details and finally the OTP.",
                "With the OTP the scammer logs in or makes a payment and empties the account."],
        "signs": ["Threat that the account will be blocked today", "Link that is not the bank's official website",
                  "Asks for OTP, PIN, CVV or password", "Personal 10-digit mobile number as 'customer care'"],
        "protect": ["Banks never ask for KYC through SMS links. Do KYC only at the branch or in the official app.",
                    "Check the link: SBI is sbi.co.in / onlinesbi.sbi, not sbi-kyc-update.xyz.",
                    "Never share OTP, PIN, CVV or passwords with anyone, even 'bank staff'."],
    },
    "sim_kyc": {
        "title": "SIM / telecom KYC scam", "category": "KYC/Bank", "icon": "📶",
        "how": ["A message or call says your SIM will be blocked within hours because of KYC or 'TRAI rules'.",
                "You are asked to call a number or install an app to 'complete KYC'.",
                "The scammer gets you to install a screen-sharing app or share OTPs, then takes over your bank apps."],
        "signs": ["SIM will be blocked in hours", "TRAI / DoT threat", "Asks to install an app or call a mobile number"],
        "protect": ["TRAI and DoT never call or message to block your number.", "Do SIM KYC only at an official store of your operator.",
                    "Never install AnyDesk/TeamViewer on request."],
    },
    "lottery": {
        "title": "Lottery / KBC / lucky draw prize", "category": "Lottery/Prize", "icon": "🎰",
        "how": ["You are told you won a big prize: KBC, a 'Jio lucky draw', a car, an iPhone.",
                "To 'release' the prize you must pay tax, GST, processing or delivery charges.",
                "After each payment there is a new fee. The prize never comes."],
        "signs": ["You won something you never entered", "Pay a fee to receive money", "Asked to keep it secret",
                  "Contact on WhatsApp / personal number"],
        "protect": ["Real prizes never ask you to pay first.", "KBC has no lottery; it never calls about prizes.",
                    "Never send money or bank details to 'claim' anything."],
    },
    "loan_app": {
        "title": "Instant loan app fraud", "category": "Loan/Credit", "icon": "💸",
        "how": ["An ad or SMS offers an instant loan with no documents and no CIBIL check.",
                "You install an app that copies your contacts and photos, or you are asked to pay a 'processing fee'.",
                "Either no loan arrives, or a tiny loan comes with huge charges and threats to shame you to your contacts."],
        "signs": ["No documents, no CIBIL", "Fee before the loan", "App from a link, not the Play Store", "Threats and harassment"],
        "protect": ["Borrow only from banks or RBI-registered NBFCs (check on rbi.org.in).",
                    "Never pay a fee before a loan is disbursed.", "Do not give apps access to contacts and photos."],
    },
    "task_job": {
        "title": "Part-time job / task scam", "category": "Job/Investment", "icon": "💼",
        "how": ["You are offered easy money: like YouTube videos, rate hotels, review restaurants.",
                "The first small tasks really pay a few hundred rupees to win your trust.",
                "Then come 'prepaid tasks': you deposit money to earn a bigger commission.",
                "Your balance grows on screen, but to withdraw you must pay 'tax' or 'upgrade'. You lose everything."],
        "signs": ["Earn thousands per day for simple tasks", "Telegram / WhatsApp groups", "Pay to unlock your earnings"],
        "protect": ["Real jobs never ask you to pay.", "Apply only through official company career pages.",
                    "If you must deposit to withdraw, it is a scam: stop paying immediately."],
    },
    "investment": {
        "title": "Fake trading / crypto investment", "category": "Job/Investment", "icon": "📈",
        "how": ["You are added to a 'VIP stock tips' or crypto group with fake success screenshots.",
                "You install a trading app that shows big fake profits.",
                "When you try to withdraw, you are asked for more money; the app then disappears."],
        "signs": ["Guaranteed or very high returns", "Pressure to invest quickly", "Unknown apps and Telegram groups"],
        "protect": ["Only SEBI-registered brokers and advisers are legal (check on sebi.gov.in).",
                    "No real investment guarantees returns.", "Start small doubts early: ask a family member before investing."],
    },
    "electricity": {
        "title": "Electricity bill disconnection scare", "category": "Other", "icon": "💡",
        "how": ["A message says your power will be cut tonight because the last bill was 'not updated'.",
                "You call the given mobile number. The 'officer' asks you to pay a small amount through a link or an app.",
                "The app or link steals your card details or gives the scammer remote access."],
        "signs": ["Power cut tonight", "Bill not updated", "Call an officer on a mobile number"],
        "protect": ["Electricity boards send bills with due dates; they do not threaten midnight cuts by SMS.",
                    "Pay only on the board's official website or app, or through your bank's BBPS."],
    },
    "parcel_customs": {
        "title": "Parcel / customs / courier scam", "category": "Other", "icon": "📦",
        "how": ["A message says your parcel is held, the address is incomplete or customs duty is due.",
                "A link asks for a small redelivery fee and then your card details.",
                "A variant says a parcel in your name has drugs; a fake officer then threatens arrest."],
        "signs": ["Parcel you don't expect", "Small fee to redeliver", "Threat of police case over a parcel"],
        "protect": ["Track parcels only on the courier's official app or website.",
                    "Couriers don't ask for fees by SMS links.", "Customs and police never settle cases over calls."],
    },
    "digital_arrest": {
        "title": "'Digital arrest' / fake police, CBI, customs", "category": "Other", "icon": "🚔",
        "how": ["A caller or message claims to be police, CBI, customs or TRAI, saying your Aadhaar or number is linked to a crime.",
                "You are put on a video call with fake officers and uniforms, and told not to tell anyone.",
                "You are told to transfer money to a 'verification account' to prove innocence."],
        "signs": ["Threat of arrest", "Stay on video call / keep it secret", "Transfer money to prove innocence"],
        "protect": ["There is NO such thing as 'digital arrest' in Indian law.",
                    "Police never ask for money or keep you on a video call.", "Hang up and call 1930 or your local police."],
    },
    "refund": {
        "title": "Fake refund / income-tax refund / customer care", "category": "Other", "icon": "🧾",
        "how": ["You are told a refund (income tax, GST, an order) is waiting.",
                "To 'receive' it you must click a link, share account details, or install a screen-sharing app.",
                "Fake customer-care numbers found on search engines work the same way."],
        "signs": ["Refund you must 'claim'", "Install AnyDesk / share screen", "Link not on a .gov.in website"],
        "protect": ["Income-tax refunds are credited automatically; check only on incometax.gov.in.",
                    "Find customer-care numbers only on the official website or app."],
    },
    "upi_collect": {
        "title": "UPI 'receive money' / QR trick", "category": "Other", "icon": "📲",
        "how": ["Someone says they sent money by mistake, or a buyer on OLX wants to pay you in advance.",
                "They send a collect request or QR code and say 'enter PIN to receive'.",
                "Entering the PIN SENDS money from your account."],
        "signs": ["Enter PIN to receive", "Approve a request to get a refund", "Overpayment by a stranger"],
        "protect": ["You NEVER need your UPI PIN or a QR scan to receive money.", "Decline unknown collect requests."],
    },
    "family_emergency": {
        "title": "Fake family emergency ('Hi Mum, new number')", "category": "Other", "icon": "👨‍👩‍👧",
        "how": ["A message from an unknown number claims to be your child, parent or friend whose phone broke.",
                "They urgently need money for fees, a hospital or an accident.",
                "The money goes to the scammer's UPI."],
        "signs": ["New number", "Urgent money request", "Asks you not to tell others"],
        "protect": ["Call the person on their OLD number or ask a question only they know.",
                    "Agree on a family 'code word' for emergencies."],
    },
    "account_takeover": {
        "title": "WhatsApp / account code theft", "category": "Other", "icon": "🔐",
        "how": ["You are asked to send back a 6-digit code 'sent by mistake' or to keep your account.",
                "That code is the login code for your WhatsApp or another account.",
                "The scammer takes over the account and asks your contacts for money."],
        "signs": ["Send me the code you just received", "Account will be deleted"],
        "protect": ["Never share any code you receive by SMS.", "Turn on two-step verification in WhatsApp."],
    },
    "unknown": {
        "title": "Other / new type of scam", "category": "Other", "icon": "❓",
        "how": ["This message does not closely match a known scam family, but it shows warning signs.",
                "New scam styles appear all the time; the same rules still protect you."],
        "signs": ["Pressure to act fast", "Requests for money or codes", "Links and numbers you can't verify"],
        "protect": ["Stop, don't click, don't pay.", "Verify through an official channel you find yourself.",
                    "Ask someone you trust before acting."],
    },
}

CATEGORY_DEFAULT = {"KYC/Bank": "kyc_bank", "Lottery/Prize": "lottery", "Loan/Credit": "loan_app",
                    "Job/Investment": "task_job", "Other": "unknown"}

# rule id -> family it most strongly suggests (checked in this order)
RULE_FAMILY = [
    ("authority", "digital_arrest"), ("collect_request", "upi_collect"), ("family_emergency", "family_emergency"),
    ("disconnection", "electricity"), ("parcel", "parcel_customs"), ("refund", "refund"),
    ("invest_bait", "investment"), ("job_bait", "task_job"), ("loan_bait", "loan_app"), ("prize", "lottery"),
    ("kyc", "kyc_bank"),
]


def family_for(category: str, rule_ids: set[str], text: str) -> str:
    t = text.lower()
    if category == "KYC/Bank" and ("sim" in t or "trai" in t) and "bank" not in t:
        return "sim_kyc"
    if ("code" in t or "otp" in t) and "whatsapp" in t:
        return "account_takeover"
    for rule, fam in RULE_FAMILY:
        if rule in rule_ids and (FAMILIES[fam]["category"] == category or category == "Other"):
            return fam
    return CATEGORY_DEFAULT.get(category, "unknown")


def advice(family: str, verdict: str) -> dict[str, list[str]]:
    if verdict == "SAFE":
        return {"do": ["This message looks genuine. Still, never share OTPs or PINs, and use official apps for payments."]}
    return {"do": REPORT_ONLY, "if_lost_money": RECOVERY_COMMON, "protect": FAMILIES[family]["protect"]}
