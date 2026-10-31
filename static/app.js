const $ = (s) => document.querySelector(s), $$ = (s) => [...document.querySelectorAll(s)];
let lang = localStorage.getItem("ss_lang") || "en", last = null, map, layer;

const T = {
  en: { tag:"Check before you click, share or pay.", t_check:"Check", t_report:"Report", t_map:"Scam map", t_learn:"Learn",
    paste:"Paste the message, link or call details", ph:"Example: Your SBI account will be blocked. Share OTP now.",
    speak_btn:"🎤 Speak it", check_btn:"Check now", try:"Try an example:", why:"Why", do:"What to do", listen:"🔊 Listen", report_it:"Report this",
    rep_h:"Report a scam in 1 minute", rep_p:"We write the complaint for you. Submit it at cybercrime.gov.in or call 1930.",
    city:"Your city / district", kind:"Type of scam", amount:"Money lost (₹, 0 if none)", suspect:"Scammer's number / UPI ID / link", what:"What happened?",
    make:"Create complaint", copy:"Copy", portal:"Open portal", map_h:"Where scams are happening",
    map_n:"Sample data is shown along with citizen reports. Panchayats, colleges and police can use this to plan awareness drives.",
    quiz_h:"Spot the scam – quick quiz", empty:"Please paste or speak a message first.", copied:"Copied", reports:"Reports", scans:"Messages checked",
    caught:"Scams caught", lost:"Money lost (₹)", topc:"Most affected cities", risk:"Risk score out of 100", score:"You scored", noVoice:"Voice typing is not supported in this browser. Please type.", listening:"Listening… tap again to stop", nomatch:"No clear red flags found. Stay careful." },
  hi: { tag:"क्लिक, शेयर या पेमेंट से पहले जाँचें।", t_check:"जाँचें", t_report:"शिकायत", t_map:"ठगी नक्शा", t_learn:"सीखें",
    paste:"संदेश, लिंक या कॉल की जानकारी यहाँ डालें", ph:"उदाहरण: आपका SBI खाता बंद हो जाएगा। अभी OTP बताएं।",
    speak_btn:"🎤 बोलकर बताएं", check_btn:"अभी जाँचें", try:"उदाहरण आज़माएं:", why:"कारण", do:"क्या करें", listen:"🔊 सुनें", report_it:"शिकायत करें",
    rep_h:"1 मिनट में शिकायत लिखें", rep_p:"शिकायत हम लिख देंगे। उसे cybercrime.gov.in पर जमा करें या 1930 पर कॉल करें।",
    city:"आपका शहर / ज़िला", kind:"ठगी का प्रकार", amount:"कितने पैसे गए (₹, नहीं गए तो 0)", suspect:"ठग का नंबर / UPI ID / लिंक", what:"क्या हुआ?",
    make:"शिकायत बनाएं", copy:"कॉपी करें", portal:"पोर्टल खोलें", map_h:"ठगी कहाँ हो रही है",
    map_n:"नमूना डेटा के साथ नागरिकों की शिकायतें दिखती हैं। पंचायत, कॉलेज और पुलिस इससे जागरूकता अभियान तय कर सकते हैं।",
    quiz_h:"ठगी पहचानें – छोटी क्विज़", empty:"पहले संदेश लिखें या बोलें।", copied:"कॉपी हो गया", reports:"शिकायतें", scans:"जाँचे गए संदेश",
    caught:"पकड़ी गई ठगी", lost:"गई रकम (₹)", topc:"सबसे प्रभावित शहर", risk:"जोखिम स्कोर (100 में से)", score:"आपके अंक", noVoice:"इस ब्राउज़र में बोलकर लिखना उपलब्ध नहीं है। कृपया टाइप करें।", listening:"सुन रहा हूँ… रोकने के लिए दोबारा दबाएं", nomatch:"कोई बड़ा खतरा नहीं मिला। फिर भी सावधान रहें।" }
};
const t = (k) => (T[lang][k] || T.en[k] || k);
const EX = {
  en: ["Dear customer your SBI account will be blocked today. Update KYC now http://sbi-kyc-update.xyz/login",
       "This is CBI. A warrant is issued against you. You are under digital arrest, stay on video call.",
       "Congratulations! You won Rs 25 lakh lottery. Pay processing fee Rs 2000 to claim.",
       "Your OTP for login is 482913. Do not share it with anyone. -HDFC Bank"],
  hi: ["आपका खाता बंद हो जाएगा। तुरंत केवाईसी अपडेट करें और OTP बताएं।", "आपके नाम पर वारंट है। डिजिटल अरेस्ट में रहें, वीडियो कॉल न काटें।",
       "बधाई! आपने 25 लाख की लॉटरी जीती है। इनाम पाने के लिए 2000 रुपये प्रोसेसिंग फीस भरें।", "आपकी बिजली आज रात कट जाएगी। तुरंत इस नंबर पर कॉल करें।"]
};

