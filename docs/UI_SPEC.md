# SAVDHAAN UI SPEC: "NAZAR" CONTROL ROOM

CONCEPT
A nazar (evil-eye charm) is India's everyday symbol of watchful protection. The UI is built around it: a guardian Eye watches the call; the transcript prints on a paper receipt tape (like an old PCO booth bill); a rubber STAMP slams down when a scam is detected; the call ends with a printed receipt. Bilingual everywhere: Devanagari first, English second. It must look hand-made and Indian, not like a generic dark dashboard.
BANNED LOOKS: purple or blue-purple gradients, glassmorphism, blurred cards, big soft shadows, emoji, stock icon packs, Bootstrap or Tailwind look, white page backgrounds, a centred hero with three cards. Use flat shapes, 2px outlines, paper, ink and stamps.

TOKENS (css/tokens.css, CSS custom properties on :root)
--night #0B0F1E page; --night-2 #121832 panels; --night-3 #1B2347 raised; --line #2C3668 borders
--text #EDE6D6; --muted #9AA3C7; --paper #F3E9D2; --paper-2 #E8DBBC; --ink #2B2116
--nazar-deep #12308F; --nazar-white #F4F7FF; --nazar-light #4DA6FF; --pupil #04060C
Level colours: --calm #4DA6FF (text version #7FC0FF); --careful #FFB400; --danger #E5391F (text version on dark #FF6A4D). Focus ring #FFD36B. --danger-deep #A82A14 is the fill for any danger surface that carries small text (--paper text on it is 5.8:1). --danger itself is for rings, borders, big display text and the stamp border; small danger-coloured text uses the text version. Control outlines (buttons, selects) use --muted, not --line.
Radius: 6px panels, 14px cards, 36px phone, 999px pills. Spacing scale 4, 8, 12, 16, 24, 32, 48. Borders 2px solid var(--line).
The body element carries data-level="calm|careful|danger"; CSS sets --level (and --level-text) from it, and every component uses var(--level).
Background: var(--night) plus a faint jaali lattice, a 48px repeating inline-SVG tile (an eight-pointed star made of two rotated squares, stroke var(--line), opacity .35) used as a CSS background-image data URI.

FONTS (one Google Fonts link in index.html, display=swap; the page must still work without it)
https://fonts.googleapis.com/css2?family=Hind:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Yatra+One&display=swap
Display (logo, stamp, headings): "Yatra One", "Noto Serif Devanagari", Georgia, serif. Body: "Hind", "Noto Sans Devanagari", system-ui, sans-serif. Mono (timecodes, numbers, badges): "IBM Plex Mono", ui-monospace, monospace.
Sizes: body 16px; slip text 19px/1.55 (must read well in a 1080p video); score number 88px mono; stamp 120px display; labels 12px mono uppercase with .08em letter spacing. Put lang="hi" on Devanagari elements.

LAYOUT (desktop 1440x900 is the recording target)
Header bar, 64px: left = small eye icon + "सावधान" (display 30px) + "SAVDHAAN" (mono 12px) + tagline "हर कॉल पर नज़र". Centre = mode badge pill (MOCK dashed grey, REPLAY blue, FILE marigold outline, LIVE MIC vermilion outline with --danger-text text and a pulsing dot) beside a SYNTHETIC pill, shown whenever the session is synthetic. Right = call select, language select, Start button (marigold fill, "कॉल शुरू करें · Start call"), Stop button (outline). Every control at least 44px tall.
Main grid, three columns 34% / 32% / 34%, 24px gaps:
  LEFT   "कान · THE TAPE": transcript slips.
  CENTRE "नज़र · THE EYE": the guardian Eye, score, level label, state line.
  RIGHT  "चौकीदार · WHY" on top (evidence list), "सामने वाले का फ़ोन · LISTENER'S PHONE" below (phone plus simulated family alert).
Bottom strip, 96px: "आवाज़" waveform across the full width. Footer line (mono 12px): "सुनता है: Gnani Prisma v2.5 · बोलता है: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls".
Responsive: 800-1199px = Eye on top spanning full width, Tape and Why side by side, phone below. Under 800px = one column: sticky mini risk bar, Eye, Tape, Why, Phone. Must work at 360px with no horizontal scroll.

