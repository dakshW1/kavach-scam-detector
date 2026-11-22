"""Builds the training/test dataset: data/messages.csv

Sources (see README "Data"):
  1. UCI SMS Spam Collection (Almeida & Hidalgo, 2011, CC BY 4.0): 'ham' messages are used as SAFE
     personal chats; 'spam' messages that promise prizes are used as SCAM / Lottery-Prize. Other UCI
     spam (ringtone subscriptions, marketing) is dropped because it is spam, not a scam.
  2. Indian messages generated here from hand-written TEMPLATES (English, Hinglish, Hindi), modelled on
     public warnings from banks, RBI, the Cyber Crime portal and news reports, with random slot values
     (banks, amounts, links, numbers) and random disguise tricks.

Every generated message keeps the id of the template it came from, and the train/test split is done
BY TEMPLATE: test messages come from templates the model never saw, so the test score is not inflated
by near-duplicates. The hand-written challenge set (data/challenge.csv) is never used for training.

Run:  python data/generate.py
"""
from __future__ import annotations

import csv
import random
import re
import string
from pathlib import Path

HERE = Path(__file__).parent
rng = random.Random(42)

BANKS = [("SBI", "sbi", "onlinesbi.sbi"), ("HDFC Bank", "hdfc", "hdfcbank.com"), ("ICICI Bank", "icici", "icicibank.com"),
         ("Axis Bank", "axis", "axisbank.com"), ("Kotak", "kotak", "kotak.com"), ("PNB", "pnb", "pnbindia.in"),
         ("Bank of Baroda", "bob", "bankofbaroda.in"), ("Canara Bank", "canara", "canarabank.com")]
FAKE_PATTERNS = ["{b}-kyc-update.xyz", "{b}-verify.top", "{b}care.online", "secure-{b}.info", "{b}.co.in-login.site",
                 "{b}-rewards.club", "{b}netbanking.live", "{b}-kyc.icu", "update-{b}.buzz", "{b}-alert.click",
                 "my{b}-account.vip", "{b}yono-update.shop", "{b}.in-secure.top"]
SHORT = ["bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "is.gd", "shorturl.at", "t.ly", "tiny.cc"]
GENERIC_FAKE = {
    "lottery": ["kbc-lottery.top", "claim-prize.xyz", "lucky-draw-winner.online", "jio-kbc.club", "reward-claim.site"],
    "loan": ["instaloan-now.online", "easyloan.club", "quickcash-loan.xyz", "loan-approve.site", "rupee-loan.top"],
    "job": ["earn-daily.site", "parttime-jobs.online", "work-home-earn.xyz", "task-pay.club", "daily-income.top"],
    "invest": ["crypto-double.xyz", "vip-trading.online", "stock-profit.club", "usdt-earn.top"],
    "electricity": ["bescom-bill.online", "power-bill-update.xyz", "bijli-bill.top", "eb-payment.site"],
    "parcel": ["indiapost-track.top", "parcel-redeliver.info", "indiapost.in-delivery.xyz", "bluedart-redelivery.online"],
    "refund": ["itrefund-gov.site", "incometax-refund.online", "gst-refund.xyz", "refund-claim.top"],
    "traffic": ["echallan-pay.xyz", "parivahan-challan.online", "traffic-fine.top"],
}
OFFICIAL_LINKS = {"Amazon": "https://amzn.in/d/{code}", "Flipkart": "https://dl.flipkart.com/s/{code}",
                  "Myntra": "https://myntr.it/{code}", "Swiggy": "https://swiggy.com", "Zomato": "https://zoma.to/{code}"}
NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Arjun", "Kavya", "Rohan", "Ananya", "Vikram", "Neha", "Karthik", "Divya",
         "Suresh", "Pooja", "Manoj", "Lakshmi", "Imran", "Fatima", "Harpreet", "Deepa"]
CITIES = ["Bengaluru", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata", "Jaipur", "Lucknow", "Mysuru"]
MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "Zomato", "BigBasket", "Myntra", "Uber", "Ola", "IRCTC", "BookMyShow",
             "Reliance Digital", "DMart", "Apollo Pharmacy", "Croma"]
COURIERS = ["India Post", "Blue Dart", "Delhivery", "DTDC", "FedEx", "Ekart"]
TELCOS = ["Airtel", "Jio", "Vi", "BSNL"]


def mobile() -> str:
    n = str(rng.choice("6789")) + "".join(rng.choice(string.digits) for _ in range(9))
    return rng.choice([n, n, f"+91 {n[:5]} {n[5:]}", f"+91{n}", f"{n[:5]} {n[5:]}"])


def code(k=6) -> str:
    return "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(k))


def amount(lo=100, hi=9999) -> str:
    v = rng.randint(lo, hi)
    s = f"{v:,}" if v >= 1000 else str(v)
    return rng.choice([f"Rs.{s}", f"Rs {s}", f"₹{s}", f"INR {s}", f"Rs.{v}.00"])


