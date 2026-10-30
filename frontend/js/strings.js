/**
 * User-visible strings. English (en) is the PRIMARY text everywhere.
 * hi / gu hold the SECONDARY text in that language only (no English words),
 * shown smaller under or beside the English by i18n.js.
 */
export const LANGS = [
  { code: "hi-IN", label: "Hindi · हिंदी" },
  { code: "gu-IN", label: "Gujarati · ગુજરાતી" },
  { code: "en-IN", label: "English · Hinglish" },
];

export const STRINGS = {
  brand_title: { hi: "सावधान", en: "SAVDHAAN", gu: "સાવધાન" },
  tagline: { hi: "हर कॉल पर नज़र", en: "Guardian Eye on every call", gu: "દરેક કોલ પર નજર" },
  synthetic_label: { hi: "सिंथेटिक कॉल", en: "SYNTHETIC", gu: "કૃત્રિમ કોલ" },
  tape_title: { hi: "कॉल की पर्ची", en: "THE TAPE", gu: "કોલની પહોંચ" },
  eye_title: { hi: "नज़र · रक्षक", en: "THE EYE", gu: "નજર · રક્ષક" },
  why_title: { hi: "यह स्कोर क्यों?", en: "WHY THIS SCORE", gu: "આ સ્કોર કેમ?" },
  phone_title: { hi: "सुनने वाले का फ़ोन", en: "LISTENER'S PHONE", gu: "સાંભળનારનો ફોન" },
  awaaz_title: { hi: "आवाज़", en: "AUDIO WAVEFORM", gu: "અવાજ" },
  footer_text: {
    hi: "",
    en: "STT: Gnani Prisma v2.5 · TTS: Gnani Timbre v3.0 · Synthetic demo, no real calls",
    gu: "",
  },
  footer_eval_link: { hi: "हिसाब-किताब", en: "Evaluation Khata", gu: "હિસાબ-કિતાબ" },
  tape_empty: { hi: "कॉल शुरू होने पर पर्चियाँ यहाँ छपेंगी।", en: "Slips print here once a call starts.", gu: "કોલ શરૂ થતાં પહોંચ અહીં છપાશે." },
  tape_jump_latest: { hi: "ताज़ा पर्ची पर जाएँ", en: "Jump to latest", gu: "નવી પહોંચ પર જાઓ" },
  why_empty: { hi: "अभी कोई संकेत नहीं", en: "No signals yet · Clean call", gu: "હજી કોઈ સંકેત નથી" },
  state_idle: { hi: "कॉल शुरू करें", en: "Start a call", gu: "કોલ શરૂ કરો" },
  state_listening: { hi: "सुन रहा हूँ", en: "Listening", gu: "સાંભળી રહ્યો છું" },
  state_ended: { hi: "कॉल ख़त्म", en: "Call ended", gu: "કોલ પૂરો થયો" },
  level_calm: { hi: "शांत", en: "CALM", gu: "શાંત" },
  level_careful: { hi: "सतर्क", en: "CAREFUL", gu: "સાવચેત" },
  level_danger: { hi: "खतरा", en: "DANGER", gu: "જોખમ" },
  btn_start: { hi: "कॉल शुरू करें", en: "Start call", gu: "કોલ શરૂ કરો" },
  btn_stop: { hi: "कॉल रोकें", en: "Stop call", gu: "કોલ રોકો" },
  speak_warning_label: { hi: "बोलकर चेतावनी", en: "Speak the warning", gu: "બોલીને ચેતવણી" },
  reconnecting: { hi: "फिर से जुड़ रहे हैं...", en: "Reconnecting...", gu: "ફરી જોડાઈ રહ્યું છે..." },
  simulated_notice: { hi: "परिवार को सूचना भेजी (नकली, कुछ भेजा नहीं गया)", en: "Family alerted (SIMULATED, nothing is sent)", gu: "પરિવારને જાણ કરી (નકલી, કંઈ મોકલાયું નથી)" },
  risk_announcement_calm: { hi: "जोखिम स्तर शांत, अंक", en: "Risk level calm, score", gu: "જોખમ સ્તર શાંત, અંક" },
  risk_announcement_careful: { hi: "जोखिम स्तर सतर्क, अंक", en: "Risk level careful, score", gu: "જોખમ સ્તર સાવચેત, અંક" },
  risk_announcement_danger: { hi: "जोखिम स्तर खतरा, अंक", en: "Risk level danger, score", gu: "જોખમ સ્તર ભયજનક, અંક" },
  alert_announcement: { hi: "सावधान! धोखाधड़ी का खतरा पहचाना गया!", en: "Alert! High scam likelihood detected!", gu: "સાવધાન! છેતરપિંડીનું જોખમ જણાયું!" },
  call_already_running: { hi: "एक कॉल पहले से चल रही है", en: "A call is already running", gu: "એક કોલ પહેલેથી ચાલુ છે" },

  /* Error codes (plain words for a worried person) */
  no_key: { hi: "API कुंजी मौजूद नहीं है", en: "API key is missing", gu: "API કી ગોઠવેલ નથી" },
  auth: { hi: "प्रमाणीकरण विफल (कुंजी जांचें)", en: "Authentication failed", gu: "ઓળખ ચકાસણી નિષ્ફળ રહી" },
  auth_failed: { hi: "प्रमाणीकरण विफल", en: "Authentication failed", gu: "ઓળખ ચકાસણી નિષ્ફળ રહી" },
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
  demo_mode: { hi: "डेमो मोड में यह सुविधा बंद है", en: "This feature is switched off in demo mode", gu: "ડેમો મોડમાં આ સુવિધા બંધ છે" },
  bad_request: { hi: "अमान्य अनुरोध भेजा गया", en: "Invalid request payload", gu: "અમાન્ય વિનંતી" },
  internal: { hi: "आंतरिक सर्वर समस्या", en: "Internal server issue", gu: "આંતરિક સર્વર સમસ્યા" },

  /* Microphone errors */
  mic_permission_needed: { hi: "माइक की अनुमति चाहिए", en: "Microphone permission needed", gu: "માઈકની મંજૂરી આપો" },
  mic_no_device: { hi: "माइक्रोफ़ोन नहीं मिला", en: "No microphone detected", gu: "કોઈ માઈક્રોફોન મળ્યો નથી" },
  mic_denied: { hi: "माइक्रोफ़ोन की अनुमति अस्वीकृत (सेटिंग्स में चालू करें)", en: "Microphone access blocked (enable in settings)", gu: "માઈક્રોફોન મંજૂરી નકારાઈ (સેટિંગ્સમાં ચાલુ કરો)" },
  mic_unsupported: { hi: "इस ब्राउज़र में माइक समर्थित नहीं है", en: "Browser does not support audio capture", gu: "આ બ્રાઉઝરમાં માઈક સમર્થિત નથી" },

  /* Phone screen */
  phone_calm_title: { hi: "कॉल पर नज़र है", en: "Savdhaan is listening", gu: "કોલ પર નજર છે" },
  phone_calm_sub: { hi: "सुरक्षित बातचीत जारी है", en: "Call in progress", gu: "સુરક્ષિત વાતચીત ચાલુ છે" },
  phone_careful: { hi: "सतर्क रहिए", en: "Stay alert · Unusual cues detected", gu: "સાવચેત રહો" },
  phone_danger_title: { hi: "रुकिए!", en: "STOP!", gu: "ઊભા રહો!" },
  phone_danger_line1: { hi: "यह कॉल धोखा हो सकती है।", en: "This call may be a scam.", gu: "આ કોલ છેતરપિંડી હોઈ શકે છે." },
  phone_danger_line2: { hi: "OTP, PIN या पैसे न दें।", en: "Do not share OTP, PIN or money.", gu: "કોઈને OTP, PIN કે પૈસા ન આપશો." },
  phone_danger_line3: { hi: "कॉल काट दें।", en: "Hang up now.", gu: "તરત જ કોલ કાપી નાખો." },
  phone_hangup_btn: { hi: "कॉल काटें", en: "Hang up", gu: "કોલ કાપો" },
  phone_ended_safe: { hi: "सुरक्षित · कॉल ख़त्म", en: "Safe · Call ended", gu: "સુરક્ષિત · કોલ પૂરો" },
  tap_to_hear: { hi: "सुनने के लिए दबाएँ", en: "Tap to hear warning", gu: "સાંભળવા માટે દબાવો" },
  voice_off: { hi: "बोलकर चेतावनी बंद है", en: "Spoken warning is switched off", gu: "બોલીને ચેતવણી બંધ છે" },
  voice_missing: { hi: "रिकॉर्ड की आवाज़ यहाँ उपलब्ध नहीं (बीप बजेगी)", en: "Recorded voice not included in this copy (beep playing)", gu: "રેકોર્ડ કરેલો અવાજ અહીં નથી (બીપ વાગશે)" },
  family_title: { hi: "परिवार को सूचना", en: "FAMILY ALERTED", gu: "પરિવારને જાણ" },

  /* Stamp */
  stamp_title: { hi: "सावधान!", en: "BEWARE!", gu: "સાવધાન!" },
  stamp_sub: { hi: "धोखा हो सकता है", en: "SCAM LIKELY", gu: "છેતરપિંડી શક્ય" },
  stamp_pinned_prefix: { hi: "मुहर लगी", en: "Stamp fired at", gu: "સિક્કો લાગ્યો" },

  /* Receipt */
  receipt_title: { hi: "कॉल रसीद", en: "CALL RECEIPT", gu: "કોલ પહોંચ" },
  receipt_safe: { hi: "सुरक्षित", en: "SAFE", gu: "સુરક્ષિત" },
  receipt_scam: { hi: "धोखा रोका गया", en: "SCAM FLAGGED", gu: "છેતરપિંડી રોકી" },
  btn_replay: { hi: "फिर से चलाएँ", en: "Replay", gu: "ફરી ચલાવો" },
  btn_close: { hi: "बंद करें", en: "Close", gu: "બંધ કરો" },
  receipt_time_none: { hi: "कोई नहीं", en: "none", gu: "કોઈ નહીં" },
  receipt_na: { hi: "लागू नहीं", en: "n/a", gu: "લાગુ નથી" },

  /* Badges and static mode */
  badge_static: { hi: "रिकॉर्डेड डेमो", en: "RECORDED DEMO", gu: "રેકોર્ડેડ ડેમો" },
  badge_demo: { hi: "रिकॉर्डेड डेमो", en: "DEMO · recorded", gu: "રેકોર્ડેડ ડેમો" },
  static_footer_note: { hi: "रिकॉर्ड किया गया डेमो; कोई लाइव कॉल नहीं सुनी जा रही", en: "Recorded demo; no live call is being analysed", gu: "રેકોર્ડ કરેલ ડેમો; કોઈ લાઈવ કોલ સાંભળાતો નથી" },

  /* Live mic mode */
  btn_listen_live: { hi: "लाइव सुनें", en: "Listen live", gu: "સીધું સાંભળો" },
  live_notice_title: { hi: "लाइव मोड के बारे में", en: "About Live Mode", gu: "Live Mode વિશે" },
  live_notice_body: { hi: "ऑडियो Gnani के क्लाउड पर जाती है। कोई रिकॉर्डिंग नहीं होती।", en: "Audio is sent to Gnani's cloud for transcription. Nothing is saved unless you enable SAVE_LIVE_RUNS.", gu: "ઓડિયો Gnani ના ક્લાઉડ પર જાય છે. SAVE_LIVE_RUNS ચાલુ ન હોય ત્યારે કંઈ સેવ નથી થતું." },
  live_notice_ok: { hi: "समझ गया, शुरू करें", en: "Got it, start", gu: "સમજ્યા, શરૂ કરો" },
  live_state_idle: { hi: "माइक के लिए तैयार", en: "Ready to listen", gu: "સાંભળવા તૈયાર" },
  live_state_permission: { hi: "माइक अनुमति माँग रहा हूँ…", en: "Requesting mic permission…", gu: "માઈક મંજૂરી માંગી રહ્યો છું…" },
  live_state_connecting: { hi: "जोड़ रहा हूँ…", en: "Connecting…", gu: "જોડાઈ રહ્યું છે…" },
  live_state_listening: { hi: "सुन रहा हूँ — बोलें", en: "Listening — speak now", gu: "સાંભળી રહ્યો છું — બોલો" },
  live_state_alert: { hi: "खतरा भाँपा — चेतावनी दी", en: "Scam detected — warning given", gu: "ખતરો ભળ્યો — ચેતવણી દઈ" },
  live_state_stopped: { hi: "सुनना बंद", en: "Stopped", gu: "બંધ" },
  live_btn_stop: { hi: "सुनना बंद करें", en: "Stop listening", gu: "સાંભળવાનું બંધ કરો" },
  live_usage_label: { hi: "उपयोग", en: "STT usage", gu: "ઉપયોગ" },
  live_no_key: { hi: "API कुंजी नहीं — लाइव बंद है", en: "API key missing — live disabled", gu: "API key ગોઠવેલ નથી — live બંધ" },
  live_demo_mode: { hi: "डेमो मोड — लाइव बंद है", en: "Demo mode — live disabled", gu: "ડેમો મોડ — live બંધ" },
  live_source_label: { hi: "स्रोत: LIVE MIC", en: "Source: LIVE MIC", gu: "સ્ત્રોત: LIVE MIC" },
  live_lang_label: { hi: "भाषा चुनें", en: "Language", gu: "ભાષા" },

  /* Try your own words */
  words_panel_title: { hi: "अपने शब्द आज़माएँ", en: "Try your own words", gu: "તમારા શબ્દ અજમાવો" },
  words_placeholder: { hi: "कोई वाक्य यहाँ लिखें या चिपकाएँ…", en: "Type or paste any sentence here…", gu: "કોઈ વાક્ય અહીં ટાઈપ કરો અથવા Paste કરો…" },
  words_btn_analyze: { hi: "विश्लेषण करें", en: "Analyze", gu: "વિશ્લેષણ કરો" },
  words_btn_scam_example: { hi: "स्कैम उदाहरण", en: "Scam example", gu: "Scam ઉદાહરણ" },
  words_btn_safe_example: { hi: "सामान्य उदाहरण", en: "Safe example", gu: "સામાન્ય ઉદાહરણ" },
  words_result_prefix: { hi: "परिणाम:", en: "Result:", gu: "પરિણામ:" },
  words_detected_prefix: { hi: "मिले:", en: "Detected:", gu: "મળ્યા:" },
  words_none_detected: { hi: "कोई संदिग्ध शब्द नहीं मिले", en: "Nothing suspicious detected", gu: "કોઈ શંકાસ્પદ શબ્દ મળ્યા નહીં" },
  words_too_long: { hi: "अधिकतम 2000 अक्षर", en: "Maximum 2000 characters", gu: "મહત્તમ 2000 અક્ષર" },

  /* Words we listen for */
  rules_panel_title: { hi: "हम किन शब्दों पर ध्यान देते हैं", en: "Words we listen for", gu: "કયા શબ્દ ધ્યાનમાં આવે છે" },
  rules_loading: { hi: "लोड हो रहा है…", en: "Loading…", gu: "લોડ થઈ રહ્યું છે…" },
  rules_unavailable: { hi: "नियम उपलब्ध नहीं", en: "Rules unavailable", gu: "નિયમ ઉપલબ્ધ નથી" },
};

const loggedFallbacks = new Set();

/** English by default. Pass "hi" / "hi-IN" / "gu-IN" to get the local text instead. */
export function t(key, lang = "en") {
  const item = STRINGS[key];
  if (!item) return key;
  const code = String(lang).startsWith("gu") ? "gu" : (String(lang).startsWith("hi") ? "hi" : "en");
  if (item[code]) return item[code];
  if (window.location.search.includes("dev=1") && !loggedFallbacks.has(`${key}_${code}`)) {
    loggedFallbacks.add(`${key}_${code}`);
    console.warn(`[I18N] Missing string key "${key}" for language "${code}". Falling back to English.`);
  }
  return item.en || key;
}
