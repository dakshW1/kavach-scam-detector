"""Link inspector: finds links in a message and checks them WITHOUT opening them.

Everything here is pure text analysis against a built-in list of official domains, so it works
offline and can never trigger a malicious page. We can prove things like "this domain is not one of
SBI's official domains" but we can never know where a short link really leads (that would need a
visit), and we say so.
"""
from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass, field

# Official domains of brands that scammers like to impersonate (registered domain only; any
# subdomain of these is official too). Banks are moving to ".bank.in" (RBI, 2025), both are listed.
OFFICIAL = {
    "SBI": ["sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "sbicard.com", "sbiyono.sbi", "onlinesbi.com"],
    "HDFC Bank": ["hdfcbank.com", "hdfc.bank.in", "hdfcbank.bank.in", "hdfc.com"],
    "ICICI Bank": ["icicibank.com", "icici.bank.in", "icicibank.bank.in"],
    "Axis Bank": ["axisbank.com", "axis.bank.in", "axisbank.bank.in"],
    "Kotak Bank": ["kotak.com", "kotak.bank.in", "kotakbank.bank.in"],
    "PNB": ["pnbindia.in", "pnb.bank.in", "netpnb.com"],
    "Bank of Baroda": ["bankofbaroda.in", "bankofbaroda.bank.in", "bobcard.co.in"],
    "Canara Bank": ["canarabank.com", "canarabank.bank.in"],
    "Union Bank": ["unionbankofindia.co.in", "unionbank.bank.in"],
    "Yes Bank": ["yesbank.in", "yesbank.bank.in"],
    "IndusInd Bank": ["indusind.com", "indusind.bank.in"],
    "RBI": ["rbi.org.in"],
    "NPCI": ["npci.org.in", "bhimupi.org.in"],
    "Paytm": ["paytm.com", "paytmbank.com", "paytm.me"],
    "PhonePe": ["phonepe.com"],
    "Google Pay": ["pay.google.com"],
    "Google": ["google.com", "g.co", "withgoogle.com", "youtube.com", "goo.gl"],
    "CRED": ["cred.club"], "Zerodha": ["zerodha.com"], "Groww": ["groww.in"], "SEBI": ["sebi.gov.in"],
    "Meesho": ["meesho.com"], "Ajio": ["ajio.com"], "Nykaa": ["nykaa.com"], "Zepto": ["zeptonow.com"], "Blinkit": ["blinkit.com"],
    "Uber": ["uber.com"], "Ola": ["olacabs.com"], "Rapido": ["rapido.bike"],
    "DigiLocker": ["digilocker.gov.in"], "Parivahan / e-Challan": ["parivahan.gov.in", "echallan.parivahan.gov.in"],
    "Jeevan Pramaan": ["jeevanpramaan.gov.in"], "PM-Kisan": ["pmkisan.gov.in"], "Passport Seva": ["passportindia.gov.in"],
    "FASTag": ["ihmcl.co.in", "nhai.gov.in", "npci.org.in"], "MSEDCL": ["mahadiscom.in"], "BSES": ["bsesdelhi.com"],
    "Tata Power": ["tatapower.com"], "Indane": ["indane.co.in", "iocl.com"], "Bharat Gas": ["ebharatgas.com"],
    "Instagram": ["instagram.com"], "Facebook": ["facebook.com"], "Telegram": ["telegram.org"],
    "Amazon": ["amazon.in", "amazon.com", "amzn.in", "amzn.to", "a.co"],
    "Flipkart": ["flipkart.com", "fkrt.it", "dl.flipkart.com"],
    "Myntra": ["myntra.com", "myntr.it"],
    "Swiggy": ["swiggy.com", "swiggy.in"],
    "Zomato": ["zomato.com", "zoma.to"],
    "India Post": ["indiapost.gov.in"],
    "Blue Dart": ["bluedart.com"],
    "Delhivery": ["delhivery.com"],
    "DTDC": ["dtdc.in", "dtdc.com"],
    "FedEx": ["fedex.com"],
    "Airtel": ["airtel.in", "airtel.com", "i.airtel.in"],
    "Jio": ["jio.com", "jio.in"],
    "Vi": ["myvi.in"],
    "BSNL": ["bsnl.co.in", "bsnl.in"],
    "BESCOM": ["bescom.co.in", "bescom.karnataka.gov.in"],
    "Income Tax": ["incometax.gov.in", "incometaxindia.gov.in"],
    "EPFO": ["epfindia.gov.in"],
    "UIDAI (Aadhaar)": ["uidai.gov.in", "myaadhaar.uidai.gov.in"],
    "TRAI": ["trai.gov.in"],
    "Cyber Crime Portal": ["cybercrime.gov.in"],
    "Sanchar Saathi": ["sancharsaathi.gov.in"],
    "IRCTC": ["irctc.co.in"],
    "LIC": ["licindia.in"],
    "WhatsApp": ["whatsapp.com"],
    "Netflix": ["netflix.com"],
}

# Words in a message (or a domain) that point to a brand. Short or ambiguous names need word boundaries.
BRAND_WORDS = {
    "SBI": ["sbi", "state bank", "yono"], "HDFC Bank": ["hdfc"], "ICICI Bank": ["icici"],
    "Axis Bank": ["axis bank", "axisbank"], "Kotak Bank": ["kotak"], "PNB": ["pnb", "punjab national"],
    "Bank of Baroda": ["bank of baroda", "bankofbaroda", "bob card"], "Canara Bank": ["canara"],
    "Union Bank": ["union bank"], "Yes Bank": ["yes bank", "yesbank"], "IndusInd Bank": ["indusind"],
    "RBI": ["rbi", "reserve bank"], "NPCI": ["npci"], "Paytm": ["paytm"], "PhonePe": ["phonepe", "phone pe"],
    "Google Pay": ["gpay", "google pay"], "Amazon": ["amazon"], "Flipkart": ["flipkart"],
    "Myntra": ["myntra"], "Swiggy": ["swiggy"], "Zomato": ["zomato"],
    "India Post": ["india post", "indiapost", "speed post"], "Blue Dart": ["bluedart", "blue dart"],
    "Delhivery": ["delhivery"], "DTDC": ["dtdc"], "FedEx": ["fedex"], "Airtel": ["airtel"],
    "Jio": ["jio"], "Vi": ["vodafone", "vi user"], "BSNL": ["bsnl"],
    "BESCOM": ["bescom", "electricity board", "bijli vibhag"], "Income Tax": ["income tax", "incometax", "itr"],
    "EPFO": ["epfo", "epf ", "pf account"], "UIDAI (Aadhaar)": ["aadhaar", "aadhar", "uidai"],
    "TRAI": ["trai"], "IRCTC": ["irctc"], "LIC": ["lic policy", " lic "], "WhatsApp": ["whatsapp"],
    "Netflix": ["netflix"], "Customs": ["customs"], "Police / CBI": ["cbi", "police", "cyber cell", "narcotics"],
    "DigiLocker": ["digilocker"], "Parivahan / e-Challan": ["parivahan", "echallan", "e-challan"],
    "Jeevan Pramaan": ["jeevan pramaan", "jeevanpramaan", "life certificate"], "PM-Kisan": ["pm kisan", "pmkisan"],
    "FASTag": ["fastag"], "MSEDCL": ["msedcl", "mahadiscom", "mahavitaran"], "Indane": ["indane"], "SEBI": ["sebi"],
    "Meesho": ["meesho"], "Zerodha": ["zerodha"], "Groww": ["groww"], "CRED": ["cred app"],
}

# Free website builders, form builders and hosting: anyone can make a page here in minutes, so a "bank" or
# "government" page on these is a classic phishing trick. They are never treated as the brand's official site.
FREE_HOSTS = ["sites.google.com", "docs.google.com", "forms.gle", "blogspot.com", "blogspot.in", "wordpress.com", "wixsite.com",
              "weebly.com", "github.io", "netlify.app", "vercel.app", "web.app", "firebaseapp.com", "pages.dev", "glitch.me",
              "000webhostapp.com", "carrd.co", "linktr.ee", "notion.site", "typeform.com", "jotform.com", "surveyheart.com",
              "onrender.com", "herokuapp.com", "replit.app", "godaddysites.com", "mystrikingly.com", "square.site", "webflow.io",
              "framer.website", "my.canva.site", "tilda.ws", "yolasite.com", "ngrok.io", "ngrok-free.app", "trycloudflare.com"]
SENSITIVE_WORDS = r"(bank|account|details|card|netbanking|password|otp|sbi|hdfc|icici|axis|kotak|pnb|kyc|pan|aadhaa?r|uidai|reward|refund|verify|verification|login|update|customer|care|support|gov|yojana|scheme|pension|loan|tax|challan|electricity|bill|parcel|courier|claim|prize|offer)"

SHORTENERS = {"bit.ly", "tinyurl.com", "t.ly", "is.gd", "cutt.ly", "rb.gy", "goo.gl", "ow.ly",
              "shorturl.at", "tiny.cc", "rebrand.ly", "s.id", "v.gd", "short.gy", "t.co", "bitly.com",
              "tinyurl.in", "u.to", "clck.ru", "lnkd.in", "shrtco.de", "bl.ink", "qr.ae"}
CHAT_LINKS = {"wa.me": "WhatsApp chat", "chat.whatsapp.com": "WhatsApp group", "t.me": "Telegram",
              "telegram.me": "Telegram", "telegram.dog": "Telegram"}
RISKY_TLDS = {"xyz", "top", "club", "online", "site", "icu", "buzz", "live", "click", "link", "vip",
              "shop", "work", "loan", "win", "bid", "info", "cyou", "rest", "fit", "monster", "cfd",
              "sbs", "quest", "today", "support", "help", "app", "pw", "tk", "ml", "ga", "cf", "gq"}
MULTI_SUFFIX = {"co.in", "org.in", "net.in", "gov.in", "nic.in", "ac.in", "edu.in", "res.in",
                "bank.in", "firm.in", "gen.in", "ind.in", "co.uk", "org.uk", "com.au", "co.za"}
TLDS = ("com|in|net|org|co|info|xyz|top|club|online|site|icu|buzz|live|click|link|vip|shop|work|loan|win|"
        "bid|ly|gl|gd|me|io|to|cc|us|uk|app|cyou|rest|fit|monster|cfd|sbs|quest|today|support|help|pw|tk|"
        "ml|ga|cf|gq|ru|cn|sbi|bank|it|at|id|ae|de|dev|ai")

URL_RE = re.compile(
    r"(?i)\b(?:(?:https?|hxxps?)://[^\s<>\"']+"
    r"|www\.[^\s<>\"']+"
    r"|(?:[a-z0-9-]+(?:\.|\[\.\]|\(\.\)))+(?:" + TLDS + r")\b(?:/[^\s<>\"']*)?)"
)


@dataclass
class LinkFinding:
    url: str                     # as written in the message
    start: int
    end: int
    host: str
    registered: str              # e.g. "sbi-kyc-update.xyz"
    verdict: str                 # "official", "suspicious", "dangerous", "unknown"
    official_brand: str | None = None
    issues: list[str] = field(default_factory=list)   # plain-language problems
    notes: list[str] = field(default_factory=list)    # neutral / reassuring facts

    @property
    def defanged(self) -> str:
        return defang(self.url)


def defang(url: str) -> str:
    """Make a link unclickable for storage and reports: http -> hxxp, '.' -> '[.]'."""
    u = re.sub(r"(?i)^http", "hxxp", url)
    return u.replace(".", "[.]")


def _registered(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_SUFFIX:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _edit_distance(a: str, b: str) -> int:
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        # transposition
        prev = cur
    return prev[-1]


_LOOKALIKE_DIGITS = str.maketrans({"0": "o", "1": "l", "3": "e", "5": "s", "4": "a", "7": "t", "8": "b"})


def _official_domains() -> dict[str, str]:
    return {d: brand for brand, ds in OFFICIAL.items() for d in ds}


OFFICIAL_INDEX = _official_domains()


def brands_in(text: str) -> list[str]:
    """Brands mentioned in a (cleaned, lowercase) text."""
    t = f" {text.lower()} "
    # "WhatsApp 98765..." / "on WhatsApp" / "WhatsApp karein" is how to contact the scammer, not impersonation
    t = re.sub(r"(on |par |pe )?whats ?app( (karein|karo|kare|me|pe|par|group|chat|number|no\.?))?(?=\s*[:\-]?\s*(\+?\d|wa\.me|$|[.,!]))", " ", t)
    t = re.sub(r"\b(on|via|par|pe) whats ?app\b|\bwhats ?app (karein|karo|kare|me|pe|par|our|the|hr|manager)\b", " ", t)
    found = []
    for brand, words in BRAND_WORDS.items():
        for w in words:
            if re.search(r"(?<![a-z])" + re.escape(w.strip()) + r"(?![a-z])", t):
                found.append(brand)
                break
    return found


def official_for(host: str) -> str | None:
    host = host.lower().strip(".")
    for dom, brand in OFFICIAL_INDEX.items():
        if host == dom or host.endswith("." + dom):
            return brand
    if host.endswith(".gov.in") or host.endswith(".nic.in"):
        return "Government of India"
    return None


def inspect_url(raw: str, start: int, end: int, mentioned_brands: list[str], context: str = "") -> LinkFinding:
    url = raw.rstrip(".,;:!?)]}'\"")
    end = start + len(url)
    u = re.sub(r"(?i)^hxxp", "http", url).replace("[.]", ".").replace("(.)", ".")
    u = re.sub(r"(?i)^https?://", "", u)
    u = re.sub(r"(?i)^www\.", "", u) if not u.lower().startswith("www.") else u
    host_part = re.split(r"[/?#]", u, maxsplit=1)[0]
    userinfo = "@" in host_part
    host = host_part.rsplit("@", 1)[-1].split(":")[0].lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    reg = _registered(host) if "." in host else host
    f = LinkFinding(url=url, start=start, end=end, host=host, registered=reg, verdict="unknown")

    try:
        ipaddress.ip_address(host)
        f.registered = host
        f.issues.append(f"The link goes to a bare IP address ({host}) instead of a website name. Real banks and companies never do this.")
        f.verdict = "dangerous"
        return f
    except ValueError:
        pass

    path = u[len(host_part):].lower()
    free = next((fh for fh in FREE_HOSTS if host == fh or host.endswith("." + fh)), None)
    if free and not (free == "docs.google.com" and "/forms" not in path):
        if free.count(".") >= 2:
            f.registered = free  # show "sites.google.com", not just "google.com"
        named = [b for b in mentioned_brands if b in OFFICIAL and b != "Google"]
        f.issues.append(f"{free} is a free website or form builder: anyone can create a page here in minutes. "
                        "Real banks, companies and government offices do not collect your details on such pages.")
        if named:
            f.issues.append(f"The message talks about {named[0]}, but this page is not on any official {named[0]} website "
                            f"(official: {', '.join(OFFICIAL[named[0]][:2])}).")
        if named or re.search(SENSITIVE_WORDS, host + path) or re.search(SENSITIVE_WORDS, context):
            f.verdict = "dangerous"
        else:
            f.verdict = "suspicious"
        return f

    brand = official_for(host)
    if brand:
        f.official_brand = brand
        f.verdict = "official"
        f.notes.append(f"{reg} is an official domain of {brand}.")
        if userinfo:
            f.issues.append("The link hides its real address after an '@' sign.")
            f.verdict = "dangerous"
        return f

    if reg in SHORTENERS or host in SHORTENERS:
        f.issues.append(f"{host} is a link shortener: it hides the real website. Where it really leads cannot be checked without opening it, which is unsafe.")
        f.verdict = "suspicious"
    if host in CHAT_LINKS or reg in CHAT_LINKS:
        f.issues.append(f"The link opens a {CHAT_LINKS.get(host, CHAT_LINKS.get(reg))} with an unknown person. Banks and companies do not move customers to private chats.")
        f.verdict = "suspicious"
    if host.startswith("xn--") or ".xn--" in host:
        f.issues.append("The domain uses 'punycode' (xn--), which can disguise lookalike letters from other alphabets.")
        f.verdict = "dangerous"
    if userinfo:
        f.issues.append("The link hides its real address after an '@' sign (everything before '@' is ignored by the browser).")
        f.verdict = "dangerous"
    if url.lower().split("?")[0].endswith(".apk"):
        f.issues.append("The link downloads an Android app file (.apk) from outside the Play Store. Such apps are used to steal OTPs and take over phones.")
        f.verdict = "dangerous"

    for dom, b in OFFICIAL_INDEX.items():
        if host.startswith(dom + ".") or host.startswith(dom + "-"):
            f.issues.append(f"The address starts with '{dom}' to look like {b}, but the real website is decided by "
                            f"the END of the address: '{reg}', which has nothing to do with {b}.")
            f.verdict = "dangerous"
            break

    # pretends to be a government site: ".gov.in" in the middle of the address, or "gov" glued into another domain
    if ".gov.in." in host + "." and not (host.endswith(".gov.in") or host.endswith(".nic.in")):
        f.issues.append(f"The address contains 'gov.in' to look official, but the real website is '{reg}', which is not a government domain.")
        f.verdict = "dangerous"
    elif re.search(r"(^|[-.])gov([-.]|$)|-gov|gov-|govt", reg.split(".")[0] + ("." + ".".join(reg.split(".")[1:-1]) if reg.count(".") > 1 else "")):
        f.issues.append(f"'{reg}' uses the word 'gov' to look like a government website, but real Indian government sites end in "
                        "'.gov.in' or '.nic.in'.")
        f.verdict = "dangerous"

    tld = reg.rsplit(".", 1)[-1]
    if tld in RISKY_TLDS and reg not in SHORTENERS:
        f.issues.append(f"The domain ends in '.{tld}', a cheap ending often used for throw-away scam sites and rarely used by genuine Indian companies.")
        f.verdict = "suspicious" if f.verdict == "unknown" else f.verdict

    # brand impersonation: brand name inside a domain that is not that brand's
    label = reg.split(".")[0] if not reg.endswith(tuple("." + s for s in MULTI_SUFFIX)) else reg.split(".")[0]
    whole = host.replace("-", " ").replace(".", " ")
    for b, words in BRAND_WORDS.items():
        if b not in OFFICIAL:
            continue
        for w in words:
            w2 = w.strip().replace(" ", "")
            if len(w2) >= 3 and (re.search(r"(?<![a-z])" + re.escape(w2) + r"(?![a-z])", whole)
                                 or (len(w2) >= 5 and w2 in host.replace("-", "").replace(".", ""))):
                offs = ", ".join(OFFICIAL[b][:2])
                f.issues.append(f"The domain contains the name '{w2}' but it is NOT an official {b} domain "
                                f"(official: {offs}). Using a brand's name inside a different domain is a classic phishing trick.")
                f.official_brand = None
                f.verdict = "dangerous"
                break
        else:
            continue
        break

    # lookalike / typo domains: sbl.co.in, hdfcbnak.com, 0nlinesbi.sbi
    if f.verdict != "dangerous":
        lab = label.translate(_LOOKALIKE_DIGITS)
        for dom, b in OFFICIAL_INDEX.items():
            olab = dom.split(".")[0]
            if len(olab) < 4 or olab == label:
                continue
            d = _edit_distance(lab, olab)
            if d <= (1 if len(olab) <= 6 else 2) or (lab == olab and label != olab):
                f.issues.append(f"'{reg}' looks almost like the official {b} domain '{dom}', but it is a different website (a typo or lookalike domain).")
                f.verdict = "dangerous"
                break

    if mentioned_brands and f.verdict != "official":
        real = [b for b in mentioned_brands if b in OFFICIAL]
        if real and not any("NOT an official" in i for i in f.issues):
            b = real[0]
            f.issues.append(f"The message talks about {b}, but this link does not go to any official {b} website "
                            f"(official: {', '.join(OFFICIAL[b][:2])}).")
            f.verdict = "dangerous" if f.verdict in ("suspicious", "dangerous") else "suspicious"

    if f.verdict == "unknown":
        f.notes.append(f"{reg} is not on our list of official domains. That alone does not make it a scam.")
    if raw.lower().startswith("http://"):
        f.notes.append("The link uses plain http (not https), so the connection would not be encrypted.")
    return f


def find_links(text: str, mentioned_brands: list[str] | None = None) -> list[LinkFinding]:
    """All links in the ORIGINAL message, with positions so they can be highlighted."""
    mentioned_brands = mentioned_brands or []
    out = []
    for m in URL_RE.finditer(text):
        raw = m.group()
        if re.fullmatch(r"(?i)[\d.]+", raw) and raw.count(".") != 3:
            continue  # "Rs.500.00" is not a link
        if re.fullmatch(r"(?i)[a-z]+\.(in|co|me|to|it|at|id)", raw) and not raw.lower().startswith(("wa.", "t.")):
            # "logged.in", "go.to" style words: only accept if it is a known domain
            if not official_for(raw.lower()) and raw.lower() not in SHORTENERS:
                continue
        out.append(inspect_url(raw, m.start(), m.end(), mentioned_brands, text.lower()))
    for m in re.finditer(r"(?i)\b(javascript|data|vbscript):[^\s]+", text):
        out.append(LinkFinding(url=m.group(), start=m.start(), end=m.end(), host=m.group(1).lower() + ":",
                               registered=m.group(1).lower() + ":", verdict="dangerous",
                               issues=[f"This is a '{m.group(1).lower()}:' link: it runs code instead of opening a website. "
                                       "Genuine messages never contain such links."]))
    return out


def phone_numbers(text: str) -> list[tuple[int, int, str, str]]:
    """Indian phone numbers: (start, end, number, kind) where kind is 'mobile', 'tollfree' or 'landline'."""
    res = []
    for m in re.finditer(r"(?<![\w*])(?:\+?91[\s-]?|0)?([6-9]\d{4}[\s-]?\d{5})(?!\d)", text):
        before = text[max(0, m.start() - 14):m.start()].lower()
        if re.search(r"(awb|ref|no|order|pnr|id|txn|utr|#|booking|tracking|shipment|article|rr|consumer)\W{0,3}$", before):
            continue  # a reference / tracking number, not a phone number
        res.append((m.start(), m.end(), m.group(), "mobile"))
    for m in re.finditer(r"(?<!\d)(1800[\s-]?\d{3}[\s-]?\d{3,4}|1860[\s-]?\d{3}[\s-]?\d{4}|1930|1909|155260)(?!\d)", text):
        res.append((m.start(), m.end(), m.group(), "tollfree"))
    for m in re.finditer(r"(?<![\w+])\+(?!91)(\d{1,3})[\s-]?\d[\d\s-]{6,13}\d(?!\d)", text):
        res.append((m.start(), m.end(), m.group(), "international"))  # e.g. +852..., +44..., common in job/investment scams
    return res
