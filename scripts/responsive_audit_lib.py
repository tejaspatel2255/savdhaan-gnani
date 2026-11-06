"""Helper functions and check logic for responsive audit."""

def check_overlap(elements):
    """Detect if visible header elements collide/overlap by more than 2px."""
    overlaps = []
    n = len(elements)
    for i in range(n):
        for j in range(i + 1, n):
            e1, e2 = elements[i], elements[j]
            r1, r2 = e1["rect"], e2["rect"]
            x_ov = max(0, min(r1["right"], r2["right"]) - max(r1["left"], r2["left"]))
            y_ov = max(0, min(r1["bottom"], r2["bottom"]) - max(r1["top"], r2["top"]))
            if x_ov > 2 and y_ov > 2:
                overlaps.append(f"{e1['label']} overlaps {e2['label']} ({round(x_ov)}x{round(y_ov)}px)")
    return overlaps


def check_responsive_rules(w, h, state, d, page="index"):
    """Evaluate responsive rules across audit parameters."""
    p = []
    if d["scrollW"] > d["W"]:
        p.append(f"horizontal scroll: page {d['scrollW']} > screen {d['W']}")
    for key, label in (("outside", "element outside screen"), ("small", "tap target too small"),
                       ("clipped", "text clipped"), ("tiny", "font under 11px"),
                       ("contrast", "low text contrast")):
        items = sorted(set(d["bad"][key]))
        if items:
            p.append(f"{label}: " + "; ".join(items[:5]) + (f" (+{len(items) - 5} more)" if len(items) > 5 else ""))
    if d.get("hdr_overlaps"):
        p.append("header overlap: " + "; ".join(d["hdr_overlaps"]))
    if page == "report":
        return p

    # Fold check: For wide short laptop viewports and standard viewports
    if w >= 1000 and h >= 520 and state != "receipt":
        if d.get("scrollH", 0) > d["H"] + 1:
            p.append(f"short/wide screen: page scrolls, height {d['scrollH']} > screen {d['H']}")
        for k in ("score", "badge", "demo", "phone", "foot"):
            if d.get(k) and d[k]["bottom"] > d["H"] + 1:
                p.append(f"{k} is below the fold (bottom {round(d[k]['bottom'])} > {d['H']})")
    elif w >= 1000 and h >= 800 and state != "receipt":
        if d["scrollH"] > d["H"] + 1:
            p.append(f"wide+tall screen: page scrolls, height {d['scrollH']} > screen {d['H']}")
        for k in ("score", "badge", "demo", "phone", "foot"):
            if d[k] and d[k]["bottom"] > d["H"] + 1:
                p.append(f"{k} is below the fold (bottom {round(d[k]['bottom'])} > {d['H']})")

    if w <= 700 and d.get("score") and d.get("tape") and d["score"]["top"] > d["tape"]["top"]:
        p.append("phone: the score must come before the tape")
    if w <= 700 and d.get("demo") and d["demo"]["top"] > d["H"] * 1.6:
        p.append(f"phone: sample buttons too far down (top {round(d['demo']['top'])})")
    if state == "receipt" and d.get("dialog"):
        if d["dialog"]["bottom"] > d["H"] + 1 or d["dialog"]["top"] < -1:
            p.append("receipt dialog does not fit the screen")
    return p
