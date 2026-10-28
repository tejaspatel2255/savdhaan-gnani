import { fill } from "./i18n.js";

let dom = null;
let currentScore = 0;
let targetScore = 0;
let scoreAnimFrame = null;
let basePupilRadius = 46;

export function init(rootEl) {
  dom = {
    root: rootEl,
    svg: rootEl.querySelector(".eye-svg"),
    gauge: rootEl.querySelector(".eye-ring-gauge"),
    ticksGroup: rootEl.querySelector(".eye-ticks"),
    pupil: rootEl.querySelector(".eye-pupil"),
    scoreNum: rootEl.querySelector(".score-num"),
    levelBadge: rootEl.querySelector(".level-badge"),
    levelText: rootEl.querySelector(".level-text"),
    levelIcon: rootEl.querySelector(".level-icon"),
    stateLine: rootEl.querySelector(".state-line"),
    vignette: document.getElementById("vignette-overlay"),
  };
  renderTicks();
  setEyeState("idle");
  updateLevelUI("calm", 0);
}

export function reset() {
  currentScore = 0;
  targetScore = 0;
  if (scoreAnimFrame) cancelAnimationFrame(scoreAnimFrame);
  if (dom && dom.scoreNum) {
    dom.scoreNum.textContent = "00";
    dom.gauge.style.strokeDashoffset = "1068";
    updateTicks(0);
    setEyeState("idle");
    updateLevelUI("calm", 0);
  }
}

function renderTicks() {
  if (!dom.ticksGroup) return;
  while (dom.ticksGroup.firstChild) dom.ticksGroup.removeChild(dom.ticksGroup.firstChild);
  const svgNS = "http://www.w3.org/2000/svg";
  for (let i = 0; i < 60; i++) {
    const angle = (i * 6 - 90) * (Math.PI / 180);
    const line = document.createElementNS(svgNS, "line");
    line.setAttribute("x1", Math.round(200 + 186 * Math.cos(angle)));
    line.setAttribute("y1", Math.round(200 + 186 * Math.sin(angle)));
    line.setAttribute("x2", Math.round(200 + 196 * Math.cos(angle)));
    line.setAttribute("y2", Math.round(200 + 196 * Math.sin(angle)));
    line.setAttribute("data-idx", String(i));
    dom.ticksGroup.appendChild(line);
  }
}

function updateTicks(score) {
  if (!dom.ticksGroup) return;
  const activeCount = Math.round((score / 100) * 60);
  const lines = dom.ticksGroup.querySelectorAll("line");
  lines.forEach((line, idx) => {
    line.classList.toggle("active", idx < activeCount);
  });
}

function animateScore(toScore) {
  targetScore = toScore;
  const startScore = currentScore;
  const startTime = performance.now();
  const duration = 400;

  if (scoreAnimFrame) cancelAnimationFrame(scoreAnimFrame);

  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    const val = Math.round(startScore + (targetScore - startScore) * ease);
    dom.scoreNum.textContent = String(val).padStart(2, "0");
    const offset = 1068 * (1 - val / 100);
    dom.gauge.style.strokeDashoffset = String(offset);
    updateTicks(val);

    if (progress < 1) {
      scoreAnimFrame = requestAnimationFrame(step);
    } else {
      currentScore = targetScore;
    }
  }
  scoreAnimFrame = requestAnimationFrame(step);
}

function setEyeState(state) {
  if (!dom.svg) return;
  dom.svg.setAttribute("data-state", state);
  if (state === "idle") {
    basePupilRadius = 46;
    fill(dom.stateLine, "state_idle");
  } else if (state === "listening") {
    basePupilRadius = 46;
    fill(dom.stateLine, "state_listening");
  } else if (state === "careful") {
    basePupilRadius = 42;
  } else if (state === "danger") {
    basePupilRadius = 32;
    if (dom.vignette) {
      dom.vignette.classList.add("active");
      setTimeout(() => dom.vignette.classList.remove("active"), 350);
    }
  } else if (state === "ended") {
    fill(dom.stateLine, "state_ended");
  }
  dom.pupil.setAttribute("r", String(basePupilRadius));
}

function updateLevelUI(level, score) {
  dom.levelBadge.setAttribute("data-level", level);
  const svgNS = "http://www.w3.org/2000/svg";
  while (dom.levelIcon.firstChild) dom.levelIcon.removeChild(dom.levelIcon.firstChild);
  if (level === "careful") {
    const poly = document.createElementNS(svgNS, "polygon");
    poly.setAttribute("points", "8,1 15,15 1,15");
    const dot = document.createElementNS(svgNS, "circle");
    dot.setAttribute("cx", "8");
    dot.setAttribute("cy", "11");
    dot.setAttribute("r", "1");
    dot.setAttribute("fill", "var(--night-3)");
    dom.levelIcon.appendChild(poly);
    dom.levelIcon.appendChild(dot);
  } else if (level === "danger") {
    const oct = document.createElementNS(svgNS, "polygon");
    oct.setAttribute("points", "5,1 11,1 15,5 15,11 11,15 5,15 1,11 1,5");
    dom.levelIcon.appendChild(oct);
  } else {
    const c1 = document.createElementNS(svgNS, "circle");
    c1.setAttribute("cx", "8");
    c1.setAttribute("cy", "8");
    c1.setAttribute("r", "6");
    const c2 = document.createElementNS(svgNS, "circle");
    c2.setAttribute("cx", "8");
    c2.setAttribute("cy", "8");
    c2.setAttribute("r", "2");
    c2.setAttribute("fill", "var(--night-3)");
    dom.levelIcon.appendChild(c1);
    dom.levelIcon.appendChild(c2);
  }
  fill(dom.levelText, `level_${level}`);
}

export function handle(msg, state) {
  if (msg.type === "session") {
    if (msg.state === "listening") setEyeState("listening");
    if (msg.state === "ended") setEyeState("ended");
  } else if (msg.type === "segment_processing") {
    if (dom.svg.getAttribute("data-state") !== "ended") {
      setEyeState("processing");
      setTimeout(() => {
        const backState = state.level === "danger" ? "danger" : (state.level === "careful" ? "careful" : "listening");
        setEyeState(backState);
      }, 120);
    }
  } else if (msg.type === "risk") {
    animateScore(msg.score);
    updateLevelUI(msg.level, msg.score);
    if (msg.level === "danger") setEyeState("danger");
    else if (msg.level === "careful" && dom.svg.getAttribute("data-state") !== "danger") setEyeState("careful");
  } else if (msg.type === "audio_level") {
    if (dom.svg.getAttribute("data-state") !== "ended") {
      const r = Math.min(basePupilRadius + (msg.rms || 0) * 10, basePupilRadius + 10);
      dom.pupil.setAttribute("r", String(r.toFixed(1)));
    }
  }
}
