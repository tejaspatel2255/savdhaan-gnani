/**
 * REST API client for Savdhaan backend.
 * Single location for all HTTP network calls in the frontend.
 */
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

let cachedBackendStatus = null;

export async function detectBackend() {
  if (cachedBackendStatus !== null) return cachedBackendStatus;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);

  try {
    const res = await fetch("/api/health", { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) {
      cachedBackendStatus = false;
      return false;
    }
    const data = await res.json();
    cachedBackendStatus = Boolean(data && data.ok);
    return cachedBackendStatus;
  } catch (_) {
    clearTimeout(timeoutId);
    cachedBackendStatus = false;
    return false;
  }
}

async function request(endpoint, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  let res;
  try {
    res = await fetch(endpoint, { ...options, headers });
  } catch (err) {
    throw new ApiError(0, err.message || "Network request failed");
  }

  let data;
  try {
    data = await res.json();
  } catch (err) {
    data = null;
  }

  if (!res.ok) {
    const detail = (data && data.detail) || (data && data.error && data.error.message) || res.statusText;
    throw new ApiError(res.status, detail);
  }

  return data;
}

export async function getHealth() {
  return request("/api/health");
}

export async function getCalls() {
  return request("/api/calls");
}

export async function startSession(body) {
  return request("/api/session/start", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function stopSession(sessionId) {
  return request("/api/session/stop", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function getUsage() {
  return request("/api/usage");
}

export async function getEval() {
  try {
    return await request("/api/eval");
  } catch (err) {
    try {
      const res = await fetch("/assets/results.json");
      if (res.ok) return await res.json();
    } catch (_) {}
    throw err;
  }
}

export async function fetchSampleRun(url) {
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, `Failed to load sample run: ${res.statusText}`);
  return res.text();
}

/** English translations of the recorded demo transcripts (optional; {} when unavailable). */
let glossCache = null;
export async function getGloss() {
  if (glossCache) return glossCache;
  try {
    const res = await fetch("/assets/gloss.json");
    glossCache = res.ok ? await res.json() : {};
  } catch (_) {
    glossCache = {};
  }
  return glossCache;
}

/**
 * Score text with the rule engine (no Gnani credits).
 * @param {string} text  Max 2000 chars.
 * @param {string} pack  "hi_en" | "gu" (default "hi_en").
 */
export async function analyzeText(text, pack = "hi_en") {
  return request("/api/analyze", {
    method: "POST",
    body: JSON.stringify({ text, pack }),
  });
}

/** Fetch rule-category summaries for the "Words we listen for" panel. */
export async function getRulesSummary() {
  return request("/api/rules/summary");
}
