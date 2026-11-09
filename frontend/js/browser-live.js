/**
 * browser-live.js — "Speak yourself" Web Speech API + Pyodide in-browser scoring.
 * Streams interim words to live-caption, scores finalized sentences in Pyodide,
 * and emits standard Savdhaan events into app.dispatch.
 */
import { t } from "./strings.js";
import { initScorer, startScoring, scoreSentence } from "./py-scorer.js";

let _recognition = null, _isRunning = false, _sessionStartTime = 0;
let _dispatch = null, _sessionId = null, _seq = 0, _sentenceIndex = 0;
let _alertTriggered = false, _maxScore = 0, _activeLang = "hi-IN", _timeoutTimer = null;
let _allCategories = new Set(), _btnMic = null, _captionEl = null;

export function initBrowserLive(dispatch) {
  _dispatch = dispatch;
  _btnMic = document.getElementById("btn-browser-mic");
  _captionEl = document.getElementById("live-caption");
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec || (!window.isSecureContext && location.hostname !== "localhost" && location.hostname !== "127.0.0.1")) {
    if (_btnMic) { _btnMic.disabled = true; _btnMic.title = t("browser_mic_unavailable"); }
    return;
  }
  if (_btnMic) _btnMic.addEventListener("click", () => (_isRunning ? stopBrowserLive() : startBrowserLive()));
}

export async function startBrowserLive(langOverride) {
  if (_isRunning) return;
  const langSel = document.getElementById("live-lang-sel");
  _activeLang = langOverride || (langSel ? langSel.value : "hi-IN");
  if (_btnMic) { _btnMic.disabled = true; _btnMic.textContent = t("browser_mic_loading"); }

  try {
    await initScorer();
    await startScoring(_activeLang, 30, 60);
  } catch (err) {
    if (_btnMic) { _btnMic.disabled = false; _btnMic.textContent = t("btn_browser_mic"); }
    alert(t("browser_mic_error"));
    return;
  }

  _isRunning = true;
  _sessionStartTime = performance.now();
  _sessionId = "br_" + Math.random().toString(36).substring(2, 9);
  _seq = 0; _sentenceIndex = 0; _alertTriggered = false; _maxScore = 0;
  _allCategories.clear();

  if (_btnMic) {
    _btnMic.disabled = false;
    _btnMic.textContent = t("btn_browser_mic_stop");
    _btnMic.classList.add("active-live");
  }
  if (_captionEl) {
    _captionEl.textContent = t("listening_caption_hint");
    _captionEl.classList.add("listening");
  }

  _emit("session", {
    state: "starting", session_id: _sessionId, mode: "mic", mode_label: "BROWSER MIC",
    call_title: "Your own words (browser mic)", synthetic: false, lang: _activeLang,
    models: { stt: "Browser speech recognition", tts: "Pre-generated Gnani Timbre warning" },
    thresholds: { careful: 30, danger: 60 },
  });
  _emit("session", { state: "listening", mode_label: "BROWSER MIC" });

  _startSpeechRec();
  _timeoutTimer = setTimeout(() => stopBrowserLive(), 180000);
}

function _startSpeechRec() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRec) return;
  _recognition = new SpeechRec();
  _recognition.continuous = true;
  _recognition.interimResults = true;
  _recognition.lang = _activeLang;

  _recognition.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; ++i) {
      const res = e.results[i];
      if (res.isFinal) _handleFinalPhrase(res[0].transcript);
      else interim += res[0].transcript;
    }
    if (_captionEl && interim) _captionEl.textContent = interim;
  };
  _recognition.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      stopBrowserLive();
      alert("Microphone permission blocked. Please allow microphone access.");
    }
  };
  _recognition.onend = () => { if (_isRunning) { try { _recognition.start(); } catch (_) {} } };
  try { _recognition.start(); } catch (_) {}
}

function _handleFinalPhrase(phrase) {
  if (_captionEl) _captionEl.textContent = "";
  const sentences = phrase.split(/[.?!।\n]+/).map(s => s.trim()).filter(Boolean);
  if (!sentences.length) sentences.push(phrase.trim());
  sentences.forEach(_processSentence);
}

function _processSentence(text) {
  const idx = _sentenceIndex++;
  _emit("transcript", {
    segment_index: idx, segment_id: "b" + idx, text,
    audio_duration_ms: Math.round(text.length * 50), stt_latency_ms: null,
  });
  const res = scoreSentence(text, idx);
  if (res.categories) {
    const cats = Array.isArray(res.categories) ? res.categories : Object.keys(res.categories);
    cats.forEach(c => _allCategories.add(c));
  }
  _maxScore = Math.max(_maxScore, res.score || 0);

  const riskEvent = Object.assign({}, res, { type: "risk", segment_index: idx });
  delete riskEvent.alert; delete riskEvent.reasons; delete riskEvent.max_score;
  _emit("risk", riskEvent);

  if (res.alert && !_alertTriggered) {
    _alertTriggered = true;
    _triggerAlert(res);
  }
}

function _triggerAlert(res) {
  const topReason = (res.reasons && res.reasons[0]) || { category: "generic", label_en: "scam trap" };
  const cat = topReason.category || "generic";
  const pfx = _activeLang.toLowerCase().replace("-", "_");
  const audioUrl = `/assets/audio/warn_${pfx}_${cat}_shivani.wav`;

  _emit("alert", {
    score: res.score, level: "danger", reasons: res.reasons || [],
    warning: { text: "", lang: _activeLang, voice: "shivani", status: "spoken" },
  });
  _emit("family_alert", {
    contact_label: "Trusted contact (simulated)", simulated: true,
    message_en: `Savdhaan alert: your family member is on a suspected scam call (${topReason.label_en || cat}). Please call them now.`,
    message: `Savdhaan alert: your family member is on a suspected scam call (${topReason.label_en || cat}). Please call them now.`,
  });
  _emit("warning_audio", { audio_url: audioUrl });
}

export function stopBrowserLive() {
  if (!_isRunning) return;
  _isRunning = false;
  if (_timeoutTimer) clearTimeout(_timeoutTimer);
  _timeoutTimer = null;
  if (_recognition) { try { _recognition.stop(); } catch (_) {} _recognition = null; }

  if (_btnMic) { _btnMic.textContent = t("btn_browser_mic"); _btnMic.classList.remove("active-live"); }
  if (_captionEl) { _captionEl.textContent = ""; _captionEl.classList.remove("listening"); }

  const durS = Math.round((performance.now() - _sessionStartTime) / 1000);
  _emit("session", { state: "ended" });
  _emit("summary", {
    duration_s: durS, segments: _sentenceIndex, time_to_alert_s: _alertTriggered ? 6.0 : null,
    max_score: _maxScore, final_level: _maxScore >= 60 ? "danger" : (_maxScore >= 30 ? "careful" : "calm"),
    categories: Array.from(_allCategories), stt_latency_ms: { p50: null, p95: null },
    credits_used: { stt_seconds: 0, tts_chars: 0 }, mode: "mic", synthetic: false,
  });
}

function _emit(type, data) {
  if (!_dispatch) return;
  _dispatch(Object.assign({
    type, seq: _seq++, session_id: _sessionId,
    t: Number(((performance.now() - _sessionStartTime) / 1000).toFixed(2)),
  }, data));
}
