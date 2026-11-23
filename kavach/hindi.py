"""Hindi (हिंदी) text for everything the result shows: sign names and reasons, checks, advice, scam types.
Used when the website is switched to Hindi. Long link explanations stay in English (they quote web addresses).
"""
from __future__ import annotations

# rule id -> (label, reason)
RULES_HI = {
    "asks_secret": ("गुप्त कोड माँग रहा है", "यह आपसे OTP / PIN / CVV / पासवर्ड बताने या डालने को कह रहा है। बैंक, पुलिस या कंपनी ये कभी नहीं माँगते।"),
    "kyc": ("मैसेज से KYC", "यह लिंक या कॉल से KYC अपडेट करने को कह रहा है। बैंक कभी SMS या WhatsApp लिंक से KYC नहीं कराते।"),
    "threat": ("बंद करने की धमकी", "यह खाता, कार्ड, सिम, पेंशन या कनेक्शन बंद करने की धमकी दे रहा है। ठग डर दिखाकर जल्दबाज़ी कराते हैं।"),
    "urgency": ("जल्दबाज़ी करा रहा है", "यह तुरंत कुछ करने का दबाव डाल रहा है। असली संस्थाएँ आपको समय देती हैं।"),
    "prize": ("इनाम का लालच", "यह कहता है कि आपने इनाम या लॉटरी जीती है जिसमें आपने हिस्सा ही नहीं लिया। SMS से कोई पैसे नहीं बाँटता।"),
    "congrats": ("बधाई दे रहा है", "बधाई से शुरुआत इनाम और नौकरी वाले धोखे में आम है (अकेले इसका ज़्यादा मतलब नहीं)।"),
    "fee": ("पहले पैसे माँग रहा है", "पैसा, लोन, नौकरी या पार्सल पाने से पहले फीस या जमा राशि माँग रहा है। पाने के लिए पहले देना ही धोखे की जड़ है।"),
    "loan_bait": ("लोन का लालच", "बिना कागज़ या जाँच के तुरंत लोन का वादा। नकली लोन ऐप डेटा चुराते हैं और फीस वसूलते हैं।"),
    "job_bait": ("नौकरी / टास्क का लालच", "आसान ऑनलाइन काम से आसान कमाई का वादा। ऐसे 'टास्क जॉब' में अंत में कमाई निकालने के लिए पैसे माँगे जाते हैं।"),
    "invest_bait": ("निवेश का लालच", "पक्के या बहुत ज़्यादा मुनाफ़े का वादा। असली निवेश कभी मुनाफ़े की गारंटी नहीं देता।"),
    "authority": ("अधिकारी बनकर धमकी", "पुलिस, CBI, कस्टम्स, कोर्ट या TRAI बनकर डराया जा रहा है। अधिकारी SMS या वीडियो कॉल पर गिरफ्तारी या पैसे की बात नहीं करते।"),
    "disconnection": ("बिल / कनेक्शन कटने का डर", "आज रात बिजली, गैस या फ़ोन कटने की बात। असली बिल में नियत तारीख होती है, आधी रात की धमकी नहीं।"),
    "parcel": ("पार्सल / डिलीवरी का जाल", "पार्सल रुका है या पता अधूरा है कहकर लिंक या फीस माँगी जा रही है। कूरियर SMS लिंक से फीस नहीं माँगते।"),
    "refund": ("रिफ़ंड / कैशबैक का लालच", "रिफ़ंड या कैशबैक 'क्लेम' करने को कहा जा रहा है। असली रिफ़ंड अपने आप वापस आता है।"),
    "collect_request": ("'पैसे पाने' के लिए PIN / QR", "पैसे पाने के लिए PIN डालने, QR स्कैन करने या रिक्वेस्ट अप्रूव करने को कहा जा रहा है। PIN सिर्फ़ पैसे भेजने में लगता है, पाने में कभी नहीं।"),
    "remote_app": ("ऐप इंस्टॉल करवाना", "AnyDesk, TeamViewer या कोई .apk इंस्टॉल करने को कहा जा रहा है। इससे ठग आपका फ़ोन चला सकता है।"),
    "pressure_secrecy": ("आपको अकेला कर रहा है", "परिवार या किसी को न बताने या कॉल पर बने रहने को कहा जा रहा है। ठग पीड़ित को अकेला करते हैं ताकि कोई रोक न सके।"),
    "money_bait": ("बड़ी रकम का लालच", "बिना माँगे आपको बड़ी रकम (इनाम, लोन या कमाई) देने की बात।"),
    "money_demand": ("पैसे भेजने को कह रहा है", "किसी व्यक्ति या खाते में पैसे भेजने या जमा करने को कहा जा रहा है। असली व्यक्ति को अपने जाने-पहचाने नंबर पर फ़ोन करके पक्का करें।"),
    "asks_details": ("बैंक / निजी जानकारी माँग रहा है", "बैंक, कार्ड, आधार या PAN की जानकारी भेजने या भरने को कहा जा रहा है। ये SMS, WhatsApp या फ़ॉर्म लिंक से नहीं माँगे जाते।"),
    "chain_forward": ("चेन फ़ॉरवर्ड", "इसे बहुत लोगों को भेजने को कहा जा रहा है, या भाग्य / नुकसान की बात है। ऐसे फ़ॉरवर्ड अफ़वाह और धोखा फैलाते हैं।"),
    "shame_threat": ("बदनाम करने की धमकी", "आपके कॉन्टैक्ट्स को मैसेज करने या फ़ोटो डालने की धमकी। अवैध लोन ऐप ऐसा करते हैं – 1930 पर शिकायत करें।"),
    "donation_request": ("दान माँग रहा है", "ऐसे UPI ID या खाते में दान माँगा जा रहा है जिसे आप जाँच नहीं सकते। नकली मंदिर और राहत अपील असली जैसी दिखती हैं।"),
    "click_now": ("लिंक दबाने का दबाव", "कुछ ठीक करने, क्लेम करने या वेरिफ़ाई करने के लिए लिंक दबाने को कहा जा रहा है।"),
    "family_emergency": ("'परिवार' की नकली इमरजेंसी", "'नया नंबर' या 'फ़ोन टूट गया' कहकर तुरंत पैसे माँगे जा रहे हैं। पैसे देने से पहले उस व्यक्ति को उसके पुराने नंबर पर फ़ोन करें।"),
    "link_dangerous": ("ख़तरनाक लिंक", "यह लिंक असली वेबसाइट का नहीं है। विवरण नीचे लिंक वाले हिस्से में देखें।"),
    "link_suspicious": ("संदिग्ध लिंक", "यह लिंक असली पता छिपाता है या किसी अनजान साइट पर ले जाता है। इसे न खोलें।"),
    "link_action": ("अनजान लिंक से काम करवाना", "रद्द करने, वेरिफ़ाई करने या पैसे देने के लिए अनजान लिंक दबाने को कहा जा रहा है। असली बैंक अपना ऐप या हेल्पलाइन बताते हैं।"),
    "personal_mobile": ("निजी मोबाइल नंबर", "आम 10 अंकों के मोबाइल नंबर पर संपर्क करने को कहा जा रहा है। बैंक और कंपनियाँ आधिकारिक हेल्पलाइन (अक्सर 1800...) देती हैं।"),
    "sender_mobile": ("निजी नंबर से आया", "मैसेज किसी संस्था के नाम से है पर आम मोबाइल नंबर से भेजा गया है। बैंक 'AX-SBIINB-S' जैसे रजिस्टर्ड ID से SMS भेजते हैं।"),
    "sender_international": ("विदेशी / अजीब नंबर", "भेजने वाला नंबर आम भारतीय मोबाइल या कंपनी ID नहीं है।"),
    "disguised": ("छिपाकर लिखा गया", "शब्दों को अंकों या मिलते-जुलते अक्षरों से छिपाया गया है ताकि फ़िल्टर पकड़ न सके। असली कंपनियाँ ऐसा नहीं करतीं।"),
    "unreadable_script": ("यह भाषा Kavach नहीं पढ़ सकता", "यह मैसेज ज़्यादातर ऐसी लिपि में है जिस पर Kavach सीखा नहीं है, इसलिए इसे सुरक्षित नहीं कहा जा सकता।"),
    # reassuring signs
    "otp_dont_share": ("कहता है: OTP किसी को न बताएँ", "यह कोड किसी को न बताने को कहता है – असली OTP मैसेज यही कहते हैं।"),
    "handover_code": ("डिलीवरी / राइड कोड", "यह आपको डिलीवरी वाले या ड्राइवर को सामने दिखाने के लिए कोड देता है – असली डिलीवरी OTP ऐसे ही होते हैं।"),
    "awareness": ("धोखे से सावधान करने वाला मैसेज", "यह धोखे के बारे में चेतावनी देता है और कुछ नहीं माँगता – असली बैंक और पुलिस अलर्ट ऐसे होते हैं।"),
    "shop_offer": ("आम शॉपिंग ऑफ़र", "यह दुकान का सामान्य डिस्काउंट या रिवॉर्ड है और न पैसे माँगता है न जानकारी।"),
    "event_result": ("असली प्रतियोगिता का नतीजा", "यह किसी प्रतियोगिता या परीक्षा का नतीजा बताता है, इनाम कहाँ-कब मिलेगा बताता है, और कुछ नहीं माँगता।"),
    "no_fee": ("कहता है कोई फीस नहीं", "यह साफ़ कहता है कि कोई फीस नहीं ली जाएगी – असली कंपनियाँ और कॉलेज यही कहते हैं।"),
    "visit_branch": ("ब्रांच / आधिकारिक ऐप भेजता है", "यह लिंक या फ़ोन नंबर के बजाय ब्रांच या आधिकारिक ऐप जाने को कहता है।"),
    "masked_account": ("छिपा हुआ खाता नंबर", "इसमें खाते के सिर्फ़ आख़िरी अंक (जैसे XX1234) हैं – असली बैंक अलर्ट ऐसे ही होते हैं।"),
    "transaction_ref": ("लेन-देन का विवरण", "इसमें रेफ़रेंस नंबर या बैलेंस है – असली लेन-देन अलर्ट में यह होता है।"),
    "order_update": ("ऑर्डर / डिलीवरी अपडेट", "यह आपके किए ऑर्डर के बारे में सामान्य अपडेट है।"),
    "not_you_report": ("शिकायत का आधिकारिक तरीका", "अगर लेन-देन आपने नहीं किया तो आधिकारिक हेल्पलाइन पर कॉल करने को कहता है – असली बैंक यही करते हैं।"),
    "planned_notice": ("तय मरम्मत की सूचना", "तारीख और समय के साथ तय बिजली कटौती या मरम्मत की सूचना – असली संस्थाएँ ऐसे ही बताती हैं।"),
    "valid_for": ("कोड कितनी देर चलेगा", "असली OTP मैसेज बताते हैं कि कोड कितनी देर मान्य है।"),
    "link_official": ("आधिकारिक लिंक", "यह लिंक संस्था की असली वेबसाइट पर जाता है।"),
}

