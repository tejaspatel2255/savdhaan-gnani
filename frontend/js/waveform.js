let dom = null;
const BUFFER_SIZE = 160;
const ringBuffer = new Array(BUFFER_SIZE).fill(0.02);
let bufferIdx = 0;
let isMock = true;

export function init(rootEl) {
  dom = {
    root: rootEl,
    path: rootEl.querySelector(".waveform-path"),
    modeTag: rootEl.querySelector(".awaaz-mode-tag"),
  };
  renderWaveform();
}

export function reset() {
  ringBuffer.fill(0.02);
  bufferIdx = 0;
  renderWaveform();
}

function renderWaveform() {
  if (!dom.path) return;
  const width = 1440;
  const height = 96;
  const midY = height / 2;
  const step = width / (BUFFER_SIZE - 1);

  let topPoints = [];
  let bottomPoints = [];

  for (let i = 0; i < BUFFER_SIZE; i++) {
    const idx = (bufferIdx + i) % BUFFER_SIZE;
    const val = ringBuffer[idx];
    const x = Math.round(i * step);
    const amp = Math.max(2, Math.min(val * 85, midY - 4));
    topPoints.push(`${x},${(midY - amp).toFixed(1)}`);
    bottomPoints.unshift(`${x},${(midY + amp).toFixed(1)}`);
  }

  const d = `M ${topPoints.join(" L ")} L ${bottomPoints.join(" L ")} Z`;
  dom.path.setAttribute("d", d);
}

export function handle(msg, state) {
  if (msg.type === "session") {
    isMock = (msg.mode === "mock");
    if (dom.modeTag) {
      dom.modeTag.textContent = msg.mode_label || (isMock ? "MOCK" : "");
    }
  } else if (msg.type === "audio_level") {
    let rms = msg.rms || 0.02;
    if (isMock && rms <= 0.05) {
      // Slight gentle synthetic wave in mock mode
      const tSec = msg.t || 0;
      rms = 0.04 + 0.03 * Math.sin(tSec * 2);
    }
    ringBuffer[bufferIdx] = rms;
    bufferIdx = (bufferIdx + 1) % BUFFER_SIZE;
    renderWaveform();
  }
}
