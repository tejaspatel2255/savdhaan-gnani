"""Responsive audit: opens the app at many screen sizes and reports layout problems.

Usage: python scripts/responsive_audit.py [--url http://127.0.0.1:8000] [--page index|report] [--shots docs/screens/responsive]
Exit code 0 only if every check passes. Needs the app running at --url.
"""
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import sync_playwright
from scripts.responsive_audit_lib import check_overlap, check_responsive_rules

SIZES = [
    (320, 568), (360, 740), (375, 667), (390, 844), (412, 915), (430, 932),
    (600, 900), (768, 1024), (820, 1180), (667, 375), (844, 390),
    (1024, 600), (1024, 768), (1280, 600), (1280, 720), (1366, 625), (1366, 768),
    (1440, 900), (1536, 730), (1920, 1080), (2560, 1440)
]
STATES = {"idle": "", "danger": "?dev=1&at=30", "receipt": "?dev=1&at=999"}

JS = r"""
() => {
  const W = innerWidth, H = innerHeight, bad = {outside: [], small: [], clipped: [], tiny: [], contrast: []};
  const zoom = parseFloat(getComputedStyle(document.documentElement).zoom || 1) || 1;
  const hiddenByDetails = (e) => { const d = e.closest('details'); return d && !d.open && !e.closest('summary'); };
  const inScroller = (e) => { for (let n = e.parentElement; n && n !== document.body; n = n.parentElement) { const o = getComputedStyle(n).overflowX; if (o === 'auto' || o === 'scroll') return true; } return false; };
  const label = (e) => (e.id ? '#' + e.id : (e.className && e.className.toString ? '.' + e.className.toString().split(' ')[0] : e.tagName));
  const parse = (c) => { const m = c.match(/[\d.]+/g).map(Number); return {r: m[0], g: m[1], b: m[2], a: m.length > 3 ? m[3] : 1}; };
  const lum = (c) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const bgOf = (e) => { for (let n = e; n; n = n.parentElement) { const c = parse(getComputedStyle(n).backgroundColor); if (c.a > 0.9) return c; } return {r: 10, g: 12, b: 24, a: 1}; };
  
  document.querySelectorAll('body *').forEach((e) => {
    if (e.closest('svg') || hiddenByDetails(e) || e.closest('.visually-hidden') || e.classList.contains('visually-hidden') || e.closest('#stamp-root')) return;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || e.closest('.hidden') || e.closest('[aria-hidden="true"]')) return;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    if ((r.right > W + 1 || r.left < -1) && !inScroller(e)) bad.outside.push(label(e) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    if (['BUTTON', 'SELECT', 'SUMMARY', 'A'].includes(e.tagName) && !e.closest('#stamp-root')) {
      const need = W <= 1024 ? 44 : 32;
      if (r.height < need || r.width < need) bad.small.push(label(e) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
    }
    if (e.children.length === 0 && e.textContent.trim() && !e.matches('option') && !e.disabled) {
      const fg = parse(cs.color), bg = bgOf(e), l1 = lum(fg), l2 = lum(bg);
      const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
      const big = parseFloat(cs.fontSize) >= 24 || (parseFloat(cs.fontSize) >= 18.66 && parseInt(cs.fontWeight) >= 700);
      if (fg.a > 0.9 && ratio < (big ? 3 : 4.5)) bad.contrast.push(label(e) + ' ' + ratio.toFixed(1) + ':1');
    }
    if (e.children.length === 0 && e.textContent.trim()) {
      const effSize = parseFloat(cs.fontSize) * zoom;
      if (effSize < 11 && !e.closest('.visually-hidden')) bad.tiny.push(label(e) + ' ' + cs.fontSize);
    }
    if (e.scrollWidth > e.clientWidth + 2 && ['hidden', 'clip'].includes(cs.overflowX) && e.clientWidth > 0 && cs.textOverflow !== 'ellipsis' && !e.matches('body,html,.app-shell,#hdr,.tape-scroll')) bad.clipped.push(label(e));
  });

  // Header element overlap check
  const hdrElements = [];
  const hdr = document.querySelector('#hdr');
  if (hdr) {
    const candidates = hdr.querySelectorAll('.hdr-left, .hdr-centre, #btn-listen-live, #live-lang-sel, #btn-live-stop, #advanced-controls');
    candidates.forEach(el => {
      const cs = getComputedStyle(el);
      if (cs.display !== 'none' && cs.visibility !== 'hidden') {
        const r = el.getBoundingClientRect();
        if (r.width > 0 && r.height > 0) {
          hdrElements.push({label: label(el), rect: {top: r.top, bottom: r.bottom, left: r.left, right: r.right}});
        }
      }
    });
  }

  const q = (s) => document.querySelector(s);
  const rect = (s) => { const e = q(s); if (!e) return null; const r = e.getBoundingClientRect(); return {top: r.top, bottom: r.bottom, left: r.left, right: r.right}; };
  return {W, H, bad, scrollW: document.documentElement.scrollWidth, scrollH: document.documentElement.scrollHeight,
          score: rect('.score-num'), badge: rect('.level-badge'), demo: rect('#btn-demo-scam'), phone: rect('#phone-slot'),
          tape: rect('#col-tape'), eye: rect('#col-eye'), foot: rect('#foot'), dialog: rect('.receipt-dialog'), hdrElements};
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--shots", default="docs/screens/responsive")
    ap.add_argument("--page", choices=["index", "report"], default="index")
    a = ap.parse_args()
    Path(a.shots).mkdir(parents=True, exist_ok=True)
    total = 0

    import urllib.request
    import http.server
    import socketserver
    import threading

    url_to_use = a.url
    try:
        urllib.request.urlopen(a.url, timeout=0.8)
    except Exception:
        class StaticHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory="frontend", **kwargs)
            def log_message(self, *args):
                pass
        httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), StaticHandler)
        port = httpd.server_address[1]
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        url_to_use = f"http://127.0.0.1:{port}"
        print(f"Backend not active at {a.url}; serving frontend statically on {url_to_use}")

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for (w, h) in SIZES:
            for state, qs in (STATES.items() if a.page == "index" else [("report", "")]):
                pg = br.new_page(viewport={"width": w, "height": h})
                errs = []
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                pg.goto(url_to_use.rstrip("/") + "/" + ("report.html" if a.page == "report" else "") + qs, wait_until="domcontentloaded")
                pg.wait_for_timeout(400)
                d = pg.evaluate(JS)
                d["hdr_overlaps"] = check_overlap(d.get("hdrElements", []))
                probs = check_responsive_rules(w, h, state, d, a.page)
                errs = [e for e in errs if "fonts" not in e.lower() and "ERR_TUNNEL" not in e and "404" not in e]
                probs += ["console error: " + e[:80] for e in errs[:2]]
                pg.screenshot(path=f"{a.shots}/{state}_{w}x{h}.png", full_page=(a.page == "report"))
                print(("PASS " if not probs else "FAIL ") + f"{w}x{h} {state}")
                for x in probs:
                    print("     - " + x)
                total += len(probs)
                pg.close()
        br.close()
    print(f"\n{total} problem(s) found")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