CHECKS_HI = {
    "Does not ask for your OTP, PIN, CVV, card or bank details": "OTP, PIN, CVV, कार्ड या बैंक की जानकारी नहीं माँगता",
    "Does not ask you to update KYC through a link or a phone call": "लिंक या फ़ोन कॉल से KYC अपडेट करने को नहीं कहता",
    "Does not threaten to block or freeze your account": "खाता बंद या फ़्रीज़ करने की धमकी नहीं देता",
    "Does not ask you to pay, transfer money or approve a request": "पैसे देने, भेजने या रिक्वेस्ट अप्रूव करने को नहीं कहता",
    "No pressure to act within minutes or hours": "मिनटों या घंटों में कुछ करने का दबाव नहीं",
    "Does not ask you to install an app or share your screen": "कोई ऐप इंस्टॉल करने या स्क्रीन शेयर करने को नहीं कहता",
    "Gives no personal mobile number to call – only an official helpline, if any": "कोई निजी मोबाइल नंबर नहीं – केवल आधिकारिक हेल्पलाइन",
    "Does not ask you to share, forward or read out the code": "कोड किसी को बताने या भेजने को नहीं कहता",
    "Gives no mobile number for you to call back": "वापस कॉल करने के लिए कोई मोबाइल नंबर नहीं देता",
    "No threat or deadline pushing you to hand the code over": "कोड देने के लिए कोई धमकी या समय-सीमा नहीं",
    "Does not ask you to install an app": "कोई ऐप इंस्टॉल करने को नहीं कहता",
    "Does not ask for a redelivery, customs or address-update fee": "दोबारा डिलीवरी, कस्टम्स या पता बदलने की फीस नहीं माँगता",
    "No 'parcel held / address incomplete' story": "'पार्सल रुका है / पता अधूरा है' वाली कहानी नहीं",
    "Does not ask for your bank, card or personal details": "बैंक, कार्ड या निजी जानकारी नहीं माँगता",
    "No customs or police threat about the parcel": "पार्सल को लेकर कस्टम्स या पुलिस की धमकी नहीं",
    "Does not ask you to pay a fee or tax to get the reward": "इनाम पाने के लिए फीस या टैक्स नहीं माँगता",
    "Does not ask for your card, bank or personal details": "कार्ड, बैंक या निजी जानकारी नहीं माँगता",
    "No big cash prize from a draw you never entered": "ऐसे ड्रॉ का बड़ा इनाम नहीं जिसमें आपने हिस्सा न लिया हो",
    "No pressure to claim it within minutes": "मिनटों में क्लेम करने का दबाव नहीं",
    "No threat to cut the service tonight unless you call or pay": "आज रात सेवा काटने की धमकी नहीं",
    "Does not ask you to pay through a link or to a person": "लिंक से या किसी व्यक्ति को पैसे देने को नहीं कहता",
    "Gives no personal mobile number of an 'officer' to call": "किसी 'अधिकारी' का निजी नंबर नहीं देता",
    "No pressure to act within minutes": "मिनटों में कुछ करने का दबाव नहीं",
    "Does not ask you for any code or personal details": "कोई कोड या निजी जानकारी नहीं माँगता",
    "Does not ask you to pay anything": "कोई पैसे नहीं माँगता",
    "Points to official helplines, not a personal mobile number": "आधिकारिक हेल्पलाइन बताता है, निजी नंबर नहीं",
    "Does not ask you to update KYC through a link or a call": "लिंक या कॉल से KYC अपडेट करने को नहीं कहता",
    "Does not ask for your OTP, PIN or bank details": "OTP, PIN या बैंक जानकारी नहीं माँगता",
    "No threat or deadline": "कोई धमकी या समय-सीमा नहीं",
    "No 'new number / lost phone / stuck somewhere' emergency story": "'नया नंबर / फ़ोन खो गया / कहीं फँसा हूँ' वाली कहानी नहीं",
    "No urgent request to send money to an account or UPI ID": "किसी खाते या UPI ID पर तुरंत पैसे भेजने को नहीं कहता",
    "Does not ask for a code you received": "आपको आया कोई कोड नहीं माँगता",
    "Not a chain forward asking you to share it with many people": "बहुत लोगों को भेजने वाला चेन फ़ॉरवर्ड नहीं",
    "Does not ask you to keep it secret from family": "परिवार से छिपाने को नहीं कहता",
    "Does not ask you for an OTP, PIN, password, card or bank details": "OTP, PIN, पासवर्ड, कार्ड या बैंक जानकारी नहीं माँगता",
    "Does not ask you to pay, transfer, deposit or approve a request": "पैसे देने, भेजने, जमा करने या रिक्वेस्ट अप्रूव करने को नहीं कहता",
    "No threat to block an account, cut a service or arrest you": "खाता बंद करने, सेवा काटने या गिरफ्तारी की धमकी नहीं",
    "No pressure to act within minutes or hours ": "मिनटों या घंटों में कुछ करने का दबाव नहीं",
    "No prize, loan, job, investment or refund offer to lure you": "इनाम, लोन, नौकरी, निवेश या रिफ़ंड का लालच नहीं",
    "Written normally – no disguised letters or hidden characters": "सामान्य तरीके से लिखा है – कोई छिपे अक्षर नहीं",
    "Contains no links to click": "कोई लिंक नहीं",
    "Sent from a registered business sender ID (TRAI format)": "रजिस्टर्ड कंपनी ID से भेजा गया (TRAI फ़ॉर्मेट)",
}