THE EYE (inline SVG, viewBox 0 0 400 400, built and updated by js/eye.js)
Layers, back to front:
1 ring-track: circle r=170, stroke var(--night-3), width 16.
2 ring-gauge: circle r=170, stroke var(--level), width 16, round caps, rotated -90deg so it starts at the top; stroke-dasharray = circumference (about 1068); dashoffset = 1068 x (1 - score/100); transition 600ms cubic-bezier(.2,.8,.2,1). In danger add a dashed stripe overlay so it is not colour-only.
3 ticks: 60 short radial ticks from r=186 to r=196; ticks up to the score are var(--level), the rest var(--line).
4 clipped eye: a group clipped by a circle r=150 holding the nazar rings: r=150 --nazar-deep, r=118 --nazar-white, r=86 --nazar-light, pupil r=46 --pupil, and a highlight circle r=8 at offset (-16,-16), white, opacity .85.
5 lids: two rects (top, bottom) filled var(--night-3), clipped by the same circle, with a lash-line curve between them. Lids closed = the eye is asleep.
6 danger overlay: circle r=150 filled var(--danger), opacity 0 normally and .22 in danger; plus 24 radial rays from r=206 to r=232, hidden until danger.
STATES (data-state on the svg element):
  idle: lids closed, 4s breathing loop (scaleY .98 to 1).
  listening: lids open over 500ms; pupil drifts +/-3px on a 6s loop.
  processing (segment_processing event): one blink, lids to 85% closed for 120ms, then open.
  careful: gauge and ticks marigold; pupil radius 42.
  danger: lids wide open, pupil radius 32 (intense stare), red overlay .22, rays pulse on a 1.2s loop, one red vignette flash on the page (a fixed overlay with a 24px solid var(--danger) border that fades in and out; no gradients or blur).
  ended: lids close slowly over 1200ms; the gauge stays at the final score.
The pupil radius also follows audio_level: radius = base + rms x 10 (smoothed, at most +10).
Under the Eye: score in mono 88px with "/100" small; the level label (शांत · CALM, सतर्क · CAREFUL, खतरा · DANGER) with a different icon shape per level (circle-dot, triangle-bang, octagon-hand); then one state line: idle "कॉल शुरू करें · Start a call", listening "सुन रहा हूँ · Listening", ended "कॉल ख़त्म · Call ended". The score counts up or down over 400ms.

THE TAPE (js/tape.js)
A vertical scroll panel. Newest slip at the bottom; auto-scroll smoothly unless the user has scrolled up, in that case show a small pill "नीचे · jump to latest". The panel has role="log" and aria-live="off".
Each slip: background var(--paper), text var(--ink), padding 12px 16px, bottom edge torn with a zigzag (CSS clip-path polygon), a 1px dashed perforation line between slips. Header row: mono timecode (mm:ss from the event t) on the left; on the right a small latency chip such as "312 ms" (hidden in MOCK mode). Body: transcript text, Hind 19px.
When the risk event for that segment arrives, wrap each hit.matched substring (case-insensitive, first occurrence) in a mark element:
  raise hit = highlighter-pen look (marigold background, slight -1deg skew);
  raise hit with weight 20 or more = also a 3px vermilion underline;
  dampen hit = dotted blue underline, no background.
Under the text show category chips: a pill with label_hi bold and label_en small, plus the weight such as "+25".
Entrance: translateY(12px) to 0 with fade over 220ms; the text reveals left to right with clip-path over 350ms.
Empty state: "पर्ची यहाँ छपेगी... Slips print here once a call starts."

THE STAMP (js/stamp.js)
On the alert event, show a stamp centred over the Tape and Eye columns: 8px double border in var(--danger), radius 14px, colour var(--danger), text "सावधान!" (display 120px) above "SCAM LIKELY · धोखा हो सकता है" (mono 16px, colour var(--danger-text)), rotated -8deg, with an SVG filter for a rough rubber edge: feTurbulence baseFrequency .04, numOctaves 2, then feDisplacementMap scale 3.
Animation "slam": from scale 2.4, rotate -14deg, opacity 0 to scale 1, rotate -8deg, opacity .95 in 160ms using cubic-bezier(.2,1.6,.4,1); then the page container shakes for 240ms (translate +/-4px) and a 120ms red flash overlay plays.
After 2.5s the big stamp shrinks into a small pinned stamp at the top of the Tape reading "मुहर · fired at 00:21" (the real alert time). Escape or a click dismisses the big stamp early.

