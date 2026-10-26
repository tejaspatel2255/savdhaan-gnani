import { t } from "./strings.js";
import * as eye from "./eye.js";
import * as tape from "./tape.js";
import * as why from "./why.js";
import * as waveform from "./waveform.js";
import { playSample } from "./devfeed.js";

export const state = {
  sessionId: null,
  mode: "mock",
  modeLabel: "MOCK",
  lang: "hi-IN",
  level: "calm",
  score: 0,
  alertFired: false,
};

let politeRegion = null;
let assertiveRegion = null;
let modeBadge = null;
let syntheticPill = null;

export function init() {
  politeRegion = document.getElementById("live-polite");
  assertiveRegion = document.getElementById("live-assertive");
  modeBadge = document.getElementById("mode-badge");
  syntheticPill = document.getElementById("synthetic-pill");

  eye.init(document.getElementById("col-eye"));
  tape.init(document.getElementById("col-tape"));
  why.init(document.getElementById("col-why"));
  waveform.init(document.getElementById("awaaz"));

  // Check dev mode
  const params = new URLSearchParams(window.location.search);
  if (params.get("dev") === "1") {
    const speed = parseFloat(params.get("speed") || "1");
    const at = params.get("at") ? parseFloat(params.get("at")) : null;
    playSample("/assets/sample_run.jsonl", dispatch, { speed, at });
  }
}

export function dispatch(msg) {
  if (!msg || typeof msg !== "object" || !msg.type) return;

  try {
    switch (msg.type) {
      case "session":
        state.sessionId = msg.session_id;
        state.mode = msg.mode || state.mode;
        state.modeLabel = msg.mode_label || state.modeLabel;
        state.lang = msg.lang || state.lang;

        if (modeBadge) {
          modeBadge.textContent = state.modeLabel;
          modeBadge.className = `badge-pill mode-${state.mode}`;
          modeBadge.classList.remove("hidden");
        }
        if (syntheticPill) {
          syntheticPill.classList.toggle("hidden", !msg.synthetic);
        }
        break;

      case "risk": {
        const prevLevel = state.level;
        state.score = msg.score;
        state.level = msg.level;
        document.body.setAttribute("data-level", msg.level);

        if (prevLevel !== msg.level && politeRegion) {
          politeRegion.textContent = `Risk level ${msg.level}, score ${msg.score}`;
        }
        break;
      }

      case "alert":
        if (!state.alertFired) {
          state.alertFired = true;
          if (assertiveRegion) {
            assertiveRegion.textContent = t("alert_announcement", "hi");
          }
        }
        break;

      default:
        // Ignore unknown message types safely
        break;
    }

    // Forward to modules
    eye.handle(msg, state);
    tape.handle(msg, state);
    why.handle(msg, state);
    waveform.handle(msg, state);
  } catch (err) {
    console.error("Error processing event:", err, msg);
  }
}

window.addEventListener("DOMContentLoaded", init);
