/**
 * Section A through C builders for Savdhaan Evaluation Khata.
 */

import { el, elLoc, renderPencilBar } from "./report-views.js";

function renderMetricBlock(parent, title, sub, dataObj, emptyCommand) {
  const block = el("div", "headline-block");
  const bHead = el("div", "headline-block-head");
  bHead.appendChild(el("h3", "block-title", title));
  bHead.appendChild(el("span", "block-sub", sub));
  block.appendChild(bHead);

  if (!dataObj || dataObj.tp === null || dataObj.tp === undefined) {
    const unmeasured = el("div", "unmeasured-box");
    unmeasured.appendChild(el("div", "unmeasured-tag", "not measured yet"));
    if (emptyCommand) {
      unmeasured.appendChild(el("code", "unmeasured-cmd", emptyCommand));
    }
    block.appendChild(unmeasured);
    parent.appendChild(block);
    return;
  }

  const grid = el("div", "headline-grid");

  // Recall card
  const cRecall = el("div", "ledger-card");
  cRecall.appendChild(elLoc("div", "card-label", "RECALL", "धोखा पहचान दर"));
  const r1 = el("div", "card-stat-row");
  const tp = dataObj.tp ?? 0;
  const fn = dataObj.fn ?? 0;
  const recVal = dataObj.recall !== null ? `${(dataObj.recall * 100).toFixed(1)}%` : "N/A";
  r1.appendChild(el("span", "card-num", recVal));
  r1.appendChild(el("span", "card-counts", `${tp} of ${tp + fn} scam calls`));
  cRecall.appendChild(r1);
  if (dataObj.recall_ci95 && dataObj.recall_ci95[0] !== null) {
    cRecall.appendChild(el("div", "card-ci", `95% CI: [${dataObj.recall_ci95[0]}, ${dataObj.recall_ci95[1]}]`));
  }
  grid.appendChild(cRecall);

  // False Alarm card
  const cFar = el("div", "ledger-card danger-card");
  cFar.appendChild(elLoc("div", "card-label", "FALSE ALARM RATE", "झूठा अलार्म"));
  const r2 = el("div", "card-stat-row");
  const fp = dataObj.fp ?? 0;
  const tn = dataObj.tn ?? 0;
  const farVal = dataObj.false_alarm_rate !== null ? `${(dataObj.false_alarm_rate * 100).toFixed(1)}%` : "N/A";
  r2.appendChild(el("span", "card-num", farVal));
  r2.appendChild(el("span", "card-counts", `${fp} of ${fp + tn} legit calls`));
  cFar.appendChild(r2);
  if (dataObj.false_alarm_ci95 && dataObj.false_alarm_ci95[0] !== null) {
    cFar.appendChild(el("div", "card-ci", `95% CI: [${dataObj.false_alarm_ci95[0]}, ${dataObj.false_alarm_ci95[1]}]`));
  }
  grid.appendChild(cFar);

  block.appendChild(grid);
  parent.appendChild(block);
}

export function renderSectionsAtoC(root, data, devSplit, testSplit) {
  // SECTION A: Headline Ledger (Separated into Real vs Perfect Transcripts)
  const secA = el("section", "khata-section");
  const headA = el("div", "section-head");
  headA.appendChild(elLoc("h2", null, "Headline performance (frozen test split)", "मुख्य आँकड़े (टेस्ट सेट)"));
  headA.appendChild(el("span", "sub", "Section A"));
  secA.appendChild(headA);

  // Block 1: Real Prisma
  renderMetricBlock(
    secA,
    "Real Prisma speech recognition",
    "Live STT through phone audio with noise",
    testSplit,
    "python scripts/run_eval.py record --split test --go"
  );

  // Block 2: Perfect transcripts (Ceiling)
  renderMetricBlock(
    secA,
    "Perfect transcripts (script text, not real speech recognition)",
    "Deterministic rule-matching ceiling without STT error",
    testSplit.ceiling,
    null
  );

  root.appendChild(secA);

  // SECTION B: Comparison Table
  const secB = el("section", "khata-section");
  const headB = el("div", "section-head");
  headB.appendChild(elLoc("h2", null, "Perfect transcripts vs real Prisma recognition", "पहचान तुलना"));
  headB.appendChild(el("span", "sub", "Section B"));
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
    trR.appendChild(el("td", "mono-num", rTp !== "-" ? `${rTp} / ${rNscam}` : "-"));
    trR.appendChild(el("td", "mono-num", item.real?.recall != null ? `${(item.real.recall * 100).toFixed(0)}%` : "-"));
    const rFp = item.real?.fp ?? "-";
    const rNlegit = (item.real?.fp ?? 0) + (item.real?.tn ?? 0);
    trR.appendChild(el("td", "mono-num", rFp !== "-" ? `${rFp} / ${rNlegit}` : "-"));
    trR.appendChild(el("td", "mono-num", item.real?.false_alarm_rate != null ? `${(item.real.false_alarm_rate * 100).toFixed(0)}%` : "-"));
    trR.appendChild(el("td", "mono-num", item.real?.f1 != null ? item.real.f1.toFixed(2) : "-"));
    tbodyB.appendChild(trR);
  });
  tB.appendChild(tbodyB);
  wrapB.appendChild(tB);
  secB.appendChild(wrapB);
  root.appendChild(secB);

  // SECTION C: Timing
  const secC = el("section", "khata-section");
  const headC = el("div", "section-head");
  headC.appendChild(elLoc("h2", null, "Alert latency and detection timings", "चेतावनी का समय (सेकंड)"));
  headC.appendChild(el("span", "sub", "Section C"));
  secC.appendChild(headC);

  const tta = testSplit.time_to_alert_s || testSplit.ceiling?.time_to_alert_s;
  const tfc = testSplit.time_from_cue_s || testSplit.ceiling?.time_from_cue_s;

  const gridC = el("div", "timing-grid");
  const boxTTA = el("div", "timing-box");
  boxTTA.appendChild(elLoc("div", "timing-label", "TIME TO ALERT (TTA)", "कॉल शुरू से चेतावनी"));
  boxTTA.appendChild(el("div", "timing-val", tta?.median ? `${tta.median.toFixed(1)}s` : "-"));
  boxTTA.appendChild(el("div", "timing-sub", `Median ${tta?.median ?? "-"}s | Mean ${tta?.mean ?? "-"}s | Max ${tta?.max ?? "-"}s`));
  gridC.appendChild(boxTTA);

  const boxTFC = el("div", "timing-box");
  boxTFC.appendChild(elLoc("div", "timing-label", "TIME FROM CUE (TFC)", "धोखे के इशारे से चेतावनी"));
  boxTFC.appendChild(el("div", "timing-val", tfc?.median ? `${tfc.median.toFixed(1)}s` : "-"));
  boxTFC.appendChild(el("div", "timing-sub", `Median ${tfc?.median ?? "-"}s | Mean ${tfc?.mean ?? "-"}s | Max ${tfc?.max ?? "-"}s`));
  gridC.appendChild(boxTFC);
  secC.appendChild(gridC);
  root.appendChild(secC);
}