KIND_HI = {
    "a delivery or ride code": "डिलीवरी या राइड का कोड",
    "a bank transaction alert": "बैंक लेन-देन का अलर्ट",
    "an order or delivery update": "ऑर्डर या डिलीवरी का अपडेट",
    "a service reminder from an organisation": "किसी संस्था का सेवा रिमाइंडर",
    "a fraud-awareness message": "धोखे से सावधान करने वाला मैसेज",
    "a one-time password (OTP) message": "OTP मैसेज",
    "a bank or payment alert": "बैंक या भुगतान अलर्ट",
    "an ordinary notice": "सामान्य सूचना",
    "a service or maintenance notice": "सेवा या मरम्मत की सूचना",
    "an ordinary shopping offer": "आम शॉपिंग ऑफ़र",
    "a message with an official link": "आधिकारिक लिंक वाला मैसेज",
    "a bank or service alert": "बैंक या सेवा अलर्ट",
    "an ordinary personal message": "आम निजी मैसेज",
    "an ordinary message with a link": "लिंक वाला आम मैसेज",
}
WHY_HI = "इसमें धोखे के बड़े संकेत नहीं मिले। फिर भी कुछ करने से पहले नीचे की बातें पढ़ें।"
SAFE_WHY_HI = "यह पैसे, कोड, निजी जानकारी या जल्दबाज़ी नहीं माँगता।"

