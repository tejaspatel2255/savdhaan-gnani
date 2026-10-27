/**
 * User-visible strings dictionary in Hindi, English, and Gujarati.
 * All visible UI labels must come from here.
 */
export const LANGS = [
  { code: "hi-IN", label: "हिंदी" },
  { code: "gu-IN", label: "ગુજરાતી" },
];

export const STRINGS = {
  brand_title: { hi: "सावधान", en: "SAVDHAAN", gu: "સાવધાન" },
  tagline: { hi: "हर कॉल पर नज़र", en: "Guardian Eye on every call", gu: "દરેક કોલ પર નજર" },
  synthetic_label: { hi: "सिंथेटिक कॉल", en: "SYNTHETIC", gu: "કૃત્રિમ કોલ" },
  tape_title: { hi: "कान · पर्ची", en: "THE TAPE", gu: "કાન · પહોંચ" },
  eye_title: { hi: "नज़र · रक्षक", en: "THE EYE", gu: "નજર · રક્ષક" },
  why_title: { hi: "क्यों? · संकेत सूची", en: "WHY THIS SCORE", gu: "કેમ? · સંકેત યાદી" },
  phone_title: { hi: "सामने वाले का फ़ोन", en: "LISTENER'S PHONE", gu: "સામેવાળાનો ફોન" },
  awaaz_title: { hi: "आवाज़", en: "AUDIO WAVEFORM", gu: "અવાજ" },
  footer_text: {
    hi: "सुनता है: Gnani Prisma v2.5 · बोलता है: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
    en: "STT: Gnani Prisma v2.5 · TTS: Gnani Timbre v3.0 · SYNTHETIC DEMO, no real calls",
    gu: "સાંભળે છે: Gnani Prisma v2.5 · બોલે છે: Gnani Timbre v3.0 · SYNTHETIC DEMO",
  },
  footer_eval_link: {
    hi: "हिसाब-किताब · Evaluation",
    en: "Khata · Evaluation",
    gu: "હિસાબ-કિતાબ · Evaluation",
  },
  tape_empty: {
    hi: "पर्ची यहाँ छपेगी... Slips print here once a call starts.",
    en: "Slips print here once a call starts.",
    gu: "પહોંચ અહીં લખાશે... Slips print here once a call starts.",
  },
  tape_jump_latest: { hi: "नीचे · ताज़ा पर्ची", en: "Bottom · Jump to latest", gu: "નીચે · નવી પહોંચ" },
  why_empty: { hi: "अभी कोई संकेत नहीं · सुरक्षित बातचीत", en: "No signals yet · Clean call", gu: "હજી કોઈ સંકેત નથી · સુરક્ષિત વાતચીત" },
  state_idle: { hi: "कॉल शुरू करें · Start a call", en: "Start a call", gu: "કોલ શરૂ કરો · Start a call" },
  state_listening: { hi: "सुन रहा हूँ · Listening", en: "Listening", gu: "સાંભળી રહ્યો છું · Listening" },
  state_ended: { hi: "कॉल ख़त्म · Call ended", en: "Call ended", gu: "કોલ પૂરો થયો · Call ended" },
  level_calm: { hi: "शांत · CALM", en: "CALM", gu: "શાંત · CALM" },
  level_careful: { hi: "सतर्क · CAREFUL", en: "CAREFUL", gu: "સાવચેત · CAREFUL" },
  level_danger: { hi: "खतरा · DANGER", en: "DANGER", gu: "જોખમ · DANGER" },
  btn_start: { hi: "कॉल शुरू करें · Start call", en: "Start call", gu: "કોલ શરૂ કરો · Start call" },
  btn_stop: { hi: "कॉल रोकें · Stop call", en: "Stop call", gu: "કોલ રોકો · Stop call" },
  speak_warning_label: { hi: "बोलकर चेतावनी", en: "Speak the warning", gu: "બોલીને ચેતવણી" },
  reconnecting: { hi: "पुनः संपर्क जोड़ रहे हैं...", en: "Reconnecting...", gu: "ફરી સંપર્ક જોડાઈ રહ્યો છે..." },
  simulated_notice: {
    hi: "परिवार को सूचना भेजी · Family alerted (SIMULATED, nothing is sent)",
    en: "Family alerted (SIMULATED, nothing is sent)",
    gu: "પરિવારને જાણ કરી · Family alerted (SIMULATED)",
  },
  risk_announcement_calm: { hi: "जोखिम स्तर शांत, अंक", en: "Risk level calm, score", gu: "જોખમ સ્તર શાંત, અંક" },
  risk_announcement_careful: { hi: "जोखिम स्तर सतर्क, अंक", en: "Risk level careful, score", gu: "જોખમ સ્તર સાવચેત, અંક" },
  risk_announcement_danger: { hi: "जोखिम स्तर खतरा, अंक", en: "Risk level danger, score", gu: "જોખમ સ્તર ભયજનક, અંક" },
  alert_announcement: { hi: "सावधान! धोखाधड़ी का खतरा पहचाना गया!", en: "Alert! High scam likelihood detected!", gu: "સાવધાન! છેતરપિંડીનું જોખમ જણાયું!" },
  call_already_running: { hi: "एक कॉल पहले से चल रही है", en: "A call is already running", gu: "એક કોલ પહેલેથી ચાલુ છે" },

  /* Error Codes (plain words for a worried person) */
  no_key: { hi: "API कुंजी मौजूद नहीं है", en: "API key is missing", gu: "API કી ગોઠવેલ નથી" },
  auth: { hi: "प्रमाणीकरण विफल (कुंजी जांचें)", en: "Authentication failed", gu: "ઓળખ ચકાસણી નિષ્ફળ રહી" },
  auth_failed: { hi: "संपर्क अनुमति अस्वीकृत", en: "Authentication failed", gu: "ઓળખ ચકાસણી નિષ્ફળ રહી" },
  rate_limited: { hi: "सर्वर व्यस्त है, थोड़ी देर में पुनः प्रयास करें", en: "Server busy, please wait a moment", gu: "સર્વર વ્યસ્ત છે, થોડીવાર રાહ જુઓ" },
  credits: { hi: "क्रेडिट समाप्त हो गए हैं", en: "Service credits exhausted", gu: "સેવા ક્રેડિટ સમાપ્ત થઈ ગયા છે" },
  network: { hi: "नेटवर्क त्रुटि (संपर्क टूटा)", en: "Network connection error", gu: "નેટવર્ક જોડાણ કપાઈ ગયું" },
  stt_closed: { hi: "वाक-पहचान संपर्क बंद हुआ", en: "Speech recognition closed", gu: "વાક-ઓળખ જોડાણ બંધ થયું" },
  stt_unreachable: { hi: "वाक-पहचान सर्वर उपलब्ध नहीं है", en: "Speech recognition server unreachable", gu: "વાક-ઓળખ સર્વર ઉપલબ્ધ નથી" },
  tts_failed: { hi: "चेतावनी आवाज़ तैयार नहीं हो सकी (बीप बजेगी)", en: "Warning audio unavailable (beep playing)", gu: "ચેતવણી અવાજ ઉપલબ્ધ નથી (બીપ વાગશે)" },
  tts_over_cap: { hi: "आवाज़ सीमा समाप्त (बीप बजेगी)", en: "Audio limit reached (beep playing)", gu: "અવાજ મર્યાદા સમાપ્ત (બીપ વાગશે)" },
  session_cap: { hi: "15 मिनट की सत्र सीमा पूरी हुई", en: "15-minute call stream limit reached", gu: "૧૫ મિનિટની કોલ મર્યાદા પૂરી થઈ" },
  bad_audio_format: { hi: "ऑडियो प्रारूप अमान्य है", en: "Invalid audio format", gu: "ઓડિયો ફોર્મેટ અયોગ્ય છે" },
  cap_reached: { hi: "सत्र सीमा समाप्त हो गई", en: "Safety usage cap reached", gu: "સુરક્ષા મર્યાદા પૂરી થઈ" },
  bad_request: { hi: "अमान्य अनुरोध भेजा गया", en: "Invalid request payload", gu: "અમાન્ય વિનંતી" },
  internal: { hi: "आंतरिक सर्वर समस्या", en: "Internal server issue", gu: "આંતરિક સર્વર સમસ્યા" },

  /* Mic errors */
  mic_permission_needed: { hi: "माइक की अनुमति चाहिए", en: "Microphone permission needed", gu: "માઈકની મંજૂરી આપો" },
  mic_no_device: { hi: "माइक्रोफ़ोन नहीं मिला", en: "No microphone detected", gu: "કોઈ માઈક્રોફોન મળ્યો નથી" },
  mic_denied: { hi: "माइक्रोफ़ोन की अनुमति अस्वीकृत (सेटिंग्स में चालू करें)", en: "Microphone access blocked (enable in settings)", gu: "માઈક્રોફોન મંજૂરી નકારાઈ (સેટિંગ્સમાં ચાલુ કરો)" },
  mic_unsupported: { hi: "इस ब्राउज़र में माइक समर्थित नहीं है", en: "Browser does not support audio capture", gu: "આ બ્રાઉઝરમાં માઈક સમર્થિત નથી" },

  /* Phone screen text */
  phone_calm_title: { hi: "कॉल पर नज़र है", en: "Savdhaan is listening", gu: "કોલ પર નજર છે" },
  phone_calm_sub: { hi: "सुरक्षित बातचीत जारी है", en: "Call in progress", gu: "સુરક્ષિત વાતચીત ચાલુ છે" },
  phone_careful: { hi: "सतर्क रहिए · Stay alert", en: "Stay alert · Unusual cues detected", gu: "સાવચેત રહો · Stay alert" },
  phone_danger_title: { hi: "रुकिए!", en: "STOP!", gu: "ઊભા રહો!" },
  phone_danger_line1_hi: { hi: "यह कॉल धोखा हो सकती है।", en: "This call may be a scam.", gu: "આ કોલ છેતરપિંડી હોઈ શકે છે." },
  phone_danger_line1_en: { hi: "This call may be a scam.", en: "This call may be a scam.", gu: "This call may be a scam." },
  phone_danger_line2_hi: { hi: "OTP, PIN या पैसे न दें।", en: "Do not share OTP, PIN or money.", gu: "કોઈને OTP, PIN કે પૈસા ન આપશો." },
  phone_danger_line2_en: { hi: "Do not share OTP, PIN or money.", en: "Do not share OTP, PIN or money.", gu: "Do not share OTP, PIN or money." },
  phone_danger_line3_hi: { hi: "कॉल काट दें।", en: "Hang up now.", gu: "તરત જ કોલ કાપી નાખો." },
  phone_danger_line3_en: { hi: "Hang up now.", en: "Hang up now.", gu: "Hang up now." },
  phone_hangup_btn: { hi: "कॉल काटें · Hang up", en: "Hang up", gu: "કોલ કાપો · Hang up" },
  phone_ended_safe: { hi: "सुरक्षित · Call ended", en: "Safe · Call ended", gu: "સુરક્ષિત · Call ended" },
  tap_to_hear: { hi: "सुनने के लिए दबाएँ", en: "Tap to hear warning", gu: "સાંભળવા માટે દબાવો" },

  /* Stamp */
  stamp_title: { hi: "सावधान!", en: "SAVDHAAN!", gu: "સાવધાન!" },
  stamp_sub: { hi: "SCAM LIKELY · धोखा हो सकता है", en: "SCAM LIKELY", gu: "SCAM LIKELY · છેતરપિંડી શક્ય" },
  stamp_pinned_prefix: { hi: "मुहर · fired at", en: "Stamp · fired at", gu: "સિક્કો · fired at" },

  /* Receipt */
  receipt_title: { hi: "कॉल रसीद · CALL RECEIPT", en: "CALL RECEIPT", gu: "કોલ પહોંચ · CALL RECEIPT" },
  receipt_safe: { hi: "सुरक्षित · SAFE", en: "SAFE", gu: "સુરક્ષિત · SAFE" },
  receipt_scam: { hi: "धोखा रोका · SCAM FLAGGED", en: "SCAM FLAGGED", gu: "છેતરપિંડી રોકી · SCAM FLAGGED" },
  btn_replay: { hi: "फिर से चलाएँ · Replay", en: "Replay", gu: "ફરી ચલાવો · Replay" },
  btn_close: { hi: "बंद करें · Close", en: "Close", gu: "બંધ કરો · Close" },
  receipt_time_none: { hi: "कोई नहीं · none", en: "none", gu: "કોઈ નહીં · none" },
  receipt_na: { hi: "लागू नहीं · n/a", en: "n/a", gu: "લાગુ નથી · n/a" },
  badge_static: {
    hi: "स्टैटिक डेमो · रिकॉर्डेड",
    en: "STATIC DEMO · recorded",
    gu: "સ્ટેટિક ડેમો · રેકોર્ડેડ",
  },
  static_footer_note: {
    hi: "रिकॉर्ड किया गया डेमो; किसी लाइव कॉल का विश्लेषण नहीं हो रहा है",
    en: "recorded demo; no live call is being analysed",
    gu: "રેકોર્ડ કરેલ ડેમો; કોઈ લાઈવ કોલનું વિશ્લેષણ કરવામાં આવી રહ્યું નથી",
  },
};

const loggedFallbacks = new Set();

export function t(key, lang = "hi") {
  const item = STRINGS[key];
  if (!item) return key;

  const code = lang.startsWith("gu") ? "gu" : (lang.startsWith("hi") ? "hi" : "en");
  if (item[code]) {
    return item[code];
  }

  // Fallback to English and log once in dev mode
  if (window.location.search.includes("dev=1") && !loggedFallbacks.has(`${key}_${code}`)) {
    loggedFallbacks.add(`${key}_${code}`);
    console.warn(`[I18N] Missing string key "${key}" for language "${code}". Falling back to English.`);
  }

  return item["en"] || item["hi"] || key;
}
