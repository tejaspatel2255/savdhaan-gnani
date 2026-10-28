/**
 * Bilingual text helpers: English is always the primary text; the chosen
 * local language (Hindi or Gujarati) is a smaller secondary line or span.
 */
import { STRINGS } from "./strings.js";

let local = "hi";

export function setLocal(code) {
  local = String(code || "").startsWith("gu") ? "gu" : "hi";
}

export function getLocal() {
  return local;
}

export function textEn(key) {
  const item = STRINGS[key];
  return item ? item.en : key;
}

export function textLoc(key) {
  const item = STRINGS[key];
  return (item && item[local]) || "";
}

/** Fill `node` with an English span and, if available, a local-language span. */
export function fill(node, key, opts = {}) {
  node.dataset.i18n = key;
  if (opts.enOnly) node.dataset.enOnly = "1";
  node.textContent = "";
  const primary = document.createElement("span");
  primary.className = "t-en";
  primary.textContent = textEn(key);
  node.appendChild(primary);
  const secondary = opts.enOnly ? "" : textLoc(key);
  if (secondary) {
    const sub = document.createElement("span");
    sub.className = "t-loc";
    sub.setAttribute("lang", local);
    sub.textContent = secondary;
    node.appendChild(sub);
  }
  return node;
}

/** Re-render every element that carries data-i18n (used after the language chip changes). */
export function applyLabels(root = document) {
  root.querySelectorAll("[data-i18n]").forEach((n) => fill(n, n.dataset.i18n, { enOnly: n.dataset.enOnly === "1" }));
}
