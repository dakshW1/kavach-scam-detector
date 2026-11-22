"""TESTER set -> data/tester_set.csv: the messages five persona testers (an elderly user, an ML judge, a cyber-crime
police officer, a product designer and a red-team student) typed into Kavach on 23 Nov 2026, labelled by hand.

Used for error analysis only (like the challenge set): the rule/data fixes of v2 were motivated by these
messages, so this set is NOT an untouched estimate. The untouched estimate is data/final_test_v2.csv.
Never used for training. Junk probes (HTML/script injection strings, random words) are left out.
"""
import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
K, L, LO, J, O = "KYC/Bank", "Lottery/Prize", "Loan/Credit", "Job/Investment", "Other"
SCAM = {0: O, 1: K, 2: O, 3: O, 4: O, 9: K, 10: O, 11: J, 14: O, 15: K, 23: K, 30: O, 31: O, 32: J, 33: K, 34: O,
        35: K, 41: O, 42: J, 43: O, 46: O, 50: O, 51: O, 53: K, 54: K, 55: L, 56: K, 59: K, 60: K, 61: O, 62: O, 63: K,
        64: LO, 67: J, 69: O, 70: O, 71: O, 73: K, 74: K, 75: O, 78: K, 81: K, 82: K, 83: K, 84: K, 86: O, 87: K, 88: L,
        89: J, 90: K, 91: K, 97: O, 98: K, 99: K, 100: K, 101: K, 102: O, 103: K, 104: K, 105: J, 106: O, 107: O, 108: O,
        109: O, 110: O, 113: K, 114: O, 116: O, 118: L, 119: K, 120: J, 122: K, 123: K, 124: K, 125: LO, 126: K, 127: K,
        128: O, 129: O, 130: O, 132: O, 133: K, 134: O}
SAFE = {"bank_alert": [8, 21, 24, 25, 28, 29, 36, 37, 38, 45, 65, 94, 111, 141],
        "otp": [13, 26, 39, 58, 66, 112], "delivery": [7, 16, 17, 18, 72, 140],
        "service": [20, 27, 44, 92, 96, 137, 143], "awareness": [5, 6, 19, 121, 135], "promo": [40, 136],
        "personal": [12, 22, 48, 52, 57, 68, 93, 95, 115, 117, 138, 139, 142, 144]}
HOAX = [47, 49]   # chain forwards / misinformation: not a money scam, but must not be called SAFE

if __name__ == "__main__":
    msgs = json.loads((HERE / "tester_msgs_raw.json").read_text(encoding="utf-8"))
    rows = []
    for i, cat in SCAM.items():
        rows.append(("SCAM", cat, msgs[i][0], msgs[i][1]))
    for kind, ids in SAFE.items():
        rows += [("SAFE", "", kind, msgs[i][1]) for i in ids]
    rows += [("HOAX", "", "hoax", msgs[i][1]) for i in HOAX]
    with (HERE / "tester_set.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["label", "category", "kind", "text"])
        w.writerows(rows)
    from collections import Counter
    print(len(rows), Counter(r[0] for r in rows))