def big_amount() -> str:
    return rng.choice([f"Rs {rng.choice([5, 10, 12, 25, 50])},00,000", f"₹{rng.choice([25, 35, 50])} lakh",
                       f"Rs.{rng.choice([1, 2, 5])} crore", f"₹{rng.randint(2, 9)},{rng.randint(10, 99)},000",
                       f"Rs {rng.choice(['10', '25', '50'])} lakh"])


def date() -> str:
    d, m = rng.randint(1, 28), rng.randint(1, 12)
    return rng.choice([f"{d:02d}-{m:02d}-26", f"{d:02d}/{m:02d}/2026", f"{d:02d}-{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]}-26"])


def acct() -> str:
    return rng.choice(["XX", "XXXX", "**", "xx", "X"]) + str(rng.randint(1000, 9999))


def fill(tpl: str, kind: str = "") -> str:
    b, bl, bdom = rng.choice(BANKS)
    vals = {
        "bank": b, "otp": str(rng.randint(100000, 999999)), "otp4": str(rng.randint(1000, 9999)),
        "amount": amount(), "amount2": amount(5000, 99999), "small": amount(49, 999), "fee": amount(499, 4999), "big": big_amount(),
        "acct": acct(), "date": date(), "mobile": mobile(), "mobile2": mobile(), "name": rng.choice(NAMES),
        "city": rng.choice(CITIES), "merchant": rng.choice(MERCHANTS), "courier": rng.choice(COURIERS),
        "telco": rng.choice(TELCOS), "hours": str(rng.choice([2, 6, 12, 24, 24, 48])),
        "time": f"{rng.randint(7, 11)}:{rng.choice(['00', '30', '45'])} PM", "ref": str(rng.randint(10**11, 10**12 - 1)),
        "order": f"{rng.randint(400, 409)}-{rng.randint(1000000, 9999999)}-{rng.randint(1000000, 9999999)}",
        "pct": str(rng.choice([20, 30, 40, 50, 60, 70, 80])), "earn": str(rng.choice([1500, 2000, 3000, 5000, 8000])),
        "ret": str(rng.choice([30, 40, 50, 100, 200, 300])), "upi": f"{rng.choice(NAMES).lower()}{rng.randint(1, 99)}@{rng.choice(['ybl', 'okaxis', 'oksbi', 'paytm', 'okicici'])}",
        "bankdom": bdom, "tollfree": f"1800{rng.randint(100, 999)}{rng.randint(1000, 9999)}",
        "short": f"{rng.choice(SHORT)}/{code(rng.randint(4, 7))}", "code": code(),
        "vpa": f"{rng.choice(MERCHANTS).lower().replace(' ', '')}@{rng.choice(['ybl', 'axl', 'icici', 'hdfcbank'])}",
        # slots used by data/templates_v3.py
        "cdate": f"{rng.randint(1, 28):02d}{rng.choice(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}{rng.choice(['25', '26', '27'])}",
        "ddmmyy": f"{rng.randint(1, 28):02d}-{rng.randint(1, 12):02d}-{rng.choice(['25', '26'])}",
        "small_n": str(rng.choice([45, 99, 120, 250, 349, 500, 780, 1200, 1999, 2500, 4300])),
        "merch_up": rng.choice(MERCHANTS).upper().replace(" ", ""), "name_up": rng.choice(NAMES).upper() + " " + rng.choice("KRSMPVA"),
        "bank_lo": bl, "merchant_lo": rng.choice(MERCHANTS).lower().replace(" ", ""), "name_lo": rng.choice(NAMES).lower(),
        "intl": rng.choice(["852 ", "44 ", "1 ", "63 ", "855 "]) + "".join(rng.choice(string.digits) for _ in range(9)),
        "acctno": str(rng.randint(10**10, 10**12)),
    }
    fake_bank = rng.choice(FAKE_PATTERNS).format(b=bl)
    proto = rng.choice(["http://", "https://", "", "www.", ""])
    vals["link"] = proto + fake_bank if rng.random() < 0.7 else vals["short"]
    for k, doms in GENERIC_FAKE.items():
        d = rng.choice(doms) + rng.choice(["", f"/{code(5)}", "/claim", "/apply"])
        vals["link_" + k] = (rng.choice(["http://", "https://", "", "www."]) + d) if rng.random() < 0.7 else vals["short"]
    vals["tg"] = rng.choice(["t.me/", "https://t.me/", "wa.me/91"]) + (code(8) if rng.random() < .5 else vals["mobile"][-10:].replace(" ", ""))
    vals["amzlink"] = OFFICIAL_LINKS["Amazon"].format(code=code(8))
    vals["fklink"] = OFFICIAL_LINKS["Flipkart"].format(code=code(8))
    return re.sub(r"\{(\w+)\}", lambda m: vals[m.group(1)], tpl)


