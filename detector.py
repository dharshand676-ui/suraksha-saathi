"""Suraksha Saathi scam detector.

Explainable, offline, rule-based engine that understands English, Hindi
(Devanagari) and Hinglish. Every point of the score maps to a human-readable
reason, so a villager (or a judge) can see *why* a message is risky.
"""
import re
from urllib.parse import urlparse

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+/[^\s]*", re.I)
BARE_DOMAIN_RE = re.compile(r"\b[a-z0-9-]{2,}\.(?:xyz|top|click|link|info|online|site|shop|icu|vip|cc|tk|ml|ga|cf|gq|apk|live|buzz|club)\b", re.I)

# id, category, weight, regex, reason_en, reason_hi
RULES = [
    ("otp", "otp_pin", 35,
     r"\b(share|send|tell|give|batao|bata|bhejo|bhej|enter|dena|de)\b.{0,30}\b(otp|pin|cvv|password|mpin)\b|\b(otp|pin|cvv|mpin)\b.{0,25}\b(share|send|batao|bata|bhejo|bhej|dena)\b|ओटीपी|पिन\s*(बताएं|बताओ|भेजें)",
     "Asks you to share an OTP, PIN, CVV or password. Banks and UPI apps never ask for these.",
     "आपसे OTP, PIN, CVV या पासवर्ड माँगा जा रहा है। बैंक या UPI ऐप कभी ये नहीं माँगते।"),
    ("block", "kyc", 25,
     r"(account|khata|khaata|card|sim|number|upi)\b.{0,30}\b(block|blocked|band|suspend|suspended|deactivat\w*|freeze|frozen|expire\w*)|(खाता|अकाउंट|कार्ड|सिम).{0,20}(बंद|ब्लॉक)",
     "Threatens that your account, card or SIM will be blocked.",
     "धमकी दी जा रही है कि आपका खाता, कार्ड या सिम बंद हो जाएगा।"),
    ("kyc", "kyc", 25,
     r"\b(kyc|pan\s*(card)?\s*update|aadhaar\s*(update|link)|re-?kyc)\b|केवाईसी|केवाइसी",
     "Mentions KYC / PAN / Aadhaar update by link or call. Real updates happen only at the bank branch or official app.",
     "KYC/PAN/आधार अपडेट के लिए लिंक या कॉल का ज़िक्र है। असली अपडेट बैंक शाखा या आधिकारिक ऐप पर ही होता है।"),
    ("urgency", "pressure", 15,
     r"\b(urgent|immediately|right now|within\s*\d+\s*(hours?|hrs?|minutes?|mins?)|last chance|today only|abhi|turant|jaldi|fauran)\b|तुरंत|जल्दी|अभी|फौरन",
     "Creates pressure to act immediately so you do not think.",
     "जल्दबाज़ी का दबाव बनाया जा रहा है ताकि आप सोच न सकें।"),
    ("prize", "prize", 35,
     r"\b(lottery|lucky draw|you (have )?won|winner|prize|jackpot|cashback of|reward points?|gift card|inaam|inam|kbc)\b|लॉटरी|इनाम|जीत|केबीसी",
     "Claims you won a prize or lottery you never entered.",
     "दावा किया जा रहा है कि आपने इनाम या लॉटरी जीती है, जबकि आपने कभी भाग नहीं लिया।"),
    ("fee", "job_loan", 30,
     r"\b(processing fee|registration fee|security deposit|advance (fee|payment)|refundable|pay\s*(rs\.?|₹|inr)?\s*\d+|to claim|claim your)\b|प्रोसेसिंग फीस|रजिस्ट्रेशन फीस|एडवांस",
     "Asks for an upfront fee or deposit. Genuine loans, jobs and prizes never charge in advance.",
     "पहले से फीस या जमा राशि माँगी जा रही है। असली लोन, नौकरी या इनाम में अग्रिम पैसे नहीं लगते।"),
    ("job", "job_loan", 20,
     r"\b(work from home|part[- ]?time job|earn\s*(rs\.?|₹)?\s*\d+[,\d]*\s*(per|/)\s*(day|daily|hour)|like youtube videos|task.{0,15}(earn|income)|instant loan|loan approved|pre-?approved)\b|घर बैठे कमाएं|लोन\s*(मंजूर|अप्रूव)",
     "Looks like a too-good-to-be-true job or instant loan offer.",
     "यह बहुत अच्छे लगने वाले नौकरी या तुरंत लोन के ऑफ़र जैसा है, जो अक्सर धोखा होता है।"),
    ("police", "digital_arrest", 60,
     r"\b(cbi|ed|narcotics|customs|trai|cyber ?cell|police|court|warrant|arrest(ed)?|digital arrest|money laundering|parcel (seized|held))\b.{0,80}\b(you|your|aapke|aapka|aap)\b|डिजिटल अरेस्ट|गिरफ्तार|वारंट|सीबीआई",
     "Pretends to be police/CBI/customs and threatens arrest. 'Digital arrest' does not exist in Indian law.",
     "पुलिस/CBI/कस्टम बनकर गिरफ्तारी की धमकी दी जा रही है। भारतीय कानून में 'डिजिटल अरेस्ट' जैसा कुछ नहीं होता।"),
    ("remote", "remote_access", 40,
     r"\b(anydesk|teamviewer|quicksupport|rustdesk|screen ?share|screen sharing|remote (access|support))\b",
     "Asks you to install a screen-sharing app. Scammers use these to see your OTPs and empty your account.",
     "स्क्रीन-शेयरिंग ऐप इंस्टॉल करने को कहा जा रहा है। ठग इससे आपके OTP देखकर खाता खाली कर देते हैं।"),
    ("collect", "upi", 35,
     r"\b(collect request|approve (the )?request|enter (your )?(upi )?pin to (receive|get)|scan.{0,20}(to )?receive|receive money.{0,30}pin|refund.{0,30}(scan|pin))\b|पैसे (पाने|लेने) के लिए.{0,20}पिन",
     "UPI trick: you never need to enter a PIN or scan a QR code to RECEIVE money.",
     "UPI चाल: पैसे पाने के लिए कभी PIN डालने या QR स्कैन करने की ज़रूरत नहीं होती।"),
    ("bill", "utility", 25,
     r"\b(electricity|bijli|power)\b.{0,40}\b(disconnect\w*|cut|katega|band|bill)\b|बिजली.{0,20}(कट|बंद)",
     "Fake electricity-bill disconnection threat — a very common SMS scam.",
     "बिजली कनेक्शन कटने की झूठी धमकी — यह बहुत आम SMS ठगी है।"),
    ("apk", "malware", 40,
     r"\.apk\b|\b(download|install)\b.{0,25}\b(app|apk)\b.{0,25}\b(link|below)\b",
     "Pushes you to install an app from a link (APK). It can steal your SMS and bank data.",
     "लिंक से ऐप (APK) इंस्टॉल करने को कहा जा रहा है। इससे आपके SMS और बैंक डेटा की चोरी हो सकती है।"),
    ("family", "impersonation", 25,
     r"\b(new number|this is my new|save this number|i am in (trouble|hospital|accident)|papa|mummy|beta).{0,50}\b(send|transfer|paytm|gpay|phonepe|money|paise)\b|नया नंबर.{0,40}(पैसे|भेज)",
     "Someone claims to be a relative on a new number and asks for money. Call the old number to verify.",
     "कोई नया नंबर बताकर रिश्तेदार बन पैसे माँग रहा है। पुराने नंबर पर फोन करके पुष्टि करें।"),
]

