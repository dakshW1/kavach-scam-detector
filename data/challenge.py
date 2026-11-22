"""Hand-written CHALLENGE set -> data/challenge.csv. Never used for training.

These messages were written separately from the generator templates, with different wording, to
check that the model works on phrasing it has not seen. They include hard cases: genuine messages
with links, money and urgency; scams with no link; disguised text; Hinglish and Hindi.

kind: for SCAM rows the language/trick ("english", "hinglish", "hindi", "disguised");
      for SAFE rows the type of genuine message ("bank_alert", "otp", "delivery", "service", "promo", "personal").
"""
import csv
from pathlib import Path

S, G = "SCAM", "SAFE"
ROWS = [
    # ---------------- KYC / Bank
    (S, "KYC/Bank", "english", "SBI: Dear user, we noticed your PAN is missing in our records. Services stop at 6 PM. Upload now on sbi-pan-verify.in"),
    (S, "KYC/Bank", "english", "Your HDFC account access is restricted. Restore it by confirming your customer ID and password here: hdfc-restore.net"),
    (S, "KYC/Bank", "english", "ICICI security team: someone tried to log in from Delhi. Reply with the code you just got so we can stop it."),
    (S, "KYC/Bank", "english", "Dear Axis customer, complete your re-KYC by 9 PM or your savings account will be frozen. Our officer will call you; keep your debit card ready."),
    (S, "KYC/Bank", "hinglish", "Sir aapka Kotak account freeze hone wala hai, KYC ke liye apna aadhar number aur OTP is number pe bhejiye 8012345678"),
    (S, "KYC/Bank", "hinglish", "PNB se bol raha hu, aapka ATM card band ho gaya hai, naya card activate karne ke liye card ke peeche ka CVV bataiye"),
    (S, "KYC/Bank", "disguised", "Y0ur S.B.I a/c is susp3nded. Reactivate n0w: tinyurl.com/sbi-react"),
    (S, "KYC/Bank", "disguised", "Dеаr custоmеr, yоur Ваnk оf Ваrоdа КYС hаs ехpirеd. Updаtе аt bоb-kус.соm"),
    (S, "KYC/Bank", "english", "Jio: your SIM will stop working within 24 hrs as e-KYC is incomplete. Call 7012345678 to complete verification."),
    (S, "KYC/Bank", "hindi", "आपका बैंक खाता निलंबित कर दिया गया है। केवाईसी पूरा करने के लिए इस लिंक पर क्लिक करें bit.ly/kyc-sbi"),
    (S, "KYC/Bank", "english", "Your YONO points (7,250) expire tonight! Convert them to cash: yono-points.click"),
    (S, "KYC/Bank", "english", "Card blocked due to suspicious activity. To unblock, install the 'Bank Support' APK from sbisupport.top/app.apk"),
    # ---------------- Lottery / Prize
    (S, "Lottery/Prize", "english", "Hurray! Your number was picked in our mega draw. Prize: Rs 12 lakh + Mahindra Thar. Send Rs 7,500 tax to receive."),
    (S, "Lottery/Prize", "english", "Amazon anniversary: you are 1 of 50 winners of a free Samsung phone. Just pay shipping Rs 99 at amzn-gifts.xyz"),
    (S, "Lottery/Prize", "hinglish", "KBC office se Rana sir bol rahe hai. Aapka 25 lakh ka lottery laga hai, claim ke liye WhatsApp pe photo aur aadhar bhejo"),
    (S, "Lottery/Prize", "disguised", "C0NGR@TULATI0NS!!! U hav w0n ₹50,00,000 in J!O lucky dr@w. Cl@im: 9988776655"),
    (S, "Lottery/Prize", "english", "Your mobile number has been awarded $500,000 by the Coca-Cola promotion. Email your bank details to claim."),
    (S, "Lottery/Prize", "hindi", "बधाई हो! आपके नंबर ने 10 लाख का इनाम जीता है। प्रोसेसिंग शुल्क 5000 रुपये जमा करें।"),
    (S, "Lottery/Prize", "english", "Spin the wheel and win upto Rs 10,000 Paytm cash. You have 1 free spin left: paytm-spin.online"),
    (S, "Lottery/Prize", "hinglish", "Badhai ho aapko Flipkart ki taraf se scooty mili hai, delivery ke liye sirf 1500 rupay bhejein"),
    # ---------------- Loan / Credit
    (S, "Loan/Credit", "english", "Rs 3,00,000 loan credited to your wallet in 2 mins. Zero paperwork. Tap: loanfast.app/get"),
    (S, "Loan/Credit", "english", "Your loan file is approved. Pay Rs 2,100 stamp duty today to receive Rs 5 lakh in your account."),
    (S, "Loan/Credit", "hinglish", "Bina CIBIL ke loan milega 5 lakh tak, sirf aadhar pan bhejo aur 999 file charge do"),
    (S, "Loan/Credit", "english", "Overdue notice: pay Rs 4,500 in 2 hours or we will send your photos to all your contacts and file a police case."),
    (S, "Loan/Credit", "english", "Pre-sanctioned HDFC personal loan up to 10 lakh at 0.5% interest. Confirm by sharing OTP received now."),
    (S, "Loan/Credit", "disguised", "L.O.A.N appr0ved ₹2,00,000!! N0 d0cuments. Inst@ll app n0w: rb.gy/loan22"),
    (S, "Loan/Credit", "hindi", "बिना दस्तावेज़ 2 लाख का लोन पाएं, सिर्फ 499 रुपये प्रोसेसिंग फीस। अभी कॉल करें 9123456780"),
    (S, "Loan/Credit", "english", "Credit card with 5 lakh limit, lifetime free, no income proof. Pay 799 activation fee to receive the card."),
    # ---------------- Job / Investment
    (S, "Job/Investment", "english", "Looking for people to review Google Maps restaurants. Rs 150 per review, paid daily. Message Riya on WhatsApp wa.me/919812345670"),
    (S, "Job/Investment", "english", "Join our stock market class on Telegram, members made 300% this month with our signals. Limited seats! t.me/profitkings"),
    (S, "Job/Investment", "hinglish", "Sirf 2 ghante kaam karo aur 25000 mahina kamao, mobile se hi. Interested ho toh reply karo"),
    (S, "Job/Investment", "english", "Hello! I'm Neha from a recruitment agency. Your profile matches a remote job paying 4000/day. Can we chat on WhatsApp?"),
    (S, "Job/Investment", "english", "Invest 10,000 in our gold scheme and receive 1,000 every week for life. 100% government approved."),
    (S, "Job/Investment", "disguised", "Earn ₹5000 d@ily fr0m h0me!!! N0 skill needed. J0in t.me/j0bsdaily"),
    (S, "Job/Investment", "hindi", "रोज़ाना 3000 रुपये कमाएं, सिर्फ यूट्यूब वीडियो लाइक करने हैं। टेलीग्राम पर जुड़ें"),
    (S, "Job/Investment", "english", "Your earnings of Rs 18,400 are ready but your account level is low. Deposit Rs 5,000 to upgrade and withdraw."),
    (S, "Job/Investment", "english", "Selected for Infosys work-from-home role. Pay Rs 1,999 for laptop security deposit, refundable after joining."),
    (S, "Job/Investment", "hinglish", "Crypto me 1 lakh lagao, 1 mahine me 3 lakh pakka. Mere group me aa jao"),
    # ---------------- Other
    (S, "Other", "english", "MSEB notice: Your power supply will be stopped at 9:30 tonight as last bill payment is not reflected. Call our office 9876501234."),
    (S, "Other", "hinglish", "Bijli bill pending hai, aaj raat light kaat di jayegi. Turant is number pe sampark karo 9012345678"),
    (S, "Other", "english", "India Post: we tried to deliver your parcel but the address was unclear. Confirm address and pay Rs 25: indiapost-help.top"),
    (S, "Other", "english", "FedEx: a parcel booked in your name to Taiwan has 5 passports and drugs. Call Mumbai Narcotics on Skype now."),
    (S, "Other", "english", "This is officer Sharma from CBI. Your Aadhaar was used in a money laundering case. Stay on this video call and do not inform family."),
    (S, "Other", "english", "Your traffic e-challan of Rs 500 is unpaid. Pay before court action: echallan-parivahan.info"),
    (S, "Other", "english", "Income tax refund of Rs 15,490 approved. Submit account number to receive: itr-refund.in/claim"),
    (S, "Other", "hinglish", "Didi main Rohit, mera phone kharab ho gaya, ye naya number hai. Jaldi 3000 bhej do please, baad me batata hu"),
    (S, "Other", "english", "Hi Dad, I lost my phone, using a friend's. Can you send 8000 to this UPI for my exam fees? Will explain later."),
    (S, "Other", "english", "I paid you 5000 by mistake on Google Pay. Please accept the request I just sent to return it."),
    (S, "Other", "english", "Your WhatsApp account will be deleted. To keep it, send the 6-digit code you received by SMS."),
    (S, "Other", "disguised", "Y0ur g@s c0nnecti0n will b3 cut t0day. C@ll 8899001122 t0 upd@te"),
    (S, "Other", "hindi", "आपके नाम पर एक पार्सल में ड्रग्स मिले हैं। कस्टम्स अधिकारी से तुरंत बात करें वरना गिरफ्तारी होगी।"),
    (S, "Other", "english", "Your FASTag KYC expired. Update now or vehicle blacklisted: fastag-kyc.online"),
    (S, "Other", "english", "Netflix: we could not process your payment. Update billing info within 24h at netflix-billing.help"),
    # ---------------- Genuine: bank alerts
    (G, "", "bank_alert", "INR 1,250.00 debited from A/c no. XX4321 on 21-11-26 for UPI txn to swiggy@icici. Ref 432198765432. Not you? Call 18002586161 - HDFC Bank"),
    (G, "", "bank_alert", "Your A/c XX7788 credited with Rs.45,000.00 on 01-Nov-26 by NEFT from ACME TECH PVT LTD. Avl Bal Rs.52,310.40 -SBI"),
    (G, "", "bank_alert", "Dear Customer, transaction of Rs 899 on your ICICI Bank Credit Card XX5521 at NETFLIX is successful. Available limit Rs 1,12,000."),
    (G, "", "bank_alert", "Rs 200 withdrawn at ATM on 20/11/26 from A/c **9012. Avl bal Rs 3,410. If not done by you, call 1800 1234 to block card. -PNB"),
    (G, "", "bank_alert", "Your Kotak A/c xx6543 is debited by Rs.15,000 towards EMI for loan ending 7781. Thank you."),
    (G, "", "bank_alert", "Minimum balance alert: your account XX2234 balance is below Rs 1,000. Please maintain balance to avoid charges. -Axis Bank"),
    (G, "", "bank_alert", "Your credit card statement is ready. Total due Rs 6,420, due date 05-Dec. Pay on the iMobile app or icicibank.com."),
    (G, "", "bank_alert", "We have received your request to update your mobile number. If you did not request this, please visit your nearest SBI branch."),
    (G, "", "bank_alert", "Your new debit card has been dispatched by Speed Post. It will reach your registered address in 5-7 days. -Canara Bank"),
    (G, "", "bank_alert", "Your KYC has been successfully updated at our branch on 18-11-26. Thank you for banking with us. -Bank of Baroda"),
    # ---------------- Genuine: OTPs
    (G, "", "otp", "839201 is the OTP for your Rs 1,499 purchase at Myntra on card XX4421. OTP valid for 5 mins. Do not share with anyone - Axis Bank"),
    (G, "", "otp", "Your Zomato verification code is 4417. Do not share it with anyone."),
    (G, "", "otp", "Use 552190 to log in to your PhonePe account. Never share your OTP, PhonePe will never call you for it."),
    (G, "", "otp", "OTP to confirm your Amazon Pay transaction of Rs 349 is 771025. Valid for 3 minutes. Don't share."),
    (G, "", "otp", "Dear Customer, 918273 is your OTP to add a new beneficiary. If not initiated by you, call 1800-425-3800. -SBI"),
    (G, "", "otp", "Your Instagram code is 334 902. Don't share it."),
    (G, "", "otp", "012345 is your OTP for EPFO UAN login. Valid for 10 minutes. Do not share this OTP with anyone."),
    (G, "", "otp", "आपका ओटीपी 664120 है। कृपया इसे किसी के साथ साझा न करें। -आईसीआईसीआई बैंक"),
    # ---------------- Genuine: delivery
    (G, "", "delivery", "Your Amazon package with Boat earphones will be delivered today by 9 PM. Track: https://amzn.in/d/8xYz2Lm"),
    (G, "", "delivery", "Delhivery: your shipment from Meesho is out for delivery. Please keep Rs 349 ready (Cash on Delivery)."),
    (G, "", "delivery", "Blue Dart: AWB 8123456789 delivered to your address on 20 Nov at 2:15 PM. Thank you."),
    (G, "", "delivery", "Your Blinkit order is arriving in 8 minutes. Delivery partner: Suresh."),
    (G, "", "delivery", "We could not deliver your Flipkart order today as no one was available. We will try again tomorrow."),
    (G, "", "delivery", "Refund of Rs 1,299 for your returned Myntra order has been processed to your UPI account. It may take 2-4 days to reflect."),
    # ---------------- Genuine: services / bills / government
    (G, "", "service", "BESCOM: Bill for RR no. 1234567 for Nov-26 is Rs 842. Due date 05-12-26. Pay online at bescom.co.in"),
    (G, "", "service", "Airtel: your prepaid pack expires tomorrow. Recharge on Airtel Thanks app to stay connected."),
    (G, "", "service", "Your Indane LPG booking 7788123 is confirmed. Cash memo amount Rs 905. Do not pay extra to the delivery person."),
    (G, "", "service", "Reminder: your appointment at Manipal Hospital is tomorrow at 10:30 AM. Please arrive 15 minutes early."),
    (G, "", "service", "Your traffic challan of Rs 500 for KA01AB1234 has been generated. Pay at echallan.parivahan.gov.in or visit the nearest traffic police station."),
    (G, "", "service", "Dear taxpayer, your ITR for AY 2026-27 has been processed. Refund of Rs 3,210 will be credited to your bank account. -Income Tax Department"),
    (G, "", "service", "Jio: you have used 90% of your daily data. Speed will reduce after 100%. Get a data booster on MyJio."),
    (G, "", "service", "Your PNR 4512367890 is waitlisted WL 12. Check status on the IRCTC app before travel."),
    (G, "", "service", "Cyber fraud alert from Bengaluru Police: never share OTP, never install screen sharing apps on request. Report fraud on 1930."),
    (G, "", "service", "Your electricity supply will be interrupted on 24-Nov from 10 AM to 2 PM for maintenance work in Jayanagar. Inconvenience regretted. -BESCOM"),
    # ---------------- Genuine: promos
    (G, "", "promo", "End of season sale! Flat 50% off at Westside this weekend only. Visit your nearest store."),
    (G, "", "promo", "Zomato: hungry? Get 60% off up to Rs 120 on your next 3 orders. Use code WELCOME60."),
    (G, "", "promo", "Upgrade to Airtel Black and get Netflix free for 6 months. Know more on the Airtel Thanks app."),
    (G, "", "promo", "Your Nykaa reward points (450) expire on 30 Nov. Use them on the app before they lapse."),
    # ---------------- Genuine: personal
    (G, "", "personal", "Bhai lottery ticket wala joke dekha tune? Group pe bheja hai, hasi nahi ruk rahi"),
    (G, "", "personal", "Mom please send 2000, I need to pay the hostel mess fee today. I'll call you tonight."),
    (G, "", "personal", "Can you share the OTP sheet for the chemistry lab? Ma'am said to bring it tomorrow."),
    (G, "", "personal", "Yaar mera phone kharab ho gaya tha, isliye reply nahi kiya. Kal baat karte hai"),
    (G, "", "personal", "Congratulations on the new job!! You deserved it. Treat pending!"),
    (G, "", "personal", "Urgent: meeting moved to 4 PM, bring the laptop and the project report."),
    (G, "", "personal", "Did the bank call you about the loan papers? Papa was asking."),
    (G, "", "personal", "Papa ka account block ho gaya tha, branch jaake KYC karwa liya, ab sab theek hai"),
    (G, "", "personal", "कल शाम को मंदिर चलेंगे, तैयार रहना।"),
    (G, "", "personal", "Sending you the link to the class recording: https://drive.google.com/file/d/1abcXYZ/view"),
]

if __name__ == "__main__":
    out = Path(__file__).parent / "challenge.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "category", "kind", "text"])
        w.writerows(ROWS)
    print(len(ROWS), "challenge messages ->", out,
          f"({sum(r[0] == S for r in ROWS)} scam, {sum(r[0] == G for r in ROWS)} genuine)")