function applyLang() {
  document.documentElement.lang = lang;
  $$("[data-i]").forEach((e) => (e.textContent = t(e.dataset.i)));
  $$("[data-ip]").forEach((e) => (e.placeholder = t(e.dataset.ip)));
  $("#langBtn").textContent = lang === "en" ? "हिंदी" : "English";
  $("#chips").innerHTML = "";
  EX[lang].forEach((x) => { const b = document.createElement("button"); b.textContent = x.slice(0, 38) + "…"; b.onclick = () => { $("#msg").value = x; check(); }; $("#chips").append(b); });
  loadQuiz();
  if ($("#map").classList.contains("on")) loadMap();
  if (last) check(true);
}
$("#langBtn").onclick = () => { lang = lang === "en" ? "hi" : "en"; localStorage.setItem("ss_lang", lang); applyLang(); };

$$(".tabs button").forEach((b) => (b.onclick = () => show(b.dataset.tab)));
function show(id) {
  $$(".tabs button").forEach((x) => x.classList.toggle("on", x.dataset.tab === id));
  $$(".panel").forEach((p) => p.classList.toggle("on", p.id === id));
  if (id === "map") loadMap();
  window.scrollTo(0, 0);
}

async function post(url, body) {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}
const li = (arr) => arr.map((x) => `<li>${esc(x)}</li>`).join("");
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function check(silent) {
  const text = $("#msg").value.trim();
  if (!text) { alert(t("empty")); return; }
  const r = await post("/api/analyze", { text, lang });
  last = r;
  const box = $("#result"); box.hidden = false; box.className = "result " + r.verdict;
  $(".ring").style.setProperty("--p", r.score); $("#score").textContent = r.score;
  $("#vlabel").textContent = r.label; $("#vsub").textContent = t("risk");
  $("#reasons").innerHTML = r.reasons.length ? li(r.reasons) : `<li>${esc(t("nomatch"))}</li>`;
  $("#advice").innerHTML = li(r.advice);
  if (!silent) { box.scrollIntoView({ behavior: "smooth", block: "nearest" }); speak(r.spoken); }
}
$("#go").onclick = () => check();

function speak(text) {
  if (!("speechSynthesis" in window)) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text); u.lang = lang === "hi" ? "hi-IN" : "en-IN"; u.rate = 0.92;
  speechSynthesis.speak(u);
}
$("#say").onclick = () => last && speak(last.spoken);

const SR = window.SpeechRecognition || window.webkitSpeechRecognition; let rec;
$("#mic").onclick = () => {
  if (!SR) { alert(t("noVoice")); return; }
  if (rec) { rec.stop(); return; }
  rec = new SR(); rec.lang = lang === "hi" ? "hi-IN" : "en-IN"; rec.interimResults = true; rec.continuous = true;
  const old = $("#msg").value, mic = $("#mic"), label = mic.textContent;
  mic.classList.add("rec"); mic.textContent = t("listening");
  rec.onresult = (e) => { let s = ""; for (const x of e.results) s += x[0].transcript; $("#msg").value = (old + " " + s).trim(); };
  rec.onend = () => { rec = null; mic.classList.remove("rec"); mic.textContent = label; if ($("#msg").value.trim()) check(); };
  rec.onerror = () => rec && rec.stop();
  rec.start();
};

