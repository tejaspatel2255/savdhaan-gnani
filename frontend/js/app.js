import { t, LANGS } from "./strings.js";
import { getCalls, startSession, stopSession, ApiError } from "./api.js";
import { connect } from "./ws.js";
import * as eye from "./eye.js";
import * as tape from "./tape.js";
import * as why from "./why.js";
import * as waveform from "./waveform.js";
import * as stamp from "./stamp.js";
import * as phone from "./phone.js";
import * as receipt from "./receipt.js";
import { playSample } from "./devfeed.js";

export const FEATURES = { mic: false };
export const state = { sessionId: null, mode: "mock", modeLabel: "MOCK", lang: "hi-IN", level: "calm", score: 0, alertFired: false };

let audioCtx = null, callsList = [];
const handledMessages = new Set();
let el = {};

export async function init() {
  const get = (id) => document.getElementById(id);
  el = {
    polite: get("live-polite"), assertive: get("live-assertive"),
    badge: get("mode-badge"), synthetic: get("synthetic-pill"), reconnect: get("reconnect-chip"),
    banner: get("banner"), bannerMsg: get("banner").querySelector(".banner-msg"),
    bannerServer: get("banner").querySelector(".banner-server-msg"),
    callSel: get("call-select"), langSel: get("lang-select"), modeSel: get("mode-select"),
    speakCb: get("speak-warning-cb"), btnStart: get("btn-start"), btnStop: get("btn-stop"),
  };

  el.banner.querySelector(".banner-close").addEventListener("click", () => el.banner.classList.add("hidden"));
  el.btnStart.addEventListener("click", handleStart);
  el.btnStop.addEventListener("click", handleStop);
  el.callSel.addEventListener("change", syncModes);

  eye.init(get("col-eye")); tape.init(get("col-tape")); why.init(get("col-why"));
  waveform.init(get("awaaz")); stamp.init(get("stamp-root")); phone.init(get("phone-slot"));
  receipt.init(get("receipt-root"), handleStart);

  for (const l of LANGS) {
    const o = document.createElement("option");
    o.value = l.code; o.textContent = l.label;
    el.langSel.appendChild(o);
  }
  await fetchCalls();

  const p = new URLSearchParams(window.location.search);
  if (p.get("dev") === "1") {
    playSample("/assets/sample_run.jsonl", dispatch, { speed: parseFloat(p.get("speed") || "1"), at: p.get("at") ? parseFloat(p.get("at")) : null });
  } else {
    connect(null, dispatch, (st) => el.reconnect.classList.toggle("hidden", st !== "reconnecting"));
  }
}

async function fetchCalls() {
  try {
    const res = await getCalls();
    callsList = res.calls || [];
    while (el.callSel.firstChild) el.callSel.removeChild(el.callSel.firstChild);
    for (const c of callsList) {
      const o = document.createElement("option");
      o.value = c.id; o.textContent = `${c.title} (SYNTHETIC)`;
      el.callSel.appendChild(o);
    }
    syncModes();
  } catch (err) { showBanner("network", err.message); }
}

function syncModes() {
  const c = callsList.find((x) => x.id === el.callSel.value);
  while (el.modeSel.firstChild) el.modeSel.removeChild(el.modeSel.firstChild);
  for (const m of (c && c.modes) || ["mock"]) {
    if (m === "mic" && !FEATURES.mic) continue;
    const o = document.createElement("option");
    o.value = m; o.textContent = m.toUpperCase();
    el.modeSel.appendChild(o);
  }
}

function unlockAudio() {
  if (!audioCtx) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (Ctx) {
      audioCtx = new Ctx();
      const b = audioCtx.createBuffer(1, audioCtx.sampleRate * 0.05, audioCtx.sampleRate);
      const s = audioCtx.createBufferSource();
      s.buffer = b; s.connect(audioCtx.destination); s.start(0);
    }
  }
  if (audioCtx && audioCtx.state === "suspended") audioCtx.resume();
}

async function handleStart() {
  unlockAudio();
  el.banner.classList.add("hidden");
  el.btnStart.disabled = true; el.btnStop.disabled = false;
  const p = new URLSearchParams(window.location.search);
  const body = {
    mode: el.modeSel.value, call_id: el.callSel.value, lang: el.langSel.value,
    speak_warning: el.speakCb.checked, speed: p.get("speed") ? parseFloat(p.get("speed")) : 1.0,
  };
  try {
    await startSession(body);
  } catch (err) {
    el.btnStart.disabled = false; el.btnStop.disabled = true;
    showBanner((err instanceof ApiError && err.status === 409) ? "call_already_running" : "internal", err.message);
  }
}

async function handleStop() {
  if (!state.sessionId) return;
  el.btnStop.disabled = true;
  try { await stopSession(state.sessionId); } catch (err) { showBanner("internal", err.message); }
}

function showBanner(code, msg = "") {
  el.bannerMsg.textContent = t(code) || code;
  el.bannerServer.textContent = msg ? `Detail: ${msg}` : "";
  el.banner.classList.remove("hidden");
}

function resetAll() {
  handledMessages.clear();
  eye.reset(); tape.reset(); why.reset(); waveform.reset();
  stamp.reset(); phone.reset(); receipt.reset();
}

export function dispatch(msg) {
  if (!msg || typeof msg !== "object" || !msg.type) return;
  const key = `${msg.session_id || "n"}_${msg.seq != null ? msg.seq : "x"}`;
  if (handledMessages.has(key)) return;
  handledMessages.add(key);

  if (msg.session_id && msg.session_id !== state.sessionId) {
    resetAll();
    state.sessionId = msg.session_id;
    state.alertFired = false;
  }

  try {
    switch (msg.type) {
      case "session":
        state.mode = msg.mode || state.mode;
        state.modeLabel = msg.mode_label || state.modeLabel;
        state.lang = msg.lang || state.lang;
        if (el.badge) {
          el.badge.textContent = state.modeLabel;
          el.badge.className = `badge-pill mode-${state.mode}`;
          el.badge.classList.remove("hidden");
        }
        if (el.synthetic) el.synthetic.classList.toggle("hidden", !msg.synthetic);
        const running = (msg.state === "listening" || msg.state === "starting");
        if (el.btnStart) el.btnStart.disabled = running;
        if (el.btnStop) el.btnStop.disabled = !running;
        break;

      case "risk": {
        const prev = state.level;
        state.score = msg.score; state.level = msg.level;
        document.body.setAttribute("data-level", msg.level);
        if (prev !== msg.level && el.polite) el.polite.textContent = `Risk level ${msg.level}, score ${msg.score}`;
        break;
      }

      case "alert":
        if (!state.alertFired) {
          state.alertFired = true;
          if (el.assertive) el.assertive.textContent = t("alert_announcement");
        }
        break;

      case "error":
        showBanner(msg.code, msg.message);
        if (!msg.recoverable) { el.btnStart.disabled = false; el.btnStop.disabled = true; }
        break;
    }

    eye.handle(msg, state); tape.handle(msg, state); why.handle(msg, state);
    waveform.handle(msg, state); stamp.handle(msg, state); phone.handle(msg, state);
    receipt.handle(msg, state);
  } catch (err) {
    console.error("Event error:", err, msg);
  }
}

window.addEventListener("DOMContentLoaded", init);
