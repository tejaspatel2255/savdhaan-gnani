import { t } from "./strings.js";
import { fill } from "./i18n.js";
import { playTwoToneBeep } from "./beep.js";

let dom = null;
let currentScreen = "calm";
let audioElement = null;
let playedSessions = new Set();

function mk(cls) {
  const d = document.createElement("div");
  d.className = cls;
  return d;
}

export function init(rootEl) {
  dom = {
    root: rootEl,
    screen: rootEl.querySelector(".phone-screen"),
    familyContainer: rootEl.querySelector(".family-card-slot"),
  };
  reset();
}

export function reset() {
  currentScreen = "calm";
  if (audioElement) { audioElement.pause(); audioElement = null; }
  renderScreen("calm");
  if (dom && dom.familyContainer) {
    while (dom.familyContainer.firstChild) dom.familyContainer.removeChild(dom.familyContainer.firstChild);
  }
}

function clearScreen() {
  if (!dom || !dom.screen) return;
  while (dom.screen.firstChild) dom.screen.removeChild(dom.screen.firstChild);
}

function renderScreen(stateName) {
  if (!dom || !dom.screen) return;
  clearScreen();
  dom.screen.setAttribute("data-state", stateName);
  currentScreen = stateName;

  if (stateName === "calm") {
    dom.screen.appendChild(fill(mk("phone-calm-title t-stack"), "phone_calm_title"));
    dom.screen.appendChild(fill(mk("phone-calm-sub t-stack"), "phone_calm_sub"));
  } else if (stateName === "careful") {
    dom.screen.appendChild(fill(mk("phone-careful-banner"), "phone_careful"));
  } else if (stateName === "danger") {
    dom.screen.appendChild(fill(mk("danger-card-title t-stack on-danger"), "phone_danger_title"));

    const lines = document.createElement("div");
    lines.className = "danger-lines";

    for (const n of [1, 2, 3]) lines.appendChild(fill(mk("t-stack on-danger"), `phone_danger_line${n}`));
    dom.screen.appendChild(lines);

    const btn = fill(document.createElement("button"), "phone_hangup_btn");
    btn.className = "btn-hangup";
    btn.addEventListener("click", () => renderScreen("safe"));
    dom.screen.appendChild(btn);
  } else if (stateName === "safe") {
    dom.screen.appendChild(fill(mk("phone-ended-safe"), "phone_ended_safe"));
  }
}

function handleWarningAudio(msg, state) {
  if (currentScreen !== "danger" || !dom.screen) return;

  const barsBox = document.createElement("div");
  barsBox.className = "audio-bars-container";

  if (msg.audio_url && !playedSessions.has(state.sessionId)) {
    playedSessions.add(state.sessionId);

    const bars = document.createElement("div");
    bars.className = "audio-bars";
    for (let i = 0; i < 5; i++) {
      const bar = document.createElement("div");
      bar.className = "audio-bar";
      bars.appendChild(bar);
    }
    barsBox.appendChild(bars);

    let srcUrl = msg.audio_url;
    if (state.isStatic && srcUrl && !srcUrl.startsWith("/assets/")) {
      const fileName = srcUrl.split("/").pop();
      srcUrl = `/assets/audio/${fileName}`;
    }

    audioElement = new Audio(srcUrl);
    audioElement.addEventListener("play", () => {});
    audioElement.addEventListener("error", () => {
      playTwoToneBeep();
      if (barsBox.parentNode) barsBox.parentNode.removeChild(barsBox);
    });
    audioElement.addEventListener("ended", () => {
      if (barsBox.parentNode) barsBox.parentNode.removeChild(barsBox);
    });

    audioElement.play().catch(() => {
      const tapBtn = document.createElement("button");
      tapBtn.className = "btn-tap-audio";
      tapBtn.textContent = t("tap_to_hear");
      tapBtn.addEventListener("click", () => {
        audioElement.play().catch(() => { playTwoToneBeep(); });
        tapBtn.remove();
      });
      barsBox.appendChild(tapBtn);
    });
  } else if (!msg.audio_url && msg.reason) {
    const switchedOff = msg.reason === "speaking_off" && !state.isStatic && !state.isSample;
    if (!switchedOff) playTwoToneBeep();
    const reasonKey = switchedOff ? "voice_off" : (state.isStatic || msg.reason === "no_audio_yet" ? "voice_missing_phone" : (msg.reason === "tts_over_cap" ? "tts_over_cap" : "tts_failed"));
    barsBox.appendChild(fill(mk("warning-reason t-stack on-danger"), reasonKey));
  }

  const existingHangup = dom.screen.querySelector(".btn-hangup");
  if (existingHangup) {
    dom.screen.insertBefore(barsBox, existingHangup);
  } else {
    dom.screen.appendChild(barsBox);
  }
}

function handleFamilyAlert(msg) {
  if (!dom.familyContainer) return;
  while (dom.familyContainer.firstChild) {
    dom.familyContainer.removeChild(dom.familyContainer.firstChild);
  }

  const card = document.createElement("div");
  card.className = "family-card";

  const hdr = document.createElement("div");
  hdr.className = "family-card-hdr";

  hdr.appendChild(fill(document.createElement("span"), "family_title"));

  const tag = document.createElement("span");
  tag.className = "simulated-tag";
  tag.textContent = "SIMULATED";
  hdr.appendChild(tag);
  card.appendChild(hdr);

  const msgDiv = document.createElement("div");
  msgDiv.className = "family-card-msg";
  msgDiv.textContent = msg.message_en || msg.message;
  card.appendChild(msgDiv);
  if (msg.message_en && msg.message && msg.message !== msg.message_en) {
    const locDiv = document.createElement("div");
    locDiv.className = "family-card-loc";
    locDiv.textContent = msg.message;
    card.appendChild(locDiv);
  }

  dom.familyContainer.appendChild(card);
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    reset();
  } else if (msg.type === "risk") {
    if (msg.level === "danger") {
      if (currentScreen !== "danger" && currentScreen !== "safe") renderScreen("danger");
    } else if (msg.level === "careful") {
      if (currentScreen === "calm") renderScreen("careful");
    }
  } else if (msg.type === "warning_audio") {
    handleWarningAudio(msg, state);
  } else if (msg.type === "family_alert") {
    handleFamilyAlert(msg);
  }
}