# ---------------------------------------------------------------- scam templates
# category -> list of templates. Families noted in comments where they differ from the category.
SCAM = {
    "KYC/Bank": [
        "Dear Customer, your {bank} account will be blocked today. Please update your KYC immediately: {link}",
        "Your {bank} YONO account has been suspended due to incomplete KYC. Click {link} to update PAN within {hours} hours.",
        "{bank} ALERT: Your netbanking is blocked. Verify your PAN card details now at {link} to avoid permanent closure.",
        "Dear {bank} user, your KYC is pending. Account will be deactivated tonight. Call our KYC officer on {mobile}.",
        "Aapka {bank} account aaj band ho jayega. KYC turant update karein: {link}",
        "Priya grahak, aapka KYC expire ho gaya hai. Account block hone se bachne ke liye is link pe click karo {link}",
        "{bank}: Your debit card is temporarily blocked. To reactivate, share the OTP sent to your mobile with our executive at {mobile}.",
        "Dear customer, {bank} reward points worth {amount} expire today. Redeem now at {link} to get cash in your account.",
        "Your {bank} credit card limit has been increased. Click {link} and enter card details to activate the new limit.",
        "URGENT: Unusual login detected on your {bank} account. If not you, verify immediately at {link} or your account will be frozen.",
        "Your PAN is not linked with your {bank} account. Link it before {time} today: {link} else account will be suspended.",
        "{bank} customer care: your account is on hold. Please tell the OTP received on your phone to our agent to remove the hold.",
        "Dear {name}, your {bank} account has been temporarily locked. Download the {bank} security app from {link} to unlock.",
        "Your SIM will be deactivated in {hours} hours due to incomplete e-KYC. Call {telco} KYC centre on {mobile} immediately.",
        "{telco}: Dear customer, your SIM card KYC is not updated as per TRAI rules. Your number will be blocked today. Call {mobile}.",
        "Your {bank} account KYC verification failed. Install AnyDesk and call {mobile} so our team can help you update it.",
        "प्रिय ग्राहक, आपका {bank} खाता आज बंद हो जाएगा। तुरंत KYC अपडेट करें: {link}",
        "Bhai {bank} se message aaya hai account block ho raha hai, ye link pe KYC kar lo jaldi {link}",
        "Your {bank} electricity-linked autopay failed. Re-verify your debit card CVV at {link} within {hours} hrs.",
        "{bank} Netbanking: your password expires today. Reset now at {link} to continue using services.",
        "Final reminder from {bank}: aadhaar not verified, account will be closed. Visit {link} and submit details.",
        "Dear user your {bank} account has been debited {amount} for a suspicious transaction. If not done by you click {link} to cancel.",
    ],
    "Lottery/Prize": [
        "Congratulations! You have won {big} in the KBC lucky draw. To claim, call {mobile} and pay {fee} processing fee.",
        "Dear {name}, your mobile number has won {big} in the {telco} anniversary lottery. Claim at {link_lottery}",
        "You are the lucky winner of a Tata Safari car and {big} cash! Contact our manager on WhatsApp {mobile}.",
        "KBC Jio lottery: your number selected for {big} prize. Lottery manager Rana Pratap: {mobile}. Pay GST {fee} to release prize.",
        "Badhai ho! Aapne {big} ka inaam jeeta hai. Inaam paane ke liye {fee} registration fee jama karein. Call {mobile}",
        "Congrats! You've won an iPhone 16 in the {merchant} lucky draw. Pay only {small} delivery charges at {link_lottery}",
        "Your email/phone has won GBP 750,000 in the international lottery. Send your name, address and bank details to claim.",
        "Aapka number {telco} lucky draw me select hua hai, {big} jeetne ke liye turant {mobile} par WhatsApp karein",
        "WINNER!! You have been selected for a cash reward of {big}. Claim before midnight: {link_lottery}",
        "Dear customer, you have won a {merchant} gift voucher worth {amount}. Click {link_lottery} to redeem before it expires.",
        "Congratulations, you are selected for {merchant} Diwali bumper prize of {big}. Pay {fee} as transfer charge to receive.",
        "बधाई हो! आपने {big} की लॉटरी जीती है। इनाम पाने के लिए {mobile} पर संपर्क करें।",
        "Your number won the Kaun Banega Crorepati prize {big}. Do not tell anyone. Call head office {mobile} for claim.",
        "You won a scratch card of {amount} on Google Pay! Scan the QR code and enter UPI PIN to receive the money.",
        "Hello, your ticket number {otp4} has won the weekly jackpot of {big}. Reply with your bank account number to receive the amount.",
        "Free gift! {merchant} is giving {amount} cashback to 100 lucky users. You are selected, claim here {link_lottery}",
    ],
    "Loan/Credit": [
        "Instant personal loan of {big} approved in 5 minutes! No documents, no CIBIL check. Apply now {link_loan}",
        "Dear {name}, your pre-approved loan of {amount2} is ready. Pay {fee} processing fee to get it disbursed today.",
        "Loan chahiye? {big} tak ka loan bina documents ke, 2% interest. WhatsApp karein {mobile}",
        "Get a {bank} loan at 1% interest without income proof. Download our app {link_loan} and start now.",
        "Congratulations! Your loan of {amount2} has been sanctioned. To receive the amount, pay refundable security deposit of {fee}.",
        "Urgent cash? Easy loan in 10 mins, no CIBIL score needed. Install app: {link_loan}",
        "Your credit card limit upgrade to {big} approved. Share the OTP sent to you to confirm the upgrade.",
        "Dhani/{bank} loan offer: {amount2} loan sanctioned on your PAN. Pay file charge {fee} to {upi} to release.",
        "Low CIBIL? No problem! Guaranteed loan approval. Call {mobile} and pay only {fee} insurance charges.",
        "आपका {amount2} का लोन मंजूर हो गया है। प्रोसेसिंग फीस {fee} जमा करें और तुरंत पैसा पाएं। {link_loan}",
        "Your loan EMI is overdue. Pay {amount} today at {link_loan} or legal action and police complaint will be filed.",
        "Mudra loan approved under PM scheme {big}. To get money pay {fee} GST charges. Contact {mobile}",
        "Hi {name}, we can increase your credit score to 800 in 7 days. Pay {fee} and get any loan approved.",
        "Need money urgently? Personal loan up to {big} credited in 15 minutes. Only Aadhaar and PAN needed. {link_loan}",
    ],
    "Job/Investment": [
        "Part time job! Earn Rs {earn} per day by liking YouTube videos from home. Join now {tg}",
        "Hello, we are hiring for online work from home. Daily income Rs {earn}-{earn}0. Contact HR on WhatsApp {mobile}",
        "Ghar baithe kamaye Rs {earn} rozana. Simple typing job, koi experience nahi chahiye. Join karein {tg}",
        "Dear {name}, your profile is selected for Amazon part-time job. Salary {amount} per day. Pay {fee} registration to start.",
        "Earn {ret}% returns monthly! Guaranteed profit with our crypto investment plan. Join VIP group {tg}",
        "Double your money in 30 days. Invest {amount} and get {amount2} back, 100% safe. Call {mobile}",
        "Stock market tips with 90% accuracy. Join our VIP trading group and earn {ret}% daily: {link_invest}",
        "Paisa double scheme! {amount} lagao aur {hours} ghante me double pao. WhatsApp {mobile}",
        "Complete simple tasks (rate hotels, like posts) and earn Rs {earn} daily. Prepaid tasks give 30% commission. {tg}",
        "Hi, I am {name} from HR team. We found your resume on Naukri. Work 1 hour a day and earn {amount}. Reply YES to know more.",
        "USDT investment: earn {pct}% weekly guaranteed. Minimum {amount}. Join on Telegram {tg}",
        "Data entry job vacancy. Earn {amount} weekly. Pay {fee} for ID card and training kit. Call {mobile}",
        "IPO allotment guaranteed with our app. Get {ret}% profit on listing day. Register: {link_invest}",
        "घर बैठे रोज़ {earn} रुपये कमाएं! बस वीडियो लाइक करें। अभी जुड़ें {tg}",
        "Congratulations! You are shortlisted for a Govt job in Railways. Pay {fee} for document verification to {upi}.",
        "Your task commission of {amount} is frozen. Recharge {fee} to unlock withdrawal. Contact mentor {tg}",
    ],
    "Other": [
        # electricity disconnection
        "Dear consumer, your electricity power will be disconnected tonight at {time} because your previous month bill was not updated. Contact officer {mobile}",
        "Aapka bijli connection aaj raat {time} kat jayega. Bill update nahi hua hai. Turant {mobile} par call karein.",
        "BESCOM: Your electricity bill is pending. Power will be cut today. Pay now at {link_electricity} to avoid disconnection.",
        # parcel / customs
        "{courier}: Your parcel is on hold due to incomplete address. Update within {hours} hours: {link_parcel}",
        "Your package could not be delivered. Pay {small} redelivery fee at {link_parcel} to reschedule.",
        "This is {courier} customs department. A parcel in your name contains illegal items. Press 9 or call {mobile} immediately.",
        # digital arrest / authority
        "This is Mumbai Police cyber cell. An FIR has been registered against your Aadhaar for money laundering. Join the video call now, do not disconnect or you will face digital arrest.",
        "CBI notice: your bank account is linked to a drugs case. Transfer your savings to the RBI verification account {upi} to prove innocence. Keep this confidential.",
        "TRAI: your mobile number will be blocked in 2 hours due to illegal activity. Press 1 to talk to the officer.",
        # tax refund / gov refund
        "Income Tax Department: you are eligible for a refund of {amount}. Verify your bank account at {link_refund} to receive it.",
        "Your GST refund of {amount} is pending. Claim within 24 hours at {link_refund}",
        # traffic challan
        "Your vehicle has an unpaid traffic challan of {small}. Pay today at {link_traffic} to avoid court action.",
        # upi collect / overpayment
        "I sent you {amount} by mistake on PhonePe, please return it. Approve the request I sent to receive your refund.",
        "Hello sir I am army officer, I want to buy your item on OLX. I will send advance, scan this QR and enter PIN to receive money.",
        # family emergency
        "Hi Mummy, this is my new number. My phone fell in water. Need {amount} urgently for college fees, please send to {upi}",
        "Papa mera accident ho gaya hai, ye mere dost ka number hai. Jaldi {amount} bhej do {upi} pe, kisi ko mat batana.",
        # fake customer care / refund
        "Your {merchant} refund of {amount} is pending. To receive it, download AnyDesk and call our customer care {mobile}.",
        "Your Netflix subscription is suspended due to payment failure. Update your card details at {link} to continue.",
        "Your FASTag is blacklisted. Re-KYC now at {link_traffic} or pay double toll.",
        "Your gas connection will be cut today. Update your consumer KYC by calling {mobile}.",
        "आपका बिजली कनेक्शन आज रात {time} काट दिया जाएगा। तुरंत {mobile} पर बिजली अधिकारी से संपर्क करें।",
        "Sir your WhatsApp will be banned in 24 hours for violating rules. Verify your account by sending the 6 digit code we sent you.",
    ],
}

