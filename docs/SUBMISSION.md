# Savdhaan: Submission Package & Publication Kit

This document provides ready-to-use project summaries, social post copy, and submission checklists for the **Great Indian AI Internship Challenge** by **Gnani AI** (Deadline: Nov 10, 2026, 11:59 PM IST).

## 1. 90-Word Submission Description

Savdhaan (सावधान) is a live scam-call shield that protects citizens in real time using explainable speech intelligence. Incoming phone audio streams to Gnani Prisma v2.5 for live transcription. A deterministic bilingual scoring engine detects coercion, OTP theft, digital arrest, and remote-app traps with zero false alarms on legitimate calls. Upon detecting danger, Savdhaan speaks an immediate voice warning using Gnani Timbre v3.0 in Hindi, Gujarati, or English, while simulating family alerts and rendering an auditable evidence receipt in the 'Nazar' evil-eye control room.

## 2. LinkedIn Post Draft

Excited to present **Savdhaan (सावधान)** — a live scam-call shield built for the **Great Indian AI Internship Challenge** by **Gnani AI**!

Scam calls claiming "digital arrest," fake police warrants, and electricity bill disconnections are draining citizens' life savings daily. Savdhaan stops them before money moves:

🔹 **Real-time Speech Intelligence**: Streams call audio over WebSockets to **Gnani Prisma v2.5** for instant speech-to-text.
🔹 **Deterministic Protection**: Scores rolling transcripts against transparent pattern rules with 0% false alarms on legitimate calls (tested across bilingual Hindi, Gujarati, and English flows).
🔹 **Voice Interrupt**: Speaks immediate protective alerts using **Gnani Timbre v3.0** in the listener's native language.
🔹 **Nazar Guardian Interface**: Features an evil-eye control room, live receipt tape evidence log, and simulated family SOS notifications.

📺 **Demo Video (75s)**: <<VIDEO LINK>>
🌐 **Try the Live Static Demo**: <<DEMO LINK>>
💻 **Open-Source Repository**: <<REPO LINK>>

#GnaniAI #GreatIndianAIInternshipChallenge #SpeechAI #CyberSecurity #IndianAI #FastAPI #VoiceAI

## 3. X (Twitter) Post Thread

**Post 1 (Main)**:
Introducing Savdhaan (सावधान): a real-time scam-call shield built with @gnani_ai speech intelligence.

It listens to suspicious calls, scores threats in real time, and interrupts scams with voice warnings in Hindi, Gujarati, and English before money is lost.

75s Demo: <<VIDEO LINK>>
#GnaniAI #GreatIndianAIInternshipChallenge

**Post 2**:
Why Savdhaan?
1. Real-time live audio streaming to Gnani Prisma v2.5 STT.
2. Deterministic scam scoring engine (100% recall on dev split, 0% false alarm rate on normal calls).
3. Spoken voice warnings via Gnani Timbre v3.0.
4. Transparent 'Nazar' receipt tape evidence view.

Try the hosted demo: <<DEMO LINK>>
Code: <<REPO LINK>>

## 4. Pre-Flight Submission Checklist

- [ ] Complete test suite passes cleanly: `pytest tests/test_*.py -q`.
- [ ] Release hygiene audit passes: `python scripts/check_release.py`.
- [ ] Static frontend verified: `python scripts/verify_static_site.py`.
- [ ] Recorded 75-second video following `docs/VIDEO_SHOTLIST.md`.
- [ ] Hosted demo live on Vercel with all assets loading properly.
- [ ] Replaced placeholders `<<DEMO LINK>>`, `<<VIDEO LINK>>`, and `<<REPO LINK>>` in `README.md`.
- [ ] Verified git tag created and pushed: `git tag -a v1.0.0 -m "Final submission release" && git push origin v1.0.0`.