CAUTIONS_HI = {
    "It does ask for a payment. Before paying, confirm the person and the amount yourself through a number you already know.":
        "यह पैसे माँग रहा है। देने से पहले अपने जाने-पहचाने नंबर पर फ़ोन करके व्यक्ति और रकम पक्की करें।",
    "It mentions a code or PIN. Only use it yourself – never share it with anyone who calls or messages you.":
        "इसमें कोड या PIN है। इसे सिर्फ़ ख़ुद इस्तेमाल करें – फ़ोन या मैसेज करने वाले को कभी न बताएँ।",
    "Share this code only with the person who is physically delivering to you or driving you – never over a phone call or chat.":
        "यह कोड सिर्फ़ सामने खड़े डिलीवरी वाले या ड्राइवर को बताएँ – फ़ोन या चैट पर कभी नहीं।",
    "If you did not make this transaction, call the number printed on your card or passbook – not a number from any message.":
        "अगर यह लेन-देन आपने नहीं किया, तो कार्ड या पासबुक पर छपे नंबर पर फ़ोन करें – किसी मैसेज के नंबर पर नहीं।",
    "Check the amount and reference in your bank's official app before assuming it is correct.":
        "रकम और रेफ़रेंस को बैंक के आधिकारिक ऐप में जाँच लें।",
    "Use this OTP only if YOU just started the login or payment. If anyone calls asking for it, it is a scam.":
        "यह OTP तभी इस्तेमाल करें जब आपने ख़ुद लॉगिन या भुगतान शुरू किया हो। कोई फ़ोन करके माँगे तो वह धोखा है।",
    "If you did not request this code, someone may be trying to use your account – do not share it, and change your password.":
        "अगर आपने यह कोड नहीं माँगा, तो कोई आपके खाते में घुसने की कोशिश कर रहा है – कोड न बताएँ और पासवर्ड बदलें।",
    "Even with an official link, it is safest to open the official app or type the website yourself.":
        "आधिकारिक लिंक होने पर भी, ऐप ख़ुद खोलना या वेबसाइट ख़ुद टाइप करना सबसे सुरक्षित है।",
    "Use offers only inside the official app or website; ignore copies of the offer that ask for payment or details.":
        "ऑफ़र सिर्फ़ आधिकारिक ऐप या वेबसाइट में इस्तेमाल करें; पैसे या जानकारी माँगने वाली नकल को नज़रअंदाज़ करें।",
    "Real awareness messages never ask you to click a link or call a mobile number to 'verify'.":
        "असली चेतावनी मैसेज कभी 'वेरिफ़ाई' के लिए लिंक या मोबाइल नंबर नहीं देते।",
    "If this person later asks for money or a code, call them on the number you already know before doing anything.":
        "अगर यह व्यक्ति बाद में पैसे या कोड माँगे, तो पहले उसके पुराने नंबर पर फ़ोन करें।",
    "Kavach reads the text only. If someone calls or messages you about this, do not share any code, PIN or password.":
        "Kavach सिर्फ़ मैसेज पढ़ता है। इसके बारे में कोई फ़ोन या मैसेज करे तो कोई कोड, PIN या पासवर्ड न बताएँ।",
    "A genuine-looking message can still be copied by scammers later – always check unexpected requests through official channels.":
        "ठग असली मैसेज की नकल भी कर सकते हैं – अचानक आई माँग को हमेशा आधिकारिक तरीके से जाँचें।",
}

