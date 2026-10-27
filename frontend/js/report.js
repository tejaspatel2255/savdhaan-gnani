/**
 * Report page entrypoint for Savdhaan Evaluation Khata.
 * Strictly textContent-only rendering.
 */

import { getEval } from "./api.js";
import { el } from "./report-views.js";
import { renderSectionsAtoC } from "./report-sections.js";
import { renderSectionsDtoG } from "./report-audit.js";

function renderCardView(root, data) {
  document.body.className = "card-view";
  root.textContent = "";

  const card = el("div", "social-card");
  const top = el("div", "social-card-top");
  top.appendChild(el("h1", "social-card-title", "हिसाब-किताब"));
  top.appendChild(el("div", "social-card-sub", "SAVDHAAN EVALUATION · FROZEN TEST SPLIT"));
  card.appendChild(top);

  const stats = el("div", "social-card-stats");
  const testSplit = (data.splits && data.splits.test) || {};
  const tp = testSplit.tp ?? 0;
  const fn = testSplit.fn ?? 0;
  const fp = testSplit.fp ?? 0;
  const tn = testSplit.tn ?? 0;

  // Recall box
  const box1 = el("div", "social-stat-box");
  box1.appendChild(el("div", "card-label", "धोखा पहचान दर · RECALL (SCAM)"));
  const row1 = el("div", "card-stat-row");
  const recPct = testSplit.recall !== null ? `${Math.round(testSplit.recall * 100)}%` : "N/A";
  row1.appendChild(el("span", "card-num", recPct));
  row1.appendChild(el("span", "card-counts", `(${tp} of ${tp + fn} caught)`));
  box1.appendChild(row1);
  if (testSplit.recall_ci95 && testSplit.recall_ci95[0] !== null) {
    box1.appendChild(el("div", "card-ci", `95% CI: [${testSplit.recall_ci95[0]}, ${testSplit.recall_ci95[1]}]`));
  }
  stats.appendChild(box1);

  // False Alarm box
  const box2 = el("div", "social-stat-box");
  box2.appendChild(el("div", "card-label", "झूठा अलार्म · FALSE ALARM RATE"));
  const row2 = el("div", "card-stat-row");
  const farPct = testSplit.false_alarm_rate !== null ? `${Math.round(testSplit.false_alarm_rate * 100)}%` : "N/A";
  row2.appendChild(el("span", "card-num", farPct));
  row2.appendChild(el("span", "card-counts", `(${fp} of ${fp + tn} legit flagged)`));
  box2.appendChild(row2);
  if (testSplit.false_alarm_ci95 && testSplit.false_alarm_ci95[0] !== null) {
    box2.appendChild(el("div", "card-ci", `95% CI: [${testSplit.false_alarm_ci95[0]}, ${testSplit.false_alarm_ci95[1]}]`));
  }
  stats.appendChild(box2);
  card.appendChild(stats);

  card.appendChild(el("div", "social-card-foot", "synthetic calls, small sample · Gnani Prisma v2.5 + Timbre v3.0"));
  root.appendChild(card);
}

function renderFullReport(root, data) {
  root.textContent = "";

  const header = el("header", "khata-header");
  header.appendChild(el("h1", "khata-title", "हिसाब-किताब · EVALUATION KHATA"));
  header.appendChild(el("p", "khata-subtitle", "synthetic calls only, measured not estimated"));
  root.appendChild(header);

  const testSplit = (data.splits && data.splits.test) || {};
  const devSplit = (data.splits && data.splits.dev) || {};

  renderSectionsAtoC(root, data, devSplit, testSplit);
  renderSectionsDtoG(root, data);

  const nav = el("div", "back-nav");
  const back = el("a", "back-link", "← मुख्य नियंत्रण कक्ष · Back to Nazar Control Room");
  back.href = "/";
  nav.appendChild(back);
  root.appendChild(nav);
}

function renderEmptyState(root) {
  root.textContent = "";
  const box = el("div", "empty-notice");
  box.appendChild(el("div", null, "अभी आँकड़े नहीं · Run the evaluation first"));
  box.appendChild(el("p", null, "To generate evaluation results, run:"));
  box.appendChild(el("div", "empty-cmd", "python scripts/run_eval.py score --split dev --ceiling"));
  root.appendChild(box);
}

async function init() {
  const root = document.getElementById("khata-root");
  if (!root) return;

  const isCardView = new URLSearchParams(window.location.search).get("card") === "1";
  try {
    const data = await getEval();
    if (!data || data.error === "no_results") {
      renderEmptyState(root);
      return;
    }
    if (isCardView) {
      renderCardView(root, data);
    } else {
      renderFullReport(root, data);
    }
  } catch (err) {
    renderEmptyState(root);
  }
}

init();
