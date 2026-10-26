/**
 * User-visible strings dictionary in Hindi and English.
 * All visible UI labels must come from here.
 */
export const LANGS = [
  { code: "hi-IN", label: "हिंदी · Hindi" },
  { code: "en-IN", label: "English" },
];

export const STRINGS = {
  brand_title: { hi: "सावधान", en: "SAVDHAAN" },
  tagline: { hi: "हर कॉल पर नज़र", en: "Guardian Eye on every call" },
  synthetic_label: { hi: "सिंथेटिक कॉल", en: "SYNTHETIC" },
  tape_title: { hi: "कान · पर्ची", en: "THE TAPE" },
  eye_title: { hi: "नज़र · रक्षक", en: "THE EYE" },
  why_title: { hi: "क्यों? · संकेत सूची", en: "WHY THIS SCORE" },
  phone_title: { hi: "सामने वाले का फ़ोन", en: "LISTENER'S PHONE" },
  awaaz_title: { hi: "आवाज़", en: "AUDIO WAVEFORM" },
  footer_text: {
    hi: "सुनता है: Gnani Prisma v2.5 · बोलता है: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
    en: "STT: Gnani Prisma v2.5 · TTS: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
  },
  tape_empty: { hi: "पर्ची यहाँ छपेगी... Slips print here once a call starts.", en: "Slips print here once a call starts." },
  tape_jump_latest: { hi: "नीचे · ताज़ा पर्ची", en: "Bottom · Jump to latest" },
  why_empty: { hi: "अभी कोई संकेत नहीं · सुरक्षित बातचीत", en: "No signals yet · Clean call" },
  state_idle: { hi: "कॉल शुरू करें · Start a call", en: "Start a call" },
  state_listening: { hi: "सुन रहा हूँ · Listening", en: "Listening" },
  state_ended: { hi: "कॉल ख़त्म · Call ended", en: "Call ended" },
  level_calm: { hi: "शांत · CALM", en: "CALM" },
  level_careful: { hi: "सतर्क · CAREFUL", en: "CAREFUL" },
  level_danger: { hi: "खतरा · DANGER", en: "DANGER" },
  btn_start: { hi: "कॉल शुरू करें · Start call", en: "Start call" },
  btn_stop: { hi: "कॉल रोकें · Stop call", en: "Stop call" },
  speak_warning_label: { hi: "बोलकर चेतावनी", en: "Speak the warning" },
  reconnecting: { hi: "पुनः संपर्क जोड़ रहे हैं...", en: "Reconnecting..." },
  simulated_notice: { hi: "परिवार को सूचना भेजी · Family alerted (SIMULATED, nothing is sent)", en: "Family alerted (SIMULATED, nothing is sent)" },
  risk_announcement_calm: { hi: "जोखिम स्तर शांत, अंक", en: "Risk level calm, score" },
  risk_announcement_careful: { hi: "जोखिम स्तर सतर्क, अंक", en: "Risk level careful, score" },
  risk_announcement_danger: { hi: "जोखिम स्तर खतरा, अंक", en: "Risk level danger, score" },
  alert_announcement: { hi: "सावधान! धोखाधड़ी का खतरा पहचाना गया!", en: "Alert! High scam likelihood detected!" },
  call_already_running: { hi: "एक कॉल पहले से चल रही है · A call is already running", en: "A call is already running" },

  /* Error Codes */
  no_key: { hi: "API कुंजी मौजूद नहीं है", en: "GNANI_API_KEY is not configured" },
  auth: { hi: "प्रमाणीकरण विफल (कुंजी जांचें)", en: "Authentication failed (check API key)" },
  rate_limited: { hi: "दर सीमा पार (कृपया प्रतीक्षा करें)", en: "Rate limit exceeded (please wait)" },
  credits: { hi: "क्रेडिट समाप्त हो गए हैं", en: "Gnani credits exhausted" },
  network: { hi: "नेटवर्क त्रुटि (संपर्क टूटा)", en: "Network connection error" },
  stt_closed: { hi: "वाक-पहचान संपर्क बंद हुआ", en: "STT connection closed" },
  tts_failed: { hi: "चेतावनी आवाज़ तैयार नहीं हो सकी", en: "Warning audio generation failed" },
  cap_reached: { hi: "सत्र सीमा समाप्त हो गई", en: "Safety usage cap reached" },
  bad_request: { hi: "अमान्य अनुरोध भेजा गया", en: "Bad request payload" },
  internal: { hi: "आंतरिक सर्वर त्रुटि", en: "Internal server error" },

  /* Phone screen text */
  phone_calm_title: { hi: "कॉल पर नज़र है", en: "Savdhaan is listening" },
  phone_calm_sub: { hi: "सुरक्षित बातचीत जारी है", en: "Call in progress" },
  phone_careful: { hi: "सतर्क रहिए · Stay alert", en: "Stay alert · Unusual cues detected" },
  phone_danger_title: { hi: "रुकिए!", en: "STOP!" },
  phone_danger_line1_hi: { hi: "यह कॉल धोखा हो सकती है।", en: "This call may be a scam." },
  phone_danger_line1_en: { hi: "This call may be a scam.", en: "This call may be a scam." },
  phone_danger_line2_hi: { hi: "OTP, PIN या पैसे न दें।", en: "Do not share OTP, PIN or money." },
  phone_danger_line2_en: { hi: "Do not share OTP, PIN or money.", en: "Do not share OTP, PIN or money." },
  phone_danger_line3_hi: { hi: "कॉल काट दें।", en: "Hang up now." },
  phone_danger_line3_en: { hi: "Hang up now.", en: "Hang up now." },
  phone_hangup_btn: { hi: "कॉल काटें · Hang up", en: "Hang up" },
  phone_ended_safe: { hi: "सुरक्षित · Call ended", en: "Safe · Call ended" },
  tap_to_hear: { hi: "सुनने के लिए दबाएँ · Tap to hear the warning", en: "Tap to hear the warning" },

  /* Stamp */
  stamp_title: { hi: "सावधान!", en: "SAVDHAAN!" },
  stamp_sub: { hi: "SCAM LIKELY · धोखा हो सकता है", en: "SCAM LIKELY" },
  stamp_pinned_prefix: { hi: "मुहर · fired at", en: "Stamp · fired at" },

  /* Receipt */
  receipt_title: { hi: "कॉल रसीद · CALL RECEIPT", en: "CALL RECEIPT" },
  receipt_safe: { hi: "सुरक्षित · SAFE", en: "SAFE" },
  receipt_scam: { hi: "धोखा रोका · SCAM FLAGGED", en: "SCAM FLAGGED" },
  btn_replay: { hi: "फिर से चलाएँ · Replay", en: "Replay" },
  btn_close: { hi: "बंद करें · Close", en: "Close" },
  receipt_time_none: { hi: "कोई नहीं · none", en: "none" },
  receipt_na: { hi: "लागू नहीं · n/a", en: "n/a" },
};

export function t(key, lang = "hi") {
  const item = STRINGS[key];
  if (!item) return key;
  return item[lang] || item["en"] || key;
}
