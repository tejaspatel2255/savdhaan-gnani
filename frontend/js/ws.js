/**
 * Resilient WebSocket client with exponential backoff and connection status events.
 */
export function connect(url, onMessage, onStatus) {
  let ws = null;
  let retryCount = 0;
  let intentionalClose = false;
  const backoffDelays = [1000, 2000, 4000, 8000, 10000];

  function getWsUrl() {
    if (url) return url;
    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${loc.host}/ws/ui`;
  }

  function start() {
    if (intentionalClose) return;

    try {
      ws = new WebSocket(getWsUrl());
    } catch (err) {
      scheduleReconnect();
      return;
    }

    ws.onopen = () => {
      retryCount = 0;
      if (onStatus) onStatus("open");
      try {
        ws.send(JSON.stringify({ type: "hello" }));
      } catch (err) {
        // Safe send
      }
    };

    ws.onmessage = (event) => {
      if (!event.data) return;
      try {
        const msg = JSON.parse(event.data);
        if (onMessage) onMessage(msg);
      } catch (err) {
        console.error("Malformed WebSocket JSON frame:", err, event.data);
      }
    };

    ws.onclose = () => {
      if (!intentionalClose) {
        if (onStatus) onStatus("reconnecting");
        scheduleReconnect();
      } else {
        if (onStatus) onStatus("closed");
      }
    };

    ws.onerror = () => {
      // Browser triggers onclose right after error
    };
  }

  function scheduleReconnect() {
    const delay = backoffDelays[Math.min(retryCount, backoffDelays.length - 1)];
    retryCount++;
    setTimeout(start, delay);
  }

  start();

  return {
    close: () => {
      intentionalClose = true;
      if (ws) ws.close();
    },
  };
}
