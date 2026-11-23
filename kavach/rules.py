"""Red-flag rules: hand-written checks for the tactics scammers use, in English and Hinglish.

Each rule runs on the CLEANED text (so "0TP" and "K.Y.C" are caught) and reports the exact span,
which is mapped back to the original message for highlighting. Rules also look for "reassuring
signs" that genuine bank, OTP and delivery messages carry, so real alerts are not flagged.

The rules do not decide the verdict on their own: their counts are extra inputs to the machine
learning model (see model.py), and their spans are the explanation shown to the user.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .links import LinkFinding, brands_in, find_links, phone_numbers
from .normalize import Normalized, normalize


@dataclass
class Flag:
    rule: str          # id
    label: str         # short name shown on the highlight
    reason: str        # plain-language explanation
    severity: str      # "high", "medium", "low", or "good" for reassuring signs
    start: int = 0     # span in the ORIGINAL message
    end: int = 0
    text: str = ""     # the highlighted words as written in the original

    @property
    def is_good(self) -> bool:
        return self.severity == "good"


# (id, label, severity, reason, regex on cleaned lowercase text)
SECRET = (r"(otp|one time password|pin|upi pin|mpin|cvv|password|passcode|atm pin|card number|card details|net ?banking (id|password)"
          r"|verification (code|number)|(\d|four|six|4|6)[- ]?digits?( (code|number|otp))?|the digits|security code|code|wo number)")
SHARE = r"(share|sharing|send|sending|tell|telling|give|giving|provide|forward|forwarding|reply with|read out|read|batao|bata ?do|bataiye|bhejo|bhej ?do|bhejiye|de ?do|enter|type)"
# genuine OTP messages: "do not share / never disclose ... OTP" (only verbs about handing a code over, not "do not tell family")
NEG_SHARE = (r"(do ?n[o']?t|never|don'?t|not to|mat|na ?kare|nahi|na)\s+(\w+\s+){0,3}(share|disclose|reveal|give|forward|provide)"
             r"|(share|disclose|reveal)\s+(\w+\s+){0,4}(mat|na ?kare|nahi ?kare)")
# "the code / number that came on your phone", "the code we just sent you", "the 6 digits you got"
CODE_RECEIVED = (r"(code|otp|number|digits|pin)\s+(\S+\s+){0,3}(that |which |jo )?(came|you (just )?(got|received|get)|u (got|received)"
                 r"|(we|i) (just )?sent|aaya|aya|aayega|received (just now|now|on))")

RULES: list[tuple[str, str, str, str, str]] = [
    ("asks_secret", "Asks for secret code", "high",
     "It asks you to share, read out or enter a secret code (OTP / PIN / CVV / password). Banks, police and companies NEVER ask for these.",
     SHARE + r"\s+(\S+\s+){0,4}" + SECRET
     + r"|" + SECRET + r"\s+(\S+\s+){0,4}(share karo|batao|bataiye|bhejo|bhejiye|bhejein|bata do|send karo|share kare|read (it )?out|share with (our|the) (executive|agent|officer)|to (our|the) (executive|agent|officer))"
     + r"|(read|tell|forward|send|share|give)\s+(\S+\s+){0,3}(code|otp|pin)\s+(\S+\s+){0,2}(you|u)\s+(just\s+)?(received|got|get|receive)"
     + r"|(code|otp)\s+(\S+\s+){0,3}(sent|went)\s+(\S+\s+){0,3}(by mistake|accidentally|galti se)|accidentally sent (my|the|a) (\S+\s+){0,2}code"
     + r"|reply with the code|(ओटीपी|पिन|पासवर्ड|सीवीवी)(\s+\S+){0,4}\s+(भेज|बता|शेयर कर)|(हमें|हमे)(\s+\S+){0,3}\s+(ओटीपी|कोड)"
     + r"|" + SHARE + r"\s+(\S+\s+){0,5}" + CODE_RECEIVED),
    ("kyc", "KYC by message", "high",
     "It asks you to update or complete KYC through a message link or call. Banks never ask for KYC by SMS or WhatsApp links.",
     r"\b(kyc|re-?kyc|e-?kyc|pan ?card|pan|aadhaa?r)\b(\s+\S+){0,4}\s+(update|expir\w*|pending|incomplete|suspend\w*|block\w*|verify|verification|link|karo|kare|nahi|not updated|missing)"
     + r"|\b(update|complete|verify|re-?verify)\s+(your\s+)?(kyc|pan|aadhaa?r)|\bkyc (team|centre|center|officer|helper|update|verification)|केवाईसी|kyc ke liye"),
    ("threat", "Threatens to block or cut off", "high",
     "It threatens that your account, card, SIM, pension or connection will be blocked or cut off. Scammers use fear to rush you.",
     r"\b(account|a/c|acct|card|sim|number|connection|wallet|yono|net ?banking|services?|bijli|electricity|power|balance|access)\b(\s+\S+){0,5}\s+(will be |is |has been |hoga |ho jayega |ho jaega |will |)?(block\w*|suspend\w*|deactivat\w*|clos\w*|disconnect\w*|disabled|band|bandh|khatam|kat jayega|cut|terminat\w*|freez\w*|frozen|on hold|hold par|barred|lock\w*|restricted|blacklisted|stop working|be lost|deleted)"
     + r"|\b(khata|khaata|pension|account)\b(\s+\S+){0,3}\s+(band|bandh|khatam|ruk) (ho|hone|kar)"
     + r"|(खाता|कार्ड|सिम|अकाउंट|बिजली)(\s+\S+){0,5}\s+(बंद|ब्लॉक|निलंबित|काट)"),
    ("urgency", "Creates urgency", "medium",
     "It pushes you to act immediately. Real organisations give you time and never need a reply within minutes.",
     r"\b(urgent\w*|immediately|right now|act now|asap|within \d+ ?(hours?|hrs?|h|minutes?|mins?)|in \d+ ?(hours?|hrs?|minutes?|mins?)|today itself|tonight|by today|at midnight|last (chance|date|day|warning|reminder)|expires? (today|tonight|soon)|turant|jaldi|abhi|aaj (hi|raat)|final (notice|warning)|before \d+ ?(pm|am)|only today|limited time|hurry|(only )?\d+ (seats?|slots?) left|(blocked|suspended|closed|deactivated|expires?|expired|cut|disconnected|stopped|stop) (today|tonight))\b|तुरंत|अभी|आज रात|जल्दी"),
    ("prize", "Promises a prize", "high",
     "It says you won a prize, lottery or reward you never entered. Nobody gives away money by SMS.",
     r"\b(you (have |'ve )?won|winners?|won\b(?!['’]t)|lottery|lucky (draw|customer|winner)|jackpot|prize|kbc|kaun banega|inaam|jeet\w*|selected for (a )?(reward|gift|prize|cash)|selected to receive|(has been |have been |is )?awarded|chosen as|chuna gaya|reward points? (expir\w*|worth|redeem)|cashback of|gift (card|voucher|hamper)|voucher worth|bumper|giveaway|free (phone|iphone|car|bike|gift|scooty|samsung)|spin the wheel|scratch card|unclaimed)\b|इनाम|लॉटरी|विजेता|लकी ड्रॉ"),
    ("congrats", "Congratulates you", "low",
     "It opens with congratulations, a common hook in prize and job scams (on its own this means little).",
     r"\b(congratulations?|congrats|mubarak|badhai ho)\b|बधाई"),
    ("fee", "Asks you to pay first", "high",
     "It asks you to pay a fee, tax or deposit before you get money, a loan, a job or a parcel. Paying to receive is the core of most frauds.",
     r"\b(processing|registration|joining|security|clearance|transfer|delivery|redelivery|customs|gst|tax|insurance|verification|activation|file|handling|shipping|upgrade|scholarship|internship|training|certificate|onboarding)\s+(fee|fees|charge|charges|deposit|amount)\b"
     + r"|\bpay\b(\s+\S+){0,8}\s+(or|warna|nahi to)\s+(you will be |you'll be |you will |aap )?(barred|debarred|blocked|cancelled|disqualified|rejected|cannot appear|can't appear)"
     + r"|\b(buy|purchase|order)\s+(\S+\s+){0,4}(product|item|kit|course)\s+(\S+\s+){0,3}(first|before)\b|\b(first|pehle)\s+(buy|purchase|pay|kharid\w*)\b"
     + r"|\bpay\s+(only\s+|just\s+)?(rs\.?|inr|₹)?\s?\d+[\d,]*\s+(\S+\s+){0,4}(to|for|and)\s+(claim|receive|release|get|unlock|activate|confirm|process)"
     + r"|\b(pay|send|bhej\w*|jama|deposit|clear)\b(\s+\S+){0,4}\s+(handling|shipping|stamp duty|duty|insurance|gst|clearance|registration|processing|file|delivery) ?(fee|fees|charge|charges)?\b"
     + r"|\b(fee|fees|charge|charges|shulk)\s+(\S+\s+){0,3}(bhej\w*|jama|bhar\w*)|\b(rupay|rupaye|rupees)\s+(bhej\w*|jama|bhar\w*)"
     + r"|\bto (withdraw|unlock|release|receive)\b(\s+\S+){0,6}\s+(pay|deposit|clear|recharge)|\b(must|need to|have to) (first )?(pay|deposit|clear)\b"
     + r"|\bdeposit (rs\.?|₹)?\s?[\d,]+ to|\brefundable (deposit|amount)\b|(deposit|jama|pay) (karo|kare|kijiye)"
     + r"|(शुल्क|फीस|चार्ज|gst|जीएसटी)(\s+\S+){0,3}\s*(जमा|भेज)|जमा करें"),
    ("loan_bait", "Loan bait", "high",
     "It offers an instant or pre-approved loan with no documents or checks. Fake loan apps steal data and charge fees.",
     r"\b(instant|pre-?approved|pre-?sanctioned|guaranteed|easy|quick|urgent)\s+(personal\s+)?(loan|credit|cash)|\bloan\s+(\S+\s+){0,3}(approved?|sanctioned|disburs\w*|ready|without|no (documents?|cibil|paperwork))"
     + r"|\b(no|without|bina)\s+(cibil|credit score|documents?|docs|paperwork|income proof|salary slip)|\bzero paperwork|\bloan (chahiye|milega|le lo|approve ho)|\bcredit limit (increase|upgrade)|\b(free )?limit upgrade|cash up to|लोन"),
    ("job_bait", "Job / task bait", "high",
     "It offers easy money for simple online tasks or part-time work. These 'task jobs' end with you paying to withdraw your earnings.",
     r"\b(part[- ]?time|work from home|wfh|home based|online (job|work)|data entry|typing job|like (videos?|posts?)|youtube (likes?|task|videos?)|subscribe (and|&) earn|daily (income|earning|payment)|paid daily"
     + r"|earn\s+(rs\.?|₹|inr)?\s?\d[\d,]*|(rs\.?|₹|inr)?\s?\d[\d,]*\s*(/|per|a)\s*(day|d|review|task|like)\b|kama(o|ye|yein|en)|rozana|ghar baithe|hiring now|urgent hiring|reviewers? needed|remote (job|role|work)|brand ambassador|collab with you|paid collab"
     + r"|(resume|profile)\s+(is\s+)?(shortlisted|selected|matches)|(you are|you have been|you're|aap) (shortlisted|selected for (the |a )?(job|role|post|position|interview))|onboarding (form|fee|kit)|hr (team|from|department) (of|from|at)?|salary \d|task (based|completion|earnings?|commission)|prepaid task|telegram task|commission per task|mentor)\b|पार्ट टाइम|घर बैठे|कमाएं|कमाइए"),
    ("invest_bait", "Investment bait", "high",
     "It promises guaranteed or very high returns. Real investments never guarantee profit; this is how trading and crypto frauds start.",
     r"\b(guaranteed (returns?|profit|income)|double (your|the)? ?money|paisa double|(money|paisa|amount|investment|returns?) (will |gets? |is )?doubled?\b|doubles? (your|in) \d+|double (hota|ho jata)|\d{1,3}\s?% (returns?|profit|monthly|daily|weekly)|\d{1,3}\s?% (\S+\s+)?daily|returns? of \d+\s?%|crypto|bitcoin|usdt|trading (tips|group|signals)|signals|stock tips|insider|ipo allotment|vip (group|trading)|forex|investment plan|gold scheme|high returns?|risk[- ]free|multiply|pakka|for life|lagao|daal de)\b"),
    ("authority", "Pretends to be an authority", "high",
     "It claims to come from police, CBI, customs, courts, TRAI or a tax office and threatens you. Officials never threaten arrest or demand money over SMS or video call.",
     r"\b(cbi|police|cyber cell|crime branch|narcotics|ncb|customs (department|officer|duty)|court (notice|summons|order|case|action)|arrest (warrant)?|digital arrest|fir|legal action|trai|ed officer|enforcement directorate|money laundering|illegal (items?|parcel|drugs?|messages?|activity)|drugs?|passports?|case (is |has been )?registered|giraftar\w*)\b|पुलिस|गिरफ्तार|ड्रग्स|कस्टम्स|सीबीआई"),
    ("disconnection", "Bill / disconnection scare", "high",
     "It says your electricity, gas or phone will be cut tonight unless you call or pay. Real boards send bills with due dates, not midnight threats.",
     r"\b(electricity|power|bijli|light|gas|supply|connection)\b(\s+\S+){0,6}\s+(disconnect\w*|cut|kat|kaat|band|off|stopped)\b|\b(bill|previous month bill|bill payment)\s+(was |is )?(not (updated|paid|reflected)|pending)|pending bill"
     + r"|contact (the )?(electricity )?officer|officer (ko|se) (call|contact|baat)|call (the )?(electricity )?officer|bill (update|jama|paid) nahi|bijli (vibhag|office)|बिजली(\s+\S+){0,6}\s+काट"),
    ("parcel", "Parcel / delivery trap", "medium",
     "It says a parcel is held or an address is incomplete and asks you to click or pay. Couriers do not ask for fees by SMS links.",
     r"\b(parcel|package|shipment|courier|consignment)\b(\s+\S+){0,6}\s+(held|on hold|stuck|ruka|returned|seized|could not be delivered|undeliver\w*|incomplete|failed|needs duty)|\b(incomplete|wrong|invalid|unclear) (address|house number)|(update|confirm) (your |the )?(delivery )?address|redeliver\w*|duty payment|before release|पार्सल"),
    ("refund", "Refund / cashback bait", "medium",
     "It offers a refund or cashback that you must 'claim' by clicking or sharing details. Real refunds come back automatically.",
     r"\b(refund|cashback|cash back|reimbursement)\b(\s+\S+){0,6}\s+(claim|on hold|verify|update|submit|release|to receive|eligible)|\bclaim (your |the )?(refund|cashback|reward|bonus|amount)|eligible for (a )?refund"),
    ("collect_request", "UPI 'receive money' trick", "high",
     "It asks you to approve a request or enter your UPI PIN to RECEIVE money, or claims money was sent 'by mistake'. A UPI PIN is only ever needed to SEND money.",
     r"\b(enter|type|use)\s+(your\s+)?(upi\s+)?pin\s+(\S+\s+){0,3}(receive|get|accept|credit)|\b(approve|accept)\s+(the\s+)?(\S+\s+)?(collect\s+)?request|\b(scan|scan the qr)\s+(\S+\s+){0,3}(receive|get)"
     + r"|(sent|paid|transferred)\s+(\S+\s+){0,5}by mistake|collect request"
     # Hinglish / Hindi: "QR scan karo aur PIN dalo, paisa aa jayega", "request bheja hai, approve kar do"
     + r"|\b(upi )?pin\s+(\S+\s+){0,2}(dalo|daalo|daal do|dal do|dalein|daalein|daliye|daaliye|enter karo|enter kare\w*|lagao|likho)"
     + r"|\bqr\s+(code\s+)?(\S+\s+){0,2}(scan|skan)\s*(karo|kare\w*|kijiye|kar do|kar ke)?(\s+\S+){0,6}\s+(paisa|paise|payment|money|amount)"
     + r"|\b(approve|accept)\s+(kar\w*|kijiye|karna|kar dena|kar do)\b|\brequest\s+(\S+\s+){0,3}(bhej\w*|aaya|aayega|gaya)\b(\s+\S+){0,6}\s+(approve|accept)"
     + r"|\bpaisa\s+(\S+\s+){0,3}(aa jayega|aa jaega|aayega|mil jayega)|\bgalti se\s+(\S+\s+){0,4}(bhej|transfer|aa)\w*"
     + r"|(यूपीआई |upi )?(पिन|pin)\s+(\S+\s+){0,2}(डाल|दर्ज)|क्यूआर|qr\s*(कोड|code)?\s+(\S+\s+){0,1}(स्कैन)|अप्रूव"),
    ("remote_app", "Asks to install an app", "high",
     "It asks you to install a screen-sharing or unknown app (AnyDesk, TeamViewer, an .apk). That gives the scammer control of your phone.",
     r"\b(anydesk|any desk|teamviewer|team viewer|quick ?support|rustdesk|airdroid|screen ?shar\w*|download (this|the|our) app|install (this|the|our) app|apk)\b|\b(install|download)\s+(\S+\s+){0,3}(app|application)\b(\s+\S+){0,2}\s+(from|at)\b"),
    ("pressure_secrecy", "Keeps you isolated", "high",
     "It tells you not to tell your family or anyone, or to stay on a (video) call. Scammers isolate victims so nobody can warn them.",
     r"\b(do ?n[o']?t|don'?t|never) (tell|inform|call|contact)( (anyone|anybody|your family|family|home|mom|mum|dad|papa|parents|police|bank)\w*)"
     r"|\b(without telling|keep (this|it) (secret|confidential|private)|kisi ko (mat|na) bata\w*|ghar (pe|par|me) mat bata\w*"
     r"|stay on (this |the |a )?(whatsapp |skype )?(video )?call|join (the |a )?(skype |whatsapp )?video call|video call will be connected"
     r"|(on|via) skype|do not disconnect|don'?t disconnect)\b|किसी को (मत|न) बता"),
    ("money_bait", "Big money offered to you", "low",
     "It offers you a large amount of money (a prize, reward, loan or earnings) that you did not ask for.",
     r"\b(won|win|winning|prize|reward|lottery|jackpot|inaam|jeet\w*|earn\w*|kama\w*|loan|bonus|cash ?back|claim|receive|get|milenge|paao)\b"
     r"(\s+\S+){0,5}\s+((rs\.?|inr|₹|\$|usd|gbp|£|€)\s?\d[\d,]*|\d+\s?(lakh|lac|crore|cr|k)\b)"
     r"|((rs\.?|inr|₹)\s?\d{1,3}(,\d{2,3})+|\d+\s?(lakh|lac|crore|cr)\b)(\s+\S+){0,5}\s+(prize|reward|lottery|jackpot|inaam|loan|cash ?back|bonus|jeet\w*)\b"),
    ("money_demand", "Asks you to send money", "medium",
     "It asks you to transfer or deposit money to a person or account. Check who you are really paying through an official channel.",
     r"\b(transfer|deposit|send|bhej\w*|jama kar\w*)\b(\s+\S+){0,4}\s+((rs\.?|inr|₹)\s?\d[\d,]*|\d[\d,]{2,}\s?(rupees|rs|lakh)?|\d+\s?(lakh|k)\b|money|paise|paisa|amount|any amount)"
     r"|\b(security|verification|clearance) deposit\b"),
    ("asks_details", "Asks for your personal / bank details", "medium",
     "It asks you to send or fill in bank, card, Aadhaar or PAN details. Banks and offices never collect these through SMS, WhatsApp or a form link.",
     r"\b(confirm|update|submit|share|fill|enter|send|provide|verify|reply with|bhej\w*|batao|bataiye)\b(\s+\S+){0,4}\s+(your |apna |apni |the )?"
     r"(bank |account |card |personal |kyc |login |netbanking )?(details|detail|information|account number|bank account|a/c (no|number)|ifsc|card number"
     r"|aadhaa?r( number| card)?|pan( number| card)?|date of birth)\b"
     r"|\b(aadhaa?r|pan|bank)( number| card| details)?\s*(,|and|aur)\s*(\S+\s+){0,2}(bank|pan|otp|account)\b(\s+\S+){0,3}\s*(bhej|send|share|on whatsapp)"
     r"|\b(details|detail|jankari|jaankari)\s+(bharo|bhariye|bharein|bhejo|bhejiye|dijiye|do)\b|\b(email|send) (us |me )?your bank details"),
    ("chain_forward", "Chain forward", "medium",
     "It asks you to forward the message to many people, or promises luck or threatens loss if you don't. Chain forwards spread hoaxes and scams.",
     r"\b(forward|share|send)\w* (this|it|the message)?\s?(\S+\s+){0,2}(to|with) (\d+|all|every\w*|your contacts|your friends|groups?|\d+ (people|friends|groups|contacts))\b"
     r"|\b(share|forward) with \d+|\bforward to all\b|\bfor (good )?luck\b|\bbad luck\b|\bforwarded (as received|many times)\b"
     r"|\bwhatsapp will (charge|delete|be (paid|closed|shut))|\bdoctors are hiding\b"
     r"|\b\d+ (groups?|logon|logo|people|log) (me|mein|ko|tak)? ?(share|forward|bhej)\w*"),
    ("shame_threat", "Threatens to shame you", "high",
     "It threatens to message your contacts, post your photos or call your relatives. Illegal loan apps and blackmailers use this; report it to 1930.",
     r"\b(message|call|tell|inform|send (it )?to|share (it )?with|whatsapp)\b(\s+\S+){0,2}\s+(all )?(your )?(contacts|relatives|family members|friends list|phonebook)"
     r"|\b(post|share|send|leak|upload)\w*\s+(your )?(morphed )?(photos?|pics?|pictures|videos?)\b(\s+\S+){0,4}\s+(online|to|on|with)"
     r"|\b(you are|as) a (fraud|defaulter|chor)\b|\bdefame\b"),
    ("donation_request", "Asks for a donation", "medium",
     "It asks for a donation to a UPI ID, number or account you can't verify. Fake temple, relief and welfare appeals copy real causes.",
     r"\b(donate|donation|contribute|contribution|daan|seva|bhandara|annadanam|relief fund|welfare fund)\b(\s+\S+){0,12}\s+(upi|\S*@\w+|a/c|account|paytm|gpay|phonepe|send|transfer|pay to|bhej\w*)"
     r"|\b(pay|send|transfer)\b(\s+\S+){0,6}\s+(for|towards) (the )?(temple|bhandara|annadanam|relief|welfare|seva|donation)"),
    ("click_now", "Pushes you to click", "low",
     "It pushes you to click a link to fix, claim or verify something.",
     r"\b(click|tap|visit|open|go to|kare click|par click|kholiye|kholo)\b(\s+\S+){0,4}\s+(link|here|below|now|to (claim|update|verify|activate|unlock|avoid|get|receive|redeem|apply))|\b(link|link pe|link par)\s+(click|tap|pe pay)|लिंक"),
]

# "never install AnyDesk", "do not pay extra" are advice: a negation just before cancels these red flags.
NEGATABLE = {"asks_secret", "remote_app", "fee", "click_now", "collect_request", "money_demand", "asks_details"}
NEGATION = re.compile(r"\b(never|do ?n[o']?t|don'?t|not to|mat|kabhi|na kare|nahi)\b(\s+[^\s.!?]+){0,3}\s*[^\s.!?]?$")  # stops at a full stop

# Fake family emergency needs two things: a "new number / lost phone" story AND a request for money.
FAMILY_STORY = re.compile(
    r"\b(new number|naya number|temporary number|friend'?s (phone|number|mobile|account)|dost ka (phone|number|mobile)"
    r"|lost my (phone|wallet|purse)|lost (wallet|purse)|broke my phone|phone (got )?(is |was )?(broken|kharab|kho|lost|fell|damaged|stolen)"
    r"|phone (broke|died)|my phone (fell|got stolen|is dead)|phone kho gaya|phone kharab|phone chori|accident ho gaya|using (a |my )?friend'?s"
    r"|stuck (at|in) (the )?(airport|station|hospital|police station|customs)|in (the )?hospital|hospital me)\b")
FAMILY_MONEY = re.compile(r"\b(send|transfer|bhej\w*|need|chahiye|pay|gpay|phonepe)\b(\s+\S+){0,5}\s*(\d|money|paise|paisa|rs|₹|upi|account)|\d{3,}\s+(bhej\w*|transfer)")

GOOD_RULES: list[tuple[str, str, str, str]] = [
    ("otp_dont_share", "Says: do not share OTP",
     "It tells you NOT to share the code with anyone, which is what genuine OTP messages say.",
     r"(" + NEG_SHARE + r")|(साझा|शेयर) न कर|never asks? for (your )?(otp|pin)|never calls?"),
    ("handover_code", "Delivery / ride code",
     "It gives YOU a code to show the delivery agent or driver in person – that is how genuine delivery and ride OTPs work.",
     r"\b(share|give|show|tell)\s+(\S+\s+){0,4}(only )?(with|to|at) (the |your )?(delivery|agent|driver|captain|rider|doorstep|door|time of delivery|partner|executive at)"
     r"|\b(delivery|ride|trip) (otp|code|pin)\b|\b(only )?after (boarding|you receive|receiving|delivery)\b|\bat (the )?(doorstep|door|time of delivery)\b"
     r"|\b(to (start|begin) (the |your )?(trip|ride|journey)|on delivery|at delivery|on arrival|when (the |your )?(order|parcel|package|food) (arrives|reaches))\b"
     r"|\b(pickup|pick-up|return|handover|hand-over) (code|otp|pin)\b"),
    ("awareness", "Fraud-awareness message",
     "It warns you about fraud and points to official channels without asking you for anything – typical of genuine bank and police alerts.",
     r"\b(beware|fraudsters?|is a scam|are fraud|such messages|never (asks?|sends?|calls?)|will never (ask|call)|do not click (on )?links"
     r"|stay alert|fraud alert|be careful of|digital arrest is)\b"),
    ("shop_offer", "Ordinary shopping offer",
     "It is a normal discount or reward from a shop (coupon code, % off, coins or cashback already added) and asks for no payment or details.",
     r"\b(\d+\s?% off|use code [a-z0-9]{3,}|with code [a-z0-9]{3,}|coupon|supercoins|reward points? (added|credited|earned)|cashback (has been |is )?(added|credited)"
     r"|added to your (\S+ ){0,2}(rewards|wallet|balance)|t&c apply|for your (recent |last )?(order|purchase)|free delivery|already applied|collect (it )?at (the )?(billing |cash )?counter|show this (sms|message) at (the )?(store|counter))\b"),
    ("event_result", "Result of a real event",
     "It announces the result of a competition, exam or event with where and when prizes are given – and asks you for nothing.",
     r"\b(tournament|competition|contest|hackathon|quiz|olympiad|sports day|race|chess|debate|fest|conference|exam results?|semester)\b"
     r"(\s+\S+){0,12}\s+(prize distribution|certificate|ceremony|auditorium|assembly|at the venue|on stage|will be (given|distributed|emailed))"
     r"|\b(prize distribution|closing ceremony|award ceremony)\b"),
    ("no_fee", "Says there is no fee",
     "It says plainly that nothing is charged – genuine employers, colleges and offices say this; scammers ask for a fee.",
     r"\b(no (fee|fees|charges?|payment|money) (is |are |will be )?(charged|required|needed|taken|at any stage)|(fee|fees|charges?) (is |are )?not (charged|required)"
     r"|never (charge|ask for|asks for|collect) (any )?(fee|fees|money|payment)|free of (cost|charge)|no registration fee)\b"),
    ("visit_branch", "Sends you to the branch / official app",
     "It asks you to visit the branch or use the official app yourself, instead of clicking a link or calling a number.",
     r"\b(visit (your |the |any )?(nearest )?(\S+ ){0,2}branch|at (any|your nearest|the nearest) (\S+ )?branch|through the official app|on the official (portal|app|website))\b"),
    ("masked_account", "Masked account number",
     "It shows only the last digits of your account or card (like XX1234), which is how real bank alerts look.",
     r"\b(a/?c|acct|account|card|ac)\s*(no\.?\s*)?(x{2,}|\*{2,}|ending( with)?\s*|xx)\s*\d{3,4}\b|\b(x{2,}|\*{2,})\d{3,4}\b"),
    ("transaction_ref", "Transaction details",
     "It has a reference number or available balance, which genuine transaction alerts include.",
     r"\b(upi ref\w*|ref\.? no|txn (id|no)|utr|imps ref|avl\.? bal|available balance|avl bal|a/c bal|ref no)\b"),
    ("order_update", "Order / delivery update",
     "It is an update about an order you placed (shipped, out for delivery, delivered) – the normal kind of shop message.",
     r"\b(order\s+(\S+\s+){0,6}(has been |is |was )?(shipped|dispatched|packed|delivered|confirmed|placed|out for delivery|on (the|its) way)|out for delivery|has been delivered|track (your order|it|at|on|here))\b"),
    ("not_you_report", "Gives an official way to report",
     "It tells you to call the official helpline or block the card if it wasn't you, which banks do in real alerts.",
     r"\b(not you|if not done by you|not done by you)\b|sms block|call (the )?(18\d{2}|1930)"),
    ("planned_notice", "Planned maintenance notice",
     "It announces a scheduled power cut or maintenance with a date and time window, which is how real utility notices look.",
     r"\b((scheduled|planned) (power )?(cut|shutdown|outage|interruption)|power shutdown|for (line |routine )?maintenance|inconvenience (is )?regretted)\b"),
    ("valid_for", "Says how long a code is valid",
     "Genuine OTP messages say how long the code is valid for.",
     r"\b(valid (for|till|upto|up to)\s+\d+\s?(min|mins|minutes|hrs?)|expires? in \d+\s?(min|mins|minutes))\b"),
]

_COMPILED = [(i, l, s, r, re.compile(p)) for i, l, s, r, p in RULES]
_GOOD = [(i, l, r, re.compile(p)) for i, l, r, p in GOOD_RULES]

RULE_IDS = [r[0] for r in RULES] + ["family_emergency"] + [g[0] for g in GOOD_RULES] + [
    "link_dangerous", "link_suspicious", "link_official", "personal_mobile", "disguised", "brand_mentioned",
    "link_action", "unreadable_script"]

# Scripts Kavach can read: Latin (English / Hinglish) and Devanagari (Hindi). Text mostly in another script
# (Malayalam, Tamil, Telugu, Bengali...) cannot be judged by the model, so it must never be called safe.
READABLE_SCRIPTS = ("LATIN", "DEVANAGARI")
LINK_ACTION = re.compile(r"\b(click|tap|visit|open|go to|log ?in|kholo|kholiye|dabayein)\b(\s+\S+){0,6}\s+(to\s+)?(cancel|stop|block|unblock|verify|"
                         r"confirm|update|claim|redeem|activate|reactivate|avoid|dispute|reverse|refund|pay|unlock)\b|\b(cancel|stop|dispute|reverse)\b(\s+\S+){0,4}\s+(click|tap|visit|open)\b")


def unreadable_share(text: str) -> tuple[float, str | None]:
    """Share of letters in scripts Kavach cannot read, and the name of the main such script."""
    import unicodedata
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0, None
    other = {}
    for c in letters:
        name = unicodedata.name(c, "")
        script = name.split(" ")[0]
        if not name.startswith(READABLE_SCRIPTS):
            other[script] = other.get(script, 0) + 1
    n = sum(other.values())
    main = max(other, key=other.get).title() if other else None
    return n / len(letters), main


def _flag_from(norm: Normalized, start: int, end: int, rule: str, label: str, sev: str, reason: str) -> Flag:
    a, b = norm.span_to_original(start, end)
    return Flag(rule, label, reason, sev, a, b, norm.original[a:b])


def find_flags(text: str, norm: Normalized | None = None) -> tuple[list[Flag], list[LinkFinding], list[str]]:
    """Return (flags, link findings, brands mentioned) for one message."""
    norm = norm or normalize(text)
    t = norm.text
    flags: list[Flag] = []

    good_spans = []
    for rid, label, reason, rx in _GOOD:
        m = rx.search(t)
        if m:
            flags.append(_flag_from(norm, m.start(), m.end(), rid, label, "good", reason))
            good_spans.append((m.start(), m.end()))

    for rid, label, sev, reason, rx in _COMPILED:
        for m in rx.finditer(t):
            if rid == "asks_secret" and any(a <= m.start() + 3 and m.start() <= b for a, b in good_spans):
                continue  # "do not share this OTP" is a good sign, not a red flag
            if rid == "asks_secret" and re.search(r"\bpin ?code\b", m.group()) and not re.search(r"\b(upi|atm|card|mpin)\b", m.group()):
                continue  # a postal PIN code for an address is not a secret
            if rid == "asks_secret" and re.search(r"(otp|code) (is|:)\s*\d{4,8}|\d{4,8} is (your|the) (otp|code)", t) \
                    and not re.search(r"(share|send|tell|forward)\s+(\w+\s+){0,3}(with|to)\s+(our|the|this|us)", t):
                continue  # an OTP message that contains the code itself is not asking for it
            if rid in NEGATABLE and NEGATION.search(t[max(0, m.start() - 30):m.start() + 1]):
                continue  # "never install AnyDesk", "do not pay extra" are advice, not demands
            flags.append(_flag_from(norm, m.start(), m.end(), rid, label, sev, reason))
            break  # one highlight per rule is enough

    rules_found = {f.rule for f in flags}
    if "planned_notice" in rules_found:
        # a scheduled-maintenance notice announces a power cut by definition; that is not a threat
        flags = [f for f in flags if f.rule not in ("disconnection", "threat")]
    if re.search(r"\b(no hurry|no rush|not urgent|whenever you can|when you can|koi jaldi nahi|jaldi nahi hai)\b", t):
        flags = [f for f in flags if f.rule != "urgency"]   # "send it when you can, no hurry" is the opposite of urgency
    if re.search(r"\b(ho gaya tha|ho gayi thi|was blocked|got blocked|had blocked)\b", t) and \
            re.search(r"\b(karwa liya|kar liya|theek|thik|sorted|fixed|resolved|ab sab|now it is fine|all good now)\b", t):
        flags = [f for f in flags if f.rule not in ("threat", "kyc")]   # telling a past, already-solved problem is not a threat
    if "handover_code" in rules_found:
        # "share OTP 4512 with the delivery agent at your door" is how delivery/ride codes work, not a request for a secret
        flags = [f for f in flags if f.rule not in ("asks_secret", "urgency")]
    if "otp_dont_share" in rules_found and not re.search(r"\b(otp|code|pin|password|cvv|one time password)\b|ओटीपी|कोड", t):
        flags = [f for f in flags if f.rule != "otp_dont_share"]  # "do not share" only reassures when it is about a code
    if "shop_offer" in rules_found and not ({"fee", "asks_secret", "kyc", "money_demand"} & rules_found):
        # "you won a 50% off coupon" is a normal promotion; only a weak hint if nothing else is wrong
        flags = [f for f in flags if f.rule not in ("prize", "congrats")]

    fm = FAMILY_STORY.search(t)
    if fm and FAMILY_MONEY.search(t):
        flags.append(_flag_from(norm, fm.start(), fm.end(), "family_emergency", "Fake emergency from 'family'", "high",
                                "Someone on a 'new number' or 'broken phone' urgently asks for money. Always call the person "
                                "on their OLD number before paying."))

    brands = brands_in(t)
    links = find_links(text, brands)
    for lf in links:
        if lf.verdict in ("dangerous", "suspicious"):
            sev = "high" if lf.verdict == "dangerous" else "medium"
            flags.append(Flag("link_" + lf.verdict, "Dangerous link" if lf.verdict == "dangerous" else "Suspicious link",
                              " ".join(lf.issues), sev, lf.start, lf.end, text[lf.start:lf.end]))
        elif lf.verdict == "official":
            flags.append(Flag("link_official", "Official link", " ".join(lf.notes), "good", lf.start, lf.end,
                              text[lf.start:lf.end]))

    # A personal mobile number as the contact for a "bank" or "company" is a red flag.
    if brands or any(f.rule in ("kyc", "threat", "prize", "loan_bait", "job_bait", "disconnection") for f in flags):
        for a, b, num, kind in phone_numbers(text):
            if kind == "mobile":
                flags.append(Flag("personal_mobile", "Personal mobile number",
                                  "It asks you to contact an ordinary 10-digit mobile number. Banks and companies use "
                                  "official helplines (often 1800...), not personal mobiles.", "medium", a, b, text[a:b]))
                break

    if "visit_branch" in {f.rule for f in flags}:
        # "update your KYC at your nearest branch" is what genuine banks say – not "KYC by message"
        flags = [f for f in flags if f.rule != "kyc"]

    risky_links = [lf for lf in links if lf.verdict in ("unknown", "suspicious", "dangerous")]
    m = LINK_ACTION.search(t)
    if risky_links and m:
        lf = risky_links[0]
        flags.append(Flag("link_action", "Asks you to act through an unknown link",
                          "It asks you to click a link that is not an official website to cancel, verify, claim or pay. "
                          "Genuine banks and companies tell you to use their official app or helpline instead.",
                          "medium", lf.start, lf.end, text[lf.start:lf.end]))

    share, script = unreadable_share(text)
    if share >= 0.3:
        flags.append(Flag("unreadable_script", f"Written in {script or 'a language'} – Kavach can't read it",
                          f"Most of this message is in {script or 'a script'} script, which Kavach's model was not trained on. "
                          "It can only check the numbers, links and English words in it, so it cannot call this message safe.",
                          "medium", 0, 0, ""))

    if norm.disguised:
        tricks = ", ".join(k for k, v in norm.tricks.items() if v and k in
                           ("lookalike letters", "invisible characters", "symbols inside words", "spaced-out letters"))
        flags.append(Flag("disguised", "Disguised text",
                          f"The text was disguised to dodge filters ({tricks}). Genuine companies have no reason to do this.",
                          "medium", 0, 0, ""))
    return flags, links, brands


def flag_vector(flags: list[Flag], brands: list[str]) -> dict[str, float]:
    """Counts per rule id: extra inputs for the model."""
    v = {r: 0.0 for r in RULE_IDS}
    for f in flags:
        if f.rule in v:
            v[f.rule] = 1.0
    v["brand_mentioned"] = 1.0 if brands else 0.0
    return v
