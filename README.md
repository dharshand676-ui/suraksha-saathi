# 🛡️ Suraksha Saathi – Voice-first, vernacular scam shield

> **Theme:** Digital Safety & Cyber Fraud Awareness · MY Bharat / Viksit Bharat Young Leaders Dialogue hackathon

Millions of first-time digital users – rural families, senior citizens, small shopkeepers – lose money to UPI fraud, fake KYC calls, "digital arrest" threats and fake job offers. Awareness material is in English, text-heavy, and reaches people **after** they are cheated.

**Suraksha Saathi checks a suspicious message in the user's own language, explains *why* it is risky (by voice too), writes the cyber-crime complaint for them, and turns every report into a local scam map for awareness drives.**

## Features
| # | Feature | How it works |
|---|---------|--------------|
| 1 | **Scan & explain** | Paste or *speak* an SMS / link / call story → risk score 0-100, verdict, plain-language reasons, next steps |
| 2 | **Vernacular + voice** | English, Hindi (Devanagari) and **Hinglish** understood; speech-in (mic) and speech-out (listen) via the browser Web Speech API |
| 3 | **Link & look-alike check** | Shorteners, raw IPs, punycode, risky TLDs, fake `sbi-kyc.xyz` style brand impersonation vs official domains |
| 4 | **One-tap complaint** | Generates a ready complaint for cybercrime.gov.in / helpline **1930** with details and evidence checklist |
| 5 | **Community scam map** | Reports are stored by city and shown on a Leaflet map + stats for panchayats, colleges and police |
| 6 | **WhatsApp bot** | `/whatsapp` webhook (Twilio-compatible): forward a message, get a verdict back in Hindi/English |
| 7 | **Learn by playing** | Bilingual "spot the scam" quiz for MY Bharat volunteers to run in villages |

Scam types covered: OTP/PIN theft, fake KYC & account-block, UPI collect/QR trick, lottery/prize, job & loan fee fraud, **digital arrest / fake CBI-police**, remote-access apps (AnyDesk), fake electricity-bill, malicious APKs, relative-on-new-number.

## Why it is different
* **Explainable, not a black box** – every point of the score maps to a sentence the user can read or hear. Builds trust and teaches while protecting.
* **Works offline-first on low-end phones** – detector is pure Python rules (no GPU, no paid API); the page is a light PWA-style site.
* **Closes the loop** – detect → explain → report → map → target awareness. Most projects stop at detection.
* **Volunteer-ready** – MY Bharat volunteers can run the quiz and bot demo in their village.

## Quick start
```bash
git clone https://github.com/<you>/suraksha-saathi && cd suraksha-saathi
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                                         # open http://localhost:8000
python -m unittest discover -s tests -v               # run tests
```
Docker: `docker build -t suraksha . && docker run -p 8000:8000 suraksha`

### Free deploy (Render / Railway)
Build: `pip install -r requirements.txt` · Start: `gunicorn app:app` · Health check: `/healthz`

### WhatsApp bot (Twilio sandbox, 5 minutes)
1. Run the app publicly (Render, or `ngrok http 8000`).
2. Twilio Console → Messaging → WhatsApp Sandbox → set *When a message comes in* to `https://<your-url>/whatsapp` (POST).
3. Join the sandbox from your phone and forward any suspicious message. Send `hi` for Hindi replies.

## Environment variables
| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port the server listens on |
| `SS_DB` | `data/suraksha.db` | SQLite file path (created automatically) |
| `DEBUG` | *(empty)* | Set to `1` for Flask debug mode |

Copy `.env.example` for reference. No API keys are needed. For the WhatsApp bot only, a free Twilio sandbox account is required (configured in the Twilio console, not in this code).

## Documentation, sample data and tests
* Technical Design Document with architecture diagrams: [`docs/TECHNICAL_DESIGN.md`](docs/TECHNICAL_DESIGN.md)
* Sample data: [`data/sample_messages.json`](data/sample_messages.json) (labelled scam / safe messages), `data/cities.json`, `data/quiz.json`
* Test cases: `tests/test_detector.py` – run `python -m unittest discover -s tests -v`
* Submission text: [`docs/SUBMISSION.md`](docs/SUBMISSION.md) · License: [`LICENSE`](LICENSE) (MIT)

## API
| Method | Path | Body / query | Returns |
|---|---|---|---|
| POST | `/api/analyze` | `{text, lang:"en"\|"hi"}` | `score, verdict, label, reasons[], advice[], category, urls[], spoken` |
| POST | `/api/report` | `{city, category, amount, suspect, text}` | `complaint` letter, helpline, portal |
| GET | `/api/heatmap` | – | report points for the map |
| GET | `/api/stats` | – | counts, money lost, top cities/categories |
| GET | `/api/quiz?lang=hi` | – | quiz questions |
| POST | `/whatsapp` | Twilio form `Body`, `From` | TwiML reply |

## Architecture
```
Browser (mic + speaker, Leaflet) ─┐
WhatsApp (Twilio) ────────────────┼─▶ Flask app.py ─▶ detector.py (rules + URL analysis, EN/HI/Hinglish)
                                  │         └────────▶ SQLite (reports, anonymous scan counts)
```
Privacy: message text is **never stored**; only the verdict label and anonymous report counts by city are saved.

## Honest limitations
* Rule-based engine: high precision on known scam patterns, may miss brand-new scripts. The rules file is easy to extend and the roadmap below adds a learned model.
* Map ships with *sample* seed data (flagged `sample=1` in the DB) until real reports arrive. Replace by clearing `data/suraksha.db`.
* Browser speech-to-text for Indian languages needs Chrome/Edge + internet.

## Roadmap
1. Add Marathi, Tamil, Bengali, Telugu rule text; use **Bhashini** APIs for speech and translation.
2. Train a lightweight classifier (public SMS-spam + phishing-URL datasets) and blend it with the rules.
3. Android app / call-screening overlay for live call warnings.
4. Verified-NGO dashboard & district-wise PDF reports for police and panchayats.
5. Integrate official scam-number lists (e.g. Sanchar Saathi) when API access is available.

## Impact plan (pilot)
Run a 100-person pilot with MY Bharat volunteers in 3 villages / colleges: measure people trained, scams detected, complaints filed, languages used, and pre/post quiz score gain.

## Project structure
```
app.py          Flask server, API, WhatsApp webhook, SQLite
detector.py     Explainable scam engine (rules, URL/brand checks, EN/HI)
templates/ static/   Mobile-first UI (voice in/out, report, map, quiz)
data/           cities.json, quiz.json (+ auto-created suraksha.db)
tests/          unit + API tests
```

## License
MIT
