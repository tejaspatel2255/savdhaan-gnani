/**
 * mic.js — Capture browser microphone, stream to /ws/mic.
 * Only this file and ws.js may contain `new WebSocket(`.
 */

export class MicError extends Error {
  /** @param {'denied'|'no_device'|'unavailable'} code */
  constructor(message, code) {
    super(message);
    this.name = "MicError";
    this.code = code;
  }
}

let _stream = null;   // MediaStream
let _ctx = null;      // AudioContext
let _ws = null;       // WebSocket to /ws/mic
let _node = null;     // AudioWorkletNode
let _active = false;

/**
 * Start capturing the microphone and streaming to /ws/mic.
 * @param {string} sessionId
 * @returns {Promise<void>}
 * @throws {MicError}
 */
export async function startMic(sessionId) {
  if (_active) return;

  // Request mic
  try {
    _stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });
  } catch (err) {
    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      throw new MicError("Microphone permission denied", "denied");
    }
    if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
      throw new MicError("No microphone found", "no_device");
    }
    throw new MicError(err.message || "Microphone unavailable", "unavailable");
  }

  // AudioContext (use existing if passed — worklet needs its own)
  _ctx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: undefined });

  await _ctx.audioWorklet.addModule("js/mic-worklet.js");
  _node = new AudioWorkletNode(_ctx, "mic-processor");

  // Open WebSocket to backend
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/mic?session_id=${encodeURIComponent(sessionId)}`;
  _ws = new WebSocket(url);
  _ws.binaryType = "arraybuffer";

  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new MicError("WebSocket timed out", "unavailable")), 5000);
    _ws.onopen = () => { clearTimeout(timer); resolve(); };
    _ws.onerror = () => { clearTimeout(timer); reject(new MicError("WebSocket error", "unavailable")); };
  });

  // Worklet → WebSocket
  _node.port.onmessage = (ev) => {
    if (_ws && _ws.readyState === WebSocket.OPEN) {
      _ws.send(ev.data);
    }
  };

  // Connect source → worklet (NOT to destination — no speaker feedback)
  const src = _ctx.createMediaStreamSource(_stream);
  src.connect(_node);
  // _node is NOT connected to _ctx.destination

  _active = true;
}

/**
 * Stop mic capture and close the WebSocket.
 */
export function stopMic() {
  _active = false;

  if (_node) { try { _node.disconnect(); } catch (_) {} _node = null; }
  if (_stream) { _stream.getTracks().forEach((t) => t.stop()); _stream = null; }
  if (_ctx) { try { _ctx.close(); } catch (_) {} _ctx = null; }

  if (_ws) {
    if (_ws.readyState === WebSocket.OPEN) {
      try { _ws.send("stop"); } catch (_) {}
      _ws.close();
    }
    _ws = null;
  }
}

export function isMicActive() {
  return _active;
}
