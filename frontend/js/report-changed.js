/**
 * What changed section builder for Savdhaan Evaluation Khata.
 * Compares script vs real STT and displays side-by-side snippet comparisons.
 */

import { el, elLoc } from "./report-views.js";

export function renderWhatChangedSection(root, data, isFixture) {
  const sec = el("section", "khata-section");
  const head = el("div", "section-head");
  head.appendChild(elLoc("h2", null, "What real speech recognition changed", "वास्तविक वाक-पहचान से क्या बदला"));
  if (isFixture) head.appendChild(el("span", "fixture-section-tag", "FIXTURE DATA - NOT MEASURED"));
  head.appendChild(el("span", "sub", "Real STT vs Script"));
  sec.appendChild(head);

  const calls = data.calls || [];
  const wrap = el("div", "table-wrapper");
  const table = el("table", "khata-table");
  const thead = el("thead");
  const trh = el("tr");
  ["Call ID", "Label", "Script Score", "Real-STT Score", "Alert Time (Script / STT)", "Status / Flag"].forEach((t) => trh.appendChild(el("th", null, t)));
  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = el("tbody");
  const flaggedCalls = [];

  calls.forEach((c) => {
    const tr = el("tr");
    tr.appendChild(el("td", "mono-num", c.id));
    tr.appendChild(el("td", null, c.label));
    const ceilScore = c.ceiling_score ?? c.max_score ?? "-";
    const ceilLevel = c.ceiling_level ?? c.max_level ?? "";
    tr.appendChild(el("td", "mono-num", `${ceilScore} (${ceilLevel})`));

    const realScore = c.max_score ?? "-";
    const realLevel = c.max_level ?? "";
    tr.appendChild(el("td", "mono-num", `${realScore} (${realLevel})`));

    const tScript = c.ceiling_alert_t != null ? `${c.ceiling_alert_t.toFixed(1)}s` : "-";
    const tReal = c.alert_t != null ? `${c.alert_t.toFixed(1)}s` : "-";
    tr.appendChild(el("td", "mono-num", `${tScript} / ${tReal}`));

    let flag = c.flag || "concordant";
    if (c.ceiling_alert_t != null && c.alert_t == null) {
      flag = "caught only with perfect text";
      flaggedCalls.push(c);
    } else if (c.ceiling_alert_t == null && c.alert_t != null) {
      flag = "caught only with real STT";
      flaggedCalls.push(c);
    } else if (c.flag) {
      flaggedCalls.push(c);
    }
    const tdFlag = el("td", null, flag);
    if (flag.includes("only") || flag.includes("missed")) tdFlag.className = "danger-text";
    tr.appendChild(tdFlag);
    tbody.appendChild(tr);
  });

  table.appendChild(tbody);
  wrap.appendChild(table);
  sec.appendChild(wrap);

  if (flaggedCalls.length > 0) {
    const snipBox = el("div", "snippet-comparison-box");
    snipBox.appendChild(el("h4", "snippet-head", "Side-by-side transcript comparison on flagged calls"));
    flaggedCalls.forEach((fc) => {
      const card = el("div", "audit-card");
      card.appendChild(el("div", "audit-header", `${fc.id} · Flag: ${fc.flag || "discrepancy"}`));
      const cols = el("div", "snippet-two-col");

      const col1 = el("div", "snippet-col");
      col1.appendChild(el("div", "snippet-col-title", "Perfect Script Transcript"));
      (fc.perfect_segments || fc.segments || []).slice(0, 3).forEach((s) => {
        col1.appendChild(el("div", "snippet-line", `[${s.t.toFixed(1)}s] ${s.text}`));
      });
      cols.appendChild(col1);

      const col2 = el("div", "snippet-col");
      col2.appendChild(el("div", "snippet-col-title", "Real Recognized STT"));
      (fc.segments || []).slice(0, 3).forEach((s) => {
        col2.appendChild(el("div", "snippet-line", `[${s.t.toFixed(1)}s] ${s.text}`));
      });
      cols.appendChild(col2);

      card.appendChild(cols);
      snipBox.appendChild(card);
    });
    sec.appendChild(snipBox);
  }

  root.appendChild(sec);
}
