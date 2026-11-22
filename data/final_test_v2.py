"""FINAL test set v2 -> data/final_test_v2.csv. Written on 23 Nov 2026 BEFORE the v2 detection fixes, and never
looked at message-by-message while fixing (only the challenge and tester sets were used for error analysis).
It deliberately covers the weak spots the persona testers found: delivery and ride OTPs, bank alerts with compact
dates, fraud-awareness SMS, promos that say "won"/"congrats", scams hosted on free sites and form builders,
requests for "the code you received" without the word OTP, donation scams, family emergencies, digital arrest,
government lookalike domains, and Hinglish/Hindi genuine messages. Never used for training.
"""
import csv
from pathlib import Path

S, G = "SCAM", "SAFE"
K, L, LO, J, O = "KYC/Bank", "Lottery/Prize", "Loan/Credit", "Job/Investment", "Other"
ROWS = [
    # ---------------- scams
    (S, K, "freehost", "SBI Rewards: 6,200 points lapse tonight. Convert to cash here https://sites.google.com/view/sbi-points-cash"),
    (S, K, "freehost", "Your ICICI netbanking will be paused. Re-confirm your details on this form: https://forms.gle/Xy7pQ2kL"),
    (S, K, "freehost", "Axis Bank: complete your account re-validation at https://axis-revalidate.blogspot.com today."),
    (S, O, "freehost", "Electricity board notice: pay pending dues at https://bescom-dues.web.app before 9 PM to keep supply."),
    (S, O, "freehost", "Apply for PM free solar panel scheme. Limited slots. Register: https://pm-solar-yojana.netlify.app"),
    (S, K, "code", "Ma'am, I'm from your bank's card department. Please tell me the 6-digit number you just got by SMS to stop the fraud transaction."),
    (S, O, "code", "Bhaiya maine galti se aapke number pe code bhej diya, wo 6 digit wala number bata do please"),
    (S, O, "code", "Hi, I entered your number by mistake for my login. Can you forward me the code you received just now?"),
    (S, K, "code", "To complete your card upgrade our executive needs the number that came on your mobile. Kindly read it out when he calls."),
    (S, O, "donation", "Flood relief appeal: families in Assam need food. Donate generously to UPI floodhelp.assam@ybl. Every rupee counts. Forward to all."),
    (S, O, "donation", "Jai Shri Ram. Contribute Rs 1100 for Ram Navami bhandara. Send to 9876512340@paytm and share with 11 groups for blessings."),
    (S, O, "donation", "Indian Army welfare fund: soldiers' families need your help. Transfer any amount to A/c 30129876543 IFSC SBIN0001234."),
    (S, O, "family", "Appa it's me, my phone got stolen at the station. Using my friend's mobile. Need 6000 urgently for the ticket, send to this UPI."),
    (S, O, "family", "Hi aunty, Neha here, new number. Stuck in hospital, can you transfer 10,000 now? Don't tell anyone at home please."),
    (S, O, "family", "Maa mera phone kharab ho gaya, ye dost ka number hai. Turant 5000 bhej do, baad me sab bataunga"),
    (S, O, "authority", "Delhi Crime Branch: a SIM in your name is used for money laundering. Stay on this WhatsApp video call. Do not inform anyone or you will be arrested."),
    (S, O, "authority", "Narcotics Control Bureau notice: drugs found in a courier with your Aadhaar. Pay security deposit of Rs 95,000 to avoid arrest."),
    (S, O, "authority", "TRAI: your number will be disconnected in 2 hours for misuse. Press 9 to speak with our legal officer."),
    (S, K, "govlookalike", "UIDAI: your Aadhaar biometric lock expires today. Renew at https://uidai-gov.in/renew to avoid deactivation."),
    (S, O, "govlookalike", "Income tax refund of Rs 18,250 is ready. Verify bank details at https://incometax-gov-refund.in"),
    (S, O, "govlookalike", "Parivahan: unpaid challan Rs 1,000 on your vehicle. Pay today at https://parivahan-gov.co.in/challan"),
    (S, K, "pension", "Dear pensioner, your Jeevan Pramaan is not updated. Pension will stop from next month. Update bank details at http://jeevan-pramaan-update.in"),
    (S, K, "pension", "Treasury office se bol rahe hain. Pension renewal ke liye apna bank account number aur OTP is number par bhejiye 9123498765"),
    (S, O, "remote", "Amazon support: your refund of Rs 2,999 is stuck. Install the QuickSupport app and share the code with our agent."),
    (S, J, "job", "Hello, we got your number from a job portal. Rate hotels on Google and earn Rs 300 per task, paid daily on Telegram."),
    (S, J, "invest", "Join our premium stock group, guaranteed 5% daily profit. Our SEBI-registered expert will guide you. Download app via link."),
    (S, L, "prize", "Dear customer, you have won a Samsung TV in the Diwali lucky draw. Pay Rs 1,499 GST to receive delivery."),
    (S, LO, "loan", "Instant loan Rs 2 lakh without salary slip. Only Aadhaar and PAN. Processing fee Rs 799. Apply via WhatsApp."),
    (S, K, "kyc", "Aapka HDFC account aaj raat band ho jayega. KYC update ke liye is link par click karein hdfc-kyc-verify.in"),
    (S, O, "parcel", "DTDC: your shipment is on hold due to address mismatch. Pay Rs 30 redelivery charge at dtdc-redeliver.top"),
    (S, O, "upi", "I accidentally sent you Rs 3,000 on PhonePe. Please approve the request I sent so it comes back to me."),
    (S, K, "hindi", "आपका एसबीआई खाता निलंबित कर दिया गया है। अपना ओटीपी हमें भेजें ताकि खाता चालू हो सके।"),
    (S, L, "hindi", "बधाई हो! आपका नंबर लकी ड्रॉ में चुना गया है। ₹10 लाख का इनाम पाने के लिए ₹2000 फीस भेजें।"),
    (S, K, "disguised", "Y0ur K.Y.C is p3nding. Upd@te n0w at hdfc-kyc.xyz or acc0unt will be bl0cked"),
    (S, O, "short", "Your electricity will be cut tonight. Call 9876543201 now."),
    # ---------------- genuine
    (G, "", "delivery", "Zomato: your order is on the way. Share OTP 3381 with the delivery partner only after you receive the food."),
    (G, "", "delivery", "Flipkart: your order arrives today. Please share the delivery code 5520 with the Ekart agent at your door."),
    (G, "", "delivery", "BigBasket: Ravi is delivering your order. Share OTP 9921 at the time of delivery. Do not share it on call."),
    (G, "", "delivery", "Blinkit: your order is 5 minutes away. Delivery OTP: 7164. Share it only with the delivery partner."),
    (G, "", "ride", "Your Uber ride OTP is 4417. Share it with your driver Suresh (KA01AB1234) to start the trip."),
    (G, "", "ride", "Rapido: Captain Manju is arriving in 3 mins. Ride PIN 2290. Share PIN only after boarding."),
    (G, "", "bank_alert", "Dear UPI user A/C X4521 debited by 250.0 on date 21Dec26 trf to RAPIDO Refno 512398761234. If not u? call 1800111109. -SBI"),
    (G, "", "bank_alert", "Dear SBI User, your A/c X8890-credited by Rs.5000 on 02Jan27 transfer from MOHAN R Ref No 512312341234 -SBI"),
    (G, "", "bank_alert", "INR 3,450.00 spent on ICICI Bank Card XX1234 on 23-Nov-26 at RELIANCE SMART. Avl Lmt: INR 82,000. Not you? Call 18002662."),
    (G, "", "bank_alert", "Your HDFC Bank Credit Card statement: total amount due Rs 15,240, minimum due Rs 760, due by 08-Dec. Pay via NetBanking or app."),
    (G, "", "bank_alert", "आपके खाते XX7781 से ₹1,200 UPI द्वारा डेबिट किए गए। यदि आपने नहीं किया तो 1800 1234 पर कॉल करें। -पीएनबी"),
    (G, "", "otp", "Your Instagram security code is 552 019. Don't share it with anyone."),
    (G, "", "otp", "OTP for your SBI YONO login is 739201. Do not disclose it to anyone. SBI never asks for OTP."),
    (G, "", "awareness", "Alert from HDFC Bank: fraudsters are posing as bank staff and asking for OTP. We never ask for OTP, PIN or card details. Report at 1930."),
    (G, "", "awareness", "BESCOM never sends SMS asking you to call a mobile number to avoid disconnection. Such messages are fraud. Pay only on bescom.co.in."),
    (G, "", "awareness", "Cyber Dost: digital arrest is a scam. Police never hold people on video call or ask for money. Hang up and call 1930."),
    (G, "", "awareness", "Dear customer, KYC can be updated at any branch or in the app. Do not click links in SMS claiming to update KYC. -Canara Bank"),
    (G, "", "promo", "Congratulations! You've won 50 SuperCoins on your last order. Use them on your next Flipkart purchase."),
    (G, "", "promo", "You won a scratch card! Rs 15 cashback has been added to your Google Pay rewards."),
    (G, "", "promo", "Lucky you! Get flat 40% off on your next Swiggy order with code FEAST40. Valid till Sunday."),
    (G, "", "prize_news", "Congrats to all winners of the inter-school quiz! Prizes will be distributed at the assembly on Monday."),
    (G, "", "prize_news", "Congratulations! You have won the Best Paper award at the student conference. Certificate will be emailed."),
    (G, "", "service", "Planned power shutdown on 26 Nov, 10 AM-3 PM in HSR Layout for maintenance. Inconvenience regretted. -BESCOM"),
    (G, "", "service", "Your FASTag has been recharged with Rs 500. Available balance Rs 640. -Paytm Payments"),
    (G, "", "service", "Your Aadhaar update request has been completed. Download e-Aadhaar from myaadhaar.uidai.gov.in."),
    (G, "", "personal", "Didi kal ghar aa rahi ho na? Mummy ne kheer banayi hai"),
    (G, "", "personal", "Bhai bill split kar dete hai, mera share 450 hai, abhi bhej deta hu"),
    (G, "", "personal", "Ma main pahunch gaya, phone ki battery khatam ho rahi hai, kal baat karta hu"),
    (G, "", "personal", "Mera account ka password bhool gaya, bank jaake reset karwaya, ab sab theek hai"),
    (G, "", "personal", "Papa ne bola hai 2000 bhej diye hai aapke account me, check kar lena"),
    (G, "", "personal", "Can you share the Google Form link for the event registration? Need it by tonight."),
    (G, "", "personal", "Here's the shared folder for the trip photos: https://drive.google.com/drive/folders/abc123"),
    (G, "", "personal", "मैं ऑफिस से निकल गया हूँ, आधे घंटे में घर पहुँचूँगा।"),
]

if __name__ == "__main__":
    out = Path(__file__).parent / "final_test_v2.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "category", "kind", "text"])
        w.writerows(ROWS)
    print(len(ROWS), "final v2 messages ->", out, f"({sum(r[0] == S for r in ROWS)} scam, {sum(r[0] == G for r in ROWS)} genuine)")
