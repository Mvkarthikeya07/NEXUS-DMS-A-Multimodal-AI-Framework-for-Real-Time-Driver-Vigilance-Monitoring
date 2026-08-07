<div align="center">

<img src="assets/banner.jpg" alt="NEXUS-DMS Banner" width="100%"/>

# 🛡️ NEXUS-DMS
### *Multimodal AI Framework for Real-Time Driver Vigilance Monitoring*

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/MediaPipe-0.10.x-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black"/>
  <img src="https://img.shields.io/badge/OpenCV-4.8%2B-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white"/>
  <img src="https://img.shields.io/badge/Twilio-SMS%20%2B%20GPS-F22F46?style=for-the-badge&logo=twilio&logoColor=white"/>
</p>

<p>
  <img src="https://img.shields.io/badge/Status-Production%20Ready-22c55e?style=flat-square"/>
  <img src="https://img.shields.io/badge/Architecture-Modular%20%7C%20Threaded-3b82f6?style=flat-square"/>
  <img src="https://img.shields.io/badge/Alerts-Voice%20%7C%20Buzzer%20%7C%20SMS%20%2B%20GPS-f59e0b?style=flat-square"/>
  <img src="https://img.shields.io/badge/License-Academic%20%26%20Research-a855f7?style=flat-square"/>
</p>

<br/>

> **"Every second of inattention is a life at risk. NEXUS-DMS ensures no second goes unmonitored."**

</div>

---

## 📋 Table of Contents

