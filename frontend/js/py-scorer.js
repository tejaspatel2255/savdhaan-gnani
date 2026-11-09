/**
 * py-scorer.js — Lazy in-browser Python rule scorer using Pyodide 0.26.4.
 * Runs byte-identical rules & scorer in WebAssembly. No backend or key needed.
 */
import { fetchTextAsset } from "./api.js";

let _pyodidePromise = null;
let _py = null;

export function initScorer(onProgress) {
  if (_pyodidePromise) return _pyodidePromise;

  _pyodidePromise = (async () => {
    if (!window.loadPyodide) {
      if (onProgress) onProgress("loading_script");
      await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js";
        script.onload = resolve;
        script.onerror = () => reject(new Error("Could not load Pyodide script from CDN"));
        document.head.appendChild(script);
      });
    }

    if (onProgress) onProgress("initializing_wasm");
    const py = await window.loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/",
    });

    // Create filesystem directories in Pyodide
    py.FS.mkdirTree("/app/backend/scorer");
    py.FS.mkdirTree("/app/rules");
    py.FS.writeFile("/app/backend/__init__.py", "");

    // Fetch and load scorer code and rules
    const files = [
      ["/assets/pyscorer/backend/scorer/__init__.py", "/app/backend/scorer/__init__.py"],
      ["/assets/pyscorer/backend/scorer/engine.py", "/app/backend/scorer/engine.py"],
      ["/assets/pyscorer/backend/scorer/matching.py", "/app/backend/scorer/matching.py"],
      ["/assets/pyscorer/backend/scorer/normalize.py", "/app/backend/scorer/normalize.py"],
      ["/assets/pyscorer/backend/scorer/rules_loader.py", "/app/backend/scorer/rules_loader.py"],
      ["/assets/pyscorer/rules/scam_rules_hi_en.json", "/app/rules/scam_rules_hi_en.json"],
      ["/assets/pyscorer/rules/scam_rules_gu.json", "/app/rules/scam_rules_gu.json"],
      ["/assets/pyscorer/glue.py", "/app/glue.py"],
    ];

    if (onProgress) onProgress("loading_rules");
    await Promise.all(
      files.map(async ([url, dest]) => {
        const content = await fetchTextAsset(url);
        py.FS.writeFile(dest, content);
      })
    );

    await py.runPythonAsync(`
import sys
sys.path.insert(0, "/app")
import glue
`);

    _py = py;
    return py;
  })();

  return _pyodidePromise;
}

export async function startScoring(langCode = "hi-IN", careful = 30, danger = 60) {
  const py = await initScorer();
  const packNames = langCode === "gu-IN" ? "hi_en,gu" : "hi_en";
  py.runPython(`glue.start("${packNames}", ${careful}, ${danger})`);
}

export function scoreSentence(text, index) {
  if (!_py) throw new Error("Pyodide scorer not initialized");
  // Safely pass text to python feed
  _py.globals.set("_feed_text", text);
  _py.globals.set("_feed_idx", index);
  const jsonStr = _py.runPython("glue.feed(_feed_text, _feed_idx)");
  return JSON.parse(jsonStr);
}
