/**
 * words.js — "Try your own words" and "Words we listen for" panels.
 * Uses POST /api/analyze and GET /api/rules/summary. No Gnani credits.
 */
import { t } from "./strings.js";
import { analyzeText, getRulesSummary } from "./api.js";

const SCAM_EXAMPLE = "आपके खाते को फ्रीज़ कर दिया जाएगा। OTP बताइए नहीं तो गिरफ्तारी होगी।";
const SAFE_EXAMPLE = "आपकी EMI की रसीद तैयार है। कोई कार्रवाई की ज़रूरत नहीं।";

let _analyzeEl = {};
let _pack = "hi_en";

export function init(pack = "hi_en") {
  _pack = pack;
  _initAnalyzePanel();
  _initRulesPanel();
}

export function setPack(lang) { _pack = lang === "gu-IN" ? "gu" : "hi_en"; }

// ── Analyze panel ──────────────────────────────────────────────────────────

function _initAnalyzePanel() {
  _toggleSetup("words-panel-header", "words-panel-body");
  _analyzeEl = {
    textarea: document.getElementById("words-textarea"),
    btnAnalyze: document.getElementById("words-btn-analyze"),
    btnScam: document.getElementById("words-btn-scam"),
    btnSafe: document.getElementById("words-btn-safe"),
    result: document.getElementById("words-result"),
  };
  if (_analyzeEl.btnScam) _analyzeEl.btnScam.addEventListener("click", () => { if (_analyzeEl.textarea) _analyzeEl.textarea.value = SCAM_EXAMPLE; });
  if (_analyzeEl.btnSafe) _analyzeEl.btnSafe.addEventListener("click", () => { if (_analyzeEl.textarea) _analyzeEl.textarea.value = SAFE_EXAMPLE; });
  if (_analyzeEl.btnAnalyze) _analyzeEl.btnAnalyze.addEventListener("click", _runAnalyze);
}

async function _runAnalyze() {
  const text = _analyzeEl.textarea && _analyzeEl.textarea.value.trim();
  if (!text) return;
  if (text.length > 2000) { _showResultError(t("words_too_long")); return; }
  if (_analyzeEl.btnAnalyze) _analyzeEl.btnAnalyze.disabled = true;
  _clearResult();
  try {
    const data = await analyzeText(text, _pack);
    _renderResult(text, data);
  } catch (err) {
    _showResultError(err.message || "Error");
  } finally {
    if (_analyzeEl.btnAnalyze) _analyzeEl.btnAnalyze.disabled = false;
  }
}

function _renderResult(originalText, data) {
  if (!_analyzeEl.result) return;
  _clearResult();
  const badge = document.createElement("span");
  badge.className = "words-score-badge";
  badge.dataset.level = data.level || "calm";
  badge.textContent = `${(data.level || "calm").toUpperCase()} · ${data.score ?? 0}/100`;
  const row = document.createElement("div"); row.className = "words-result-row"; row.appendChild(badge);
  _analyzeEl.result.appendChild(row);

  const textDiv = document.createElement("div");
  textDiv.className = "words-highlighted-text";
  _buildHighlight(textDiv, originalText, data.segments || []);
  _analyzeEl.result.appendChild(textDiv);

  const detRow = document.createElement("div"); detRow.className = "words-detected-row";
  const allHits = (data.segments || []).flatMap(s => (s.hits || []).filter(h => h.polarity === "raise"));
  const labels = [...new Set(allHits.map(h => h.label_en || h.category).filter(Boolean))];
  const lbl = document.createElement("span"); lbl.className = "words-detected-label"; lbl.textContent = t("words_detected_prefix");
  detRow.appendChild(lbl);
  if (!labels.length) {
    const none = document.createElement("span"); none.className = "words-none-detected"; none.textContent = t("words_none_detected");
    detRow.appendChild(none);
  } else {
    labels.forEach(l => { const c = document.createElement("span"); c.className = "words-chip"; c.textContent = l; detRow.appendChild(c); });
  }
  _analyzeEl.result.appendChild(detRow);
}