$("#toReport").onclick = () => { $("#rTxt").value = $("#msg").value; if (last) { const m = { otp_pin:"otp_pin", kyc:"kyc", upi:"upi", prize:"prize", job_loan:"job_loan", digital_arrest:"digital_arrest", remote_access:"remote_access", utility:"utility", malware:"malware", impersonation:"impersonation", link:"link" }; $("#rCat").value = m[last.category] || "other"; if (last.urls[0]) $("#rSus").value = last.urls[0]; } show("report"); };
$("#rGo").onclick = async () => {
  const r = await post("/api/report", { city: $("#rCity").value, category: $("#rCat").value, amount: $("#rAmt").value, suspect: $("#rSus").value, text: $("#rTxt").value });
  if (r.error) { alert(r.error); return; }
  $("#rLetter").value = r.complaint; $("#rOut").hidden = false; $("#rOut").scrollIntoView({ behavior: "smooth" });
};
$("#copy").onclick = async () => { try { await navigator.clipboard.writeText($("#rLetter").value); } catch { $("#rLetter").select(); document.execCommand("copy"); } alert(t("copied")); };

async function loadMap() {
  const [pts, st] = await Promise.all([fetch("/api/heatmap").then((r) => r.json()), fetch("/api/stats").then((r) => r.json())]);
  $("#stats").innerHTML = [["reports", st.reports], ["scans", st.scans], ["caught", st.scams_caught], ["lost", st.amount.toLocaleString("en-IN")]]
    .map(([k, v]) => `<div class="stat"><b>${v}</b>${esc(t(k))}</div>`).join("");
  $("#top").innerHTML = `<h3>${esc(t("topc"))}</h3><ol>${st.top_cities.map((c) => `<li>${esc(c.city)} – ${c.n}</li>`).join("")}</ol>`;
  if (typeof L === "undefined") { $("#mapbox").textContent = "Map needs internet."; return; }
  if (!map) { map = L.map("mapbox").setView([22.5, 79], 4.6); L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: "© OpenStreetMap" }).addTo(map); }
  if (layer) layer.remove();
  layer = L.layerGroup(pts.map((p) => L.circleMarker([p.lat, p.lng], { radius: 9, stroke: false, fillColor: "#C62828", fillOpacity: 0.18 }).bindPopup(esc(p.city) + " – " + esc(p.category.replace("_", " "))))).addTo(map);
  setTimeout(() => map.invalidateSize(), 100);
}

async function loadQuiz() {
  const qs = await fetch("/api/quiz?lang=" + lang).then((r) => r.json()); let score = 0, done = 0; const box = $("#quiz"); box.innerHTML = "";
  qs.forEach((q) => {
    const d = document.createElement("div"); d.className = "q"; d.innerHTML = `<p>${esc(q.q)}</p>`;
    q.options.forEach((o, i) => { const b = document.createElement("button"); b.textContent = o; b.onclick = () => {
      if (d.classList.contains("done")) return; d.classList.add("done"); done++;
      if (i === q.answer) { score++; b.classList.add("ok"); } else { b.classList.add("no"); d.querySelectorAll("button")[q.answer].classList.add("ok"); }
      if (done === qs.length) { const f = document.createElement("p"); f.id = "score-final"; f.textContent = `${t("score")}: ${score}/${qs.length}`; box.append(f); } };
      d.append(b); });
    const w = document.createElement("div"); w.className = "why"; w.textContent = q.why; d.append(w); box.append(d);
  });
}
applyLang();
