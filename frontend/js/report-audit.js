/**
 * Section D through G builders for Savdhaan Evaluation Khata.
 */

import { el, renderDotPlot } from "./report-views.js";

export function renderSectionsDtoG(root, data) {
  // SECTION D: Time to Alert Dot Plot
  const secD = el("section", "khata-section");
  const headD = el("div", "section-head");
  headD.appendChild(el("h2", null, "चेतावनी समय (0 से 60 सेकंड)"));
  headD.appendChild(el("span", "sub", "Section D · Time to Alert on Detected Scam Calls"));
  secD.appendChild(headD);

  const plotBox = el("div", "dot-plot-container");
  const plotSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const scamCalls = (data.calls || []).filter((c) => c.label === "scam");
  renderDotPlot(plotSvg, scamCalls);
  plotBox.appendChild(plotSvg);
  secD.appendChild(plotBox);
  root.appendChild(secD);

  // SECTION E: STT Latency
  const secE = el("section", "khata-section");
  const headE = el("div", "section-head");
  headE.appendChild(el("h2", null, "वाक-पहचान विलंब (Latency)"));
  headE.appendChild(el("span", "sub", "Section E · Prisma STT Segment Latency Distribution"));
  secE.appendChild(headE);

  const lData = data.latency_ms || {};
  const gridE = el("div", "headline-grid");
  const boxP50 = el("div", "ledger-card");
  boxP50.appendChild(el("div", "card-label", "P50 विलंब · MEDIAN LATENCY"));
  boxP50.appendChild(el("div", "card-num", lData.p50 != null ? `${lData.p50} ms` : "N/A"));
  gridE.appendChild(boxP50);

  const boxP95 = el("div", "ledger-card");
  boxP95.appendChild(el("div", "card-label", "P95 विलंब · 95TH PERCENTILE"));
  boxP95.appendChild(el("div", "card-num", lData.p95 != null ? `${lData.p95} ms` : "N/A"));
  gridE.appendChild(boxP95);
  secE.appendChild(gridE);
  root.appendChild(secE);

  // SECTION F: Misses and False Alarms
  const secF = el("section", "khata-section");
  const headF = el("div", "section-head");
  headF.appendChild(el("h2", null, "त्रुटि समीक्षा (चूक एवं झूठा अलार्म)"));
  headF.appendChild(el("span", "sub", "Section F · Audit of Missed Scams & False Alarms"));
  secF.appendChild(headF);

  const auditList = el("div", "audit-list");
  const anomalousCalls = (data.calls || []).filter((c) => (c.label === "scam" && !c.alerted) || (c.label === "legit" && c.alerted));
  if (anomalousCalls.length === 0) {
    auditList.appendChild(el("div", "card-ci", "कोई चूक या झूठा अलार्म नहीं मिला · Zero misses or false alarms."));
  } else {
    anomalousCalls.forEach((c) => {
      const card = el("div", "audit-card");
      const hRow = el("div", "audit-header");
      const typeText = c.label === "scam" ? "MISSED SCAM (FN)" : "FALSE ALARM (FP)";
      hRow.appendChild(el("span", "danger-text", `${typeText}: ${c.id}`));
      hRow.appendChild(el("span", null, `Max score: ${c.max_score} (${c.max_level})`));
      card.appendChild(hRow);

      const dBox = el("div", "audit-dialogue");
      (c.segments || []).forEach((seg) => dBox.appendChild(el("div", null, `[${seg.t.toFixed(1)}s] ${seg.text}`)));
      card.appendChild(dBox);
      auditList.appendChild(card);
    });
  }
  secF.appendChild(auditList);
  root.appendChild(secF);

  // SECTION G: Limitations
  const secG = el("section", "khata-section");
  const headG = el("div", "section-head");
  headG.appendChild(el("h2", null, "सीमाएं एवं प्रकटीकरण"));
  headG.appendChild(el("span", "sub", "Section G · Limitations & Methodology Disclosures"));
  secG.appendChild(headG);

  const uList = el("ul", "limitations-list");
  (data.limitations || []).forEach((item) => uList.appendChild(el("li", null, item)));
  const tScoring = data.test_scoring || {};
  const changedStr = tScoring.rules_changed_since_first ? "YES (WARNING: rules modified)" : "NO (rules unchanged)";
  uList.appendChild(el("li", null, `Test split scoring disclosure: scored ${tScoring.times_scored || 0} time(s); rules changed since first scoring: ${changedStr}.`));
  secG.appendChild(uList);
  root.appendChild(secG);
}