| Section | Description |
|---|---|
| [Overview](#-overview) | What NEXUS-DMS does and why it matters |
| [Key Features](#-key-features) | Complete feature breakdown |
| [System Architecture](#-system-architecture) | How the pipeline is structured |
| [Detection Engine](#-detection-engine) | AI models and algorithms |
| [Alert Escalation](#-alert-escalation-pipeline) | Staged response system |
| [SMS Alert Format](#-sms-alert-format) | Real message examples with GPS |
| [Project Structure](#-project-structure) | File and module layout |
| [Installation](#-installation) | Step-by-step setup |
| [Configuration](#️-configuration) | All environment variables explained |
| [Usage](#-usage) | How to run NEXUS-DMS |
| [Changelog](#-changelog) | All changes and bug fixes |
| [Technologies](#-technologies) | Full tech stack |

---

## 🌟 Overview

**NEXUS-DMS** is a production-grade, AI-powered Driver Monitoring System (DMS) that operates entirely in real-time using a standard webcam — no specialized hardware required. It fuses two of the world's most powerful computer vision frameworks — **Google MediaPipe Face Mesh** and **Ultralytics YOLOv8** — into a unified, multimodal vigilance engine.

When a driver shows signs of fatigue, distraction, or phone usage, NEXUS-DMS responds through a **staged alert escalation pipeline**: voice warnings → buzzer alarms → emergency SMS messages with **live GPS coordinates and a Google Maps link** sent directly to the driver's registered phone number.

### 🎯 The Problem

<table>
<tr>
<td>

> 🇺🇸 The **NHTSA** reports drowsy driving causes **100,000+ crashes**, **71,000 injuries**, and **1,550 fatalities** annually in the US alone.

</td>
<td>

> 🌍 **WHO** estimates distracted driving accounts for **25% of all road traffic deaths** globally — over **300,000 deaths per year**.

</td>
</tr>
</table>

### 💡 Why NEXUS-DMS?

| Traditional DMS | NEXUS-DMS |
|---|---|
| Expensive proprietary hardware | Standard USB/laptop webcam |
| Single-sensor detection | Multimodal: Face + Pose + Object |
| Alert logs only | Real-time SMS + GPS to your phone |
| Static emergency contact | Dynamic phone registration at startup |
| Approximate location | City + State + Coordinates + Maps link |

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧠 Multimodal Detection Engine
| Feature | AI Method | Trigger |
|---------|-----------|---------|
| 😴 Drowsiness | EAR Analysis — 6 landmarks | EAR < 0.25 for 15 frames |
| 🥱 Yawn Detection | MAR Analysis — 8 landmarks | MAR > 0.65 |
| 👀 Head Pose | 5-point estimation | Deviation > 3% from center |
| 📱 Phone Usage | YOLOv8 COCO class 67 | Confidence ≥ 30% |

</td>
<td width="50%">

### 🚨 Staged Alert System
| Stage | Technology | Trigger |
|-------|-----------|---------|
| 🔊 Voice | pyttsx3 threaded TTS | Immediate |
| 🔔 Buzzer | Pygame looping audio | 8s drowsy |
| 📲 SMS + GPS | Twilio + ip-api.com | 13s drowsy / 5s phone |
| 📸 Screenshot | OpenCV auto-capture | Every alert event |

</td>
</tr>
</table>

### 🗺️ Accurate Multi-Source GPS
NEXUS-DMS resolves location using **three providers in priority order**:

```
1st → ip-api.com   — City, State, Country + Coordinates   (most detailed)
2nd → ipinfo.io    — City, Region + Coordinates            (reliable fallback)
3rd → geocoder     — Coordinates only                      (last resort)
```

Every SMS includes the **full address, precise coordinates, and a one-click Google Maps link**.

---

## 🏗️ System Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                     NEXUS-DMS v2.0 Pipeline                     ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   [Webcam Input]                                                 ║
║        │                                                         ║
║        ▼                                                         ║
║   [Camera Module] ──── BGR frames ────────────────────────────  ║
║        │                                           │            ║
║        ▼ (RGB)                                     ▼            ║
║   [FaceAnalyzer]                        [PhoneDetector]         ║
║    MediaPipe FaceMesh                   YOLOv8 (COCO-67)        ║
║        │                                           │            ║
║     Landmarks                              Bounding boxes        ║
║        │                                           │            ║
║   ┌────┴──────────────┐                            │            ║
║   │                   │                            │            ║
║   ▼                   ▼                            │            ║
║ [DrowsinessDetector] [DistractionDetector]         │            ║
║  EAR threshold        Head pose estimation         │            ║
║        │                   │                       │            ║
║        └────────┬──────────┘                       │            ║
║                 │                                  │            ║
║                 ▼                                  │            ║
║          [YawnDetector]                            │            ║
║           MAR threshold                            │            ║
║                 │                                  │            ║
║                 └──────────────┬───────────────────┘            ║
║                                ▼                                ║
║                        [AlertManager]                           ║
║                    ┌──────────────────────┐                     ║
║                    │  Voice → Buzzer →    │                     ║
║                    │  SMS + GPS Location  │                     ║
║                    └──────────────────────┘                     ║
║                                │                                ║
║                    ┌───────────┼───────────┐                    ║
║                    ▼           ▼           ▼                    ║
║              [pyttsx3]    [Pygame]    [Twilio SMS]              ║
║              Voice TTS    Buzzer      + GPS + Maps              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🔬 Detection Engine

### Eye Aspect Ratio (EAR) — Drowsiness

The EAR uses 6 facial landmarks per eye to compute the ratio of vertical to horizontal eye opening:

$$EAR = \frac{||p_2 - p_6|| + ||p_3 - p_5||}{2 \cdot ||p_1 - p_4||}$$

- EAR **≥ 0.25** → Eyes open, driver alert
- EAR **< 0.25** for **15+ consecutive frames** → Drowsiness confirmed

### Mouth Aspect Ratio (MAR) — Yawn Detection

$$MAR = \frac{||p_2 - p_8|| + ||p_3 - p_7|| + ||p_4 - p_6||}{3 \cdot ||p_1 - p_5||}$$

- MAR **> 0.65** → Yawn detected

### Head Pose — Distraction Detection

Nose tip position relative to face center:
- Horizontal deviation **> 3%** → Looking LEFT or RIGHT
- Vertical ratio outside **[0.42, 0.58]** → Looking UP or DOWN

---

## 🚨 Alert Escalation Pipeline

### 😴 Drowsiness Response

```
t=0s   Eyes close (EAR drops below threshold)
  │
  ├─ t=2s  ──  🔊  Voice: "Warning. Driver appears drowsy. Please stay alert."
  │
  ├─ t=3.5s ─  🔔  Buzzer alarm starts (looping audio)
  │
  └─ t=5s  ──  📲  Emergency SMS sent:
                     • Driver's full location (City, State, Country)
                     • GPS coordinates + Google Maps link
                     • Timestamp of incident
                     • Screenshot captured automatically
```

### 📱 Phone Detection Response

```
t=0s   Phone detected in frame (YOLOv8 confidence ≥ 30%)
  │
  ├─ t=0s  ──  🔊  Voice: "Warning. Mobile phone detected."
  │
  └─ t=5s  ──  📲  SMS sent with GPS location + screenshot
```

### 👀 Distraction Response

```
t=0s   Head turned away (horizontal/vertical threshold exceeded)
  │
  ├─ t=3s  ──  🔊  Voice: "Driver distraction detected."
  │              📸  Screenshot captured
  │
  └─ t=3s  ──  📲  SMS sent with direction + GPS location
```

---

## 📲 SMS Alert Format

All SMS messages include **full address**, **precise GPS coordinates**, **Google Maps link**, and **timestamp**.

### 🚨 Drowsy Emergency Alert
```
🚨 NEXUS-DMS — EMERGENCY ALERT
━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Driver unresponsive for 13s!
🕐 Time: 07-Aug-2026 03:23 PM
📍 Chennai, Tamil Nadu, India
   Coordinates: 13.0895, 80.2739
   Maps: https://maps.google.com/?q=13.0895,80.2739
━━━━━━━━━━━━━━━━━━━━━━━━
Please check on the driver immediately.
```

### 📱 Phone Usage Alert
```
📱 NEXUS-DMS — PHONE ALERT
━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Driver using mobile phone while driving!
🕐 Time: 07-Aug-2026 03:25 PM
📍 Chennai, Tamil Nadu, India
   Coordinates: 13.0895, 80.2739
   Maps: https://maps.google.com/?q=13.0895,80.2739
━━━━━━━━━━━━━━━━━━━━━━━━
Please put the phone down and focus on the road.
```

### 👀 Distraction Alert
```
👀 NEXUS-DMS — DISTRACTION ALERT
━━━━━━━━━━━━━━━━━━━━━━━━
⚠ Driver looking LEFT — not watching road!
🕐 Time: 07-Aug-2026 03:27 PM
📍 Chennai, Tamil Nadu, India
   Coordinates: 13.0895, 80.2739
   Maps: https://maps.google.com/?q=13.0895,80.2739
━━━━━━━━━━━━━━━━━━━━━━━━
Please keep your eyes on the road.
```

---

## 📁 Project Structure

```
NEXUS-DMS/
│
├── 📄 main.py                     # Entry point: phone registration + main loop
├── 📄 config.py                   # Centralized config — reads from .env
├── 📄 logger.py                   # CSV event logger with timestamps
├── 📄 dashboard.py                # Flask web analytics dashboard
├── 📄 requirements.txt            # Pinned dependencies
├── 📄 .env                        # Private credentials (never commit)
├── 📄 .env.example                # Template for environment setup
│
├── 📦 modules/
│   ├── alert_manager.py           # Core alert engine: voice/buzzer/SMS+GPS
│   ├── camera.py                  # Camera abstraction layer
│   ├── face_analyzer.py           # MediaPipe Face Mesh wrapper + landmark extractor
│   ├── drowsiness.py              # EAR-based drowsiness detector
│   ├── yawn_detector.py           # MAR-based yawn detector
│   ├── distraction_detector.py    # Head pose distraction detector
│   └── phone_detector.py          # YOLOv8 phone detection (COCO class 67)
│
├── 🔊 sounds/
│   └── alarm.wav                  # Buzzer alarm audio
│
├── 📸 screenshots/                # Auto-captured alert evidence images
├── 📊 logs/alerts.csv             # Timestamped event log
└── 🖼️ assets/                     # README and UI assets
```

---

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- Webcam (USB or built-in)
- Twilio account (free trial works)
- Chrome or Edge browser (for WhatsApp fallback if needed)

### Step 1 — Clone

```bash
git clone https://github.com/your-username/NEXUS-DMS.git
cd NEXUS-DMS
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Critical:** `protobuf` is pinned to `>=4.25.3,<5.0.0`. Do **not** upgrade it.
> Protobuf 5.x and above break MediaPipe's internal descriptor APIs.

### Step 3 — Configure Environment

```bash
cp .env.example .env
```

Then edit `.env` with your credentials (see [Configuration](#️-configuration) below).

---

## ⚙️ Configuration

All settings live in `.env`. **Use `KEY=VALUE` format — no quotes, no spaces around `=`.**

```ini
# ─────────────────────────────────────────────────────────────────
# Twilio SMS — required for emergency alerts
# Get credentials at: https://console.twilio.com
# ─────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx   # Starts with AC
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      # 32-char hex string
TWILIO_FROM_NUMBER=+1xxxxxxxxxx                        # Your Twilio number
EMERGENCY_CONTACT=+91xxxxxxxxxx                        # Fallback if dialog skipped

# ─────────────────────────────────────────────────────────────────
# Detection Thresholds
# ─────────────────────────────────────────────────────────────────
EAR_THRESHOLD=0.25       # Eye Aspect Ratio — lower = more sensitive
MAR_THRESHOLD=0.65       # Mouth Aspect Ratio — yawn trigger
DROWSY_FRAMES=15         # Consecutive low-EAR frames before alert fires
HEAD_TURN_THRESHOLD=0.03 # Nose horizontal deviation from face center
PHONE_CONFIDENCE=0.30    # YOLOv8 minimum detection confidence

# ─────────────────────────────────────────────────────────────────
# Alert Timing (seconds)
# ─────────────────────────────────────────────────────────────────
VOICE_ALERT_DELAY=3.0        # Seconds before voice warning fires
BUZZER_ALERT_DELAY=8.0       # Seconds before buzzer alarm starts
EMERGENCY_ALERT_DELAY=13.0   # Seconds before emergency SMS fires
DISTRACTION_ALERT_DELAY=3.0  # Seconds looking away before alert
PHONE_SMS_DELAY=5.0          # Seconds phone visible before SMS

# ─────────────────────────────────────────────────────────────────
# Camera
# ─────────────────────────────────────────────────────────────────
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
```

### Twilio Setup (5 minutes)

1. Sign up at **[twilio.com](https://twilio.com)** — free trial gives $15 credit
2. From the [Console Dashboard](https://console.twilio.com):
   - Copy **Account SID** → `TWILIO_ACCOUNT_SID`
   - Click 👁 eye icon → Copy **Auth Token** → `TWILIO_AUTH_TOKEN`
3. Get a free **Twilio phone number** → `TWILIO_FROM_NUMBER`
4. Add your personal number to **[Verified Caller IDs](https://console.twilio.com/us1/develop/phone-numbers/manage/verified-caller-ids)** (trial requirement)

---

## ▶️ Usage

```bash
python main.py
```

### Step 1 — Phone Registration

A dark-mode GUI dialog appears:

```
┌──────────────────────────────────────────┐
│  🚗  NEXUS-DMS                           │
│  Driver Monitoring System                │
│  ──────────────────────────────          │
│  Enter your phone number to receive      │
│  safety alerts:                          │
│                                          │
│  [ +91_________________ ]               │
│                                          │
│  [ Start Monitoring ]  [ Skip ]         │
└──────────────────────────────────────────┘
```

- Enter your number (e.g. `+916309533888`)
- Press **Enter** or click **Start Monitoring**
- Click **Skip** to use the `EMERGENCY_CONTACT` from `.env`

The registered number overrides `.env` and receives **all** SMS alerts for that session.

### Step 2 — Live Monitoring HUD

| HUD Field | Description |
|---|---|
| `Status` | `ATTENTIVE` / `DROWSY` / `DISTRACTED` / `PHONE DETECTED` / `NO FACE` |
| `EAR` | Eye Aspect Ratio — drowsy if below 0.25 |
| `MAR` | Mouth Aspect Ratio — yawn if above 0.65 |
| `Head` | Current head direction (`CENTER` / `LEFT` / `RIGHT` / `UP` / `DOWN`) |
| `Yawns` | Cumulative yawn count for the session |
| `Drowsy Timer` | Seconds elapsed since eyes closed |
| `Voice / Buzzer` | Current alert stage indicators |

Press **ESC** to exit gracefully.

---

## 📋 Changelog

### v2.0.0 — August 2026

#### 🐛 Critical Bug Fixes

| Error | Cause | Fix |
|---|---|---|
| `AttributeError: 'MessageFactory' object has no attribute 'GetPrototype'` | `protobuf 7.x` incompatible with `mediapipe 0.10.x` | Pinned `protobuf>=4.25.3,<5.0.0` |
| `AttributeError: 'FieldDescriptor' object has no attribute 'label'` | Same root cause | Same fix |
| SMS `Error 20003: Authenticate` | `.env` used Python variable syntax (`key = "value"`) | Fixed to proper `KEY=VALUE` dotenv format |
| SMS `Error 20003` via API Key | API Key (`SK...`) lacked SMS send permissions | Removed API Key — Auth Token only |

#### ✨ New Features

**📱 Dynamic Phone Registration at Startup**
- Dark-mode Tkinter GUI dialog appears before camera opens
- Pre-filled with `+91` country code
- Input validated (7–15 digits) with inline error message
- Registered number overrides `.env` `EMERGENCY_CONTACT` for the session
- Keyboard: `Enter` to submit, `Escape` to skip

**🗺️ Accurate Multi-Source GPS in Every SMS**
- Three-provider cascade: `ip-api.com` → `ipinfo.io` → `geocoder`
- Returns **City, State, Country** (not just raw coordinates)
- Includes **precise coordinates** (4 decimal places)
- Includes **one-click Google Maps link**
- Includes **timestamp** of the incident

**📲 GPS Added to All Three Alert Types**
- Previously: only drowsy emergency had GPS
- Now: **drowsy, phone, and distraction** all include full GPS + Maps link + timestamp

**📲 Distraction SMS (New)**
- Distraction events now send SMS in addition to voice warning
- SMS includes the head direction (LEFT/RIGHT/UP/DOWN) and GPS

#### 🔧 Code Improvements
- Removed all WhatsApp/pywhatkit integration
- Removed Twilio API Key support — simplified to Account SID + Auth Token
- Improved SMS logging — shows SID, status, recipient on success; full error detail on failure
- Cleaned all modules — removed dead code, unused imports, redundant parameters

---

## 🔧 Technologies

<table>
<tr><th>Technology</th><th>Version</th><th>Role</th></tr>
<tr><td>🐍 Python</td><td>3.10+</td><td>Runtime</td></tr>
<tr><td>🎯 MediaPipe</td><td>0.10.x</td><td>Face mesh, landmark detection</td></tr>
<tr><td>👁️ OpenCV</td><td>4.8+</td><td>Video capture, frame processing, screenshots</td></tr>
<tr><td>⚡ YOLOv8 (Ultralytics)</td><td>8.x</td><td>Real-time phone object detection</td></tr>
<tr><td>🔢 NumPy</td><td>1.24+</td><td>Numerical array operations</td></tr>
<tr><td>📲 Twilio</td><td>9.x</td><td>SMS delivery</td></tr>
<tr><td>🗺️ ip-api.com / ipinfo.io</td><td>Free API</td><td>Multi-source GPS location</td></tr>
<tr><td>📍 geocoder</td><td>1.38+</td><td>IP geolocation fallback</td></tr>
<tr><td>🔊 pyttsx3</td><td>2.90+</td><td>Threaded text-to-speech alerts</td></tr>
<tr><td>🔔 Pygame</td><td>2.5+</td><td>Buzzer alarm audio engine</td></tr>
<tr><td>⚙️ python-dotenv</td><td>1.0+</td><td>Environment variable loading</td></tr>
<tr><td>🔒 protobuf</td><td>≥4.25.3, <5.0.0</td><td>MediaPipe dependency (pinned)</td></tr>
<tr><td>🖥️ tkinter</td><td>stdlib</td><td>Phone registration GUI dialog</td></tr>
</table>

---

## 🔮 Future Roadmap

- [ ] 🧠 Transformer-based drowsiness model for higher accuracy
- [ ] 📡 Real device GPS via USB/Bluetooth OBD-II dongle integration
- [ ] 📊 Real-time Flask dashboard with live alert feed
- [ ] 🎥 Cloud video upload on emergency events (AWS S3 / Firebase)
- [ ] 🚗 CAN bus integration for speed-aware alert thresholds
- [ ] 📱 Mobile companion app for alert management

---

## 📄 License

This project is licensed for **Academic and Research** use only.

© 2026 NEXUS-DMS. All rights reserved.

---

<div align="center">

**Built with ❤️ to make roads safer.**

*NEXUS-DMS — Because every driver deserves to arrive home safely.*

</div>
