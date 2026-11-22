"""Train the scam + category models on the training split and save models/kavach.joblib.

Run:  python data/generate.py && python data/challenge.py && python scripts/train.py
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kavach.model import MODEL_PATH, train  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main():
    rows = [r for r in csv.DictReader(open(ROOT / "data" / "messages.csv", encoding="utf-8")) if r["split"] == "train"]
    model = train([r["text"] for r in rows], [int(r["label"] == "SCAM") for r in rows],
                  [r["category"] for r in rows], [r["group"] for r in rows])
    model.save(MODEL_PATH)
    print(f"saved -> {MODEL_PATH.relative_to(ROOT)} ({MODEL_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
