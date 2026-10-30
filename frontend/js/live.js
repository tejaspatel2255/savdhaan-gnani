/**
 * live.js — "Listen live" button controller.
 * States: idle → permission → connecting → listening → alert → stopped
 * No Gnani calls in this file — calls go through mic.js / api.js.
 */
import { t } from "./strings.js";
import { getHealth, startSession, stopSession } from "./api.js";
import { startMic, stopMic, MicError } from "./mic.js";

const NOTICE_KEY = "savdhaan_live_notice_seen";

let _state = "idle";   // idle | permission | connecting | listening | alert | stopped
let _sessionId = null;
let _usageCap = 180;
let _onDispatch = null; // callback to forward events to app.dispatch

const STATES = {
  idle: "idle", permission: "permission", connecting: "connecting",
  listening: "listening", alert: "alert", stopped: "stopped",
};

let el = {};

export function init(opts = {}) {
  /** opts: { onDispatch, onShowBanner } */
  _onDispatch = opts.onDispatch || null;
  el = {
    btnLive: document.getElementById("btn-listen-live"),
    btnStop: document.getElementById("btn-live-stop"),
    strip: document.getElementById("live-status-strip"),
    stateBadge: document.getElementById("live-state-badge"),
    sourceLabel: document.getElementById("live-source-label"),
    usageBar: document.getElementById("live-usage-bar-inner"),
    usageText: document.getElementById("live-usage-text"),
    langSel: document.getElementById("live-lang-sel"),
    noticeOverlay: document.getElementById("live-notice-overlay"),
    noticeOk: document.getElementById("live-notice-ok"),
    disabledReason: document.getElementById("live-disabled-reason"),
  };

  if (el.noticeOk) el.noticeOk.addEventListener("click", _acceptNotice);
  if (el.btnLive) el.btnLive.addEventListener("click", _onLiveClick);
  if (el.btnStop) el.btnStop.addEventListener("click", _onStopClick);

  _checkHealth();
}

async function _checkHealth() {
  if (!el.btnLive) return;
  try {
    const h = await getHealth();
    _usageCap = h.max_stt_seconds ?? 180;
    if (!h.gnani_key_present) {
      el.btnLive.disabled = true;
      if (el.disabledReason) { el.disabledReason.textContent = t("live_no_key"); el.disabledReason.style.display = ""; }
    } else if (h.demo) {
      el.btnLive.disabled = true;
      if (el.disabledReason) { el.disabledReason.textContent = t("live_demo_mode"); el.disabledReason.style.display = ""; }
    }
  } catch (_) {}
}

function _onLiveClick() {
  if (sessionStorage.getItem(NOTICE_KEY)) {
    _startLive();
  } else if (el.noticeOverlay) {
    el.noticeOverlay.classList.remove("hidden");
    if (el.noticeOk) el.noticeOk.focus();
  } else {
    _startLive();
  }
}

function _acceptNotice() {
  sessionStorage.setItem(NOTICE_KEY, "1");
  if (el.noticeOverlay) el.noticeOverlay.classList.add("hidden");
  _startLive();
}

async function _startLive() {
  const lang = (el.langSel && el.langSel.value) || "hi-IN";
  _setState("permission");

  let sessionId;
  try {
    const res = await startSession({ mode: "mic", lang, speak_warning: true });
    sessionId = res.session_id;
    _sessionId = sessionId;
  } catch (err) {
    _setState("idle");
    if (_onDispatch) _onDispatch({ type: "error", code: err.status === 403 ? "live_local_only" : "internal", message: err.message, recoverable: true });
    return;
  }

  _setState("connecting");
  try {
    await startMic(sessionId);
    _setState("listening");
    _showStrip();
  } catch (merr) {
    _setState("stopped");
    const code = merr instanceof MicError ? (merr.code === "denied" ? "mic_denied" : "mic_no_device") : "internal";
    if (_onDispatch) _onDispatch({ type: "error", code, message: merr.message, recoverable: true });
    try { await stopSession(sessionId); } catch (_) {}
    _sessionId = null;
  }
}

async function _onStopClick() {
  stopMic();
  if (_sessionId) {
    try { await stopSession(_sessionId); } catch (_) {}
    _sessionId = null;
  }
  _setState("stopped");
  setTimeout(() => _setState("idle"), 2000);
}

function _setState(s) {
  _state = s;
  const labels = {
    idle: t("live_state_idle"), permission: t("live_state_permission"),
    connecting: t("live_state_connecting"), listening: t("live_state_listening"),
    alert: t("live_state_alert"), stopped: t("live_state_stopped"),
  };
  if (el.stateBadge) { el.stateBadge.textContent = labels[s] || s; el.stateBadge.dataset.state = s; }
  if (el.btnLive) { el.btnLive.dataset.liveState = s; el.btnLive.disabled = (s !== "idle" && s !== "stopped"); }
  if (el.btnStop) el.btnStop.style.display = (s === "listening" || s === "alert") ? "" : "none";
  if (s === "idle" || s === "stopped") _hideStrip();
}

function _showStrip() {
  if (el.strip) el.strip.classList.add("visible");
  if (el.sourceLabel) el.sourceLabel.textContent = t("live_source_label");
}

function _hideStrip() {
  if (el.strip) el.strip.classList.remove("visible");
}

/** Called by app.js dispatch for session / alert / usage_tick events. */
export function handle(msg) {
  if (msg.type === "alert") _setState("alert");
  if (msg.type === "session" && (msg.state === "ended" || msg.state === "error")) {
    _sessionId = null; _setState("idle");
  }
  if (msg.type === "usage_tick") _updateUsage(msg.stt_seconds_used, msg.stt_seconds_cap || _usageCap);
}

function _updateUsage(used, cap) {
  if (!el.usageBar) return;
  const pct = cap > 0 ? Math.min(100, (used / cap) * 100) : 0;
  el.usageBar.style.width = `${pct}%`;
  el.usageBar.dataset.warn = pct >= 90 ? "2" : pct >= 70 ? "1" : "0";
  if (el.usageText) el.usageText.textContent = `${Math.round(used)}s / ${Math.round(cap)}s`;
}