# ---------------------------------------------------------------- genuine templates
SAFE = {
    "bank_alert": [
        "{amount} debited from A/c {acct} on {date} to VPA {vpa} (UPI Ref No {ref}). Not you? Call {tollfree} to block. -{bank}",
        "Dear Customer, {amount} has been credited to your A/c {acct} on {date}. Avl Bal: {amount2}. -{bank}",
        "Your A/c {acct} is debited for {amount} on {date} at {merchant}. Avl bal {amount2}. If not done by you, SMS BLOCK to {tollfree}.",
        "{bank}: INR {amount} spent on your credit card ending {otp4} at {merchant} on {date}. Avl limit: INR {amount2}.",
        "Salary of {amount2} credited to your account {acct} on {date}. -{bank}",
        "Dear customer, your {bank} account statement for Oct 2026 has been sent to your registered email id.",
        "IMPS of {amount} to {name} successful. Ref no {ref}. A/c {acct}. -{bank}",
        "Your cheque no. {otp} for {amount} has been cleared on {date}. -{bank}",
        "Your FD of {amount2} in A/c {acct} will mature on {date}. Visit {bankdom} or your branch to renew.",
        "Your {bank} credit card bill of {amount} is due on {date}. Pay via {bankdom} or the mobile app. Ignore if already paid.",
        "Reminder: your loan EMI of {amount} will be auto-debited from A/c {acct} on {date}. Please maintain sufficient balance.",
        "Dear Customer, autopay of {amount} for {telco} postpaid set up successfully on your card ending {otp4}. -{bank}",
        "आपके खाते {acct} में {amount} जमा किए गए हैं। उपलब्ध शेष: {amount2} -{bank}",
    ],
    "otp": [
        "{otp} is your OTP for transaction of {amount} at {merchant}. Valid for 10 mins. Do not share it with anyone. -{bank}",
        "Your OTP for login is {otp}. Do not share this OTP with anyone. {bank} never asks for your OTP.",
        "{otp} is the OTP to verify your mobile number on {merchant}. Valid for 5 minutes. Don't share it with anyone.",
        "Use {otp4} as your verification code for {merchant}. Never share this code.",
        "OTP {otp} for your Aadhaar authentication (valid 10 mins). UIDAI never asks for OTP over call.",
        "{otp} is your OTP to reset your {merchant} password. If you didn't request this, ignore this message.",
        "Dear customer, OTP for your {bank} netbanking registration is {otp}. Do not disclose it to anyone.",
        "{otp} आपका OTP है। इसे किसी के साथ साझा न करें। -{bank}",
        "Your Uber code is {otp4}. Never share this code with anyone.",
        "{otp} is your one time password for your DigiLocker account. It is valid for 10 minutes. Do not share.",
    ],
    "delivery": [
        "Your {merchant} order {order} has been shipped and will arrive by {date}. Track: {amzlink}",
        "Out for delivery: your {courier} shipment will be delivered today. Delivery OTP {otp4} - share only with the delivery agent at your door.",
        "Your Swiggy order is on the way! {name} is your delivery partner and will reach in 25 minutes.",
        "Delivered: your Flipkart package was delivered on {date}. Rate your experience: {fklink}",
        "{courier}: Shipment {otp} for you is out for delivery today. For queries visit the official app.",
        "Your Zomato order from {city} Biryani House has been delivered. Enjoy your meal!",
        "Hi {name}, your {merchant} order was cancelled and a refund of {amount} has been initiated to your original payment method. It will reflect in 5-7 days.",
        "Your BigBasket slot is confirmed for tomorrow 7-9 AM. Order total {amount}.",
        "India Post: Speed Post article EK{otp}IN booked on {date} has been delivered.",
        "Your IRCTC ticket PNR {otp}0000 is confirmed. Train departs at {time} from {city}. Happy journey!",
    ],
    "bills_service": [
        "Your electricity bill of {amount} for Oct 2026 is generated. Due date {date}. Pay via BBPS, bescom.co.in or any UPI app.",
        "{telco}: Your plan expires on {date}. Recharge now to continue enjoying unlimited calls and data.",
        "Dear customer, your {telco} postpaid bill of {amount} is due on {date}. Pay via the official app. Ignore if already paid.",
        "Your Jio plan expires today. Recharge at jio.com or the MyJio app to avoid interruption.",
        "Payment of {amount} towards electricity bill received. Thank you. -BESCOM",
        "Your FASTag wallet balance is low ({small}). Recharge through your bank app to avoid double toll.",
        "Your appointment with Dr. {name} at Apollo Clinic is confirmed for {date} at {time}.",
        "Gas cylinder booking confirmed. Ref no {otp}. Delivery expected by {date}. Pay only the amount on the bill.",
        "Your Netflix payment of {small} was successful. Next billing date {date}.",
        "Last date to file your income tax return is 31 July. File on the official portal incometax.gov.in.",
        "Your vehicle insurance for KA05{otp4} expires on {date}. Renew on the official app of your insurer.",
        "Dear voter, your polling station details are available on the official ECI app.",
    ],
    "promo": [
        "Flash sale ends tonight! Up to {pct}% off on fashion at Myntra. Shop now on the app.",
        "Big Billion Days are live! Grab deals up to {pct}% off on Flipkart. T&C apply.",
        "Get {pct}% off on your next Swiggy order with code TASTY{otp4}. Valid till {date}.",
        "{merchant} Diwali sale: extra {pct}% off on electronics this weekend only. Visit your nearest store.",
        "Pizza party! Buy 1 get 1 free at Domino's today. Order on the app.",
        "Congratulations on completing 1 year with {telco}! Enjoy 2 GB extra data free for 7 days.",
        "New arrivals at Lifestyle {city}. Flat {pct}% off on your first purchase. Visit us this weekend.",
        "Your {merchant} SuperCoins balance is {otp4}. Use them on your next order.",
    ],
    "personal": [
        "Bhai kal ki class cancel hai kya?",
        "Hey {name}, are we still meeting at 6 near the metro station?",
        "Mummy, I will be late today, don't wait for dinner.",
        "Kal milte hai college me, notes le aana please",
        "Did you reach home safely? Message me once you do.",
        "Congrats yaar! You won the hackathon, party kab de raha hai?",
        "Can you send me the assignment pdf? Deadline is tomorrow.",
        "Happy birthday {name}! Have a great year ahead 🎉",
        "Papa ne bola hai shaam ko market chalna hai, ready rehna",
        "I transferred {amount} for the trip, check your account.",
        "Bro urgent, send me the meeting link, I can't find it",
        "Dinner at my place tonight? Mom is making biryani",
        "Ok I'll call you after the lecture",
        "Did you see the match last night? What a finish!",
        "Pls pick up milk on your way back",
        "Main abhi bus me hoon, 10 min me pahunch jaunga",
        "कल मिलते हैं, खाना खा लिया?",
        "Thanks for the help yesterday, really appreciate it!",
        "Your share for the pizza is {small}, pay whenever",
        "Hey, the team meeting is moved to 3 pm today. Please be on time.",
    ],
    "gov_info": [
        "Beware of fraud calls. {bank} never asks for your OTP, PIN or password. Report fraud at cybercrime.gov.in or call 1930.",
        "RBI says: never share your card details or OTP with anyone. Know more at rbi.org.in.",
        "Your Aadhaar has been successfully updated. Download your updated Aadhaar from myaadhaar.uidai.gov.in.",
        "Your PAN-Aadhaar link status: linked. -Income Tax Department",
        "Dear citizen, check if your mobile connections are genuine on sancharsaathi.gov.in.",
        "Your vaccination certificate is ready. Download from the official CoWIN portal.",
    ],
}

