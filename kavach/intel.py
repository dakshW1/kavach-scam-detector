"""Online Scam Intel (OPTIONAL, off by default): "Is this kind of scam happening to other people?"

Rules:
  * Never sends the message. The search is built only from the RESULT: scam type + brand name,
    e.g. "SBI KYC scam". The user sees exactly these words and must click "Send this search".
  * Only one host is contacted (news.google.com, public RSS search, no account or API key), inside
    netguard.allow(), so the rest of the app stays blocked even while this runs.
  * Results are summarised on this computer (counts, dates, cities, headlines). Nothing is sent to
    any AI service.
"""
from __future__ import annotations

import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from . import netguard

HOST = "news.google.com"
FAMILY_TERMS = {
    "kyc_bank": "KYC update scam", "sim_kyc": "SIM KYC scam", "lottery": "lottery prize scam",
    "loan_app": "loan app fraud", "task_job": "part time job task scam", "investment": "trading investment fraud",
    "electricity": "electricity bill disconnection scam", "parcel_customs": "parcel courier customs scam",
    "digital_arrest": "digital arrest scam", "refund": "refund scam", "upi_collect": "UPI collect request fraud",
    "family_emergency": "new number family emergency scam", "account_takeover": "WhatsApp OTP account hijack scam",
    "unknown": "SMS scam",
}
CITIES = ["Bengaluru", "Bangalore", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai", "Kolkata", "Ahmedabad",
          "Jaipur", "Lucknow", "Noida", "Gurugram", "Gurgaon", "Mysuru", "Mangaluru", "Kochi", "Indore", "Bhopal",
          "Chandigarh", "Patna", "Nagpur", "Surat", "Thane", "Coimbatore", "Visakhapatnam", "Vadodara", "Ludhiana"]


@dataclass
class IntelResult:
    query: str
    articles: list[dict] = field(default_factory=list)
    error: str | None = None
    fetched_at: str = ""

    @property
    def last_30(self) -> int:
        cut = datetime.now(timezone.utc) - timedelta(days=30)
        return sum(1 for a in self.articles if a["date"] and a["date"] >= cut)

    @property
    def cities(self) -> list[tuple[str, int]]:
        c = Counter()
        for a in self.articles:
            for city in CITIES:
                if re.search(rf"\b{city}\b", a["title"], re.I):
                    c["Bengaluru" if city == "Bangalore" else "Gurugram" if city == "Gurgaon" else city] += 1
        return c.most_common(6)

    @property
    def amounts(self) -> list[str]:
        out = []
        for a in self.articles:
            out += re.findall(r"(?:Rs\.?|₹)\s?[\d.,]+\s?(?:lakh|crore|cr)?", a["title"], re.I)
        return out[:6]


def build_query(result) -> str:
    """Generic words only: brand + scam type. No message text, numbers, links or names."""
    words = []
    brand = next((b for b in result.brands if b not in ("Customs", "Police / CBI")), None)
    if brand and result.family in ("kyc_bank", "refund", "parcel_customs", "lottery", "task_job", "electricity", "sim_kyc"):
        words.append(brand.split(" (")[0])
    words.append(FAMILY_TERMS.get(result.family or "unknown", "SMS scam"))
    words.append("India")
    return " ".join(words)


def search(query: str, days: int = 120, timeout: float = 8.0) -> IntelResult:
    url = (f"https://{HOST}/rss/search?" + urllib.parse.urlencode(
        {"q": f"{query} when:{days}d", "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}))
    res = IntelResult(query=query, fetched_at=datetime.now().strftime("%d %b %Y %H:%M"))
    try:
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Kavach offline scam checker)"})
        with netguard.allow({HOST}):
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                data = r.read()
        root = ET.fromstring(data)
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            src = item.find("source")
            source = src.text if src is not None else ""
            if source and title.endswith(" - " + source):
                title = title[: -len(source) - 3]
            try:
                date = parsedate_to_datetime(item.findtext("pubDate") or "")
            except (TypeError, ValueError):
                date = None
            res.articles.append({"title": title, "link": item.findtext("link") or "", "source": source, "date": date})
        res.articles.sort(key=lambda a: a["date"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    except netguard.NetworkBlocked as e:
        res.error = str(e)
    except Exception as e:  # no internet, timeout, site changed...
        res.error = f"Could not reach the news search ({type(e).__name__}). The offline Scam Library below still has the full guide."
    return res
