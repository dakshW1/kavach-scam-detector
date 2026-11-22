# 🛡️ Kavach – an offline scam message checker

Paste an SMS or WhatsApp message and Kavach tells you, **on your own laptop and without the internet**:

1. **SCAM, SUSPICIOUS or SAFE**
2. **What kind of scam:** KYC/Bank · Lottery/Prize · Loan/Credit · Job/Investment · Other
3. **How sure it is:** a confidence % that is checked to be honest (calibrated)

It also shows **why**: the suspicious words are highlighted, and every link is inspected without being opened.

Built for the Tinyverse Hackathon, problem statement PS-01 (On-Device Scam Message Detector).

## Features

| Feature | What the user gets |
|---|---|
| **Verdict + category + confidence** | SCAM / SUSPICIOUS / SAFE, one of 5 categories (scams that don't closely match a known type are labelled "Other"), and a calibrated confidence |
| **Highlighted message** | The original message with each warning sign marked; hover over a highlight to see the reason |
| **Link inspector** | Fake bank domains (`sbi-kyc-update.xyz`), addresses that start with an official name (`onlinesbi.sbi.secure-login.top`), typo domains (`hdfcbnak.com`), short links, `.apk` files, raw IP addresses. Links are **never opened** |
| **Hinglish, Hindi and disguised text** | Undoes `L0TT3RY`, `K.Y.C`, Cyrillic lookalike letters and invisible characters before checking, and shows what it read |
| **Genuine-message protection** | Recognises real OTPs ("do not share"), masked account numbers, transaction references and planned-maintenance notices |
| **What to do** | Steps to report and to recover (1930, cybercrime.gov.in, Sanchar Saathi / Chakshu, the bank) |
| **Evidence report** | A PDF or text report for a complaint: the original message, a SHA-256 fingerprint, evidence point by point, link analysis, where to report, and a short paragraph ready to paste into the complaint form |
| **Scam Diary** (opt-in) | A local history with a dashboard (scam types, tricks, impersonated brands, a weekly timeline). It stores only **masked** snippets |
| **Family alert** | A warning in English and Hindi, as text or an image card, with no personal data. The user shares it themselves |
| **Scam Library** (offline) | 13 scam families: how each works, warning signs, protection and recovery |
| **Online Scam Intel** (opt-in) | "Is this happening to others?" A news search that sends **only** the scam type and brand (shown first, sent only after the user clicks) and summarises the results locally |
| **Try to fool it** | Disguise a scam and watch Kavach still catch it |
| **Batch check** | Check a whole file of messages and download the results as CSV |
| **Results & privacy page** | Accuracy, false alarms, a reliability chart, the effect of disguises, a live network-blocked check, data sources and limitations |

## Run it

You need Python 3.11 or newer. No GPU, no API keys and no internet are needed after installing.

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py              # then open http://localhost:8501
pytest                            # 34 tests, including the privacy proof
```

The trained model (`models/kavach.joblib`, 1.2 MB) is included. To rebuild everything from scratch:

```bash
python data/generate.py        # builds data/messages.csv (needs data/raw/SMSSpamCollection, included)
python data/challenge.py       # hand-written challenge set
python data/final_test.py      # hand-written final test set
python scripts/train.py        # trains the models in about 20 s on a laptop CPU
python scripts/evaluate.py     # writes results/metrics.json and results/reliability.png
```

## How it works

```
message ──► 1. clean text ──► 2. red-flag rules + link inspector ──► 3. ML model ──► 4. verdict + category + confidence
              (normalize.py)      (rules.py, links.py)                 (model.py)      (detector.py)
```

1. **Cleaning (normalisation).** Lowercase, fold fancy Unicode, replace lookalike letters from other alphabets, delete
   invisible characters, turn digits inside words back into letters (`L0TT3RY` → `lottery`, but `Rs.500` and
   `XX1234` stay untouched), join spaced letters (`K.Y.C` → `kyc`). Every cleaned character remembers where it came
   from, so highlights land on the original text.
2. **Rules.** Hand-written patterns for scam tactics in English, Hinglish and Hindi: asking for an OTP/PIN, KYC threats,
   urgency, prizes, pay-first fees, loan, job and investment bait, fake authorities ("digital arrest"), disconnection
   scares, parcel traps, UPI "receive money" tricks, remote-access apps, fake family emergencies. There are also
   *reassuring* patterns, and negation is handled ("never install AnyDesk" is advice, not a demand). Each rule has a
   plain-language reason.
   **Link inspector:** extracts links and checks them against a built-in list of official domains of 41 brands,
   banks and government sites, without opening them.
3. **Model.** TF-IDF features on the cleaned text (word 1–2-grams plus character 2–5-grams, which survive typos and
   Hinglish spellings), plus one 0/1 column per rule. These feed a **logistic regression** for SCAM vs SAFE and a
   second one for the category, trained on scams only.
4. **Confidence.** The raw scores are **calibrated with Platt scaling**, fitted on cross-validated predictions grouped
   by template, so "90%" means right about 9 times in 10.
   - p ≥ 0.70 → SCAM
   - p < 0.35 → SAFE
   - in between → SUSPICIOUS

   If the category model's top probability is below 0.45, the scam is called "Other (does not closely match a known
   type)".

Why this model and not a large language model? It is about 1 MB, answers in under 20 ms on any laptop, runs fully
offline, and every decision can be explained by its rules and word weights.

## Results

Every number is on messages the model never saw during training (from `results/metrics.json`).

| Test set | Messages | Accuracy | Scams caught (SCAM or SUSPICIOUS) | Genuine marked SCAM | Genuine marked SUSPICIOUS | Category accuracy |
|---|---|---|---|---|---|---|
| **Final test** (hand-written, written before tuning, never used to improve the model) | 72 | 95.8% | 100% (37/37) | 5.7% (2/35) | 5.7% (2/35) | 97.3% |
| Challenge set (hand-written, used for error analysis) | 101 | 95.0% | 100% (53/53) | 6.2% (3/48) | 2.1% (1/48) | 84.9% |
| Held-out templates + UCI messages (split by template) | 1,101 | 98.4% | 96.6% | 0.1% | 1.8% | 80.1% |

- **Languages (final test):** English 21/21, Hinglish 6/6, Hindi 5/5 and disguised 5/5 scams caught.
- **Real bank alerts, OTPs and deliveries (final test):** none marked SCAM. 1 of 7 bank alerts was marked SUSPICIOUS.
- **Confidence reliability:** expected calibration error 0.006, Brier score 0.016 (all test sets together). The chart
  is in `results/reliability.png`.
- **Disguised text:** test scams were caught 96.7% of the time as written and 99.2% after random disguise tricks.
  Retrained without the cleaner, the model catches 94.8% of the disguised copies. The character n-grams already give
  some robustness, and the cleaner adds the rest.
- **Speed:** about 15–25 ms per message on a laptop CPU. The model is 1.2 MB.

**Read these numbers with care.** Much of the Indian training data is generated from templates. The hand-written sets
are small (72 and 101 messages), so each message moves the percentages by 1–2 points. Real-world accuracy will
probably be lower. The remaining mistakes are listed on the app's Results page.

## Privacy: how to verify it is offline

- **Wi-Fi off:** turn off the network. Everything works except the optional news search.
- **Network guard:** `kavach/netguard.py` replaces Python's socket functions when the app starts. Any connection to a
  non-local address raises an error, whether it comes from our code or from a library. The sidebar shows a live
  check and the number of blocked attempts.
- **Automated proof:** `pytest tests/test_privacy.py` checks that:
  - analysis and report building make **zero** outgoing connections;
  - the internet really is unreachable while the guard is on;
  - the diary is off by default;
  - the diary file contains no phone numbers, OTPs, account numbers, UPI IDs, names or clickable links;
  - the family alert and the online-search query contain no message details.
- **Streamlit:** `.streamlit/config.toml` turns off usage statistics and listens only on `127.0.0.1`.
- **Nothing is stored** unless the Scam Diary is switched on. The diary is masked, kept in `local_data/` (git-ignored),
  and can be auto-deleted or deleted with one click. Evidence reports are made in memory and saved only when the user
  downloads them.
- **The only online feature** (Online Scam Intel) is off until clicked. It shows the exact words first, sends only the
  scam type and brand, and can reach a single host (news.google.com RSS) through `netguard.allow()`.

## Data

| Source | Use |
|---|---|
| [UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection) (Almeida & Hidalgo, 2011, CC BY 4.0) | 2,500 genuine personal messages as SAFE. Prize/claim spam as Lottery/Prize scams. Other UCI spam (marketing, ringtones) was left out: it is spam, not fraud |
| `data/generate.py`: Indian messages from 235 hand-written templates (124 scam, 111 genuine) | Scams in 5 categories and genuine bank alerts, OTPs, deliveries, bills, promotions, government notices and chats, in English, Hinglish and Hindi. Based on public warnings from RBI, banks, the cyber-crime portal and news reports, with random banks, amounts, links and disguise tricks. **Synthetic.** |
| `data/challenge.py` (101) and `data/final_test.py` (72) | Hand-written test sets with different wording. Never used for training |

The split is **by template**: messages generated from one template are either all in training or all in test.

## Project layout

```
app.py                Streamlit entry point (turns on the network guard first)
kavach/
  normalize.py        text cleaner with position mapping
  rules.py            red-flag and reassuring-sign rules
  links.py            link inspector, official domain list, phone numbers
  model.py            TF-IDF + logistic regression + Platt calibration
  detector.py         analyze(message) -> Result
  library.py          offline Scam Library (13 families, recovery steps)
  report.py           evidence report (text + PDF)
  diary.py            opt-in local Scam Diary, dashboard stats, family alert
  redact.py           masks private details
  netguard.py         blocks all outgoing connections
  intel.py            optional online news search
ui/                   one file per page
data/                 dataset builders, UCI data, generated and hand-written sets
scripts/              train.py, evaluate.py
tests/                test_core.py, test_privacy.py
results/              metrics.json, reliability.png
```

## Limitations

- **Text only.** No voice calls, images or screenshots.
- **Synthetic training data.** The Indian training data is template-generated, so unusual real wording can still be
  missed or wrongly flagged. A genuine message that looks like a scam (for example, "Mom please send 2000 for the mess
  fee") can be flagged.
- **New scam styles** may come out as SUSPICIOUS or "Other". That is intentional.
- **Short links** can't be followed: Kavach can't see where a shortened link leads, because finding out would mean
  opening it.
- **The official domain list is hand-made** and covers 41 organisations.

## Credits and AI assistance

- Dataset: UCI SMS Spam Collection (CC BY 4.0).
- Libraries: scikit-learn, Streamlit, pandas, matplotlib, ReportLab, uharfbuzz.
- Scam descriptions and recovery steps are based on public advice from RBI, cybercrime.gov.in (1930) and Sanchar
  Saathi.
- **AI assistance:** this project was built with the help of an AI coding assistant (code, templates and
  documentation), as allowed by the hackathon rules, which ask participants to credit it.