REPORT_ONLY_HI = [
    "जवाब न दें, वापस फ़ोन न करें, लिंक न दबाएँ।",
    "मैसेज की शिकायत **संचार साथी → चक्षु** (sancharsaathi.gov.in) पर करें ताकि नंबर की जाँच हो और उसे बंद किया जाए।",
    "फ़ोन / WhatsApp पर भेजने वाले को ब्लॉक करें।",
    "अगर मैसेज में बैंक का नाम है, तो बैंक की आधिकारिक वेबसाइट पर दिए धोखाधड़ी-शिकायत पते पर भी भेज सकते हैं।",
]
RECOVERY_HI = [
    "तुरंत **1930** (राष्ट्रीय साइबर अपराध हेल्पलाइन) पर कॉल करें। पहले कुछ घंटे ('गोल्डन आवर') सबसे ज़रूरी हैं – जितनी जल्दी शिकायत, पैसे रोकने की उतनी संभावना।",
    "कार्ड या पासबुक पर छपे नंबर पर बैंक को फ़ोन करें (मैसेज वाले नंबर पर नहीं) और कार्ड, UPI और नेट बैंकिंग बंद करवाएँ।",
    "**cybercrime.gov.in** पर शिकायत दर्ज करें ('Report Financial Fraud' चुनें) और शिकायत नंबर संभालकर रखें।",
    "सबूत बचाएँ: मैसेज के स्क्रीनशॉट, भेजने वाले का नंबर, लिंक, ट्रांज़ैक्शन ID और UPI ID। Kavach की रिपोर्ट इनमें से ज़्यादातर इकट्ठा कर देती है।",
    "अगर पासवर्ड या UPI PIN बताया था तो उसे बदलें और सभी डिवाइस से लॉग-आउट करें।",
]

