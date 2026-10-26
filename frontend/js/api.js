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

export async function fetchSampleRun(url) {
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, `Failed to load sample run: ${res.statusText}`);
  return res.text();
}