BRANDS = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "sbi.bank.in"],
    "hdfc": ["hdfcbank.com", "hdfc.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"],
    "gpay": ["pay.google.com"],
    "npci": ["npci.org.in"],
    "irctc": ["irctc.co.in"],
    "uidai": ["uidai.gov.in"],
    "amazon": ["amazon.in", "amazon.com"],
    "flipkart": ["flipkart.com"],
    "epfo": ["epfindia.gov.in"],
    "incometax": ["incometax.gov.in", "incometaxindiaefiling.gov.in"],
    "indiapost": ["indiapost.gov.in"],
}
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "is.gd", "shorturl.at", "goo.gl", "ow.ly", "tiny.cc", "wa.me"}
BAD_TLDS = {"xyz", "top", "click", "link", "icu", "vip", "cc", "tk", "ml", "ga", "cf", "gq", "buzz", "club", "shop", "site", "online", "live", "info", "apk"}
TRUSTED_SUFFIX = (".gov.in", ".nic.in")

def _host(url):
    u = url if "://" in url else "http://" + url
    return (urlparse(u).hostname or "").lower()

def _registered(host):
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "org", "gov", "nic", "ac", "net"} and parts[-1] == "in":
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])

def analyze_url(url):
    """Return list of (points, reason_en, reason_hi, category) for a URL."""
    out, host = [], _host(url)
    if not host:
        return out
    reg = _registered(host)
    if host.endswith(TRUSTED_SUFFIX):
        return out
    if reg in SHORTENERS:
        out.append((20, "Uses a shortened link that hides the real website.", "छोटा लिंक असली वेबसाइट छुपा रहा है।", "link"))
    if re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host):
        out.append((35, "Link points to a raw IP address, not a real website name.", "लिंक असली वेबसाइट नहीं, सिर्फ़ IP एड्रेस पर जाता है।", "link"))
    if host.startswith("xn--") or ".xn--" in host:
        out.append((30, "Link uses look-alike characters to imitate a real site.", "लिंक असली साइट जैसे दिखने वाले अक्षरों का इस्तेमाल करता है।", "link"))
    tld = host.rsplit(".", 1)[-1]
    if tld in BAD_TLDS:
        out.append((20, f"Link ends in .{tld}, an extension scammers use heavily.", f"लिंक .{tld} पर ख़त्म होता है, जिसे ठग बहुत इस्तेमाल करते हैं।", "link"))
    if host.count("-") >= 2 or host.count(".") >= 4:
        out.append((10, "Web address looks unusually long or stuffed with hyphens.", "वेब पता असामान्य रूप से लंबा या हाइफ़न से भरा है।", "link"))
    flat = re.sub(r"[^a-z]", "", host)
    for brand, official in BRANDS.items():
        if brand in flat and reg not in official:
            out.append((45, f"Pretends to be '{brand.upper()}' but the real website is {official[0]}.",
                        f"'{brand.upper()}' होने का दिखावा करता है, जबकि असली वेबसाइट {official[0]} है।", "brand"))
            break
    if url.lower().startswith("http://") and not out:
        out.append((5, "Link is not encrypted (http, not https).", "लिंक सुरक्षित (https) नहीं है।", "link"))
    return out