SAFETY_NET_HI = {
    "two": "मॉडल सुरक्षित की ओर था, पर दो या ज़्यादा गंभीर चेतावनी संकेत मिले, इसलिए सावधान रहें।",
    "chain": "यह चेन फ़ॉरवर्ड या दान की अपील लगती है। आगे न भेजें और संस्था से सीधे जाँचे बिना पैसे न दें।",
    "asks": "भाषा सामान्य लगती है, पर यह वही चीज़ माँग रहा है जो ठग माँगते हैं – कुछ करने से पहले जाँच लें।",
    "unreadable": "Kavach इस मैसेज की ज़्यादातर भाषा नहीं पढ़ सकता, इसलिए इसे सुरक्षित नहीं कह सकता। किसी पढ़ने वाले से पूछें, और न समझ आने वाले मैसेज पर कभी OTP, PIN न दें या पैसे न भेजें।",
    "similar": "पहले जाँचा गया लगभग ऐसा ही मैसेज धोखा निकला था, इसलिए इसे भी उतनी ही सावधानी से देखें।",
}

BANDS_HI = {
    "Very likely a scam": "लगभग पक्का धोखा", "Likely a scam": "शायद धोखा",
    "Not sure – some warning signs": "पक्का नहीं – कुछ चेतावनी संकेत", "Can't read this language": "यह भाषा पढ़ नहीं सकता",
    "Very likely genuine": "लगभग पक्का असली", "Probably genuine": "शायद असली", "Looks genuine – please verify": "असली लगता है – फिर भी जाँचें",
}


