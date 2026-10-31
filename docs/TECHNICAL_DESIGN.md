# Technical Design Document – Suraksha Saathi

## 1. Goal
Protect first-time digital users from cyber fraud by checking messages in their own language, explaining the risk by voice/text, filing the complaint, and mapping hotspots for awareness drives.

## 2. System architecture
```mermaid
flowchart LR
  U[Citizen - phone browser] -->|text / speech| W[Web UI<br/>HTML + JS + Web Speech API]
  WA[Citizen - WhatsApp] -->|forward message| TW[Twilio WhatsApp]
  W -->|POST /api/analyze| API[Flask app.py]
  TW -->|POST /whatsapp| API
  API --> DET[detector.py<br/>rules + URL/brand analysis<br/>EN / HI / Hinglish]
  API --> DB[(SQLite<br/>reports, scan counts)]
  API -->|complaint draft| CC[cybercrime.gov.in / 1930]
  DB -->|/api/heatmap, /api/stats| MAP[Leaflet scam map]
  MAP --> V[Volunteers, panchayats,<br/>colleges, police]
```

## 3. Message-check flow
```mermaid
sequenceDiagram
  participant C as Citizen
  participant UI as Web UI
  participant A as Flask API
  participant D as Detector
  C->>UI: Paste or speak message
  UI->>A: POST /api/analyze {text, lang}
  A->>D: analyze(text, lang)
  D-->>A: score, verdict, reasons, advice
  A-->>UI: JSON (message text not stored)
  UI-->>C: Verdict card + spoken explanation
  C->>UI: Tap "Report this"
  UI->>A: POST /api/report
  A-->>UI: Complaint letter for cybercrime.gov.in
```

## 4. Detection engine (detector.py)
```mermaid
flowchart TD
  T[Input text] --> R[Pattern rules<br/>OTP, KYC, block threat, prize,<br/>fee, digital arrest, remote app,<br/>UPI collect, bill, APK, relative]
  T --> X[Extract URLs]
  X --> U[URL checks<br/>shortener, raw IP, punycode,<br/>risky TLD, brand look-alike]
  R --> S[Add weights, cap at 100]
  U --> S
  S --> B[Bonus when 3+ flags<br/>or link + action request]
  B --> V{Score}
  V -->|>= 60| A[SCAM]
  V -->|30-59| B2[SUSPICIOUS]
  V -->|< 30| C[LIKELY SAFE]
```
Every matched rule carries a bilingual reason string, so the verdict is fully explainable.

## 5. Data model (SQLite)
| Table | Columns |
|---|---|
| `reports` | id, city, lat, lng, category, amount, created, sample (1 = seed data) |
| `scans` | id, verdict, created |
Message text is never persisted.

## 6. API
See README → API table. All JSON except `/whatsapp` (TwiML XML).

## 7. Design decisions
* **Rule-based, explainable engine:** no GPU or paid API, works on low-cost servers, every score can be justified to the user.
* **Browser Web Speech API:** zero-cost Indian-language voice input/output without extra infrastructure.
* **SQLite:** zero-setup storage suitable for a pilot; swap for PostgreSQL by changing `db()`/`init_db()`.
* **Privacy by design:** no message storage, no login, city-level location only.

## 8. Security & privacy
Input length capped (4000 chars); parameterised SQL; HTML-escaped output in the UI; amounts clamped; report city validated against an allow-list.

## 9. Testing
`python -m unittest discover -s tests -v` covers scam and safe messages, look-alike domains, Hindi output, all API routes, the WhatsApp webhook, and the labelled file `data/sample_messages.json`.

## 10. Scalability / roadmap
Learned classifier blended with rules, Bhashini for 22 languages, Android call overlay, PostgreSQL + dashboards for district authorities.
