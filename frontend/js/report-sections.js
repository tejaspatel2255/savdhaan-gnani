/**
 * Section A through C builders for Savdhaan Evaluation Khata.
 */

import { el, renderPencilBar } from "./report-views.js";

export function renderSectionsAtoC(root, data, devSplit, testSplit) {
  // SECTION A: Headline Ledger
  const secA = el("section", "khata-section");
  const headA = el("div", "section-head");
  headA.appendChild(el("h2", null, "मुख्य आँकड़े (टेस्ट सेट)"));
  headA.appendChild(el("span", "sub", "Section A · Headline Performance on Frozen Test Split"));
  secA.appendChild(headA);

  const gridA = el("div", "headline-grid");
  const cRecall = el("div", "ledger-card");
  cRecall.appendChild(el("div", "card-label", "धोखा पहचान दर · RECALL"));
  const r1 = el("div", "card-stat-row");
  const tp = testSplit.tp ?? 0;
  const fn = testSplit.fn ?? 0;
  const recVal = testSplit.recall !== null ? `${(testSplit.recall * 100).toFixed(1)}%` : "N/A";
  r1.appendChild(el("span", "card-num", recVal));
  r1.appendChild(el("span", "card-counts", `${tp} of ${tp + fn} scam calls`));
  cRecall.appendChild(r1);
  if (testSplit.recall_ci95 && testSplit.recall_ci95[0] !== null) {
    cRecall.appendChild(el("div", "card-ci", `95% CI: [${testSplit.recall_ci95[0]}, ${testSplit.recall_ci95[1]}]`));
  }
  gridA.appendChild(cRecall);

  const cFar = el("div", "ledger-card danger-card");
  cFar.appendChild(el("div", "card-label", "झूठा अलार्म · FALSE ALARM RATE"));
  const r2 = el("div", "card-stat-row");
  const fp = testSplit.fp ?? 0;
  const tn = testSplit.tn ?? 0;
  const farVal = testSplit.false_alarm_rate !== null ? `${(testSplit.false_alarm_rate * 100).toFixed(1)}%` : "N/A";
  r2.appendChild(el("span", "card-num", farVal));
  r2.appendChild(el("span", "card-counts", `${fp} of ${fp + tn} legit calls`));
  cFar.appendChild(r2);
  if (testSplit.false_alarm_ci95 && testSplit.false_alarm_ci95[0] !== null) {
    cFar.appendChild(el("div", "card-ci", `95% CI: [${testSplit.false_alarm_ci95[0]}, ${testSplit.false_alarm_ci95[1]}]`));
  }
  gridA.appendChild(cFar);
  secA.appendChild(gridA);
  root.appendChild(secA);

  // SECTION B: Comparison Table
  const secB = el("section", "khata-section");
  const headB = el("div", "section-head");
  headB.appendChild(el("h2", null, "पहचान तुलना"));
  headB.appendChild(el("span", "sub", "Section B · Perfect Transcripts vs Real Prisma Recognition"));
  secB.appendChild(headB);

  const wrapB = el("div", "table-wrapper");
  const tB = el("table", "khata-table");
  const theadB = el("thead");
  const trhB = el("tr");
  ["Split", "Condition", "Scam Caught (TP/N)", "Recall", "False Alarms (FP/N)", "FAR", "F1"].forEach((t) => trhB.appendChild(el("th", null, t)));
  theadB.appendChild(trhB);
  tB.appendChild(theadB);

  const tbodyB = el("tbody");
  [{ name: "DEV", real: devSplit, ceil: devSplit.ceiling }, { name: "TEST (FROZEN)", real: testSplit, ceil: testSplit.ceiling }].forEach((item) => {
    const trC = el("tr");
    trC.appendChild(el("td", "mono-num", item.name));
    trC.appendChild(el("td", null, "Perfect Scripts (Ceiling)"));
    const cTp = item.ceil?.tp ?? "-";
    const cNscam = (item.ceil?.tp ?? 0) + (item.ceil?.fn ?? 0);
    trC.appendChild(el("td", "mono-num", `${cTp} / ${cNscam}`));
    trC.appendChild(el("td", "mono-num", item.ceil?.recall != null ? `${(item.ceil.recall * 100).toFixed(0)}%` : "-"));
    const cFp = item.ceil?.fp ?? "-";
    const cNlegit = (item.ceil?.fp ?? 0) + (item.ceil?.tn ?? 0);
    trC.appendChild(el("td", "mono-num", `${cFp} / ${cNlegit}`));
    trC.appendChild(el("td", "mono-num", item.ceil?.false_alarm_rate != null ? `${(item.ceil.false_alarm_rate * 100).toFixed(0)}%` : "-"));
    trC.appendChild(el("td", "mono-num", item.ceil?.f1 != null ? item.ceil.f1.toFixed(2) : "-"));
    tbodyB.appendChild(trC);

    const trR = el("tr");
    trR.appendChild(el("td", "mono-num", "↳ Real STT"));
    trR.appendChild(el("td", null, "Gnani Prisma (phone_noise)"));
    const rTp = item.real?.tp ?? "-";
    const rNscam = (item.real?.tp ?? 0) + (item.real?.fn ?? 0);
    trR.appendChild(el("td", "mono-num", `${rTp} / ${rNscam}`));
    trR.appendChild(el("td", "mono-num", item.real?.recall != null ? `${(item.real.recall * 100).toFixed(0)}%` : "No STT data"));
    const rFp = item.real?.fp ?? "-";
    const rNlegit = (item.real?.fp ?? 0) + (item.real?.tn ?? 0);
    trR.appendChild(el("td", "mono-num", `${rFp} / ${rNlegit}`));
    trR.appendChild(el("td", "mono-num", item.real?.false_alarm_rate != null ? `${(item.real.false_alarm_rate * 100).toFixed(0)}%` : "-"));
    trR.appendChild(el("td", "mono-num", item.real?.f1 != null ? item.real.f1.toFixed(2) : "-"));
    tbodyB.appendChild(trR);
  });
  tB.appendChild(tbodyB);
  wrapB.appendChild(tB);
  secB.appendChild(wrapB);
  root.appendChild(secB);

  // SECTION C: WER
  const secC = el("section", "khata-section");
  const headC = el("div", "section-head");
  headC.appendChild(el("h2", null, "शब्द त्रुटि दर (शोर स्थितियाँ)"));
  headC.appendChild(el("span", "sub", "Section C · Word Error Rate across Audio Conditions"));
  secC.appendChild(headC);

  const wrapC = el("div", "table-wrapper");
  const tC = el("table", "khata-table");
  const theadC = el("thead");
  const trhC = el("tr");
  ["Audio Condition", "Sample Clips", "WER (%)", "Error Bar (0-100%)"].forEach((t, i) => trhC.appendChild(el("th", i === 3 ? "bar-svg-cell" : null, t)));
  theadC.appendChild(trhC);
  tC.appendChild(theadC);

  const tbodyC = el("tbody");
  const werConds = (data.wer && data.wer.conditions) || {};
  [
    { key: "clean", label: "Clean Studio (24 kHz)" },
    { key: "phone", label: "Telephone Bandpass (8 kHz, μ-law)" },
    { key: "phone_noise", label: "Telephone + Street Noise (15 dB SNR)" },
    { key: "phone_noise_drops", label: "Telephone + Noise + 3 Packet Drops" },
  ].forEach((item) => {
    const row = el("tr");
    row.appendChild(el("td", null, item.label));
    const cData = werConds[item.key];
    const nVal = cData && cData.n != null ? cData.n : "-";
    const werVal = cData && cData.wer != null ? (cData.wer * 100).toFixed(1) : "-";
    row.appendChild(el("td", "mono-num", String(nVal)));
    row.appendChild(el("td", "mono-num", werVal !== "-" ? `${werVal}%` : "Not evaluated"));

    const svgCell = el("td", "bar-svg-cell");
    const svgElem = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    renderPencilBar(svgElem, werVal !== "-" ? parseFloat(werVal) : 0);
    svgCell.appendChild(svgElem);
    row.appendChild(svgCell);
    tbodyC.appendChild(row);
  });
  tC.appendChild(tbodyC);
  wrapC.appendChild(tC);
  secC.appendChild(wrapC);
  if (data.wer && data.wer.note) secC.appendChild(el("p", "card-ci", data.wer.note));
  root.appendChild(secC);
}
