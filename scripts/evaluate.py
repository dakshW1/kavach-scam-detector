"""Evaluate the saved model and write results/metrics.json + charts (shown on the app's Results page).

Test sets
  * test      : generated + UCI messages from templates/messages never used in training
  * challenge : 101 hand-written messages (used for error analysis while improving the rules)
  * final     : 72 hand-written messages (v1), written before the first tuning
  * final_v2  : 68 hand-written messages written before the v2 fixes, never used for error analysis
  * tester    : 137 messages typed by five persona testers (used for error analysis in v2)

Metrics
  * detection : accuracy, precision, recall, F1 (a message counts as flagged if the verdict is SCAM)
  * caught    : share of scams flagged as SCAM or SUSPICIOUS (the user is warned either way)
  * false alarms on genuine messages: SCAM rate and SUSPICIOUS rate, overall and for bank alerts / OTPs / deliveries
  * category  : accuracy and macro-F1 on scams
  * robustness: detection on disguised copies of the test scams, with and without the text cleaner
  * calibration: reliability chart, expected calibration error (ECE), Brier score
  * speed     : milliseconds per message, model size

Run:  python scripts/evaluate.py          (add --no-ablation to skip the 'without cleaner' retraining)
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data"))

from kavach import detector, normalize as norm_mod, rules as rules_mod  # noqa: E402
from kavach.model import CATEGORIES, MODEL_PATH, KavachModel, train  # noqa: E402

RESULTS = ROOT / "results"


def load(name):
    return list(csv.DictReader(open(ROOT / "data" / name, encoding="utf-8")))


def run(model, rows):
    out = []
    for r in rows:
        res = detector.analyze(r["text"], model=model)
        out.append((r, res))
    return out


def summarise(pairs):
    y = np.array([r["label"] == "SCAM" for r, _ in pairs])
    v = np.array([res.verdict for _, res in pairs])
    flagged = v == "SCAM"
    warned = v != "SAFE"
    tp, fp = int((flagged & y).sum()), int((flagged & ~y).sum())
    fn, tn = int((~flagged & y).sum()), int((~flagged & ~y).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    m = {
        "n": len(pairs), "n_scam": int(y.sum()), "n_safe": int((~y).sum()),
        "accuracy": float((flagged == y).mean()), "precision": prec, "recall": rec,
        "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
        "caught_scam_or_suspicious": float(warned[y].mean()) if y.any() else None,
        "safe_marked_scam": float(flagged[~y].mean()) if (~y).any() else None,
        "safe_marked_suspicious": float((v[~y] == "SUSPICIOUS").mean()) if (~y).any() else None,
        "verdicts": {k: {"SCAM": int(((v == "SCAM") & (y == (k == "scam"))).sum()),
                         "SUSPICIOUS": int(((v == "SUSPICIOUS") & (y == (k == "scam"))).sum()),
                         "SAFE": int(((v == "SAFE") & (y == (k == "scam"))).sum())} for k in ("scam", "safe")},
    }
    # false alarms on the genuine messages that matter most
    by_kind = {}
    for kind in ("bank_alert", "otp", "delivery"):
        sel = [res.verdict for r, res in pairs if r["label"] == "SAFE" and r.get("kind") == kind]
        if sel:
            by_kind[kind] = {"n": len(sel), "marked_scam": sum(s == "SCAM" for s in sel) / len(sel),
                             "marked_suspicious": sum(s == "SUSPICIOUS" for s in sel) / len(sel)}
    m["false_alarms_by_kind"] = by_kind
    # category on scams that were warned about
    cats = [(r["category"], res.category) for r, res in pairs if r["label"] == "SCAM" and res.verdict != "SAFE"]
    if cats:
        from sklearn.metrics import f1_score
        t, p = zip(*cats)
        m["category_accuracy"] = float(np.mean([a == b for a, b in cats]))
        m["category_macro_f1"] = float(f1_score(t, p, labels=CATEGORIES, average="macro", zero_division=0))
        conf = {a: {b: 0 for b in CATEGORIES} for a in CATEGORIES}
        for a, b in cats:
            if a in conf and b in conf[a]:
                conf[a][b] += 1
        m["category_confusion"] = conf
    # scam detection by language / trick (hand-written sets)
    kinds = {}
    for r, res in pairs:
        if r["label"] == "SCAM" and r.get("kind") in ("english", "hinglish", "hindi", "disguised"):
            kinds.setdefault(r["kind"], []).append(res.verdict != "SAFE")
    if kinds:
        m["caught_by_kind"] = {k: {"n": len(v_), "caught": float(np.mean(v_))} for k, v_ in kinds.items()}
    return m


def calibration(pairs, bins=5):
    p = np.array([res.p_scam for _, res in pairs])
    y = np.array([r["label"] == "SCAM" for r, _ in pairs], dtype=float)
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        if sel.sum():
            conf, acc = float(p[sel].mean()), float(y[sel].mean())
            ece += sel.sum() / len(p) * abs(conf - acc)
            rows.append({"lo": float(lo), "hi": float(hi), "n": int(sel.sum()), "mean_p": conf, "frac_scam": acc})
    return {"bins": rows, "ece": float(ece), "brier": float(np.mean((p - y) ** 2))}


def plot_reliability(cal, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5, 4.2), dpi=130)
    ax.plot([0, 1], [0, 1], ls="--", color="#999", lw=1, label="perfectly honest")
    xs = [b["mean_p"] for b in cal["bins"]]
    ys = [b["frac_scam"] for b in cal["bins"]]
    ns = [b["n"] for b in cal["bins"]]
    ax.plot(xs, ys, marker="o", color="#2a6fdb", lw=2, label="Kavach")
    for x, y_, n in zip(xs, ys, ns):
        ax.annotate(str(n), (x, y_), textcoords="offset points", xytext=(4, -10), fontsize=7, color="#555")
    ax.set_xlabel("Confidence the model gave (scam probability)")
    ax.set_ylabel("How often it really was a scam")
    ax.set_title(f"Confidence reliability  (ECE {cal['ece']:.3f})", fontsize=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(alpha=.25)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def robustness(model, test_rows, seed=7):
    import generate
    generate.rng.seed(seed)
    scams = [r for r in test_rows if r["label"] == "SCAM" and r["source"] == "generated"]
    disguised = [dict(r, text=generate.obfuscate(r["text"])) for r in scams]
    clean = summarise(run(model, scams))["caught_scam_or_suspicious"]
    obf = summarise(run(model, disguised))["caught_scam_or_suspicious"]
    return {"n": len(scams), "caught_original": clean, "caught_disguised": obf, "examples": [d["text"] for d in disguised[:5]]}, disguised


def ablation_no_cleaner(train_rows, disguised, scams):
    """Retrain with the text cleaner switched off and measure the same disguised scams."""
    real = norm_mod.normalize

    def identity(text):
        n = real("")
        return norm_mod.Normalized(text, text.lower(), list(range(len(text))), {})

    norm_mod.normalize = identity
    rules_mod.normalize = identity
    detector.normalize = identity
    orig_clean = norm_mod.clean
    import kavach.model as km
    km.clean = lambda t: t.lower()
    try:
        m = train([r["text"] for r in train_rows], [int(r["label"] == "SCAM") for r in train_rows],
                  [r["category"] for r in train_rows], [r["group"] for r in train_rows], log=lambda *a: None)
        res = {"caught_original": summarise(run(m, scams))["caught_scam_or_suspicious"],
               "caught_disguised": summarise(run(m, disguised))["caught_scam_or_suspicious"]}
    finally:
        norm_mod.normalize = real
        rules_mod.normalize = real
        detector.normalize = real
        km.clean = orig_clean
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ablation", action="store_true")
    args = ap.parse_args()
    RESULTS.mkdir(exist_ok=True)
    model = KavachModel.load(MODEL_PATH)
    rows = load("messages.csv")
    train_rows = [r for r in rows if r["split"] == "train"]
    test_rows = [r for r in rows if r["split"] == "test"]
    tester_all = load("tester_set.csv")
    sets = {"test": test_rows, "challenge": load("challenge.csv"), "final": load("final_test.csv"),
            "final_v2": load("final_test_v2.csv"), "tester": [r for r in tester_all if r["label"] in ("SCAM", "SAFE")]}

    metrics = {"model": {"size_mb": MODEL_PATH.stat().st_size / 1e6, "t_safe": model.t_safe, "t_scam": model.t_scam,
                         "n_train": model.info.get("n_train"), "n_features": model.info.get("n_features")}}
    all_pairs = []
    for name, rs in sets.items():
        t0 = time.perf_counter()
        pairs = run(model, rs)
        dt = (time.perf_counter() - t0) / len(rs) * 1000
        metrics[name] = summarise(pairs)
        metrics[name]["ms_per_message"] = dt
        metrics[name]["calibration"] = calibration(pairs)
        all_pairs += pairs
        if name != "test":
            metrics[name]["mistakes"] = [{"text": r["text"], "label": r["label"], "category": r["category"],
                                          "verdict": res.verdict, "p_scam": round(res.p_scam, 3), "pred_category": res.category}
                                         for r, res in pairs
                                         if (res.verdict == "SAFE") == (r["label"] == "SCAM") or res.verdict == "SUSPICIOUS"
                                         or (r["label"] == "SCAM" and res.category != r["category"])]
        print(f"{name:9s} n={len(rs):4d} acc={metrics[name]['accuracy']:.3f} P={metrics[name]['precision']:.3f} "
              f"R={metrics[name]['recall']:.3f} caught={metrics[name]['caught_scam_or_suspicious']:.3f} "
              f"safe->scam={metrics[name]['safe_marked_scam']:.3f} safe->susp={metrics[name]['safe_marked_suspicious']:.3f} "
              f"cat_acc={metrics[name].get('category_accuracy', 0):.3f} ECE={metrics[name]['calibration']['ece']:.3f} "
              f"{dt:.1f} ms/msg")

    hoax = [r for r in tester_all if r["label"] == "HOAX"]
    metrics["hoax_not_safe"] = {"n": len(hoax), "warned": sum(detector.analyze(r["text"], model=model).verdict != "SAFE" for r in hoax)}
    cal = calibration([p for p in all_pairs])
    metrics["calibration_all"] = cal
    plot_reliability(cal, RESULTS / "reliability.png")

    rob, disguised = robustness(model, test_rows)
    metrics["robustness"] = rob
    print(f"robustness: caught original {rob['caught_original']:.3f} -> disguised {rob['caught_disguised']:.3f}")
    if not args.no_ablation:
        scams = [r for r in test_rows if r["label"] == "SCAM" and r["source"] == "generated"]
        ab = ablation_no_cleaner(train_rows, disguised, scams)
        metrics["robustness"]["without_cleaner"] = ab
        print(f"without cleaner: original {ab['caught_original']:.3f} -> disguised {ab['caught_disguised']:.3f}")

    (RESULTS / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print("wrote results/metrics.json and results/reliability.png")


if __name__ == "__main__":
    main()