def extract_urls(text):
    urls = [u.rstrip(".,);]") for u in URL_RE.findall(text)]
    seen = set(urls)
    for m in BARE_DOMAIN_RE.findall(text):
        if not any(m in u for u in seen):
            urls.append(m)
    return urls

ADVICE = {
    "en": {
        "SCAM": ["Do NOT click, reply or share anything.", "Block the sender.", "If money is lost, call 1930 within the hour and report at cybercrime.gov.in."],
        "SUSPICIOUS": ["Do not click links or share OTP/PIN.", "Verify by calling the official number printed on your card or passbook.", "Ask a trusted family member before acting."],
        "LIKELY_SAFE": ["No strong scam signs found, but stay careful.", "Never share OTP/PIN with anyone.", "When in doubt, check with your bank branch."],
    },
    "hi": {
        "SCAM": ["लिंक पर क्लिक न करें, जवाब न दें, कुछ भी साझा न करें।", "भेजने वाले को ब्लॉक करें।", "पैसे कटे हों तो तुरंत 1930 पर कॉल करें और cybercrime.gov.in पर शिकायत करें।"],
        "SUSPICIOUS": ["लिंक न खोलें, OTP/PIN साझा न करें।", "अपने कार्ड या पासबुक पर छपे आधिकारिक नंबर पर फोन करके पुष्टि करें।", "कुछ भी करने से पहले घर के किसी भरोसेमंद व्यक्ति से पूछें।"],
        "LIKELY_SAFE": ["कोई बड़ा खतरा नहीं दिखा, फिर भी सावधान रहें।", "OTP/PIN किसी को न बताएं।", "संदेह हो तो बैंक शाखा में पूछें।"],
    },
}
LABELS = {
    "en": {"SCAM": "Likely SCAM", "SUSPICIOUS": "Suspicious", "LIKELY_SAFE": "Looks safe"},
    "hi": {"SCAM": "ठगी की संभावना ज़्यादा", "SUSPICIOUS": "संदिग्ध", "LIKELY_SAFE": "सुरक्षित लगता है"},
}

def analyze(text, lang="en"):
    lang = "hi" if lang == "hi" else "en"
    text = (text or "").strip()[:4000]
    if not text:
        return {"score": 0, "verdict": "LIKELY_SAFE", "label": LABELS[lang]["LIKELY_SAFE"], "reasons": [], "advice": ADVICE[lang]["LIKELY_SAFE"], "category": "none", "urls": []}
    low = text.lower()
    hits, cats = [], {}
    for rid, cat, w, rx, en, hi in RULES:
        if re.search(rx, low if rid not in ("kyc",) else low + " " + text, re.I | re.S):
            hits.append((w, en, hi, cat))
    urls = extract_urls(text)
    for u in urls[:5]:
        hits.extend(analyze_url(u))
    if urls and any(h[3] in ("kyc", "otp_pin", "prize", "job_loan", "utility") for h in hits):
        hits.append((10, "Combines a link with a request for action or money.", "लिंक के साथ कार्रवाई या पैसे की माँग की गई है।", "combo"))
    for w, _, _, c in hits:
        cats[c] = cats.get(c, 0) + w
    raw = sum(h[0] for h in hits)
    score = min(100, raw)
    # Several independent red flags reinforce each other.
    if len(hits) >= 3 and score < 75:
        score = min(100, score + 10)
    verdict = "SCAM" if score >= 60 else "SUSPICIOUS" if score >= 30 else "LIKELY_SAFE"
    top = max(cats, key=cats.get) if cats else "none"
    ix = 2 if lang == "hi" else 1
    return {
        "score": score, "verdict": verdict, "label": LABELS[lang][verdict],
        "reasons": [h[ix] for h in sorted(hits, key=lambda x: -x[0])],
        "advice": ADVICE[lang][verdict], "category": top, "urls": urls[:5],
    }

def spoken_summary(result, lang="en"):
    """Short text suitable for text-to-speech / voice note."""
    if lang == "hi":
        s = f"{result['label']}। जोखिम {result['score']} प्रतिशत।"
        if result["reasons"]:
            s += " कारण: " + result["reasons"][0]
        return s + " " + result["advice"][0]
    s = f"{result['label']}. Risk score {result['score']} out of 100."
    if result["reasons"]:
        s += " Reason: " + result["reasons"][0]
    return s + " " + result["advice"][0]
