import { t } from "./strings.js";
import { fill, getLocal } from "./i18n.js";
import { getGloss } from "./api.js";

let dom = null;
let userScrolledUp = false;
const segmentSlips = new Map();
let gloss = {};

function localLabel(h) {
  return getLocal() === "gu" && h.label_gu ? h.label_gu : (h.label_hi || "");
}

export function init(rootEl) {
  dom = {
    root: rootEl,
    scroll: rootEl.querySelector(".tape-scroll"),
    empty: rootEl.querySelector(".tape-empty"),
    btnJump: rootEl.querySelector("#btn-jump-latest"),
  };

  if (dom.empty) fill(dom.empty, "tape_empty");
  getGloss().then((g) => { gloss = g || {}; });
  if (dom.btnJump) {
    dom.btnJump.textContent = t("tape_jump_latest");
    dom.btnJump.addEventListener("click", () => { userScrolledUp = false; dom.btnJump.classList.remove("visible"); scrollToBottom(); });
  }

  if (dom.scroll) {
    dom.scroll.addEventListener("scroll", () => {
      userScrolledUp = (dom.scroll.scrollHeight - dom.scroll.scrollTop - dom.scroll.clientHeight) > 60;
      dom.btnJump.classList.toggle("visible", userScrolledUp);
    });
  }
}

export function reset() {
  segmentSlips.clear();
  userScrolledUp = false;
  if (dom && dom.scroll) {
    while (dom.scroll.firstChild) {
      dom.scroll.removeChild(dom.scroll.firstChild);
    }
    if (dom.empty) dom.scroll.appendChild(dom.empty);
    if (dom.btnJump) dom.btnJump.classList.remove("visible");
  }
}

function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function scrollToBottom() {
  if (userScrolledUp || !dom.scroll) return;
  dom.scroll.scrollTop = dom.scroll.scrollHeight;
}

function renderHighlightedText(container, text, hits) {
  while (container.firstChild) container.removeChild(container.firstChild);

  if (!hits || !hits.length) {
    container.textContent = text;
    return;
  }

  // Find first matching hit
  let firstMatch = null;
  let matchHit = null;

  for (const h of hits) {
    if (!h.matched) continue;
    const idx = text.toLowerCase().indexOf(h.matched.toLowerCase());
    if (idx !== -1 && (firstMatch === null || idx < firstMatch.index)) {
      firstMatch = { index: idx, length: h.matched.length };
      matchHit = h;
    }
  }

  if (!firstMatch) {
    container.textContent = text;
    return;
  }

  const before = text.substring(0, firstMatch.index);
  const matched = text.substring(firstMatch.index, firstMatch.index + firstMatch.length);
  const after = text.substring(firstMatch.index + firstMatch.length);

  if (before) container.appendChild(document.createTextNode(before));

  const mark = document.createElement("mark");
  let cls = "hit-raise";
  if (matchHit.polarity === "dampen") cls = "hit-dampen";
  else if (matchHit.weight >= 20) cls = "hit-high-raise";
  mark.className = cls;
  mark.textContent = matched;
  container.appendChild(mark);

  if (after) container.appendChild(document.createTextNode(after));
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    reset();
  } else if (msg.type === "transcript") {
    if (dom.empty && dom.empty.parentNode) dom.empty.remove();

    const slip = document.createElement("article");
    slip.className = "tape-slip";
    slip.dataset.segmentIndex = String(msg.segment_index);

    const hdr = document.createElement("div");
    hdr.className = "slip-header";

    const timeSpan = document.createElement("span");
    timeSpan.className = "slip-time";
    timeSpan.textContent = formatTime(msg.t);
    hdr.appendChild(timeSpan);

    if (msg.stt_latency_ms != null && state.mode !== "mock") {
      const latSpan = document.createElement("span");
      latSpan.className = "slip-latency";
      latSpan.textContent = `${msg.stt_latency_ms} ms`;
      hdr.appendChild(latSpan);
    }
    slip.appendChild(hdr);

    const textEl = document.createElement("div");
    textEl.className = "slip-text";
    textEl.setAttribute("lang", state.lang || "hi");
    textEl.textContent = msg.text;
    slip.appendChild(textEl);

    let glossEl = null;
    const english = gloss[msg.text];
    if (english) {
      glossEl = document.createElement("div");
      glossEl.className = "slip-gloss";
      glossEl.textContent = `English: ${english}`;
      slip.appendChild(glossEl);
    } else if (state.mode === "mic") {
      glossEl = document.createElement("div");
      glossEl.className = "slip-gloss";
      glossEl.textContent = t("words_none_detected");
      slip.appendChild(glossEl);
    }

    const chipsEl = document.createElement("div");
    chipsEl.className = "slip-chips";
    slip.appendChild(chipsEl);

    dom.scroll.appendChild(slip);
    segmentSlips.set(msg.segment_index, { text: msg.text, textEl, chipsEl, glossEl });
    scrollToBottom();
  } else if (msg.type === "risk") {
    const slipData = segmentSlips.get(msg.segment_index);
    if (!slipData) return;

    if (msg.hits && msg.hits.length > 0) {
      renderHighlightedText(slipData.textEl, slipData.text, msg.hits);
      while (slipData.chipsEl.firstChild) {
        slipData.chipsEl.removeChild(slipData.chipsEl.firstChild);
      }

      if (slipData.glossEl && !gloss[slipData.text] && state.mode === "mic") {
        const labels = [...new Set(msg.hits.map(h => h.label_en || h.category).filter(Boolean))];
        slipData.glossEl.textContent = labels.length ? `Detected: ${labels.join(", ")}` : t("words_none_detected");
      }

      for (const h of msg.hits) {
        const chip = document.createElement("span");
        chip.className = "slip-chip";

        const labelEn = document.createElement("span");
        labelEn.className = "chip-label-en";
        labelEn.textContent = h.label_en || h.category || "";
        chip.appendChild(labelEn);

        const labelLoc = document.createElement("span");
        labelLoc.className = "chip-label-loc";
        labelLoc.setAttribute("lang", getLocal());
        labelLoc.textContent = localLabel(h);
        chip.appendChild(labelLoc);

        const weight = document.createElement("span");
        const pol = h.polarity === "dampen" ? "dampen" : "raise";
        weight.className = `chip-weight ${pol}`;
        weight.textContent = `${h.polarity === "dampen" ? "-" : "+"}${Math.abs(h.weight)}`;
        chip.appendChild(weight);

        slipData.chipsEl.appendChild(chip);
      }
    }
    scrollToBottom();
  }
}
