/**
 * User-visible strings dictionary in Hindi and English.
 * All visible UI labels must come from here.
 */
export const STRINGS = {
  brand_title: {
    hi: "सावधान",
    en: "SAVDHAAN",
  },
  tagline: {
    hi: "हर कॉल पर नज़र",
    en: "Guardian Eye on every call",
  },
  synthetic_label: {
    hi: "सिंथेटिक कॉल",
    en: "SYNTHETIC",
  },
  tape_title: {
    hi: "कान · पर्ची",
    en: "THE TAPE",
  },
  eye_title: {
    hi: "नज़र · रक्षक",
    en: "THE EYE",
  },
  why_title: {
    hi: "क्यों? · संकेत सूची",
    en: "WHY THIS SCORE",
  },
  phone_title: {
    hi: "सामने वाले का फ़ोन",
    en: "LISTENER'S PHONE",
  },
  awaaz_title: {
    hi: "आवाज़",
    en: "AUDIO WAVEFORM",
  },
  footer_text: {
    hi: "सुनता है: Gnani Prisma v2.5 · बोलता है: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
    en: "STT: Gnani Prisma v2.5 · TTS: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
  },
  tape_empty: {
    hi: "पर्ची यहाँ छपेगी... कॉल शुरू होने पर शब्द यहाँ दिखेंगे।",
    en: "Slips print here once a call starts.",
  },
  tape_jump_latest: {
    hi: "नीचे · ताज़ा पर्ची",
    en: "Bottom · Jump to latest",
  },
  why_empty: {
    hi: "अभी कोई संकेत नहीं · सुरक्षित बातचीत",
    en: "No signals yet · Clean call",
  },
  state_idle: {
    hi: "कॉल शुरू करें · Start a call",
    en: "Start a call",
  },
  state_listening: {
    hi: "सुन रहा हूँ · Listening",
    en: "Listening",
  },
  state_ended: {
    hi: "कॉल ख़त्म · Call ended",
    en: "Call ended",
  },
  level_calm: {
    hi: "शांत · CALM",
    en: "CALM",
  },
  level_careful: {
    hi: "सतर्क · CAREFUL",
    en: "CAREFUL",
  },
  level_danger: {
    hi: "खतरा · DANGER",
    en: "DANGER",
  },
  btn_start: {
    hi: "कॉल शुरू करें · Start call",
    en: "Start call",
  },
  btn_stop: {
    hi: "कॉल रोकें · Stop call",
    en: "Stop call",
  },
  reconnecting: {
    hi: "पुनः संपर्क जोड़ रहे हैं...",
    en: "Reconnecting...",
  },
  simulated_notice: {
    hi: "परिवार को सूचना (सिंथेटिक डेमो)",
    en: "Family alerted (SIMULATED)",
  },
  risk_announcement_calm: {
    hi: "जोखिम स्तर शांत, अंक",
    en: "Risk level calm, score",
  },
  risk_announcement_careful: {
    hi: "जोखिम स्तर सतर्क, अंक",
    en: "Risk level careful, score",
  },
  risk_announcement_danger: {
    hi: "जोखिम स्तर खतरा, अंक",
    en: "Risk level danger, score",
  },
  alert_announcement: {
    hi: "सावधान! धोखाधड़ी का खतरा पहचाना गया!",
    en: "Alert! High scam likelihood detected!",
  },
};

export function t(key, lang = "hi") {
  const item = STRINGS[key];
  if (!item) return key;
  return item[lang] || item["en"] || key;
}
