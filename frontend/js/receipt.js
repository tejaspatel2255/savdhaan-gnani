import { t } from "./strings.js";
import { fill } from "./i18n.js";

let root = null;
let replayCallback = null;
let startButtonRef = null;

export function init(rootEl, onReplay) {
  root = rootEl;
  replayCallback = onReplay;
  startButtonRef = document.getElementById("btn-start");

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && root && !root.classList.contains("hidden")) {
      closeReceipt();
    }
  });
}

export function reset() {
  if (root) {
    while (root.firstChild) root.removeChild(root.firstChild);
    root.classList.add("hidden");
  }
}

function closeReceipt() {
  reset();
  if (startButtonRef) startButtonRef.focus();
}

function formatTime(sec) {
  if (sec === null || sec === undefined) return t("receipt_time_none");
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function createRow(label, value) {
  const row = document.createElement("div");
  row.className = "receipt-row";

  const lbl = document.createElement("span");
  lbl.className = "receipt-row-label";
  lbl.textContent = label;
  row.appendChild(lbl);

  const val = document.createElement("span");
  val.className = "receipt-row-value";
  val.textContent = String(value);
  row.appendChild(val);

  return row;
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    reset();
  } else if (msg.type === "summary") {
    reset();

    const dialog = document.createElement("div");
    dialog.className = "receipt-dialog";
    dialog.setAttribute("role", "dialog");
    dialog.setAttribute("aria-modal", "true");
    dialog.setAttribute("aria-label", t("receipt_title"));

    const title = fill(document.createElement("div"), "receipt_title");
    title.className = "receipt-title on-paper";
    dialog.appendChild(title);

    const table = document.createElement("div");
    table.className = "receipt-table";

    table.appendChild(createRow("Mode", msg.mode || state.mode));
    table.appendChild(createRow("Synthetic", msg.synthetic ? "Yes" : "No"));
    table.appendChild(createRow("Duration", formatTime(msg.duration_s)));
    table.appendChild(createRow("Segments", msg.segments));
    table.appendChild(createRow("Time to alert", formatTime(msg.time_to_alert_s)));
    table.appendChild(createRow("Max score", `${msg.max_score}/100`));

    const p50 = (msg.stt_latency_ms && msg.stt_latency_ms.p50 != null) ? `${msg.stt_latency_ms.p50} ms` : t("receipt_na");
    const p95 = (msg.stt_latency_ms && msg.stt_latency_ms.p95 != null) ? `${msg.stt_latency_ms.p95} ms` : t("receipt_na");
    table.appendChild(createRow("STT Latency (p50 / p95)", `${p50} / ${p95}`));

    const sttSec = (msg.credits_used && msg.credits_used.stt_seconds) || 0;
    const ttsChars = (msg.credits_used && msg.credits_used.tts_chars) || 0;
    table.appendChild(createRow("Credits Used", `${sttSec}s STT, ${ttsChars} chars TTS`));
    dialog.appendChild(table);

    // Verdict stamp
    const isScam = msg.time_to_alert_s !== null || msg.final_level === "danger";
    const verdict = fill(document.createElement("div"), isScam ? "receipt_scam" : "receipt_safe");
    verdict.className = `receipt-verdict on-paper ${isScam ? "scam" : "safe"}`;
    dialog.appendChild(verdict);

    // Action buttons
    const actions = document.createElement("div");
    actions.className = "receipt-actions";

    const btnReplay = fill(document.createElement("button"), "btn_replay", { enOnly: true });
    btnReplay.className = "btn-receipt btn-receipt-replay";
    btnReplay.addEventListener("click", () => {
      closeReceipt();
      if (replayCallback) replayCallback();
    });
    actions.appendChild(btnReplay);

    const btnClose = fill(document.createElement("button"), "btn_close", { enOnly: true });
    btnClose.className = "btn-receipt btn-receipt-close";
    btnClose.addEventListener("click", closeReceipt);
    actions.appendChild(btnClose);

    dialog.appendChild(actions);
    root.appendChild(dialog);
    root.classList.remove("hidden");

    btnReplay.focus();
  }
}
