"""The Scam Diary recognises a message checked before (same or very similar) and does not store it twice."""
import pytest

from kavach import diary
from kavach.detector import analyze

SCAM = "Dear customer, your SBI account will be blocked today. Update KYC at http://sbi-kyc-update.xyz or call 9876543210"
VARIANT = "Dear customer, your SBI account will be blocked today. Update KYC at http://sbi-verify-now.top or call 9123400000"
OTHER = "Congratulations! You won Rs 25 lakh in the KBC lottery. Pay Rs 4999 processing fee to claim."


@pytest.fixture
def tmp_diary(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(diary, "_SESSION", [])
    diary.save_settings({"diary_enabled": True})
    return tmp_path / "diary.db"


def check(text, db):
    r = analyze(text)
    prev = diary.lookup(r, path=db)
    saved = diary.add(r, path=db, previous=prev)
    diary.remember(r)
    return prev, saved


def test_same_message_is_counted_not_duplicated(tmp_diary):
    prev, saved = check(SCAM, tmp_diary)
    assert prev is None and saved["times_seen"] == 1
    prev, saved = check(SCAM, tmp_diary)
    assert prev["match"] == "same" and saved["updated"] and saved["times_seen"] == 2
    rows = diary.entries(tmp_diary)
    assert len(rows) == 1 and rows[0]["times_seen"] == 2 and diary.stats(rows)["received"] == 2


def test_similar_scam_with_other_number_and_link_is_recognised(tmp_diary):
    check(SCAM, tmp_diary)
    prev, _ = check(VARIANT, tmp_diary)
    assert prev["match"] == "similar" and prev["similarity"] >= diary.SIMILAR_MIN
    assert len(diary.entries(tmp_diary)) == 1


def test_different_scam_is_a_new_entry(tmp_diary):
    check(SCAM, tmp_diary)
    prev, saved = check(OTHER, tmp_diary)
    assert prev is None and not saved["updated"] and len(diary.entries(tmp_diary)) == 2


def test_fingerprint_does_not_reveal_the_message(tmp_diary):
    check(SCAM, tmp_diary)
    raw = tmp_diary.read_bytes().decode("utf-8", errors="ignore")
    assert "9876543210" not in raw and "sbi-kyc-update.xyz" not in raw


def test_session_memory_works_with_diary_off(tmp_path, monkeypatch):
    monkeypatch.setattr(diary, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(diary, "_SESSION", [])
    db = tmp_path / "diary.db"
    check(SCAM, db)
    prev, saved = check(SCAM, db)
    assert saved is None and not db.exists()
    assert prev["match"] == "same" and prev["source"] == "session"
