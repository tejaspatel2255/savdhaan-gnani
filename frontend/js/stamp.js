import { t } from "./strings.js";
import { fill, textLoc, getLocal } from "./i18n.js";

let root = null;
let currentStampEl = null;
let shrinkTimer = null;
let tapeScrollEl = null;
let pinnedEl = null;

export function init(rootEl) {
  root = rootEl;
  tapeScrollEl = document.querySelector("#col-tape .tape-scroll");

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && currentStampEl) {
      dismissBigStamp();
    }
  });
}

export function reset() {
  if (shrinkTimer) clearTimeout(shrinkTimer);
  shrinkTimer = null;
  if (currentStampEl && currentStampEl.parentNode) {
    currentStampEl.parentNode.removeChild(currentStampEl);
  }
  currentStampEl = null;
  if (pinnedEl && pinnedEl.parentNode) {
    pinnedEl.parentNode.removeChild(pinnedEl);
  }
  pinnedEl = null;
  document.body.classList.remove("shake-page");
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function dismissBigStamp(alertTime = null) {
  if (shrinkTimer) clearTimeout(shrinkTimer);
  shrinkTimer = null;

  if (currentStampEl && currentStampEl.parentNode) {
    currentStampEl.parentNode.removeChild(currentStampEl);
  }
  currentStampEl = null;

  if (alertTime !== null && tapeScrollEl && !pinnedEl) {
    pinnedEl = document.createElement("div");
    pinnedEl.className = "pinned-stamp";

    pinnedEl.appendChild(fill(document.createElement("span"), "stamp_pinned_prefix"));

    const timeSpan = document.createElement("span");
    timeSpan.className = "pinned-stamp-mono";
    timeSpan.textContent = ` ${formatTime(alertTime)}`;
    pinnedEl.appendChild(timeSpan);

    tapeScrollEl.insertBefore(pinnedEl, tapeScrollEl.firstChild);
  }
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    reset();
  } else if (msg.type === "alert") {
    if (currentStampEl) return;

    // Trigger page shake & flash
    document.body.classList.add("shake-page");
    setTimeout(() => document.body.classList.remove("shake-page"), 240);

    const flash = document.createElement("div");
    flash.className = "stamp-flash";
    document.body.appendChild(flash);
    setTimeout(() => {
      if (flash.parentNode) flash.parentNode.removeChild(flash);
    }, 130);

    const stamp = document.createElement("div");
    stamp.className = "rubber-stamp";
    stamp.setAttribute("role", "alert");

    const title = document.createElement("div");
    title.className = "stamp-title";
    title.textContent = t("stamp_title");
    stamp.appendChild(title);

    const sub = document.createElement("div");
    sub.className = "stamp-sub";
    sub.textContent = t("stamp_sub");
    stamp.appendChild(sub);

    const loc = document.createElement("div");
    loc.className = "stamp-loc";
    loc.setAttribute("lang", getLocal());
    loc.textContent = `${textLoc("stamp_title")} · ${textLoc("stamp_sub")}`;
    stamp.appendChild(loc);

    const alertTime = msg.t || 0;
    stamp.addEventListener("click", () => dismissBigStamp(alertTime));

    root.appendChild(stamp);
    currentStampEl = stamp;

    shrinkTimer = setTimeout(() => {
      dismissBigStamp(alertTime);
    }, 2500);
  }
}
