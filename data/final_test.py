"""FINAL held-out test set -> data/final_test.csv

Written BEFORE any tuning of rules/templates, and never looked at message-by-message while improving
the model (only the challenge set was used for error analysis). The headline numbers in the README
come from this file, so they are an honest estimate on unseen wording.
"""
import csv
from pathlib import Path

S, G = "SCAM", "SAFE"
ROWS = [
    # KYC / Bank
    (S, "KYC/Bank", "english", "Attention: your Union Bank debit card will be permanently disabled at midnight. Re-verify here: union-card-verify.com"),
    (S, "KYC/Bank", "english", "We are calling from SBI head office. For your safety we will send a code, please read it out to us to secure your account."),
    (S, "KYC/Bank", "hinglish", "Namaste, HDFC bank se. Aapka account hold par hai, PAN update karne ke liye niche link kholiye hdfc-pan.co"),
    (S, "KYC/Bank", "disguised", "ІСІСІ Bаnk: yоur ассоunt wіll bе lосkеd. Vеrіfy: icici-lock.top"),
    (S, "KYC/Bank", "english", "Airtel KYC team: your number will be disconnected in 3 hours. Install 'KYC Helper' app from airtel-kyc.app to continue."),
    (S, "KYC/Bank", "hindi", "प्रिय ग्राहक, आपका डेबिट कार्ड ब्लॉक हो गया है। अनब्लॉक करने के लिए अपना ओटीपी हमें भेजें।"),
    (S, "KYC/Bank", "english", "Your Paytm wallet KYC will expire today, after which your balance will be lost. Call support 9871234560."),
    (S, "KYC/Bank", "disguised", "Dear user, ur net-b@nking acc0unt is l0cked. Unl0ck: bit.ly/unl0ck-nb"),
    # Lottery / Prize
    (S, "Lottery/Prize", "english", "You've been chosen as our Lucky Customer of the month! Collect your Rs 1,00,000 voucher by paying Rs 2,999 handling fee."),
    (S, "Lottery/Prize", "hinglish", "Mubarak ho! Aapka mobile number 15 lakh ke inaam ke liye chuna gaya hai. Claim ke liye hamare agent se baat karein 9765432109"),
    (S, "Lottery/Prize", "english", "Final notice: unclaimed prize money Rs 8,50,000 in your name. Reply with account number and IFSC before it is cancelled."),
    (S, "Lottery/Prize", "disguised", "Y0u are a W1NNER of a brand new Royal Enfield! Cl@im n0w at re-giveaway.online"),
    (S, "Lottery/Prize", "hindi", "आप हमारे लकी ड्रॉ के विजेता हैं! 25 लाख रुपये पाने के लिए 3500 रुपये GST जमा करें।"),
    (S, "Lottery/Prize", "english", "Congratulations! Your WhatsApp number won the Diwali bumper draw. Contact our claims office to collect Rs 35 lakh."),
    # Loan / Credit
    (S, "Loan/Credit", "english", "Hi! Get cash up to 5 lakh in your bank in 10 minutes, no salary slip needed. Download: cashnow-loan.apk"),
    (S, "Loan/Credit", "hinglish", "Loan approve ho gaya hai 3 lakh ka, bas 1200 insurance charge bhejo phir paisa account me aa jayega"),
    (S, "Loan/Credit", "english", "Last warning: your loan repayment is late. Pay now or we will call your relatives and post your photo online."),
    (S, "Loan/Credit", "disguised", "Instant L0AN ₹50,000 – n0 CIBIL, n0 d0cs!! Apply: tinyurl.com/l0an50"),
    (S, "Loan/Credit", "hindi", "आपका 5 लाख का पर्सनल लोन तैयार है। सिर्फ 999 रुपये फाइल चार्ज भेजें और लोन पाएं।"),
    (S, "Loan/Credit", "english", "Your credit card has been selected for a free limit upgrade. Tell us the OTP you receive to confirm."),
    # Job / Investment
    (S, "Job/Investment", "english", "Hiring: product reviewers needed, 30 mins a day, earn Rs 2,500 daily. No interview. Contact HR on Telegram @hr_priya"),
    (S, "Job/Investment", "hinglish", "Bhai ek app hai jisme paisa 20 din me double hota hai, maine bhi lagaya, tu bhi 5000 daal de"),
    (S, "Job/Investment", "english", "Your resume is shortlisted for a Data Entry role at Rs 35,000/month. Pay Rs 1,500 registration to book your interview slot."),
    (S, "Job/Investment", "english", "Exclusive: join our insider trading WhatsApp group, members earn 10% daily guaranteed. Only 5 seats left."),
    (S, "Job/Investment", "disguised", "W0rk fr0m h0me & earn ₹4000/d@y. J0in t.me/earn4k"),
    (S, "Job/Investment", "hindi", "घर बैठे पार्ट टाइम जॉब, रोज़ 2000 से 5000 रुपये कमाएं। अभी व्हाट्सएप करें।"),
    (S, "Job/Investment", "english", "To withdraw your task earnings of Rs 26,000 you must first clear the tax of Rs 3,900. Contact your mentor."),
    # Other
    (S, "Other", "english", "Electricity Dept: your connection will be cut off at 10 PM due to pending bill verification. Call the officer at 8123456790 now."),
    (S, "Other", "hinglish", "Aapka parcel customs me ruka hua hai, 450 rupay clearance fees bharni hogi, link pe pay karo indpost-clear.top"),
    (S, "Other", "english", "Delhi Police: a case is registered against your mobile number for sending illegal messages. Join the video call immediately and do not disconnect."),
    (S, "Other", "english", "Mum it's me, I broke my phone and this is a temporary number. Can you transfer 6000 now? It's urgent, I'll explain."),
    (S, "Other", "english", "Your income tax refund of Rs 12,300 is on hold. Update your bank account at incometax-refunds.co to release it."),
    (S, "Other", "english", "Hello, I sent Rs 2,000 to your number by mistake. Kindly approve the collect request to send it back."),
    (S, "Other", "hinglish", "Aapki gaadi ka challan pending hai, court case se bachne ke liye aaj hi pay karo echallan-pay.site"),
    (S, "Other", "english", "Hey, I accidentally sent my WhatsApp verification code to your number. Can you forward it to me please?"),
    (S, "Other", "hindi", "आपके बिजली बिल का भुगतान नहीं हुआ है। आज रात 9 बजे आपकी बिजली काट दी जाएगी। तुरंत संपर्क करें 9988123456"),
    (S, "Other", "english", "Customs: your international package needs duty payment of Rs 1,850 before release. Pay within 12 hours or it will be returned."),
    # Genuine
    (G, "", "bank_alert", "UPI txn of Rs 75.00 to CHAI POINT on 22-11-26 from A/c XX3412. UPI Ref 512398765400. Not you? SMS BLOCK to 9215676766 -Axis Bank"),
    (G, "", "bank_alert", "Rs 12,000.00 credited to A/c XXXX8890 on 15-Nov-26 (IMPS from RAVI KUMAR). Available balance Rs 18,442.10. -Canara Bank"),
    (G, "", "bank_alert", "Your SBI Credit Card ending 4411 has a payment due of Rs 3,560 on 28 Nov. Pay via SBI Card app. Ignore if paid."),
    (G, "", "bank_alert", "Dear customer, your ATM PIN was changed successfully on 20-11-26. If not done by you, call 1800 1080 immediately. -SBI"),
    (G, "", "bank_alert", "Your NACH mandate for Rs 2,000 monthly SIP has been registered on A/c XX7621. -ICICI Bank"),
    (G, "", "bank_alert", "Your account XX9910 has been credited with interest of Rs 423.00 for the quarter. -Kotak Mahindra Bank"),
    (G, "", "bank_alert", "Your fixed deposit of Rs 1,00,000 has been renewed for 12 months at 7.1%. Details in the YONO app."),
    (G, "", "otp", "Do not share this OTP with anyone. 274591 is your OTP to log in to Paytm. Paytm never calls for OTP."),
    (G, "", "otp", "Your OTP for ITR e-verification is 662013. It is valid for 15 minutes. -Income Tax Department"),
    (G, "", "otp", "773402 is your Swiggy login OTP. Please don't share it with anyone."),
    (G, "", "otp", "OTP for card XX9087 txn of INR 4,999.00 at FLIPKART is 448120. Valid 5 min. Never share OTP. -HDFC Bank"),
    (G, "", "otp", "Your Google verification code is 552183."),
    (G, "", "otp", "Your Aadhaar OTP is 810362 for updating address. UIDAI never asks for OTP on phone call or email."),
    (G, "", "delivery", "Ekart: your Flipkart order with 2 items will be delivered today. Share the delivery code 4421 only with the agent."),
    (G, "", "delivery", "Your Nykaa order has been packed and will be shipped soon. Track it on the Nykaa app."),
    (G, "", "delivery", "India Post: your Speed Post article EB123456789IN is out for delivery today."),
    (G, "", "delivery", "Your Domino's order is out for delivery and will reach you in 15 mins."),
    (G, "", "delivery", "Amazon: we have issued a refund of Rs 649 for your cancelled order. It will be credited in 3-5 business days."),
    (G, "", "service", "Your Airtel bill of Rs 599 is generated. Due date 03-Dec. Pay via Airtel Thanks app or airtel.in."),
    (G, "", "service", "Planned power shutdown in Koramangala on 25-Nov, 10 AM to 4 PM, for line maintenance. -BESCOM"),
    (G, "", "service", "Your ITR has been successfully filed and verified. Acknowledgement number 4512XXXX. -Income Tax Department"),
    (G, "", "service", "Your vehicle registration KA03MM1234 PUC certificate expires on 30-11-26. Renew at an authorised centre."),
    (G, "", "service", "RBI cautions: never share card details, OTP or UPI PIN with anyone, including bank staff. Report fraud at 1930."),
    (G, "", "service", "Your Practo consultation with Dr. Mehta is confirmed for tomorrow 6 PM. Join via the Practo app."),
    (G, "", "promo", "Weekend special: buy 2 get 1 free on all T-shirts at Max Fashion. Valid till Sunday."),
    (G, "", "promo", "Swiggy One: get free deliveries for 3 months at just Rs 99. Upgrade in the app."),
    (G, "", "promo", "Congratulations! You have earned 120 reward points on your last purchase at Reliance Digital."),
    (G, "", "personal", "Ma, I reached the hostel. Phone battery low, will call you tomorrow."),
    (G, "", "personal", "Bhai mera naya number save kar le, purana wala band kar diya"),
    (G, "", "personal", "Can you lend me 500 till Friday? Will return on payday, promise"),
    (G, "", "personal", "Kal ka quiz postpone ho gaya, sir ne group pe bataya"),
    (G, "", "personal", "We won the inter-college cricket match today!! 🏏"),
    (G, "", "personal", "Did you pay the electricity bill? Last date is tomorrow I think"),
    (G, "", "personal", "Hey, the code for the wifi is on the fridge"),
    (G, "", "personal", "बेटा, खाना टाइम पर खा लेना और पढ़ाई पर ध्यान देना।"),
]

if __name__ == "__main__":
    out = Path(__file__).parent / "final_test.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "category", "kind", "text"])
        w.writerows(ROWS)
    print(len(ROWS), "final test messages ->", out,
          f"({sum(r[0] == S for r in ROWS)} scam, {sum(r[0] == G for r in ROWS)} genuine)")
