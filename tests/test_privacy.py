"""Privacy proof: Kavach works with the network blocked and never stores private details.

Run:  pytest tests/test_privacy.py -v
"""
import socket
import urllib.request

import pytest

from kavach import diary, netguard, report
from kavach.detector import analyze

SCAM = ("Dear Rahul, your SBI account XX4321 will be blocked today. Update KYC at http://sbi-kyc-update.xyz "
        "or call 9876543210. Share OTP 482913 with our officer. Pay to rahul99@ybl")


@pytest.fixture
def guard():
    netguard.enable()
    netguard.blocked_attempts.clear()
    yield
    netguard.disable()


@pytest.fixture
def spy(monkeypatch):
    """Counts every outgoing connection attempt at the lowest level, whatever library makes it."""
    calls = []
    real = socket.socket.connect

    def counting_connect(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            calls.append(address)
        return real(self, address)

    monkeypatch.setattr(socket.socket, "connect", counting_connect)
    return calls


def test_internet_is_blocked_when_guard_is_on(guard):
    with pytest.raises(OSError):
        urllib.request.urlopen("https://example.com", timeout=3)
    with pytest.raises(netguard.NetworkBlocked):
        socket.create_connection(("1.1.1.1", 443), timeout=1)
    assert netguard.self_test()
    assert netguard.blocked_attempts  # the attempts were recorded


def test_full_analysis_makes_no_network_calls(spy):
    res = analyze(SCAM, sender="9876543210")
    rep = report.build(res)
    report.text_report(rep)
    report.pdf_report(rep)
    assert res.verdict == "SCAM"
    assert spy == [], f"unexpected network connections: {spy}"


def test_analysis_works_with_guard_on(guard):
    res = analyze(SCAM)
    assert res.verdict == "SCAM" and res.category == "KYC/Bank"
    assert not netguard.blocked_attempts, "analysis tried to reach the internet"


def test_diary_is_off_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(diary, "settings", lambda path=tmp_path / "settings.json": diary.DEFAULTS | {})
    assert diary.is_enabled() is False
    assert diary.add(analyze(SCAM), path=tmp_path / "diary.db") is None
    assert not (tmp_path / "diary.db").exists()


def test_diary_stores_only_masked_lesson(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "is_enabled", lambda: True)
    db = tmp_path / "diary.db"
    diary.add(analyze(SCAM), path=db)
    raw = db.read_bytes().decode("utf-8", errors="ignore")
    for secret in ("9876543210", "482913", "4321", "rahul99@ybl", "Rahul", "http://sbi-kyc-update.xyz"):
        assert secret not in raw, f"diary file contains private detail {secret!r}"
    e = diary.entries(path=db)[0]
    assert e["category"] == "KYC/Bank" and "hxxp://sbi-kyc-update[.]xyz" in e["snippet"]
    diary.delete_all(path=db)
    assert not db.exists()


def test_family_alert_has_no_personal_data(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "is_enabled", lambda: True)
    db = tmp_path / "diary.db"
    diary.add(analyze(SCAM), path=db)
    alert = diary.family_alert(diary.entries(path=db))
    for secret in ("9876543210", "482913", "rahul", "sbi-kyc-update"):
        assert secret not in (alert["en"] + alert["hi"]).lower()


def test_online_intel_query_contains_no_message_details():
    from kavach import intel
    q = intel.build_query(analyze(SCAM)).lower()
    for secret in ("9876543210", "482913", "rahul", "sbi-kyc-update", "4321"):
        assert secret not in q
    assert "scam" in q
