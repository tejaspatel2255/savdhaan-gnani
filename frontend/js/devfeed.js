/**
 * Dev feed replay driver for deterministic visual testing and design polish.
 */
export async function playSample(url, dispatch, { speed = 1, at = null } = {}) {
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.warn("Could not load sample run:", url, res.status);
      return;
    }

    const text = await res.text();
    const lines = text.split("\n");
    const messages = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        messages.push(JSON.parse(trimmed));
      } catch (e) {
        // Skip malformed lines safely
      }
    }

    if (at !== null && at !== undefined) {
      // Deterministic snapshot mode at timestamp N
      document.body.classList.add("no-anim");
      for (const msg of messages) {
        if (msg.t <= at) {
          dispatch(msg);
        }
      }
      return;
    }

    // Timed replay
    const effectiveSpeed = Math.max(0.1, Number(speed) || 1);
    const startMonotonic = performance.now();

    for (const msg of messages) {
      const targetTimeMs = ((msg.t || 0) / effectiveSpeed) * 1000;
      const elapsedMs = performance.now() - startMonotonic;
      const delay = Math.max(0, targetTimeMs - elapsedMs);

      if (delay > 0) {
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
      dispatch(msg);
    }
  } catch (err) {
    console.error("Failed to play devfeed sample:", err);
  }
}