function _buildHighlight(container, text, segments) {
  const hits = segments.flatMap(s => s.hits || []).filter(h => h.matched);
  if (!hits.length) { container.textContent = text; return; }
  const tl = text.toLowerCase();
  let best = null;
  for (const h of hits) { const idx = tl.indexOf(h.matched.toLowerCase()); if (idx !== -1 && (!best || idx < best.idx)) best = { idx, len: h.matched.length, polarity: h.polarity, weight: h.weight || 0 }; }
  if (!best) { container.textContent = text; return; }
  if (best.idx > 0) container.appendChild(document.createTextNode(text.substring(0, best.idx)));
  const mark = document.createElement("mark");
  mark.className = best.polarity === "dampen" ? "hit-dampen" : best.weight >= 20 ? "hit-high-raise" : "hit-raise";
  mark.textContent = text.substring(best.idx, best.idx + best.len);
  container.appendChild(mark);
  if (best.idx + best.len < text.length) container.appendChild(document.createTextNode(text.substring(best.idx + best.len)));
}

function _clearResult() { if (_analyzeEl.result) while (_analyzeEl.result.firstChild) _analyzeEl.result.removeChild(_analyzeEl.result.firstChild); }

function _showResultError(msg) {
  _clearResult();
  if (!_analyzeEl.result) return;
  const p = document.createElement("p"); p.style.color = "var(--danger,#A82A14)"; p.textContent = msg;
  _analyzeEl.result.appendChild(p);
}

// ── Rules panel ────────────────────────────────────────────────────────────

function _initRulesPanel() {
  const header = document.getElementById("rules-panel-header");
  const body = document.getElementById("rules-panel-body");
  if (!header || !body) return;
  let loaded = false;
  _toggleSetup("rules-panel-header", "rules-panel-body", () => { if (!loaded) { loaded = true; _loadRules(body); } });
}

async function _loadRules(body) {
  const loading = body.querySelector(".words-panel-loading");
  try {
    const data = await getRulesSummary();
    if (loading) loading.remove();
    const logic = document.createElement("p"); logic.className = "rules-logic"; logic.textContent = data.logic_en || "";
    body.appendChild(logic);
    const grid = document.createElement("div"); grid.className = "rules-category-grid";
    for (const cat of (data.categories || [])) {
      const card = document.createElement("div"); card.className = "rules-category-card";
      const lbl = document.createElement("div"); lbl.className = "rules-cat-label"; lbl.textContent = cat.label_en || cat.id; card.appendChild(lbl);
      if (cat.label_hi) { const loc = document.createElement("div"); loc.className = "rules-cat-local"; loc.setAttribute("lang","hi"); loc.textContent = cat.label_hi; card.appendChild(loc); }
      const ul = document.createElement("ul"); ul.className = "rules-cat-examples";
      (cat.examples || []).slice(0, 4).forEach(ex => { const li = document.createElement("li"); li.textContent = ex; ul.appendChild(li); });
      card.appendChild(ul); grid.appendChild(card);
    }
    body.appendChild(grid);
  } catch (_) { if (loading) loading.textContent = t("rules_unavailable"); }
}

// ── Shared helper ──────────────────────────────────────────────────────────

function _toggleSetup(headerId, bodyId, onOpen) {
  const header = document.getElementById(headerId);
  const body = document.getElementById(bodyId);
  if (!header || !body) return;
  header.setAttribute("role", "button"); header.setAttribute("tabindex", "0"); header.setAttribute("aria-expanded", "false");
  const toggle = () => {
    const open = header.getAttribute("aria-expanded") !== "true";
    header.setAttribute("aria-expanded", open ? "true" : "false");
    body.classList.toggle("open", open);
    const ch = header.querySelector(".words-panel-chevron"); if (ch) ch.textContent = open ? "▲" : "▼";
    if (open && onOpen) onOpen();
  };
  header.addEventListener("click", toggle);
  header.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
}