# ---- second batch of templates (added after error analysis on the challenge set): more scams WITHOUT
# links, more Hindi/Hinglish, and genuine messages that contain scary words (refund, block, police, prize).
SCAM["KYC/Bank"] += [
    "Hello sir, calling from {bank} fraud department. Someone is trying to use your card. Tell me the code we just sent so I can cancel it.",
    "{bank} officer here. Your account has been put on hold for verification. Please confirm your debit card number and expiry date.",
    "Aapka {bank} ATM card aaj raat se kaam nahi karega. Naya card chalu karne ke liye card number aur OTP bataiye.",
    "Your {bank} savings account will be restricted from tomorrow as your PAN is missing. Reply with PAN and date of birth.",
    "आपका {bank} डेबिट कार्ड बंद होने वाला है। चालू रखने के लिए कार्ड नंबर और ओटीपी बताएं।",
    "Dear user, your UPI ID will be disabled today. To keep it active, share the 4 digit code you get on SMS with our support team.",
]
SCAM["Lottery/Prize"] += [
    "Hi, this is from the {merchant} customer reward team. You were picked as today's lucky customer and get a Honda Activa. Pay {small} registration to book delivery.",
    "Aapka naam lucky draw me aaya hai! 5 lakh ka cash prize aapka hai, bas {fee} tax jama karna hoga.",
    "Dear winner, your prize money of {big} is waiting. Send a copy of your aadhaar and bank passbook to our claims office on WhatsApp.",
    "हमारी कंपनी की ओर से आपको {big} का इनाम मिला है। इनाम पाने के लिए {fee} टैक्स जमा करें।",
    "You've been chosen to receive a free Samsung Galaxy in our festive giveaway. Only {small} courier charges to be paid.",
]
SCAM["Loan/Credit"] += [
    "Sir, your personal loan of {amount2} is ready for disbursal. Just pay {fee} insurance charges and the amount will be in your account today.",
    "Paisa chahiye? 2 lakh tak loan sirf aadhar card pe, 10 minute me account me. File charge {fee} pehle dena hoga.",
    "Your loan repayment is overdue. If you don't pay {amount} today, we will message all your contacts that you are a fraud.",
    "बिना गारंटी के लोन पाएं। सिर्फ आधार और पैन से तुरंत पैसा। प्रोसेसिंग फीस {fee}।",
    "Get credit card with {big} limit without any income proof. Pay {small} joining fee to get your card at home.",
]
SCAM["Job/Investment"] += [
    "Hi, we need people to give 5-star ratings to hotels on Google. Rs 120 per rating, payment every evening. Interested? Reply on WhatsApp.",
    "Hello dear, I am a recruiter from an online marketing company. Simple work on your phone, 3000-6000 per day. Can I share details?",
    "Mera dost har mahine 50 hazaar kama raha hai is trading app se. Tu bhi {amount} se start kar, pakka profit hai.",
    "Your withdrawal of {amount2} is pending. Please pay {fee} service tax first, then the money will be released to your bank.",
    "Invest {amount} today and get {amount2} after 15 days. Fully safe, many people have already earned.",
    "रोज़ 5000 रुपये कमाने का मौका! मोबाइल से आसान काम। पहले {fee} रजिस्ट्रेशन फीस जमा करें।",
    "Congratulations, you are selected for a remote job with {merchant}. Monthly salary {amount2}. Pay {fee} for the onboarding kit.",
]
SCAM["Other"] += [
    "Dear consumer, your electricity supply will be stopped at {time} as your bill payment is not reflected in our system. Call {mobile}.",
    "Gas agency: your LPG connection will be cut today because of pending KYC. Call our officer {mobile} immediately.",
    "Hi Mom, my phone is broken and this is a friend's number. Please transfer {amount} urgently, I will explain later.",
    "Beta bol raha hu papa, ye mere dost ka phone hai, mera phone kho gaya. {amount} bhej do jaldi.",
    "I accidentally sent my login code to your number, can you please forward it to me?",
    "Hello, by mistake I transferred {amount} to your account. Please accept the payment request I sent to return it.",
    "This is from Delhi Police crime branch. Your number is involved in an illegal activity case. Stay on this call and do not tell anyone.",
    "Customs office: your international parcel is held. Pay duty of {small} within {hours} hours or it will be destroyed.",
    "आपकी गाड़ी का चालान बकाया है। कोर्ट केस से बचने के लिए आज ही भुगतान करें।",
    "आपके नाम का पार्सल पकड़ा गया है जिसमें अवैध सामान है। तुरंत पुलिस अधिकारी से बात करें।",
    "Your Instagram account will be removed for copyright violation. Verify ownership by sending us the code you received.",
]
SAFE["bank_alert"] += [
    "Dear Customer, your debit card ending {otp4} has been blocked as requested by you on {date}. -{bank}",
    "Your request for a new cheque book has been received and will be dispatched in 7 days. -{bank}",
    "Your {bank} account has been successfully linked to Aadhaar. No further action is needed.",
    "Dear customer, a temporary hold of {small} has been placed on your card for a hotel booking. It will be released after checkout.",
    "Your {bank} net banking password was changed on {date}. If you did not do this, call {tollfree}.",
]
SAFE["delivery"] += [
    "Refund of {amount} for your returned order has been processed and will be credited to your original payment method in 3-5 days.",
    "{courier}: your shipment {otp} has been delivered on {date} at {time}. Thank you for choosing us.",
    "Your order could not be delivered today. Our delivery partner will try again tomorrow.",
    "Your {merchant} return pickup is scheduled for tomorrow. Keep the item packed with the original tags.",
]
SAFE["bills_service"] += [
    "Your income tax return for AY 2026-27 has been processed. Refund of {amount} has been credited to your bank account.",
    "Scheduled power cut on {date} from 10 AM to 2 PM in your area for maintenance. -BESCOM",
    "Power supply will be interrupted in {city} on {date} between 9 AM and 1 PM for line maintenance. Inconvenience regretted.",
    "Planned water supply shutdown on {date} due to pipeline work. Please store water in advance. -BWSSB",
    "Your traffic challan of {small} has been generated. Pay on echallan.parivahan.gov.in.",
    "Your {telco} number has been ported successfully. Welcome!",
    "Your passport application has been received. Track status on passportindia.gov.in.",
]
SAFE["gov_info"] += [
    "Police advisory: never share OTP, never install screen sharing apps on a stranger's request. Report cyber fraud on 1930.",
    "Beware of fake KYC messages. Banks never send links for KYC. Report suspicious messages on sancharsaathi.gov.in.",
    "Cyber Dost: there is no such thing as digital arrest. If someone threatens you on video call, hang up and call 1930.",
    "Fraud alert: do not believe messages about lottery wins or prize money. Never pay to receive a prize.",
]
SAFE["personal"] += [
    "Haha that lottery message you forwarded was so fake 😂",
    "Congrats on the promotion! When is the party?",
    "Mera account freeze ho gaya tha, bank jaake theek karwa liya",
    "Please send 1500 for the trip booking when you can, no hurry",
    "Bro my phone screen broke, I'll be on this number for a few days. Call me tonight",
    "Did you get the refund for the cancelled flight?",
    "Kal police verification ke liye documents le jaana hai passport ke liye",
    "Mummy ne bola hai paise bhej diye hai, check kar lo",
    "I won 500 in the office quiz today!",
    "पापा, मैं ठीक हूँ, शाम को फ़ोन करूँगा।",
    "Hey can you send me the code for the netflix profile? the one on the tv",
    "Remember to pay the electricity bill before Friday",
]


