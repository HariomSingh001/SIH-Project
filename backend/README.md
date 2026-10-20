# Parman AI Backend API

AI-Powered Monitoring and Telemetry Ingestion Engine built with **FastAPI**, **SQLAlchemy** (async), and **SQLite** (aiosqlite).

---

## Architecture Overview

```mermaid
flowchart TD
    EdgeAI["Edge Vision AI\n(YOLOv8 + OpenCV)"] -->|POST /api/telemetry\n(JSON + Evidence Frame)| Ingestion["Telemetry Ingestion\n(/api/telemetry)"]
    Admin["Centres / Trainers"] -->|POST /api/attendance\n(Claimed Attendance)| Attendance["Attendance Records\n(/api/attendance)"]
    
    Ingestion --> DiscEngine["Discrepancy Engine\n(Cross-Reference & Severity)"]
    Attendance --> DiscEngine
    
    DiscEngine --> Scoring["Anomaly & Trust Scoring\n(0 - 100 Dynamic Score)"]
    DiscEngine --> Alerts["Discrepancy Alerts\n(/api/discrepancies)"]
    
    Scoring --> Dashboard["National Dashboard API\n(/api/dashboard/stats & /map)"]
    Alerts --> Dashboard
```

---

## Key Features

1. **Edge AI Telemetry Ingestion**: Ingests timestamped detection telemetry from edge cameras with ~97.3% bandwidth savings over raw video streaming.
2. **Discrepancy Engine**:
   - Compares claimed attendance with computer vision headcounts.
   - Detects **Ghost Batches** (claim full attendance when 0 or near 0 detected).
   - Detects **Attendance Deficits** (Classifies Normal $\le 10\%$, Warning $15-29\%$, Critical $\ge 30\%$).
   - Compares physical equipment counts against sanctioned minimums.
3. **Dynamic Trust Scoring**:
   - Calculates a 0–100 rating for each centre based on compliance history, open critical alerts, and verification track record.
   - Auto-transitions compliance statuses: `Normal` ($\ge 85$), `Warning` ($60 - 84.9$), `Critical` ($< 60$).
4. **Interactive Dashboard Endpoints**:
   - Aggregated national monitoring KPIs.
   - Geo-coordinates and status markers for India-wide overview map.
   - Grouped state-level compliance summaries.
5. **Auto-Seeding**: Automatically seeds initial centres, batches, cameras, inventory, and attendance records on first boot.

---

## Running the API Server

```bash
cd backend
python main.py
```
The server will start on `http://127.0.0.1:8000`.

- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative Documentation (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## Running Tests

```bash
cd backend
python test_api.py
```
Executes the comprehensive automated test suite testing all endpoints, edge ingestion, and discrepancy evaluation.
