# 🔍 Pramaan AI (प्रमाण AI)

### AI-Powered Real-Time Verification of Attendance & Infrastructure Compliance for MSDE Training Centres

**Smart India Hackathon (SIH) Problem Statement ID:** 26245  
**Ministry:** Ministry of Skill Development and Entrepreneurship (MSDE)  
**Theme:** Smart Education / Governance  
**Project Status:** ✅ **100% Complete, Fully Tested & SIH Submission Ready**

---

## 🎯 What Pramaan AI Solves

Under government skill development schemes (e.g. PMKVY), training centres claim financial disbursements based on self-reported attendance and mandated infrastructure. Physical audits are rare, resource-intensive, and susceptible to collusion, resulting in **Ghost Batches** (claims with zero students present) and unfulfilled lab equipment mandates.

**Pramaan AI** solves this through a lightweight, privacy-preserving computer vision telemetry pipeline:
1. **Privacy-Preserving Vision AI**: YOLOv8s detects student headcount and verifies sanctioned equipment without individual biometric identification.
2. **DPDP Act 2023 Compliant**: All faces in evidence frames are Gaussian-blurred at the edge before cloud upload. Every image is anchored with a cryptographic SHA-256 hash.
3. **Over 99.7% Bandwidth Savings**: Replaces expensive continuous video streaming (21.1 GB/day) with smart frame telemetry (49.8 MB/day) — ideal for rural 2G/4G connectivity.
4. **Store-and-Forward Offline Resilience**: Encrypted local queues buffer telemetry during network outages and flush chronologically upon reconnection with zero data loss.
5. **Dynamic Trust Scoring**: Automatically calculates a 0–100 reliability rating for each training centre to prioritize automated alerts and surprise physical inspections.
6. **Bilingual Light-Themed Dashboard**: Clean, modern web portal with instant English / हिन्दी switching, interactive Leaflet national map, and real-time WebSocket alert push.

---

## 📸 System Showcase & Visuals

- **Executive Dashboard**: Light-colored UI with KPI hero cards, Leaflet map, attendance trend bar charts, and live discrepancy feed.
- **National Geo-Map**: Geo-spatial compliance pulse markers across Delhi, Jaipur, Bengaluru, Kolkata, and Lucknow.
- **Evidence Inspector**: DPDP 2023 face-blur visualizer with cryptographic SHA-256 tamper-proof fingerprinting.
- **Edge Simulator**: Network outage toggle, offline queue counter, and real-time cloud batch sync.
- **Bandwidth ROI Calculator**: Real-time slider math proving 99.77% cellular data savings.

---

## 📁 Repository Structure

```
pramaan-ai/
├── ai_engine/                   # Edge Computer Vision Pipeline
│   ├── detectors/               # YOLOv8s person & equipment detection modules
│   ├── privacy/                 # DPDP Act 2023 Gaussian face blur engine
│   ├── sampler/                 # Smart 1-per-25s frame sampler & bandwidth calculator
│   ├── edge/                    # Store-and-Forward offline buffer & sync engine
│   └── main.py                  # CLI and module entry point for video processing
│
├── backend/                     # Central FastAPI Cloud Backend
│   ├── app/
│   │   ├── api/                 # REST & WebSocket route handlers
│   │   ├── core/                # Database setup, config, WebSocket connection manager
│   │   ├── models/              # Async SQLAlchemy ORM models (7 tables)
│   │   ├── schemas/             # Pydantic request & response validation schemas
│   │   └── services/            # Discrepancy calculation & Trust Scoring engine
│   ├── test_live_server.py      # Automated 17-point integration test suite
│   ├── verify_all.py            # Pre-submission verification script
│   └── main.py                  # FastAPI server entry point
│
├── frontend/                    # Modern Light-Themed React + Vite Dashboard
│   ├── src/
│   │   ├── components/          # Sidebar, TopBar, NationalMap, DiscrepancyFeed, etc.
│   │   ├── utils/               # English & Hindi translations dictionary
│   │   ├── App.jsx              # Main app controller with WebSocket client
│   │   └── index.css            # Custom light-theme design system tokens
│   ├── vite.config.js           # Vite dev server with proxy to backend port 8000
│   └── package.json
│
├── data/                        # Mock Data & Verification Assets
│   ├── centres/                 # Empanelled training institutes JSON
│   ├── attendance/              # Claimed attendance records with intentional deficits
│   ├── inventory/               # Sanctioned lab equipment manifests
│   ├── telemetry/               # Sample AI telemetry output
│   └── videos/                  # Sample classroom video clip for live testing
│
└── pramaan_ai.db                # Central SQLite Database (7 tables populated)
```

---

## 🚀 Quick Start (Running Locally for Evaluators)

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Launch Everything with 1 Click (Windows)
Double-click `start_all.bat` or run:
```bat
start_all.bat
```

Or start manually:

### 2. Start the Backend API (FastAPI)
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```
- API Documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- WebSocket Channel: `ws://127.0.0.1:8000/ws`
- Health Endpoint: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Start the Frontend Dashboard (React + Vite)
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- Open **[http://127.0.0.1:5173](http://127.0.0.1:5173)** in your browser.

### 4. Run Automated System Integration Tests
```bash
cd backend
python verify_all.py
```
*Executes all 22 verification tests with 100% pass rate.*

---

## 📊 Bandwidth Economy & Data Transmission Proof

| Parameter | Continuous CCTV Streaming | Pramaan AI Edge Telemetry | Savings |
|:---|:---|:---|:---|
| **Transmission Mode** | Raw RTSP 1080p @ 30fps | 1 sample / 25s JSON + key blurred JPEGs | **Edge processed** |
| **Daily Data (1 Cam)** | **21.1 GB / day** | **49.8 MB / day** | **99.77% reduction** |
| **Monthly Data (3 Cams)**| **633 GB / month** | **1,493 MB / month (~1.5 GB)** | **631.5 GB saved** |
| **Estimated Cellular Cost**| ₹7,596 / centre / month | ₹18 / centre / month | **₹7,578 saved / centre / month** |

---

## ⚖️ Compliance & Privacy
- **DPDP Act 2023**: Zero raw facial biometrics stored or transmitted. All faces are Gaussian-blurred at the edge.
- **Tamper Evidence**: Every evidence frame is anchored with a cryptographic SHA-256 hash.
- **Auditing Integrity**: Discrepancies are logged immutably and timestamped.

---

## 🏆 SIH 2026 Submission Note
Built by Team Pramaan AI for the **Smart India Hackathon 2026** evaluation under the Ministry of Skill Development and Entrepreneurship (MSDE).
