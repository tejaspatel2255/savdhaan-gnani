import { t } from "./strings.js";

let dom = null;
let userScrolledUp = false;
const segmentSlips = new Map();

export function init(rootEl) {
  dom = {
    root: rootEl,
    scroll: rootEl.querySelector(".tape-scroll"),
    empty: rootEl.querySelector(".tape-empty"),
    btnJump: rootEl.querySelector("#btn-jump-latest"),
  };

  if (dom.empty) dom.empty.textContent = t("tape_empty");
  if (dom.btnJump) {
    dom.btnJump.textContent = t("tape_jump_latest");
    dom.btnJump.addEventListener("click", () => {
      userScrolledUp = false;
      dom.btnJump.classList.remove("visible");
      scrollToBottom();
    });
  }

  if (dom.scroll) {
    dom.scroll.addEventListener("scroll", () => {
      const distanceToBottom = dom.scroll.scrollHeight - dom.scroll.scrollTop - dom.scroll.clientHeight;
      userScrolledUp = distanceToBottom > 60;
      dom.btnJump.classList.toggle("visible", userScrolledUp);
    });
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

function highlightText(text, hits) {
  if (!hits || !hits.length) return text;
  let result = text;
  for (const h of hits) {
    if (!h.matched) continue;
    const regex = new RegExp(`(${h.matched.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "iu");
    const m = regex.exec(result);
    if (!m) continue;

    let cls = "hit-raise";
    if (h.polarity === "dampen") cls = "hit-dampen";
    else if (h.weight >= 20) cls = "hit-high-raise";

    const mark = `<mark class="${cls}">${m[1]}</mark>`;
    result = result.substring(0, m.index) + mark + result.substring(m.index + m[1].length);
  }
  return result;
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    segmentSlips.clear();
    if (dom.scroll) {
      dom.scroll.innerHTML = "";
      if (dom.empty) dom.scroll.appendChild(dom.empty);
    }
  } else if (msg.type === "transcript") {
    if (dom.empty && dom.empty.parentNode) dom.empty.remove();

    const slip = document.createElement("article");
    slip.className = "tape-slip";
    slip.dataset.segmentIndex = msg.segment_index;

    const isMock = state.mode === "mock";
    const latencyHtml = (msg.stt_latency_ms != null && !isMock)
      ? `<span class="slip-latency">${msg.stt_latency_ms} ms</span>`
      : "";

    slip.innerHTML = `
      <div class="slip-header">
        <span class="slip-time">${formatTime(msg.t)}</span>
        ${latencyHtml}
      </div>
      <div class="slip-text" lang="${state.lang || 'hi'}">${msg.text}</div>
      <div class="slip-chips"></div>
    `;

    dom.scroll.appendChild(slip);
    segmentSlips.set(msg.segment_index, {
      el: slip,
      text: msg.text,
      chipsContainer: slip.querySelector(".slip-chips"),
      textEl: slip.querySelector(".slip-text"),
    });

    scrollToBottom();
  } else if (msg.type === "risk") {
    const slipData = segmentSlips.get(msg.segment_index);
    if (!slipData) return;

    if (msg.hits && msg.hits.length > 0) {
      slipData.textEl.innerHTML = highlightText(slipData.text, msg.hits);
      let chipsHtml = "";
      for (const h of msg.hits) {
        const sign = h.polarity === "dampen" ? "-" : "+";
        const polCls = h.polarity === "dampen" ? "dampen" : "raise";
        chipsHtml += `
          <span class="slip-chip">
            <span class="chip-label-hi">${h.label_hi || ""}</span>
            <span class="chip-label-en">${h.label_en || ""}</span>
            <span class="chip-weight ${polCls}">${sign}${Math.abs(h.weight)}</span>
          </span>
        `;
      }
      slipData.chipsContainer.innerHTML = chipsHtml;
    }
    scrollToBottom();
  }
}
