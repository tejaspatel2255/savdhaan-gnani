import { t } from "./strings.js";

let dom = null;
const allHits = [];
const catCounts = {};

const ICONS = {
  authority: '<path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"/>',
  threat: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
  secrecy: '<path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>',
  urgency: '<path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>',
  payment: '<path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>',
  credentials: '<path d="M12.65 10C11.83 7.67 9.61 6 7 6c-3.31 0-6 2.69-6 6s2.69 6 6 6c2.61 0 4.83-1.67 5.65-4H17v4h4v-4h2v-4H12.65zM7 14c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"/>',
  remote_app: '<path d="M20 18c1.1 0 1.99-.9 1.99-2L22 6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"/>',
  lottery: '<path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.65-.5-.65C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76V8h2v.76L15.38 12 17 10.83 14.92 8H20v6z"/>',
  dampener: '<path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>',
};

export function init(rootEl) {
  dom = {
    root: rootEl,
    list: rootEl.querySelector(".why-list"),
    empty: rootEl.querySelector(".why-empty"),
    footer: rootEl.querySelector(".why-footer"),
  };
  if (dom.empty) dom.empty.textContent = t("why_empty");
  renderFooter();
}

function renderFooter() {
  if (!dom.footer) return;
  const cats = ["threat", "secrecy", "urgency", "payment", "credentials", "remote_app"];
  let html = "";
  for (const c of cats) {
    const count = catCounts[c] || 0;
    let dots = "";
    for (let i = 0; i < 4; i++) {
      dots += `<span class="meter-dot ${i < count ? 'active' : ''}"></span>`;
    }
    html += `
      <div class="meter-group">
        <span>${c.slice(0, 4)}</span>
        <span class="meter-dots">${dots}</span>
      </div>
    `;
  }
  dom.footer.innerHTML = html;
}

export function handle(msg, state) {
  if (msg.type === "session" && msg.state === "listening") {
    allHits.length = 0;
    for (const k in catCounts) delete catCounts[k];
    if (dom.list) {
      dom.list.innerHTML = "";
      if (dom.empty) dom.list.appendChild(dom.empty);
    }
    renderFooter();
  } else if (msg.type === "risk") {
    if (!msg.hits || !msg.hits.length) return;
    if (dom.empty && dom.empty.parentNode) dom.empty.remove();

    for (const h of msg.hits) {
      allHits.unshift(h);
      catCounts[h.category] = (catCounts[h.category] || 0) + 1;

      const row = document.createElement("div");
      row.className = "why-row";

      const iconPath = ICONS[h.category] || (h.polarity === "dampen" ? ICONS.dampener : ICONS.threat);
      const isRaise = h.polarity !== "dampen";
      const sign = isRaise ? "+" : "-";
      let pillCls = "dampen";
      if (isRaise) pillCls = h.weight >= 20 ? "raise-high" : "raise";

      row.innerHTML = `
        <div class="why-row-left">
          <svg class="why-cat-icon" viewBox="0 0 24 24">${iconPath}</svg>
          <div class="why-labels">
            <span class="why-label-hi">${h.label_hi || ""}</span>
            <span class="why-label-en">${h.label_en || h.category}</span>
          </div>
        </div>
        <div class="why-matched">"${h.matched}"</div>
        <span class="why-weight-pill ${pillCls}">${sign}${Math.abs(h.weight)}</span>
      `;
      dom.list.insertBefore(row, dom.list.firstChild);
    }
    renderFooter();
  }
}
