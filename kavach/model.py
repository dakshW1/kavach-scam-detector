"""The machine-learning part: TF-IDF features + logistic regression, with calibrated confidence.

Two models share the same features:
  * scam model      SCAM vs SAFE  (trained on all training messages)
  * category model  KYC/Bank, Lottery/Prize, Loan/Credit, Job/Investment, Other  (trained on scams only)

Features for one message (all computed on the cleaned text, see normalize.py):
  * word TF-IDF (single words and pairs)   -> learns phrases like "kyc update", "processing fee"
  * character TF-IDF (2-5 letter pieces)   -> robust to typos, Hinglish spellings and leftover tricks
  * red-flag rules (see rules.py), one 0/1 column per rule

Confidence: logistic regression already outputs probabilities, but they are often over- or
under-confident. We fix that with "Platt scaling": on predictions the model made for messages it
was NOT trained on (cross-validation, grouped by template), we fit a small curve that maps raw
scores to honest probabilities. The Results page shows the reliability chart that checks it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import numpy as np
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from .normalize import clean
from .rules import RULE_IDS, find_flags, flag_vector

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "kavach.joblib"
CATEGORIES = ["KYC/Bank", "Lottery/Prize", "Loan/Credit", "Job/Investment", "Other"]
RULE_WEIGHT = 1.0


def rule_matrix(texts: list[str]) -> sparse.csr_matrix:
    rows = []
    for t in texts:
        flags, _, brands = find_flags(t)
        v = flag_vector(flags, brands)
        rows.append([v[r] for r in RULE_IDS])
    return sparse.csr_matrix(np.array(rows, dtype=np.float64) * RULE_WEIGHT)


@dataclass
class Featurizer:
    word: TfidfVectorizer = field(default_factory=lambda: TfidfVectorizer(
        preprocessor=clean, ngram_range=(1, 2), min_df=2, max_features=20000, sublinear_tf=True,
        token_pattern=r"(?u)\b\w[\w'/-]*\b"))
    char: TfidfVectorizer = field(default_factory=lambda: TfidfVectorizer(
        preprocessor=clean, analyzer="char_wb", ngram_range=(2, 5), min_df=3, max_features=40000, sublinear_tf=True))

    def fit(self, texts):
        self.word.fit(texts)
        self.char.fit(texts)
        return self

    def transform(self, texts, rules: sparse.csr_matrix | None = None):
        r = rules if rules is not None else rule_matrix(texts)
        return sparse.hstack([self.word.transform(texts), self.char.transform(texts), r]).tocsr()

    @property
    def names(self) -> list[str]:
        return ([f"word:{w}" for w in self.word.get_feature_names_out()]
                + [f"char:{c}" for c in self.char.get_feature_names_out()]
                + [f"rule:{r}" for r in RULE_IDS])


@dataclass
class Platt:
    a: float = 1.0
    b: float = 0.0

    def fit(self, scores, y):
        lr = LogisticRegression(C=1e4).fit(np.asarray(scores).reshape(-1, 1), y)
        self.a, self.b = float(lr.coef_[0, 0]), float(lr.intercept_[0])
        return self

    def __call__(self, scores):
        return 1.0 / (1.0 + np.exp(-(self.a * np.asarray(scores) + self.b)))


@dataclass
class KavachModel:
    feats: Featurizer
    scam: LogisticRegression
    platt: Platt
    category: LogisticRegression
    t_safe: float = 0.35      # below -> SAFE
    t_scam: float = 0.70      # at/above -> SCAM ; in between -> SUSPICIOUS
    other_min: float = 0.45   # category probability below this -> "Other (unfamiliar pattern)"
    info: dict = field(default_factory=dict)

    # ---- inference
    def scam_proba(self, texts, X=None) -> np.ndarray:
        X = X if X is not None else self.feats.transform(texts)
        return self.platt(self.scam.decision_function(X))

    def raw_proba(self, texts, X=None) -> np.ndarray:
        X = X if X is not None else self.feats.transform(texts)
        return self.scam.predict_proba(X)[:, 1]

    def category_proba(self, texts, X=None) -> np.ndarray:
        X = X if X is not None else self.feats.transform(texts)
        return self.category.predict_proba(X)

    def contributions(self, X_row, top=8) -> list[tuple[str, float]]:
        """Which features pushed this message towards SCAM (+) or SAFE (-): weight x value."""
        row = X_row.tocsr()
        idx = row.indices
        vals = row.data * self.scam.coef_[0, idx]
        names = self.info.setdefault("_names", self.feats.names)
        order = np.argsort(-np.abs(vals))[:top * 3]
        out = []
        for i in order:
            out.append((names[idx[i]], float(vals[i])))
        return out

    def save(self, path: Path = MODEL_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.info.pop("_names", None)
        joblib.dump(self, path, compress=3)

    @staticmethod
    def load(path: Path = MODEL_PATH) -> "KavachModel":
        return joblib.load(path)


def train(texts, labels, categories, groups, C=4.0, log=print) -> KavachModel:
    """labels: 1 = scam, 0 = safe. categories: category string for scams ('' for safe)."""
    texts = list(texts)
    y = np.asarray(labels)
    groups = np.asarray(groups)
    log(f"training on {len(texts)} messages ({y.sum()} scam / {len(y) - y.sum()} safe)")
    R = rule_matrix(texts)
    feats = Featurizer().fit(texts)
    X = feats.transform(texts, R)

    def make():
        return LogisticRegression(C=C, class_weight="balanced", max_iter=3000)

    # out-of-fold scores (grouped by template, so near-duplicates never leak) -> Platt calibration
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(n_splits=5).split(X, y, groups):
        m = make().fit(X[tr], y[tr])
        oof[va] = m.decision_function(X[va])
    platt = Platt().fit(oof, y)
    scam = make().fit(X, y)

    is_scam = y == 1
    cat_y = np.asarray(categories)[is_scam]
    category = LogisticRegression(C=C, class_weight="balanced", max_iter=3000).fit(X[is_scam], cat_y)
    model = KavachModel(feats, scam, platt, category)
    model.info.update({"n_train": len(texts), "n_features": X.shape[1], "C": C,
                       "oof_scores": oof.tolist(), "oof_labels": y.tolist()})
    log(f"features: {X.shape[1]:,}  (word {len(feats.word.vocabulary_):,}, char {len(feats.char.vocabulary_):,}, rules {len(RULE_IDS)})")
    return model
