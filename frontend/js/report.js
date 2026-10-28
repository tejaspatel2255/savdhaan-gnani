/**
 * Report page entrypoint for Savdhaan Evaluation Khata.
 * Strictly textContent-only rendering.
 */

import { getEval } from "./api.js";
import { el, elLoc } from "./report-views.js";
import { renderSectionsAtoC } from "./report-sections.js";
import { renderSectionsDtoG } from "./report-audit.js";

function renderCardView(root, data) {
  document.body.className = "card-view";
  root.textContent = "";

  const card = el("div", "social-card");
  const top = el("div", "social-card-top");
  top.appendChild(elLoc("h1", "social-card-title", "EVALUATION KHATA", "हिसाब-किताब"));
  top.appendChild(el("div", "social-card-sub", "SAVDHAAN EVALUATION · FROZEN TEST SPLIT"));
  card.appendChild(top);

  const stats = el("div", "social-card-stats");
  const testSplit = (data.splits && data.splits.test) || {};
  const hasReal = testSplit.tp !== null && testSplit.tp !== undefined;
  const targetObj = hasReal ? testSplit : (testSplit.ceiling || {});

  const tp = targetObj.tp ?? 0;
  const fn = targetObj.fn ?? 0;
  const fp = targetObj.fp ?? 0;
  const tn = targetObj.tn ?? 0;

  // Recall box
  const box1 = el("div", "social-stat-box");
  box1.appendChild(elLoc("div", "card-label", "RECALL (SCAM)", "धोखा पहचान दर"));
  const row1 = el("div", "card-stat-row");
  const recPct = targetObj.recall !== null && targetObj.recall !== undefined ? `${Math.round(targetObj.recall * 100)}%` : "N/A";
  row1.appendChild(el("span", "card-num", recPct));
  if (!hasReal) {
    row1.appendChild(el("span", "card-num-note", "perfect transcripts"));
  }
  row1.appendChild(el("span", "card-counts", `(${tp} of ${tp + fn} caught)`));
  box1.appendChild(row1);
  if (targetObj.recall_ci95 && targetObj.recall_ci95[0] !== null) {
    box1.appendChild(el("div", "card-ci", `95% CI: [${targetObj.recall_ci95[0]}, ${targetObj.recall_ci95[1]}]`));
  }
  stats.appendChild(box1);

  // False Alarm box
  const box2 = el("div", "social-stat-box");
  box2.appendChild(elLoc("div", "card-label", "FALSE ALARM RATE", "झूठा अलार्म"));
  const row2 = el("div", "card-stat-row");
  const farPct = targetObj.false_alarm_rate !== null && targetObj.false_alarm_rate !== undefined ? `${Math.round(targetObj.false_alarm_rate * 100)}%` : "N/A";
  row2.appendChild(el("span", "card-num", farPct));
  if (!hasReal) {
    row2.appendChild(el("span", "card-num-note", "perfect transcripts"));
  }
  row2.appendChild(el("span", "card-counts", `(${fp} of ${fp + tn} legit flagged)`));
  box2.appendChild(row2);
  if (targetObj.false_alarm_ci95 && targetObj.false_alarm_ci95[0] !== null) {
    box2.appendChild(el("div", "card-ci", `95% CI: [${targetObj.false_alarm_ci95[0]}, ${targetObj.false_alarm_ci95[1]}]`));
  }
  stats.appendChild(box2);
  card.appendChild(stats);

  const footText = hasReal
    ? "synthetic calls, small sample · Gnani Prisma v2.5 + Timbre v3.0"
    : "perfect transcripts ceiling · Gnani Prisma v2.5 + Timbre v3.0";
  card.appendChild(el("div", "social-card-foot", footText));
  root.appendChild(card);
}

function renderFullReport(root, data) {
  root.textContent = "";

  const header = el("header", "khata-header");
  header.appendChild(elLoc("h1", "khata-title", "EVALUATION KHATA", "हिसाब-किताब"));
  header.appendChild(el("p", "khata-subtitle", "synthetic calls only, measured not estimated"));
  root.appendChild(header);

  const testSplit = (data.splits && data.splits.test) || {};
  const devSplit = (data.splits && data.splits.dev) || {};

  renderSectionsAtoC(root, data, devSplit, testSplit);
  renderSectionsDtoG(root, data);

  const nav = el("div", "back-nav");
  const back = elLoc("a", "back-link", "← Back to the Nazar control room", "मुख्य नियंत्रण कक्ष");
  back.href = "/";
  nav.appendChild(back);
  root.appendChild(nav);
}

function renderEmptyState(root) {
  root.textContent = "";
  const box = el("div", "empty-notice");
  box.appendChild(elLoc("div", null, "No figures yet · Run the evaluation first", "अभी आँकड़े नहीं"));
  box.appendChild(el("p", null, "To generate evaluation results, run:"));
  box.appendChild(el("div", "empty-cmd", "python scripts/run_eval.py score --split dev --ceiling"));
  root.appendChild(box);
}

async function init() {
  const root = document.getElementById("khata-root");
  if (!root) return;

  let data = null;
  try {
    data = await getEval();
  } catch (err) {}

  if (!data || !data.splits) {
    renderEmptyState(root);
    return;
  }

  const params = new URLSearchParams(window.location.search);
  if (params.get("card") === "1") {
    renderCardView(root, data);
  } else {
    renderFullReport(root, data);
  }
}

window.addEventListener("DOMContentLoaded", init);
