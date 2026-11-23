# 🛡️ Kavach – an offline scam message checker

Paste an SMS or WhatsApp message and Kavach tells you, **on your own laptop and without the internet**:

1. **SCAM, SUSPICIOUS or SAFE**
2. **What kind of scam:** KYC/Bank · Lottery/Prize · Loan/Credit · Job/Investment · Other
3. **How sure it is:** a confidence % that is checked to be honest (calibrated)

It also shows **why**: the suspicious words are highlighted, and every link is inspected without being opened.

## Features

| Feature | What the user gets |
|---|---|
| **Verdict + category + confidence** | SCAM / SUSPICIOUS / SAFE, one of 5 categories (scams that don't closely match a known type are labelled "Other"), and a calibrated confidence |
| **"This message wants you to…"** | One line inside the verdict card that lists what the message asks for: *pay ₹4,999 · WhatsApp 9123456780*, *open onlinesbi.sbi.secure-login.top/kyc*, or *nothing – it gives you a code for something you started*. Built from the rules, links, numbers and amounts already found (no language model), in English or Hindi |
| **Highlighted message** | The original message with each warning sign marked; hover over a highlight to see the reason |
| **Link inspector** | Fake bank domains (`sbi-kyc-update.xyz`), addresses that start with an official name (`onlinesbi.sbi.secure-login.top`), typo domains (`hdfcbnak.com`), short links, `.apk` files, raw IP addresses. Links are **never opened** |
| **Hinglish, Hindi and disguised text** | Undoes `L0TT3RY`, `K.Y.C`, Cyrillic lookalike letters and invisible characters before checking, and shows what it read |
| **Genuine-message protection** | Recognises real OTPs ("do not share"), masked account numbers, transaction references and planned-maintenance notices |
| **What to do** | Steps to report and to recover (1930, cybercrime.gov.in, Sanchar Saathi / Chakshu, the bank) |
| **Evidence report** | A PDF or text report for a complaint: the original message, a SHA-256 fingerprint, evidence point by point, link analysis, where to report, and a short paragraph ready to paste into the complaint form |
| **Scam Diary** (opt-in) | A local history with a dashboard (scam types, tricks, impersonated brands, a weekly timeline). It stores only **masked** snippets |
| **Family alert** | A warning in English and Hindi, as text or an image card, with no personal data. The user shares it themselves |
| **Scam Library** (offline) | 17 scam families: how each works, warning signs, protection and recovery |
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
python server.py                  # the website: open http://127.0.0.1:8000
pytest                            # 80 tests, including the privacy proof
```

The website is already built (`web/dist`), so Node.js is **not** needed to run it. A simpler Streamlit version of the
same app is also included: `streamlit run app.py` (http://localhost:8501).

To change the website's code, rebuild it with Node.js 20+: `cd web && npm install && npm run build`.

The trained model (`models/kavach.joblib`, 1.4 MB) is included. To rebuild everything from scratch:

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
   **Link inspector:** extracts links and checks them against a built-in list of official domains of 68 brands,
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
| **Final test v2** (hand-written before the v2 fixes, never used to improve the model) | 68 | 95.6% | 34/35 | 2/33 | 0/33 | 97.1% |
| Final test v1 (hand-written before the first tuning) | 72 | 98.6% | 37/37 | 1/35 | 2/35 | 94.6% |
| Messages typed by 5 persona testers, round 1 (used for error analysis) | 137 | 98.5% | 83/83 | 2/54 | 0/54 | 89.2% |
| Challenge set (hand-written, used for error analysis) | 101 | 98.0% | 53/53 | 2/48 | 1/48 | 84.9% |
| Held-out templates + UCI messages (split by template) | 1,551 | 99.4% | 610/617 | 0/934 | 13/934 | 89.0% |

- **Real delivery OTPs, bank alerts and OTPs (final test v2):** none marked SCAM or SUSPICIOUS.
- **The 7 genuine messages called SCAM** across the four hand-written sets: 3 prize/award announcements (quiz,
  best paper, hackathon), 3 family messages about money or a new number, 1 joke about a lottery ticket. None is a
  bank alert, OTP or delivery message.
- **How SUSPICIOUS is counted:** for "scams caught", SCAM or SUSPICIOUS counts as caught (the user is warned). For
  "genuine called SCAM", only SCAM counts; SUSPICIOUS on a genuine message is reported in its own column.
- **Chain forwards and hoaxes:** both hoaxes in the tester set are flagged, not called SAFE.
- **Confidence reliability:** expected calibration error 0.009, Brier score 0.009 (all test sets together, model
  probability before the rule safety nets). Most
  messages are easy, so the 20–80% range holds few examples. A very short message with no clear sign is capped at 85%.
- **Disguised text:** test scams were caught 99.5% of the time as written and 99.6% after random disguise tricks
  (568 messages). Retrained without the cleaner, the model still catches 99.5% of the disguised copies: the character
  n-grams already absorb most tricks, and the cleaner's main job now is showing the user what it read.
- **Speed and size:** about 15–25 ms per message on a laptop CPU. The model is 1.4 MB.

**Read these numbers with care.** Much of the Indian training data is generated from templates. The hand-written sets
are small (68–137 messages), so each message moves the percentages by 1–3 points. Real-world accuracy will probably be
lower. The remaining mistakes are listed on the app's "How accurate is it?" page.

**In one line:** across all 378 hand-written and real-user messages, Kavach caught 207 of 208 scams and wrongly called
7 of 170 genuine messages a scam.

The untouched final test v2 moved from 0 to 2 genuine messages called SCAM after the v3 changes. That set is kept
untouched, so the model was not tuned to get those two back.

### v3.1 – two fixes found while choosing website examples

- The Hinglish word "pakka" ("sure") alone no longer counts as investment bait ("kal ka plan pakka?" was marked
  SUSPICIOUS). It still counts next to money ("30k pakka milega", "pakka profit").
- A request for money that also says "don't tell anyone" can no longer come out SAFE.
- The check page now has three rows of examples: obvious scams, **subtle scams** (no links, no "blocked today" –
  Kavach is less sure about these, which is the honest answer) and genuine messages.
- Verdicts on every test set are unchanged. Category accuracy dropped on three sets after the retrain (final v1
  97.3% → 94.6%, testers 90.4% → 89.2%, challenge 86.8% → 84.9%; one or two messages each).

### What changed in v3 (second round of five persona testers)

A shopkeeper, a student, a bank helpdesk officer, a jury member and a low-vision user tried v2.

- **Scams that passed as safe:**
  - "Scan the QR / enter your PIN / approve the request to receive money" in Hinglish and Hindi.
  - Exam-fee and hall-ticket scams.
  - "Buy a product first" brand collaborations.
  - Fake e-mandate "click to cancel" links.
- **Unreadable languages:** messages written mostly in a language the model cannot read (Malayalam, Tamil...) are now
  never called safe. Kavach says it cannot read them and caps its confidence at 60%.
- **Genuine messages that were flagged:**
  - "No fee at any stage" job invites.
  - Postal PIN codes.
  - Delivery, return and ride codes.
  - "No hurry" money requests from friends.
  - Problems that were already solved.
- **Explanations:**
  - Order updates are no longer called bank alerts.
  - A branch KYC reminder no longer shows a red KYC flag.
  - "Does not ask for money or codes" is never claimed when the message does.
- **Website:**
  - Plain confidence bands ("Very likely a scam", "Probably genuine"), with the percentage as a small detail.
  - A full Hindi mode.
  - Paste button, autofocus, "Check another message" and a WhatsApp-ready share card.
  - Accessibility: !/?/✓ symbols inside highlights, stronger text contrast, dim-only focus mode, screen-reader
    announcements, and reduced motion when the system asks for it.
  - A one-page customer slip and helper fields for bank or police staff.
  - One honest headline on the accuracy page.
- **Method:** the train/test split now depends only on a hash of each template's id, so adding templates can no longer
  reshuffle the test set.

### What changed in v2, and why

Five persona testers used v1 and typed 145 messages of their own: an elderly user, an ML judge, a cyber-crime
police officer, a product designer and a red-team student. Their messages are labelled in `data/tester_set.py`, and
the fixes are tested in `tests/test_tester_regressions.py`.

**Before any fix, I wrote a new untouched test set (`data/final_test_v2.py`) to measure the changes fairly.**

| Untouched final test v2 | v1 | v2 |
|---|---|---|
| Scams caught | 28/35 | 34/35 |
| Genuine messages wrongly called SCAM | 7/33 | 0/33 |

Main fixes:

- **Genuine messages wrongly flagged:**
  - Delivery and ride OTPs ("share the code with the agent at your door") were called scams. They are now a
    reassuring sign.
  - Dates like `23Nov26` were read as disguised text, which flagged a genuine SBI alert. They are no longer "decoded".
  - Ordinary amounts in bank alerts triggered "Big money offer". Only money *offered* to you counts now.
- **Scams that got through:**
  - "Tell me the number that came on your phone" (no word "OTP") passed. Code requests are caught in any wording.
  - Scam pages on Google Sites, Forms, Blogspot, Netlify and other free builders were trusted. They are never
    official now, and they are dangerous when the message talks about banks, accounts or KYC.
  - Fake government domains (`incometax-gov.in`) are now detected.
  - New rules cover chain forwards, donation appeals, family emergencies (Ma, Appa, airport, hospital), digital
    arrest over video call, loan-app shaming threats, and requests for bank or Aadhaar details.
- **Wrong explanations:**
  - "Do not tell your family" was shown as a green "do not share OTP" sign. It is now an isolation red flag.
  - The category now follows a proven scam type, so the UI can't show "KYC/Bank" next to "Digital arrest".
- **Training data:** a third batch of 141 templates targets the gaps (`data/templates_v3.py`). It includes many
  genuine Hinglish and Hindi messages, because v1 had learned that "Hinglish = scam".
- **Evidence report:**
  - New "money trail" section: UPI IDs, account numbers, IFSC codes, Indian and foreign phone numbers, the amount,
    the transaction reference (UTR), the debit time and the victim's bank.
  - "Delete the message" was replaced with "keep the original for investigators".
  - Typed-in fields can no longer forge lines in the report.

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
| `data/generate.py` + `data/templates_v3.py`: Indian messages from 376 hand-written templates (175 scam, 201 genuine) | Scams in 5 categories and genuine bank alerts, OTPs, deliveries, bills, promotions, government notices and chats, in English, Hinglish and Hindi. Based on public warnings from RBI, banks, the cyber-crime portal and news reports, with random banks, amounts, links and disguise tricks. **Synthetic.** |
| `data/challenge.py` (101), `data/final_test.py` (72), `data/final_test_v2.py` (68), `data/tester_set.py` (137) | Hand-written and real-user test sets with different wording. Never used for training |

The split is **by template**: messages generated from one template are either all in training or all in test.

## Project layout

```
server.py             website server: local API + web/dist (turns on the network guard first)
web/                  React + Vite website (src/ = code, dist/ = built site, src/reactbits/ = React Bits components)
app.py                simpler Streamlit version of the same app
kavach/
  normalize.py        text cleaner with position mapping
  rules.py            red-flag and reassuring-sign rules
  links.py            link inspector, official domain list, phone numbers
  model.py            TF-IDF + logistic regression + Platt calibration
  detector.py         analyze(message) -> Result
  asks.py             "this message wants you to…" line
  library.py          offline Scam Library (13 families, recovery steps)
  report.py           evidence report (text + PDF)
  diary.py            opt-in local Scam Diary, dashboard stats, family alert
  redact.py           masks private details
  netguard.py         blocks all outgoing connections
  intel.py            optional online news search
ui/                   Streamlit pages
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
- **The official domain list is hand-made** and covers 68 organisations plus every .gov.in / .nic.in site. Free site builders are never trusted, but a brand-new lookalike domain that names no known brand can still look "unknown".

## Credits and AI assistance

- Dataset: UCI SMS Spam Collection (CC BY 4.0).
- Libraries: scikit-learn, FastAPI, Streamlit, pandas, matplotlib, ReportLab, uharfbuzz.
- Website design: [Lenis](https://github.com/darkroomengineering/lenis) (smooth scrolling, MIT),
  [Vanta.js](https://github.com/tengbao/vanta) + three.js (animated 3D network in the hero, MIT),
  [React Bits](https://github.com/DavidHDev/react-bits) by David Haz (BlurText, ShinyText, DecryptedText,
  SpotlightCard, StarBorder, FadeContent and Magnet, copied into `web/src/reactbits/`; MIT + Commons
  Clause, licence included), Motion and GSAP for animation, and Fontsource for the fonts (Bricolage Grotesque, Manrope,
  Instrument Serif and Noto Sans Devanagari, all bundled locally). The visual language follows my earlier projects
  Kilometre, Clausewise and Approvals.
- Scam descriptions and recovery steps are based on public advice from RBI, cybercrime.gov.in (1930) and Sanchar
  Saathi.
- **AI assistance:** this project was built with the help of an AI coding assistant (code, templates and
  documentation), as allowed by the hackathon rules, which ask participants to credit it.
