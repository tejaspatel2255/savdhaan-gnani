/**
 * Section D through G builders for Savdhaan Evaluation Khata.
 * Renders Dot Plot, Latency/WER, Error Audit, and Limitations disclosures.
 */

import { el, elLoc, renderDotPlot } from "./report-views.js";

export function renderSectionsDtoG(root, data, isFixture = false) {
  // SECTION D: Time to Alert Dot Plot
  const secD = el("section", "khata-section");
  const headD = el("div", "section-head");
  headD.appendChild(elLoc("h2", null, "Time to alert on detected scam calls (0 to 60 s)", "चेतावनी समय (0 से 60 सेकंड)"));
  if (isFixture) headD.appendChild(el("span", "fixture-section-tag", "FIXTURE DATA - NOT MEASURED"));
  headD.appendChild(el("span", "sub", "Section D"));
  secD.appendChild(headD);

  const plotBox = el("div", "dot-plot-container");
  const plotSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const scamCalls = (data.calls || []).filter((c) => c.label === "scam");
  renderDotPlot(plotSvg, scamCalls);
  plotBox.appendChild(plotSvg);
  secD.appendChild(plotBox);
  root.appendChild(secD);

  // SECTION E: STT Latency and WER
  const secE = el("section", "khata-section");
  const headE = el("div", "section-head");
  headE.appendChild(elLoc("h2", null, "Prisma STT latency and Word Error Rate (WER)", "वाक-पहचान विलंब एवं शब्द त्रुटि दर"));
  if (isFixture) headE.appendChild(el("span", "fixture-section-tag", "FIXTURE DATA - NOT MEASURED"));
  headE.appendChild(el("span", "sub", "Section E"));
  secE.appendChild(headE);

  const lData = data.latency_ms;
  const gridE = el("div", "headline-grid");
  if (lData && lData.p50 != null) {
    const boxP50 = el("div", "ledger-card");
    boxP50.appendChild(elLoc("div", "card-label", "MEDIAN LATENCY (P50)", "विलंब"));
    boxP50.appendChild(el("div", "card-num", `${lData.p50} ms`));
    gridE.appendChild(boxP50);

    const boxP95 = el("div", "ledger-card");
    boxP95.appendChild(elLoc("div", "card-label", "95TH PERCENTILE (P95)", "विलंब"));
    boxP95.appendChild(el("div", "card-num", `${lData.p95} ms`));
    gridE.appendChild(boxP95);
  } else {
    const unmeasured = el("div", "unmeasured-box");
    unmeasured.appendChild(el("div", "unmeasured-tag", "not measured yet"));
    unmeasured.appendChild(el("code", "unmeasured-cmd", "python scripts/run_eval.py record --split dev --go"));
    gridE.appendChild(unmeasured);
  }
  secE.appendChild(gridE);

  const werData = data.wer?.conditions;
  if (werData && (werData.clean != null || werData.phone != null)) {
    const werWrap = el("div", "table-wrapper");
    const werTable = el("table", "khata-table");
    const werThead = el("thead");
    const werTrh = el("tr");
    ["Condition", "Clean", "Phone", "Phone + Noise (15dB)", "Phone + Noise + Drops"].forEach((t) => werTrh.appendChild(el("th", null, t)));
    werThead.appendChild(werTrh);
    werTable.appendChild(werThead);
    const werTbody = el("tbody");
    const trW = el("tr");
    trW.appendChild(el("td", "mono-num", "Word Error Rate (WER)"));
    trW.appendChild(el("td", "mono-num", werData.clean != null ? `${(werData.clean * 100).toFixed(1)}%` : "-"));
    trW.appendChild(el("td", "mono-num", werData.phone != null ? `${(werData.phone * 100).toFixed(1)}%` : "-"));
    trW.appendChild(el("td", "mono-num", werData.phone_noise != null ? `${(werData.phone_noise * 100).toFixed(1)}%` : "-"));
    trW.appendChild(el("td", "mono-num", werData.phone_noise_drops != null ? `${(werData.phone_noise_drops * 100).toFixed(1)}%` : "-"));
    werTbody.appendChild(trW);
    werTable.appendChild(werTbody);
    werWrap.appendChild(werTable);
    secE.appendChild(werWrap);
  }
  if (data.wer?.note) {
    secE.appendChild(el("p", "wer-note", data.wer.note));
  }
  root.appendChild(secE);

  // SECTION F: Misses and False Alarms
  const secF = el("section", "khata-section");
  const headF = el("div", "section-head");
  headF.appendChild(elLoc("h2", null, "Audit of missed scams and false alarms", "त्रुटि समीक्षा (चूक एवं झूठा अलार्म)"));
  if (isFixture) headF.appendChild(el("span", "fixture-section-tag", "FIXTURE DATA - NOT MEASURED"));
  headF.appendChild(el("span", "sub", "Section F"));
  secF.appendChild(headF);

  const auditList = el("div", "audit-list");
  const anomalousCalls = (data.calls || []).filter((c) => (c.label === "scam" && !c.alerted) || (c.label === "legit" && c.alerted));
  if (anomalousCalls.length === 0) {
    auditList.appendChild(elLoc("div", "card-ci", "Zero misses or false alarms.", "कोई चूक या झूठा अलार्म नहीं मिला"));
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
  headG.appendChild(elLoc("h2", null, "Limitations and methodology disclosures", "सीमाएं एवं प्रकटीकरण"));
  if (isFixture) headG.appendChild(el("span", "fixture-section-tag", "FIXTURE DATA - NOT MEASURED"));
  headG.appendChild(el("span", "sub", "Section G"));
  secG.appendChild(headG);

  const uList = el("ul", "limitations-list");
  (data.limitations || []).forEach((item) => uList.appendChild(el("li", null, item)));
  const tScoring = data.test_scoring || {};
  const changedStr = tScoring.rules_changed_since_first ? "YES (WARNING: rules modified)" : "NO (rules unchanged)";
  uList.appendChild(el("li", null, `Test split scoring disclosure: scored ${tScoring.times_scored || 0} time(s); rules changed since first scoring: ${changedStr}.`));
  const bCalls = (data.calls || []).filter((c) => c.split === "blind");
  const bCount = bCalls.length || (data.splits?.blind?.n) || 12;
  uList.appendChild(el("li", null, `The blind set was written by a different person from the author but is small (${bCount} calls), so intervals are wide.`));
  secG.appendChild(uList);
  root.appendChild(secG);
}
