import { t } from "./strings.js";
import { playTwoToneBeep } from "./beep.js";

let dom = null;
let currentScreen = "calm";
let audioElement = null;
let playedSessions = new Set();

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
    const title = document.createElement("div");
    title.className = "phone-calm-title";
    title.textContent = t("phone_calm_title");
    dom.screen.appendChild(title);

    const sub = document.createElement("div");
    sub.className = "phone-calm-sub";
    sub.textContent = t("phone_calm_sub");
    dom.screen.appendChild(sub);
  } else if (stateName === "careful") {
    const banner = document.createElement("div");
    banner.className = "phone-careful-banner";
    banner.textContent = t("phone_careful");
    dom.screen.appendChild(banner);
  } else if (stateName === "danger") {
    const title = document.createElement("div");
    title.className = "danger-card-title";
    title.textContent = t("phone_danger_title");
    dom.screen.appendChild(title);

    const lines = document.createElement("div");
    lines.className = "danger-lines";

    const linesData = [
      { hi: t("phone_danger_line1_hi"), en: t("phone_danger_line1_en") },
      { hi: t("phone_danger_line2_hi"), en: t("phone_danger_line2_en") },
      { hi: t("phone_danger_line3_hi"), en: t("phone_danger_line3_en") },
    ];

    for (const l of linesData) {
      const box = document.createElement("div");
      const hiSpan = document.createElement("div");
      hiSpan.className = "danger-line-hi";
      hiSpan.textContent = l.hi;
      box.appendChild(hiSpan);

      const enSpan = document.createElement("div");
      enSpan.className = "danger-line-en";
      enSpan.textContent = l.en;
      box.appendChild(enSpan);
      lines.appendChild(box);
    }
    dom.screen.appendChild(lines);

    const btn = document.createElement("button");
    btn.className = "btn-hangup";
    btn.textContent = t("phone_hangup_btn");
    btn.addEventListener("click", () => renderScreen("safe"));
    dom.screen.appendChild(btn);
  } else if (stateName === "safe") {
    const safeTag = document.createElement("div");
    safeTag.className = "phone-ended-safe";
    safeTag.textContent = t("phone_ended_safe");
    dom.screen.appendChild(safeTag);
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
    playTwoToneBeep();
    const reasonSpan = document.createElement("div");
    reasonSpan.className = "warning-reason";
    reasonSpan.textContent = t("tts_failed");
    barsBox.appendChild(reasonSpan);
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

  const titleSpan = document.createElement("span");
  titleSpan.textContent = "परिवार को सूचना";
  hdr.appendChild(titleSpan);

  const tag = document.createElement("span");
  tag.className = "simulated-tag";
  tag.textContent = "SIMULATED";
  hdr.appendChild(tag);
  card.appendChild(hdr);

  const msgDiv = document.createElement("div");
  msgDiv.className = "family-card-msg";
  msgDiv.textContent = msg.message;
  card.appendChild(msgDiv);

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
