/**
 * Report page entrypoint for Savdhaan Evaluation Khata.
 * Strictly textContent-only rendering.
 */

import { getEval } from "./api.js";
import { el, elLoc } from "./report-views.js";
import { renderSectionsAtoC } from "./report-sections.js";
import { renderWhatChangedSection } from "./report-changed.js";
import { renderSectionsDtoG } from "./report-audit.js";

function renderCardView(root, data, isFixture = false) {
  document.body.className = "card-view";
  root.textContent = "";

  if (isFixture) {
    const banner = el("div", "fixture-top-banner", "FIXTURE DATA - NOT MEASURED");
    root.appendChild(banner);
  }

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
  box1.appendChild(el("div", "card-small-sample", `n = ${targetObj.n || 10} calls per split, so intervals are wide`));
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
  box2.appendChild(el("div", "card-small-sample", `n = ${targetObj.n || 10} calls per split, so intervals are wide`));
  stats.appendChild(box2);
  card.appendChild(stats);

  const footText = hasReal
    ? "synthetic calls, small sample · Gnani Prisma v2.5 + Timbre v3.0"
    : "perfect transcripts ceiling · Gnani Prisma v2.5 + Timbre v3.0";
  card.appendChild(el("div", "social-card-foot", footText));
  root.appendChild(card);
}

function renderFullReport(root, data, isFixture = false) {
  root.textContent = "";

  if (isFixture) {
    const banner = el("div", "fixture-top-banner", "FIXTURE DATA - NOT MEASURED");
    root.appendChild(banner);
  }

  const header = el("header", "khata-header");
  header.appendChild(elLoc("h1", "khata-title", "EVALUATION KHATA", "हिसाब-किताब"));
  header.appendChild(el("p", "khata-subtitle", "synthetic calls only, measured not estimated"));
  root.appendChild(header);

  const testSplit = (data.splits && data.splits.test) || {};
  const devSplit = (data.splits && data.splits.dev) || {};
  const blindSplit = (data.splits && data.splits.blind) || {};

  renderSectionsAtoC(root, data, devSplit, testSplit, blindSplit, isFixture);
  renderWhatChangedSection(root, data, isFixture);
  renderSectionsDtoG(root, data, isFixture);

  // Footer metadata
  const foot = el("footer", "khata-footer");
  const genAt = data.generated_at ? `Generated at: ${data.generated_at}` : "";
  const sha = data.rules_sha256 ? `Rules SHA: ${data.rules_sha256.substring(0, 12)}` : "";
  const devScores = data.dev_scoring?.times_scored != null ? `Dev scored: ${data.dev_scoring.times_scored}` : "";
  const testScores = data.test_scoring?.times_scored != null ? `Test scored: ${data.test_scoring.times_scored}` : "";
  const blindScores = data.blind_scoring?.times_scored != null ? `Blind scored: ${data.blind_scoring.times_scored}` : "";
  const metaParts = [genAt, sha, devScores, testScores, blindScores].filter(Boolean);
  foot.appendChild(el("div", "footer-meta", metaParts.join(" · ")));

  const nav = el("div", "back-nav");
  const back = elLoc("a", "back-link", "← Back to the Nazar control room", "मुख्य नियंत्रण कक्ष");
  back.href = "/";
  nav.appendChild(back);

  const sep = el("span", "footer-sep", " · ");
  nav.appendChild(sep);

  const archLink = el("a", "back-link", "Architecture & Data Flow Diagram");
  archLink.href = "/docs/how_it_works.svg";
  archLink.target = "_blank";
  nav.appendChild(archLink);

  foot.appendChild(nav);
  root.appendChild(foot);
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

  const params = new URLSearchParams(window.location.search);
  const isFixture = params.get("fixture") === "1";

  let data = null;
  try {
    data = await getEval(isFixture);
  } catch (err) {}

  if (!data || !data.splits) {
    renderEmptyState(root);
    return;
  }

  if (params.get("card") === "1") {
    renderCardView(root, data, isFixture);
  } else {
    renderFullReport(root, data, isFixture);
  }
}

window.addEventListener("DOMContentLoaded", init);
