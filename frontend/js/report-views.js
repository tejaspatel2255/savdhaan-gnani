/**
 * Helper DOM & SVG rendering utilities for the Khata report page.
 */

export function el(tag, className, text) {
  const elem = document.createElement(tag);
  if (className) elem.className = className;
  if (text !== undefined && text !== null) elem.textContent = text;
  return elem;
}

/** Element with English text first and a smaller Hindi secondary span. */
export function elLoc(tag, className, en, hi) {
  const elem = el(tag, className, en);
  if (hi) {
    const sub = document.createElement("span");
    sub.className = "t-loc";
    sub.setAttribute("lang", "hi");
    sub.textContent = hi;
    elem.appendChild(sub);
  }
  return elem;
}

export function renderPencilBar(svg, pct) {
  svg.setAttribute("viewBox", "0 0 100 16");
  svg.setAttribute("preserveAspectRatio", "none");
  svg.classList.add("pencil-bar-svg");

  const w = Math.min(100, Math.max(0, pct));
  const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  bg.setAttribute("x", "0");
  bg.setAttribute("y", "2");
  bg.setAttribute("width", "100");
  bg.setAttribute("height", "12");
  bg.setAttribute("fill", "rgba(0,0,0,0.06)");
  bg.setAttribute("rx", "2");
  svg.appendChild(bg);

  if (w > 0) {
    const bar = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bar.setAttribute("x", "0");
    bar.setAttribute("y", "2");
    bar.setAttribute("width", String(w));
    bar.setAttribute("height", "12");
    bar.setAttribute("fill", "#2B2116");
    bar.setAttribute("rx", "2");
    svg.appendChild(bar);
  }
}

export function renderDotPlot(plotSvg, scamCalls) {
  plotSvg.setAttribute("viewBox", "0 0 600 220");
  plotSvg.classList.add("dot-plot-svg");

  const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
  axis.setAttribute("x1", "120"); axis.setAttribute("y1", "200");
  axis.setAttribute("x2", "580"); axis.setAttribute("y2", "200");
  axis.setAttribute("stroke", "#2B2116"); axis.setAttribute("stroke-width", "2");
  plotSvg.appendChild(axis);

  [0, 15, 30, 45, 60].forEach((s) => {
    const x = 120 + (s / 60) * 460;
    const tick = document.createElementNS("http://www.w3.org/2000/svg", "line");
    tick.setAttribute("x1", String(x)); tick.setAttribute("y1", "200");
    tick.setAttribute("x2", String(x)); tick.setAttribute("y2", "206");
    tick.setAttribute("stroke", "#2B2116");
    plotSvg.appendChild(tick);

    const lbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    lbl.setAttribute("x", String(x)); lbl.setAttribute("y", "216");
    lbl.setAttribute("font-size", "10"); lbl.setAttribute("text-anchor", "middle");
    lbl.setAttribute("font-family", "IBM Plex Mono");
    lbl.textContent = `${s}s`;
    plotSvg.appendChild(lbl);
  });

  scamCalls.slice(0, 10).forEach((c, idx) => {
    const y = 20 + idx * 18;
    const nameLbl = document.createElementNS("http://www.w3.org/2000/svg", "text");
    nameLbl.setAttribute("x", "110"); nameLbl.setAttribute("y", String(y + 4));
    nameLbl.setAttribute("font-size", "10"); nameLbl.setAttribute("text-anchor", "end");
    nameLbl.setAttribute("font-family", "IBM Plex Mono");
    nameLbl.textContent = c.id;
    plotSvg.appendChild(nameLbl);

    if (c.alerted && c.alert_t != null) {
      const dotX = 120 + Math.min(1.0, Math.max(0, c.alert_t / 60)) * 460;
      const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", String(dotX)); dot.setAttribute("cy", String(y));
      dot.setAttribute("r", "5"); dot.setAttribute("fill", "#A82A14");
      plotSvg.appendChild(dot);
    } else {
      const cross = document.createElementNS("http://www.w3.org/2000/svg", "text");
      cross.setAttribute("x", "125"); cross.setAttribute("y", String(y + 4));
      cross.setAttribute("font-size", "12"); cross.setAttribute("fill", "#A82A14");
      cross.setAttribute("font-weight", "bold"); cross.setAttribute("font-family", "IBM Plex Mono");
      cross.textContent = "✕ MISSED";
      plotSvg.appendChild(cross);
    }
  });
}
