/**
 * AudioWorkletProcessor: captures mic audio, resamples to 16 kHz,
 * converts to Int16 LE, and posts ArrayBuffers to the main thread.
 */

const TARGET_RATE = 16000;
// Accumulate this many target samples before posting (≈64 ms at 16 kHz)
const BATCH_SAMPLES = 1024;

class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buf = new Float32Array(0);
    this._step = 0; // resampling step (set on first process)
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const ch = input[0]; // mono

    // Compute downsampling step once (native sampleRate is globalThis.sampleRate)
    if (!this._step) {
      this._step = sampleRate / TARGET_RATE;
    }

    // Resample: simple nearest-neighbour decimation
    const outLen = Math.floor(ch.length / this._step);
    const resampled = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      resampled[i] = ch[Math.floor(i * this._step)];
    }

    // Append to buffer
    const combined = new Float32Array(this._buf.length + resampled.length);
    combined.set(this._buf);
    combined.set(resampled, this._buf.length);
    this._buf = combined;

    // Drain in BATCH_SAMPLES chunks
    while (this._buf.length >= BATCH_SAMPLES) {
      const slice = this._buf.subarray(0, BATCH_SAMPLES);
      const int16 = new Int16Array(BATCH_SAMPLES);
      for (let i = 0; i < BATCH_SAMPLES; i++) {
        const s = Math.max(-1, Math.min(1, slice[i]));
        int16[i] = s < 0 ? s * 32768 : s * 32767;
      }
      // Transfer ownership — zero-copy
      this.port.postMessage(int16.buffer, [int16.buffer]);
      this._buf = this._buf.slice(BATCH_SAMPLES);
    }

    return true; // keep processor alive
  }
}

registerProcessor("mic-processor", MicProcessor);
