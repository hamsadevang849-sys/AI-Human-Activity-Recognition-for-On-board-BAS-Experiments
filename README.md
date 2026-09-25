# AI Human Activity Recognition for On-board BAS Experiments

> **Autonomous Standalone Edge AI Assistant for Microgravity Scientific Experiments**  
> *Designed for space missions (BAS, Lunar Gateway) where real-time ground control communication is restricted by speed-of-light delays.*

---

## 🛰️ Project Overview

In deep space exploration and microgravity research on the **BAS (Bharatiya Antariksh Station)**, astronauts execute complex, delicate scientific protocols. Due to orbital communication latency (1.3s to 24 minutes) and restricted bandwidth to Earth ground stations, real-time procedural verification from mission control is physically impossible.

This project delivers an **autonomous on-board AI assistant** that:
- Observes astronaut activities via **fixed-payload cameras**.
- Executes local, zero-cloud edge neural inference (**Pose Estimation**, **Object Detection**, and **Hand-Object Interaction**).
- Validates the execution of predefined scientific experiments against a **deterministic state machine**.
- Automatically detects **skipped steps** and **out-of-sequence protocol deviations**.
- Issues real-time **voice alerts** to guide crew members without taking their hands off the experiment.
- Generates **lightweight, timestamped structured text logs** (`.txt`) for periodic downlinks to Earth.
- Provides local **NVMe video storage** and **IP-based video streaming** to station terminals.
- Features an optional **Orientation-Agnostic 3D Human Mesh Recovery (HMR)** module that tracks astronaut posture relative to the payload rack rather than a virtual floor.

---

## ⚡ Core Architecture

```
                       [ ON-BOARD SPACE STATION EDGE NODE ]
                                        │
┌─────────────────────────┐             ▼
│  Fixed-Payload Cameras  │ ──► [ Local Edge AI Inference ]
│   (1080p 60fps Video)   │     ├─ Object Localization (Vials, Centrifuge, Racks)
└─────────────────────────┘     ├─ 34-Point Skeletal Kinematics
                                └─ Hand-Object Contact & Interaction
                                        │
                                        ▼
                        [ Sequence Validation State Engine ]
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
          [ Nominal Next Step ]                   [ Sequence Deviation ]
                    │                                       │
                    ▼                                       ▼
        "Step Validated. Next: ..."             "Warning: Step 03 Skipped!"
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                        ┌───────────────────────────────┐
                        │ Local Synthesized Voice Alert │
                        │ Lightweight Text Log (.txt)   │
                        │ Local NVMe Video Archive      │
                        │ Optional RTSP/UDP IP Stream   │
                        └───────────────────────────────┘
                                        │
                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                 CONSTRAINED DEEP-SPACE DOWNLINK (HIGH LATENCY)
                 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                        │
                                        ▼
                            [ Earth Mission Control ]
                             (< 4.2 KB text digest)
```

---

## 🚀 Key Features

1. **Cinematic System Initialization Sequence**
   - The on-board AI wakes up upon connection, sequentially introducing its role, capabilities, and mission parameters with synthesized vocal cues and audio waveforms.
2. **Interactive 3D WebGL Space Station Vista**
   - Built with Three.js; features a photorealistic procedural low-Earth orbit Earth horizon, space station truss structure, and deep space starfield that interactively responds to user scroll and mouse parallax.
3. **Deterministic Sequence Validation & Deviation Engine**
   - Interactive testing suite for **BAS-EXP-04: Biological Specimen Extraction**.
   - Trigger nominal workflows, simulate skipped procedural steps, or test out-of-sequence activities with instant vocal and visual alerts.
4. **Voice-Based Alert Assistant**
   - Real-time vocal supervision using browser speech synthesis and Web Audio API synthesizer.
5. **Lightweight Structured Text Logging & Export**
   - Maintains an auditable record in format: `[timestamp] | step | activity | status | outcome`.
   - Direct download button for `.txt` logs.
6. **Dataset Generation Lab**
   - 7-stage interactive dataset pipeline visualizer with multi-modal annotation toggles (Pose Skeleton, Object Bounding Boxes, Hand-Object Contact Vectors, Spatial Attention Heatmaps).
