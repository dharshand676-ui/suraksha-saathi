"""Suraksha Saathi - Flask backend (web UI + JSON API + WhatsApp webhook)."""
import json, os, random, sqlite3, time
from datetime import datetime, timezone
from xml.sax.saxutils import escape
from flask import Flask, jsonify, render_template, request, Response, g

import detector

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SS_DB", os.path.join(BASE, "data", "suraksha.db"))
CITIES = json.load(open(os.path.join(BASE, "data", "cities.json"), encoding="utf-8"))
QUIZ = json.load(open(os.path.join(BASE, "data", "quiz.json"), encoding="utf-8"))
CATEGORIES = ["otp_pin", "kyc", "upi", "prize", "job_loan", "digital_arrest", "remote_access", "utility", "malware", "impersonation", "link", "other"]

app = Flask(__name__)

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, city TEXT, lat REAL, lng REAL, category TEXT,
        amount INTEGER DEFAULT 0, created TEXT, sample INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS scans(id INTEGER PRIMARY KEY, verdict TEXT, created TEXT);
    """)
    if c.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 0:
        rnd = random.Random(7)
        weights = {"Delhi": 9, "Mumbai": 8, "Pune": 5, "Jaipur": 5, "Lucknow": 5, "Patna": 4, "Hyderabad": 6, "Bengaluru": 7,
                   "Nashik": 3, "Prayagraj": 4, "Ujjain": 3, "Haridwar": 2}
        cats = ["otp_pin", "kyc", "upi", "job_loan", "digital_arrest", "prize", "utility"]
        for city, wt in weights.items():
            lat, lng = CITIES[city]
            for _ in range(wt * 3):
                c.execute("INSERT INTO reports(city,lat,lng,category,amount,created,sample) VALUES(?,?,?,?,?,?,1)",
                          (city, lat + rnd.uniform(-.15, .15), lng + rnd.uniform(-.15, .15), rnd.choice(cats),
                           rnd.choice([0, 500, 2000, 5000, 12000, 40000]), datetime.now(timezone.utc).isoformat()))
    c.commit(); c.close()

def log_scan(verdict):
    try:
        db().execute("INSERT INTO scans(verdict,created) VALUES(?,?)", (verdict, datetime.now(timezone.utc).isoformat()))
        db().commit()
    except sqlite3.Error:
        pass

@app.get("/")
def index():
    return render_template("index.html", cities=sorted(CITIES), categories=CATEGORIES)

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.post("/api/analyze")
def api_analyze():
    d = request.get_json(silent=True) or {}
    lang = d.get("lang", "en")
    res = detector.analyze(d.get("text", ""), lang)
    res["spoken"] = detector.spoken_summary(res, lang)
    log_scan(res["verdict"])
    return jsonify(res)

def complaint_text(d):
    cat = d.get("category", "other")
    return (
        "To,\nThe Officer-in-Charge, Cyber Crime Cell / National Cyber Crime Reporting Portal (cybercrime.gov.in)\n\n"
        "Subject: Complaint regarding online financial fraud (" + cat.replace("_", " ") + ")\n\n"
        f"Date: {datetime.now().strftime('%d-%m-%Y')}\nLocation: {d.get('city', '')}\n"
        f"Amount lost (Rs): {d.get('amount', 0)}\n"
        f"Suspect number / UPI ID / link: {d.get('suspect', 'not known')}\n\n"
        "Details of incident:\n" + (d.get("text") or "").strip()[:1500] + "\n\n"
        "I request you to kindly register my complaint, freeze the beneficiary account and take action.\n"
        "I have also informed / will inform the national helpline 1930.\n\nYours faithfully,\n[Name]  [Mobile]  [Address]\n"
        "\nAttach: screenshots of messages, call log, transaction ID / UTR, bank statement.")

@app.post("/api/report")
def api_report():
    d = request.get_json(silent=True) or {}
    city = d.get("city")
    if city not in CITIES:
        return jsonify(error="Please choose your city / district."), 400
    cat = d.get("category") if d.get("category") in CATEGORIES else "other"
    try:
        amount = max(0, min(int(d.get("amount") or 0), 10**8))
    except ValueError:
        amount = 0
    lat, lng = CITIES[city]
    db().execute("INSERT INTO reports(city,lat,lng,category,amount,created,sample) VALUES(?,?,?,?,?,?,0)",
                 (city, lat + random.uniform(-.1, .1), lng + random.uniform(-.1, .1), cat, amount, datetime.now(timezone.utc).isoformat()))
    db().commit()
    d["category"] = cat
    return jsonify(complaint=complaint_text(d), helpline="1930", portal="https://cybercrime.gov.in")

@app.get("/api/heatmap")
def api_heatmap():
    rows = db().execute("SELECT lat,lng,category,city FROM reports").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/stats")
def api_stats():
    q = lambda s: db().execute(s).fetchone()[0]
    top = db().execute("SELECT city, COUNT(*) n FROM reports GROUP BY city ORDER BY n DESC LIMIT 5").fetchall()
    cats = db().execute("SELECT category, COUNT(*) n FROM reports GROUP BY category ORDER BY n DESC LIMIT 5").fetchall()
    return jsonify(reports=q("SELECT COUNT(*) FROM reports"), scans=q("SELECT COUNT(*) FROM scans"),
                   scams_caught=q("SELECT COUNT(*) FROM scans WHERE verdict='SCAM'"),
                   amount=q("SELECT COALESCE(SUM(amount),0) FROM reports"),
                   top_cities=[dict(r) for r in top], top_categories=[dict(r) for r in cats])

@app.get("/api/quiz")
def api_quiz():
    lang = "hi" if request.args.get("lang") == "hi" else "en"
    return jsonify([{"q": x["q"][lang], "options": x["options"][lang], "answer": x["answer"], "why": x["why"][lang]} for x in QUIZ])

HELP = ("Suraksha Saathi\nForward any suspicious SMS / link / message here and I will check it.\n"
        "Type 'hi' for Hindi replies, 'en' for English. Fraud happened? Call 1930.")
HELP_HI = ("सुरक्षा साथी\nकोई भी संदिग्ध SMS / लिंक / संदेश यहाँ भेजें, मैं जाँच करूँगा।\nठगी हो गई? तुरंत 1930 पर कॉल करें।")
_wa_lang = {}

@app.post("/whatsapp")
def whatsapp():
    """Twilio WhatsApp webhook (form-encoded Body/From). Replies with TwiML."""
    body = (request.form.get("Body") or "").strip()
    who = request.form.get("From", "anon")
    low = body.lower()
    if low in ("hi", "hindi", "हिंदी", "hindi mein"):
        _wa_lang[who] = "hi"; msg = HELP_HI
    elif low in ("en", "english"):
        _wa_lang[who] = "en"; msg = HELP
    elif low in ("", "help", "start", "hello", "menu"):
        msg = HELP_HI if _wa_lang.get(who) == "hi" else HELP
    else:
        lang = _wa_lang.get(who) or ("hi" if any("\u0900" <= ch <= "\u097f" for ch in body) else "en")
        r = detector.analyze(body, lang)
        icon = {"SCAM": "🚨", "SUSPICIOUS": "⚠️", "LIKELY_SAFE": "✅"}[r["verdict"]]
        reasons = "\n".join("• " + x for x in r["reasons"][:3])
        msg = f"{icon} {r['label']} ({r['score']}/100)\n{reasons}\n\n" + "\n".join("👉 " + a for a in r["advice"])
        log_scan(r["verdict"])
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escape(msg)}</Message></Response>'
    return Response(xml, mimetype="application/xml")

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=bool(os.environ.get("DEBUG")))
