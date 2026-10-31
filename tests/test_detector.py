import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["SS_DB"] = os.path.join(tempfile.mkdtemp(), "t.db")
import detector, app as appmod

SCAMS = [
    "Dear customer your SBI account will be blocked today. Update KYC now http://sbi-kyc-update.xyz/login",
    "Aapka account band ho jayega. Turant OTP batao warna khata block.",
    "आपका बिजली कनेक्शन आज रात कट जाएगा। तुरंत इस नंबर पर कॉल करें।  आपका केवाईसी अपडेट नहीं है",
    "This is CBI. A warrant is issued against you. You are under digital arrest, stay on video call.",
    "Congratulations! You have won a lottery of Rs 25 lakh. Pay processing fee Rs 2000 to claim your prize.",
    "Install AnyDesk and share the 9 digit code so we can refund your money.",
    "Work from home part-time job earn Rs 3000 per day. Registration fee Rs 500 refundable.",
]
SAFE = [
    "Hi, are you coming for dinner tonight? Mom made paneer.",
    "Your OTP for login is 482913. Do not share it with anyone. -HDFC Bank",
    "Meeting moved to 4pm tomorrow, see agenda at https://www.incometax.gov.in/iec/foportal",
    "Happy birthday bhai! Party on Saturday.",
]

class T(unittest.TestCase):
    def test_scams_flagged(self):
        for s in SCAMS:
            r = detector.analyze(s)
            self.assertIn(r["verdict"], ("SCAM", "SUSPICIOUS"), s)
        self.assertEqual(detector.analyze(SCAMS[0])["verdict"], "SCAM")
        self.assertEqual(detector.analyze(SCAMS[3])["verdict"], "SCAM")

    def test_safe_not_flagged(self):
        for s in SAFE:
            self.assertEqual(detector.analyze(s)["verdict"], "LIKELY_SAFE", s)

    def test_lookalike(self):
        r = detector.analyze("check https://paytm-rewards.top/claim")
        self.assertTrue(any("PAYTM" in x for x in r["reasons"]))

    def test_hindi_output(self):
        r = detector.analyze("OTP batao account block ho jayega", "hi")
        self.assertTrue(any("\u0900" <= ch <= "\u097f" for ch in r["reasons"][0]))

    def test_api(self):
        c = appmod.app.test_client()
        r = c.post("/api/analyze", json={"text": SCAMS[0], "lang": "en"}).get_json()
        self.assertEqual(r["verdict"], "SCAM")
        r = c.post("/api/report", json={"city": "Pune", "category": "upi", "amount": 500, "text": "x"}).get_json()
        self.assertIn("cybercrime.gov.in", r["complaint"])
        self.assertEqual(c.post("/api/report", json={"city": "Nowhere"}).status_code, 400)
        self.assertGreater(len(c.get("/api/heatmap").get_json()), 50)
        self.assertEqual(len(c.get("/api/quiz?lang=hi").get_json()), 5)
        w = c.post("/whatsapp", data={"Body": SCAMS[1], "From": "whatsapp:+910000"})
        self.assertIn(b"<Message>", w.data)
        self.assertEqual(c.get("/").status_code, 200)

class SampleData(unittest.TestCase):
    """Runs every labelled message in data/sample_messages.json through the detector."""
    def test_samples(self):
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_messages.json")
        rows = json.load(open(path, encoding="utf-8"))
        wrong = [r["text"] for r in rows
                 if (detector.analyze(r["text"])["verdict"] == "LIKELY_SAFE") != (r["expected"] == "LIKELY_SAFE")]
        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main()
