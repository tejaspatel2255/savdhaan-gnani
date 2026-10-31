# Hard Cases Evaluation Census

> **Notice**: These 40 diagnostic test cases evaluate boundary behaviors (negations, customer service,
> delivery OTPs, UPI collects, QR codes, remote apps). They represent known-behavior regression checks,
> **NOT** an official benchmark accuracy figure. These counts are not added to `data/eval/results.json`.

**Summary**: 27 of 40 behave as expected.

| Case ID | Group | Expected | Actual Level | Max Score | Status | Scenario |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `HN01` | hard_negative | **CALM** | CALM | 22 | **PASS** | Bank fraud-awareness automated broadcast |
| `HN02` | hard_negative | **CALM** | CALM | 0 | **PASS** | Courier at the door asking for delivery OTP |
| `HN03` | hard_negative | **CALM** | CALM | 6 | **PASS** | Parent reminding child to pay college fee |
| `HN04` | hard_negative | **CALM** | CALM | 0 | **PASS** | Insurance renewal reminder with email quotation |
| `HN05` | hard_negative | **CALM** | CALM | 6 | **PASS** | Telecom promotional plan offer |
| `HN06` | hard_negative | **CALM** | CALM | 10 | **PASS** | Passport police verification in-person appointment |
| `HN07` | hard_negative | **CALM** | DANGER | 62 | **FAIL** | Friend making a casual joke using the word arrest |
| `HN08` | hard_negative | **CALM** | CALM | 0 | **PASS** | Doctor office appointment confirmation |
| `HN09` | hard_negative | **CALM** | CALM | 0 | **PASS** | Cab driver asking for ride start PIN code in Hinglish/English |
| `HN10` | hard_negative | **CALM** | CALM | 0 | **PASS** | LPG gas cylinder booking reminder |
| `HN11` | hard_negative | **CALM** | CALM | 0 | **PASS** | Society maintenance bill intimation |
| `HN12` | hard_negative | **CALM** | CALM | 0 | **PASS** | Credit card statement generated notice in Gujarati |
| `HN13` | hard_negative | **CALM** | CALM | 0 | **PASS** | Debit card dispatch notification |
| `HN14` | hard_negative | **CALM** | CALM | 0 | **PASS** | Family grocery errand conversation |
| `HN15` | hard_negative | **CALM** | CALM | 0 | **PASS** | Broadband monthly billing advisory |
| `HN16` | hard_negative | **CALM** | CALM | 0 | **PASS** | School parent-teacher meeting intimation |
| `HN17` | hard_negative | **CALM** | CALM | 0 | **PASS** | Appliance maintenance service schedule confirmation |
| `HN18` | hard_negative | **CALM** | CALM | 0 | **PASS** | Casual temple visit conversation in Gujarati |
| `HN19` | hard_negative | **CALM** | CALM | 0 | **PASS** | Utility meter reading confirmation |
| `HN20` | hard_negative | **CALM** | CALM | 0 | **PASS** | Customer support feedback survey |
| `HP01` | hard_positive | **DANGER** | CALM | 6 | **FAIL** | UPI collect request scam (enter PIN to receive money) |
| `HP02` | hard_positive | **DANGER** | CALM | 0 | **FAIL** | QR code scan refund fraud |
| `HP03` | hard_positive | **DANGER** | CAREFUL | 51 | **FAIL** | Remote desktop malware removal scam (AnyDesk) |
| `HP04` | hard_positive | **DANGER** | CALM | 0 | **FAIL** | Work from home task scam with advance fee |
| `HP05` | hard_positive | **DANGER** | DANGER | 75 | **PASS** | SIM block threat with Aadhaar OTP phishing |
| `HP06` | hard_positive | **DANGER** | CALM | 6 | **FAIL** | Extortion loan app blackmail threat |
| `HP07` | hard_positive | **DANGER** | CAREFUL | 44 | **FAIL** | Electricity power cutoff urgency scam |
| `HP08` | hard_positive | **DANGER** | CAREFUL | 39 | **FAIL** | Crypto double money investment fraud |
| `HP09` | hard_positive | **DANGER** | DANGER | 100 | **PASS** | Relative in emergency arrest extortion |
| `HP10` | hard_positive | **DANGER** | DANGER | 100 | **PASS** | Classic digital arrest with secrecy and money transfer |
| `HP11` | hard_positive | **DANGER** | DANGER | 100 | **PASS** | Customs courier parcel threat in Hinglish/English |
| `HP12` | hard_positive | **DANGER** | CAREFUL | 46 | **FAIL** | Credit card reward points phishing |
| `HP13` | hard_positive | **DANGER** | CAREFUL | 44 | **FAIL** | DoT fake multiple SIM seizure threat |
| `HP14` | hard_positive | **DANGER** | DANGER | 60 | **PASS** | Crime branch money laundering extortion in Gujarati |
| `HP15` | hard_positive | **DANGER** | CALM | 6 | **FAIL** | Lottery prize GST payment advance fee |
| `HP16` | hard_positive | **DANGER** | DANGER | 64 | **PASS** | PAN-Aadhaar linkage OTP harvesting |
| `HP17` | hard_positive | **DANGER** | DANGER | 100 | **PASS** | Customs airport contraband threat in Hinglish |
| `HP18` | hard_positive | **DANGER** | CALM | 16 | **FAIL** | Virtual kidnapping urgent ransom threat |
| `HP19` | hard_positive | **DANGER** | CAREFUL | 40 | **FAIL** | Urgent bank account block OTP trap in Gujarati |
| `HP20` | hard_positive | **DANGER** | DANGER | 100 | **PASS** | High-urgency national security legal threat and FD liquidation |