import sys as _sys  # noqa: E402

_sys.path.insert(0, str(HERE))
from templates_v3 import SAFE_V3, SCAM_V3  # noqa: E402  (third batch, see that file for why each group exists)

for _cat, _tpls in SCAM_V3.items():
    SCAM[_cat] = SCAM[_cat] + _tpls
for _kind, _tpls in SAFE_V3.items():
    SAFE[_kind] = SAFE.get(_kind, []) + _tpls


def obfuscate(text: str) -> str:
    """Apply 1-3 random disguise tricks, the way real scammers do (used for augmentation and robustness tests)."""
    tricks = rng.sample(["leet", "space", "homoglyph", "zw", "stretch"], k=rng.randint(1, 3))
    words = text.split(" ")
    idx = [i for i, w in enumerate(words) if re.fullmatch(r"[A-Za-z]{4,}[.,!]?", w)]
    rng.shuffle(idx)
    leet = {"o": "0", "i": "1", "e": "3", "a": "@", "s": "$"}
    homo = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "i": "і"}
    for i in idx[: max(1, len(idx) // 4)]:
        w = words[i]
        t = rng.choice(tricks)
        if t == "leet":
            w = "".join(leet.get(c.lower(), c) if rng.random() < .5 else c for c in w)
        elif t == "space":
            w = rng.choice([" ", ".", "-"]).join(w.upper())
        elif t == "homoglyph":
            w = "".join(homo.get(c, c) if rng.random() < .6 else c for c in w)
        elif t == "zw":
            w = "​".join(w)
        elif t == "stretch":
            w = w + w[-1] * rng.randint(2, 4)
        words[i] = w
    return " ".join(words)


def build(per_scam=14, per_safe=12, obf_rate=0.3):
    rows = []
    for cat, tpls in SCAM.items():
        for ti, tpl in enumerate(tpls):
            seen = set()
            for _ in range(per_scam):
                msg = fill(tpl)
                if rng.random() < obf_rate:
                    msg = obfuscate(msg)
                if msg in seen:
                    continue
                seen.add(msg)
                rows.append({"text": msg, "label": "SCAM", "category": cat, "group": f"scam:{cat}:{ti}", "source": "generated"})
    for kind, tpls in SAFE.items():
        for ti, tpl in enumerate(tpls):
            seen = set()
            for _ in range(per_safe):
                msg = fill(tpl)
                if msg in seen:
                    continue
                seen.add(msg)
                rows.append({"text": msg, "label": "SAFE", "category": "", "group": f"safe:{kind}:{ti}", "source": "generated", "kind": kind})

    # UCI SMS Spam Collection
    uci = HERE / "raw" / "SMSSpamCollection"
    prize = re.compile(r"(?i)\b(won|win|winner|prize|claim|awarded|selected to receive|cash|guaranteed £|bonus)\b")
    ham = []
    for i, line in enumerate(uci.read_text(encoding="utf-8", errors="replace").splitlines()):
        lab, _, txt = line.partition("\t")
        if lab == "ham":
            ham.append((i, txt))
        elif prize.search(txt):
            rows.append({"text": txt, "label": "SCAM", "category": "Lottery/Prize", "group": f"uci:{i}", "source": "uci"})
    rng.shuffle(ham)
    for i, txt in ham[:2500]:
        rows.append({"text": txt, "label": "SAFE", "category": "", "group": f"uci:{i}", "source": "uci", "kind": "personal"})

    # split by group: 25% of templates (and 20% of UCI messages) go to test
    groups = sorted({r["group"] for r in rows})
    test_groups = set()
    by_prefix: dict[str, list[str]] = {}
    for g in groups:
        by_prefix.setdefault(g.rsplit(":", 1)[0], []).append(g)
    for prefix, gs in by_prefix.items():
        rng.shuffle(gs)
        frac = 0.2 if prefix == "uci" else 0.25
        test_groups.update(gs[: max(1, round(len(gs) * frac))])
    for r in rows:
        r["split"] = "test" if r["group"] in test_groups else "train"
        r.setdefault("kind", "scam" if r["label"] == "SCAM" else "personal")
    return rows


if __name__ == "__main__":
    rows = build()
    out = HERE / "messages.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["text", "label", "category", "kind", "group", "source", "split"])
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(len(rows), "messages ->", out)
    print(Counter((r["split"], r["label"]) for r in rows))
    print(Counter(r["category"] for r in rows if r["label"] == "SCAM"))