def translate(out: dict) -> dict:
    """Translate the user-facing parts of an /api/analyze result to Hindi (in place)."""
    for f in out["flags"]:
        if f["rule"] in RULES_HI:
            label, reason = RULES_HI[f["rule"]]
            f["label"] = label
            if not f["rule"].startswith("link_") or f["rule"] == "link_action":
                f["reason"] = reason
    g = out.get("genuine")
    if g:
        g["passed"] = [CHECKS_HI.get(p, CHECKS_HI.get(p + " ", p)) if not p.startswith("Every link goes") else
                       "हर लिंक आधिकारिक वेबसाइट पर जाता है" + p[p.find(" ("):] for p in g["passed"]]
        g["cautions"] = [CAUTIONS_HI.get(c, c) for c in g["cautions"]]
        if g.get("summary"):
            kind_hi = KIND_HI.get(g["kind"], g["kind"])
            why = WHY_HI if "No strong scam signs" in g["summary"] else SAFE_WHY_HI
            g["summary"] = f"यह {kind_hi} लगता है। {why}"
    out["report_only"] = REPORT_ONLY_HI
    out["recovery"] = RECOVERY_HI
    sn = out.get("safety_net") or ""
    for key, needle in (("two", "two or more serious"), ("chain", "chain forward"), ("asks", "wording looks ordinary"),
                        ("unreadable", "cannot read most"), ("similar", "very similar message")):
        if needle in sn:
            out["safety_net"] = SAFETY_NET_HI[key]
    out["confidence_band"] = BANDS_HI.get(out.get("confidence_band"), out.get("confidence_band"))
    return out

FAMILY_HI = {
    "kyc_bank": "नकली KYC / खाता बंद", "sim_kyc": "सिम / टेलीकॉम KYC धोखा", "pension_ppo": "पेंशन / PPO / जीवन प्रमाण धोखा",
    "lottery": "लॉटरी / KBC / लकी ड्रॉ", "loan_app": "तुरंत लोन ऐप धोखा", "task_job": "पार्ट-टाइम नौकरी / टास्क धोखा",
    "investment": "नकली ट्रेडिंग / क्रिप्टो निवेश", "electricity": "बिजली बिल / कनेक्शन कटने का डर",
    "parcel_customs": "पार्सल / कस्टम्स / कूरियर धोखा", "digital_arrest": "'डिजिटल अरेस्ट' / नकली पुलिस, CBI",
    "refund": "नकली रिफ़ंड / कस्टमर केयर", "upi_collect": "UPI 'पैसे पाने' का धोखा", "family_emergency": "परिवार की नकली इमरजेंसी",
    "account_takeover": "WhatsApp / अकाउंट कोड चोरी", "donation": "नकली दान / राहत अपील", "hoax_forward": "चेन फ़ॉरवर्ड / अफ़वाह",
    "remote_access": "नकली कस्टमर केयर / स्क्रीन-शेयर ऐप", "unknown": "दूसरा / नया तरह का धोखा",
}


def translate_family(out: dict) -> None:
    fam = out.get("family")
    if fam in FAMILY_HI and out.get("family_info"):
        out["family_info"] = {**out["family_info"], "title": FAMILY_HI[fam]}