7. **Orientation-Agnostic 3D HMR (Advanced Optional Module)**
   - Microgravity reference frame viewer: tracks astronaut 3D body orientation relative to a fixed payload rack coordinate system `[X_rack, Y_rack, Z_rack]`.
8. **Mission Operations Dashboard (GUI)**
   - Top status bar: Mission, Camera 01, AI Core, Experiment, Sequence, Alert, Storage.
   - Live camera feed simulation, IP streaming address input, and local NVMe storage archive.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, FastAPI, Uvicorn, Pydantic, WebSockets, NumPy, OpenCV.
- **Frontend**: Vanilla HTML5, CSS3, Modern ES6+ JavaScript.
- **3D Graphics**: Three.js (WebGL), procedural canvas textures.
- **Audio & Voice**: Web Audio API (synthesized drones and blips), Web Speech API.
- **Networking**: REST API endpoints + 10Hz real-time WebSocket telemetry stream.

---

## 📦 Quick Start Guide

### Prerequisites
- Python 3.9+ (Python 3.12 recommended)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/hamsadevang849-sys/AI-Human-Activity-Recognition-for-On-board-BAS-Experiments.git
cd AI-Human-Activity-Recognition-for-On-board-BAS-Experiments
pip install -r requirements.txt
```

### 2. Launch Application
Run the unified launcher (automatically starts the FastAPI server and opens your browser):

**On Windows:**
Double-click `start.bat` or run:
```bash
python run.py
```

**On Linux/macOS:**
```bash
python3 run.py
```

The application will be live at:
**[http://127.0.0.1:8080/](http://127.0.0.1:8080/)**

---

## 📡 REST API & WebSocket Documentation

Once the server is running, interactive Swagger API documentation is available at:
**[http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)**

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | Current edge AI and mission status |
| `GET` | `/api/protocol` | List predefined experiment steps and state |
| `POST` | `/api/protocol/reset` | Re-initialize experiment protocol state machine |
| `POST` | `/api/sequence/validate` | Validate an observed action against protocol |
| `GET` | `/api/logs` | Fetch all timestamped experiment logs |
| `GET` | `/api/logs/export` | Download structured lightweight `.txt` audit log |
| `GET` | `/api/storage` | Query local NVMe video storage capacity & files |
| `POST` | `/api/storage/record/toggle` | Toggle local recording state |
| `POST` | `/api/stream/start` | Start video stream to target destination IP |
| `POST` | `/api/stream/stop` | Terminate active stream |
| `WS` | `/ws/telemetry` | 10Hz live WebSocket telemetry and kinematics stream |

---

## 📂 Project Directory Structure

```
AI-HAR/
├── backend/
│   ├── __init__.py             # Backend Python package
│   ├── app.py                  # FastAPI server with REST + WebSockets
│   ├── sequence_engine.py      # Experiment state machine & validation engine
│   ├── edge_inference.py       # CV & HAR inference pipeline simulator
│   ├── storage_manager.py      # NVMe storage & structured text log manager
│   ├── ip_streamer.py          # IP video transmission manager
│   └── models.py               # Pydantic data schemas
├── logs/
│   └── bas_exp_audit.txt       # Structured audit log output
├── storage/                    # Local video storage archive directory
├── index.html                  # 3D interactive landing page & mission dashboard
├── three.min.js                # Standalone Three.js library for offline operation
├── run.py                      # One-click unified application launcher
├── start.bat                   # Windows batch launcher
├── requirements.txt            # Python dependencies
├── package.json                # Project configuration & npm scripts
└── README.md                   # System documentation
```

---

## ⚖️ Standalone & Data Principles

- **Process Locally**: All neural inference occurs in-situ on the edge node.
- **Communicate Minimally**: High-definition video is stored locally; only structured text digests and anomaly alerts are transmitted to Earth.
- **Offline Resilient**: Operates 100% standalone without internet, cloud dependencies, or ground contact.
- **Demo vs. Real Data**: Clearly distinguishes synthetic simulations from physical hardware integration.

---

## 📄 License
ISC License. Designed for On-board BAS (Bharatiya Antariksh Station) scientific experiment research.
