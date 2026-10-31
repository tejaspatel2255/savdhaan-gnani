# Responsive Design & Layout Architecture

Savdhaan adapts seamlessly across all viewports from 320 px phones to 2560 px displays without layout breaks or horizontal overflow.

## Viewport Adaptations

1. **Mobile Phones (< 600 px)**:
   - Single-column linear layout. The Nazar Eye and score appear immediately above the fold, followed by the phone frame, tape slips, and why-list.
   - Touch targets for all buttons and interactive controls are guaranteed `>= 44 px`.
   - Headers wrap smoothly into a two-line mobile grid with side-by-side live controls.

2. **Tablets Portrait & Phablets (600 px - 999 px)**:
   - Two-column layout: Eye spans top width; phone frame and score evidence sit side-by-side; tape scrolls below.

3. **Laptops & Landscape Displays (1000 px+)**:
   - Three-column control room: Left tape slips, center sticky Eye and risk meter, right why-list and active phone frame.

4. **Fit-to-Screen Dashboard (>= 1000 px wide and >= 800 px tall)**:
   - Page scrolling is eliminated (`overflow: hidden` on viewport); inner panels (tape, why-list, phone) scroll independently.

## Accessibility & Contrast Standards

- **Touch Targets**: Minimum `44x44 px` on all viewports `<= 1024 px` (minimum `32 px` on desktop).
- **Legibility**: Minimum font size `11 px` for all secondary Indic labels and metadata chips.
- **Color Contrast**: Minimum `4.5:1` ratio for normal text and `3.0:1` for large/bold text across dark and light surfaces.

## Automated Auditing

Run the audit suite against the active demo server or static server:

```bash
# Audit control room UI (15 viewports x 3 states)
python scripts/responsive_audit.py --shots docs/screens/responsive

# Audit Khata evaluation report (15 viewports)
python scripts/responsive_audit.py --page report --shots docs/screens/responsive_report
```
Screenshots are written to `docs/screens/responsive/` and `docs/screens/responsive_report/`.
