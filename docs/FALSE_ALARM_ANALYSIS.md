# False-Alarm and Miss Analysis (Seen Dev and Test Splits)

> **Disclosure**: Both the dev split and test split have already been seen and scored during earlier phases (test split scored twice). Rule proposals arising from this analysis are documented adaptations to seen data, not blind generalizations. The blind test set (`blind_calls.json`) was strictly excluded from this analysis.

---

## 1. Executive Summary Table

| Split | Call ID | Ground Truth | Final Score | Highest Level | Outcome | Root Cause / Note |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Dev** | `D06_emi_reminder` | Legit | 0 | CALM | Clean | Dampened by "आपकी ईएमआई" (`SAFE_REMINDER`, -15) |
| **Dev** | `D07_delivery` | Legit | 0 | CALM | Clean | Dampened by "डिलीवरी पार्टनर" (`SAFE_DELIVERY`, -15) |
| **Dev** | `D08_doctor_appointment` | Legit | 0 | CALM | Clean | Dampened by "अपॉइंटमेंट" (`SAFE_APPT`, -15) |
| **Dev** | `D09_family` | Legit | 6 | CALM | Clean | Mild urgency ("जल्दी", "अभी"), under careful threshold (30) |
| **Dev** | `D10_bank_awareness` | Legit | 0 | CALM | Clean | Multiple safe dampeners ("किसी के साथ शेयर न", "बैंक कभी ओटीपी") |
| **Test** | `T06_electricity_bill` | Legit | 0 | CALM | Clean | No scam patterns matched |
| **Test** | `T07_passport_verification` | Legit | 10 | CALM | Clean | Authority hit ("पुलिस" +10), remains well below careful |
| **Test** | `T08_friend_news` | Legit | 45 | **CAREFUL** | Elevated | Matched "गिरफ्तार" (+22 threat) and "पुलिस" (+10 authority) + combo |
| **Test** | `T09_courier_otp` | Legit | 46 | **CAREFUL** | Elevated | Courier asks for delivery OTP: "ओटीपी दे" (+30 credentials) + "अभी" (+6) |
| **Test** | `T10_customer_care` | Legit | 0 | CALM | Clean | No scam patterns matched |
| **Test** | `T05_card_pin` | Scam | 43 | **CAREFUL (Missed Alert)** | **Miss (FN)** | Needs score ≥ 60 for DANGER. Only reached 43 (no combo fired) |

---

## 2. Detailed Breakdown: Legit Calls Reaching Careful

### A. `T08_friend_news` (Friends discussing a crime news report)
- **Max Score**: 45 / 100
- **Level**: `careful`
- **Turns and Trigger Hits**:
  - Turn 0 (Caller): *"सुना तुमने? शर्मा जी के बेटे को पुलिस ने गिरफ्तार कर लिया।"*
    - Hit: Category `threat`, Matched `गिरफ्तार`, Weight: +22
  - Turn 1 (Listener): *"क्या बात कर रहे हो? पुलिस क्यों ले गई?"*
    - Hit: Category `authority`, Matched `पुलिस`, Weight: +10
- **Why it reached Careful**:
  - The combination of a criminal arrest threat keyword and police department keyword in the rolling window triggered combo bonus multipliers, raising the score from 32 to 45 (threshold 30).
  - *Context*: The dialogue is third-person news gossip ("शर्मा जी के बेटे को..."), not a direct threat against the listener.

### B. `T09_courier_otp` (Legitimate delivery boy asking for delivery code at door)
- **Max Score**: 46 / 100
- **Level**: `careful`
- **Turns and Trigger Hits**:
  - Turn 2 (Caller): *"सर, पार्सल देने के लिए कंपनी का एक ओटीपी आया होगा, वह ओटीपी दे दीजिए अभी।"*
    - Hit: Category `credentials`, Matched `ओटीपी दे`, Weight: +30
    - Hit: Category `urgency`, Matched `अभी`, Weight: +6
- **Why it reached Careful**:
  - Direct request for OTP is inherently high-risk (+30) and immediately crosses the careful boundary (30).
  - *Context*: Delivery OTPs are ubiquitous in India, but asking for OTP over a phone call is indistinguishable from scam harvesting unless an explicit delivery context dampener is active. Turn 0 mentions *"डिलीवरी बॉय"* which was not in the safe delivery dampener list.

---

## 3. Detailed Breakdown: Missed Scam `T05_card_pin`

- **Call Title**: Debit card expiry / PIN & CVV theft
- **Max Score**: 43 / 100
- **Alert Triggered**: No (Danger threshold is 60; never alerted)
- **Turn-by-turn trace**:
  - Turn 0: *"नमस्ते, मैं कार्ड सुरक्षा विभाग से बोल रहा हूँ। आपका डेबिट कार्ड बंद होने वाला है।"* -> Score 0 (Unmatched)
  - Turn 2: *"इसे चालू रखने के लिए आपको अपना पिन बताना होगा।"* -> Matched `अपना पिन` (Credentials +30) -> Score 30
  - Turn 3: Listener refuses (*"पिन तो मैं नहीं बताता।"*) -> Score decays to 27
  - Turn 4: *"बस सीवीवी और कार्ड नंबर बताइए, पाँच मिनट में काम हो जाएगा।"* -> Matched `कार्ड नंबर बताइए` (Credentials +30, duplicate category capped) -> Score 30
  - Turn 5: *"जल्दी कीजिए, वरना कार्ड हमेशा के लिए बंद हो जाएगा।"* -> Matched `जल्दी` (Urgency +6) -> Score 43
- **Root Cause of Miss**:
  - The scammer never uttered direct police/arrest threats, legal actions, or digital arrest.
  - The call only hit `credentials` (+30) and `urgency` (+6). The combo rule `COMBO_CRED_URGENCY` provides a +10 boost, totaling 46, which is below the 60 danger threshold required for a spoken interruption.