THE WHY LIST (js/why.js)
Heading "क्यों? · Why this score". One row per hit, newest first, sliding in over 200ms. Each row: a small inline-SVG category icon; label_hi (weight 600) over label_en (muted); the matched phrase in mono inside quotation marks; and a pill "+25" (raise; var(--careful), or var(--danger-text) when weight is 20 or more) or "-15" (dampen; var(--calm-text)). A footer row shows category counts as small dot meters. If there are no hits yet: "अभी कोई संकेत नहीं · No signals yet".

THE PHONE (js/phone.js)
A CSS phone frame 280x560, radius 36px, 2px border var(--line), with a notch. Screen states:
  calm: small blue eye icon, "कॉल पर नज़र है" and under it "Savdhaan is listening".
  careful: marigold banner "सतर्क रहिए · Stay alert".
  danger: full-screen vermilion card (background var(--danger-deep), paper text) with "रुकिए!" (display 56px) and three lines, each with an English line below in muted text: "यह कॉल धोखा हो सकती है।" / "OTP, PIN या पैसे न दें।" / "कॉल काट दें।" and a big button "कॉल काटें · Hang up" (a mock: it switches to a "सुरक्षित · Call ended" state).
While the warning audio plays, show 5 animated bars on the card.
Below the phone, a notification card: "परिवार को सूचना भेजी · Family alerted (SIMULATED, nothing is sent)" with the family_alert message. The word SIMULATED is always visible.

THE AWAAZ STRIP (js/waveform.js)
Full-width inline SVG path from a ring buffer of the last 160 audio_level values, mirrored about the centre line, stroke var(--level), 2px, with a soft glow. In MOCK mode draw a gentle synthetic wave and label it MOCK.

THE RECEIPT (js/receipt.js), shown after the summary event
Centred overlay on a dim backdrop. Cream paper, perforated top and bottom edges, mono text. Title "कॉल रसीद · CALL RECEIPT". Rows: Mode; Synthetic yes or no; Duration; Segments; Time to alert (mm:ss, or "none"); Max score; STT latency p50 and p95; Credits used (STT seconds, TTS characters). A verdict stamp: blue "सुरक्षित · SAFE" when no alert fired, vermilion "धोखा रोका · SCAM FLAGGED" when one did. Buttons "फिर से चलाएँ · Replay" and "बंद करें · Close". It prints in with a top-to-bottom clip-path reveal over 900ms.

BEHAVIOUR RULES
- All content comes from WebSocket events (docs/EVENTS.md). Never fake data in the UI. The mode badge always shows the real mode label.
- Audio autoplay: on the Start click, create and resume an AudioContext and play a 0.05s silent buffer so the warning audio can play later. The warning plays through an Audio element using audio_url.
- The WebSocket client auto-reconnects with backoff (1s, 2s, 4s, max 10s) and shows a small "reconnecting" chip.
- Errors: a dismissible bilingual banner under the header showing the error event message.
- Accessibility: an aria-live="polite" region announces level changes ("Risk level careful, score 38"); the alert is announced once with aria-live="assertive". Focus ring 3px #FFD36B, 2px offset. prefers-reduced-motion: no blink, no rays, no shake, no slam; state changes are instant crossfades under 100ms. Text contrast 4.5:1 or better. Colour is never the only signal (icons, labels, stripes).
- Files: frontend/index.html; css/tokens.css, base.css, header.css, eye.css, tape.css, why.css, phone.css, stamp.css, receipt.css; js/app.js, ws.js, api.js, strings.js, eye.js, tape.js, why.js, phone.js, stamp.js, receipt.js, waveform.js. Each CSS file under 300 lines, each JS file under 200.

REPORT PAGE, "KHATA" (frontend/report.html, css/khata.css, js/report.js)
Same tokens and fonts, but the page is a ledger book: cream paper, ruled lines (repeating-linear-gradient every 32px, colour #C9B98F at .5), a red vertical margin line at 72px, headings in the display font, numbers in mono. Title "हिसाब-किताब · EVALUATION KHATA" with the note "synthetic calls only, measured not estimated". Sections: error rate by noise condition (a table plus hand-drawn SVG bars that look like pencil strokes); scam detection (precision, recall, F1, false alarms); time to alert (a dot plot on a 0 to 60 s axis, one dot per scam call); STT latency p50 and p95; a list of missed or falsely flagged calls with their transcripts. Data only from GET /api/eval. If it is absent show "अभी आँकड़े नहीं · Run the evaluation first".

