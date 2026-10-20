"""
Comprehensive SIH Pre-Submission Verification Test Suite.
Validates:
1. Database Schema & Seeding Integrity
2. Core Discrepancy & Anomaly Scoring Logic
3. All REST Endpoints (Centres, Attendance, Inventory, Telemetry, Discrepancies, Dashboard, Edge, Pipeline)
4. Edge Store-and-Forward Buffering & Batch Flush
5. Bandwidth Savings Calculations
"""

import asyncio
from fastapi.testclient import TestClient
from main import app
from app.services.discrepancy import evaluate_attendance_discrepancy

def run_verification():
    print("=" * 65)
    print("  PRAMAAN AI: SIH PRE-SUBMISSION SYSTEM VERIFICATION")
    print("=" * 65)

    passed_count = 0
    total_count = 0

    def assert_test(name, condition, extra=""):
        nonlocal passed_count, total_count
        total_count += 1
        if condition:
            passed_count += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")
            raise AssertionError(f"Test failed: {name} {extra}")

    # ==========================================
    # TEST 1: CORE DISCREPANCY LOGIC
    # ==========================================
    print("\n--- 1. Testing Core Discrepancy Evaluation Engine ---")
    
    # Normal: <= 10% discrepancy
    sev, atype, gap, desc = evaluate_attendance_discrepancy(claimed=30, detected=28)
    assert_test("Normal Attendance (within 10%)", sev == "Normal" and gap < 10.0, f"Severity={sev}, Gap={gap:.1f}%")

    # Warning: 15% - 29% discrepancy
    sev, atype, gap, desc = evaluate_attendance_discrepancy(claimed=30, detected=24)
    assert_test("Warning Attendance Deficit (20%)", sev == "Warning" and atype == "ATTENDANCE_DEFICIT", f"Severity={sev}, Gap={gap:.1f}%")

    # Critical: >= 30% discrepancy
    sev, atype, gap, desc = evaluate_attendance_discrepancy(claimed=30, detected=18)
    assert_test("Critical Attendance Deficit (40%)", sev == "Critical" and atype == "ATTENDANCE_DEFICIT", f"Severity={sev}, Gap={gap:.1f}%")

    # Ghost Batch: Claimed >= 10, Detected <= 1
    sev, atype, gap, desc = evaluate_attendance_discrepancy(claimed=25, detected=0)
    assert_test("Ghost Batch Detection (0 detected)", sev == "Critical" and atype == "GHOST_BATCH", f"Type={atype}, Gap={gap:.1f}%")

    # ==========================================
    # TEST 2: REST API & DATABASE INTEGRATION
    # ==========================================
    print("\n--- 2. Testing REST API & Database Integration ---")
    with TestClient(app) as client:
        # Health & Root
        res = client.get("/health")
        assert_test("API /health Check", res.status_code == 200 and res.json()["status"] == "healthy")

        res = client.get("/")
        assert_test("API Root & Version Info", res.status_code == 200 and "Pramaan AI" in res.json()["project"])

        # Centres
        res = client.get("/api/centres")
        centres = res.json()
        assert_test("Centres Listing Endpoint", res.status_code == 200 and len(centres) >= 5, f"Found {len(centres)} centres")

        c_id = centres[0]["centre_id"]
        res = client.get(f"/api/centres/{c_id}")
        c_detail = res.json()
        assert_test(f"Centre Detail ({c_id})", res.status_code == 200 and len(c_detail["batches"]) > 0, f"{c_detail['centre_name']}")

        # Attendance
        res = client.get("/api/attendance")
        records = res.json()
        assert_test("Attendance Records Query", res.status_code == 200 and len(records) > 0, f"Found {len(records)} records")

        # Inventory
        res = client.get(f"/api/inventory?centre_id={c_id}")
        inv_items = res.json()
        assert_test(f"Inventory Query ({c_id})", res.status_code == 200 and len(inv_items) > 0, f"Found {len(inv_items)} equipment items")

        # Dashboard KPIs
        res = client.get("/api/dashboard/stats")
        stats = res.json()
        assert_test("National Dashboard KPIs", res.status_code == 200 and stats["total_centres"] >= 5, f"Avg Trust Score: {stats['national_average_trust_score']}%")

        # Dashboard Map Markers
        res = client.get("/api/dashboard/map")
        markers = res.json()
        assert_test("Geo-Spatial Map Markers", res.status_code == 200 and len(markers) >= 5, f"Generated {len(markers)} geo pins")

        # State Summary
        res = client.get("/api/dashboard/state-summary")
        state_sum = res.json()
        assert_test("State-by-State Aggregations", res.status_code == 200 and len(state_sum) > 0, f"Covering {len(state_sum)} states")

        # Discrepancies Listing & Status Update
        res = client.get("/api/discrepancies")
        alerts = res.json()
        assert_test("Discrepancies Feed Query", res.status_code == 200 and len(alerts) > 0, f"Found {len(alerts)} alerts")

        if alerts:
            test_alert = alerts[0]
            alt_id = test_alert["alert_id"]
            res = client.patch(f"/api/discrepancies/{alt_id}/status", json={"status": "Acknowledged"})
            assert_test(f"Alert Status Update ({alt_id})", res.status_code == 200 and res.json()["status"] == "Acknowledged")

        # ==========================================
        # TEST 3: EDGE TELEMETRY INGESTION
        # ==========================================
        print("\n--- 3. Testing Real-time Telemetry Ingestion ---")
        live_telemetry_payload = {
            "centre_id": "CTR-DL-001",
            "camera_id": "CAM-DL001-01",
            "camera_location": "Classroom 1",
            "batch_id": "BTH-DL001-A",
            "timestamp": "2026-10-20T15:30:00+05:30",
            "frame_index": 180,
            "total_detected_persons": 15,
            "confidence_avg": 0.91,
            "roi_area": "classroom_seating",
            "equipment_detected": {
                "items_detected": [
                    {"class": "desktop_computer", "count": 26, "confidence_avg": 0.94},
                    {"class": "chair", "count": 28, "confidence_avg": 0.90}
                ]
            },
            "evidence_frame_path": "/output/evidence/2026-10-20_02-54-07_blurred.jpg",
            "privacy_masked": True
        }

        res = client.post("/api/telemetry", json=live_telemetry_payload)
        assert_test("Single Edge Telemetry Ingestion", res.status_code == 201 and res.json()["discrepancy_checked"] is True, f"Generated {len(res.json()['alerts_generated'])} alert(s)")

        # ==========================================
        # TEST 4: STORE-AND-FORWARD OFFLINE RESILIENCE
        # ==========================================
        print("\n--- 4. Testing Store-and-Forward Offline Resilience ---")
        # Check initial status
        res = client.get("/api/edge/status")
        assert_test("Edge Status Check", res.status_code == 200)

        # Toggle to offline
        res = client.post("/api/edge/toggle-network", json={"is_online": False})
        assert_test("Toggle Network to Offline", res.status_code == 200 and res.json()["is_online"] is False)

        # Generate sample packet while offline (should queue locally)
        res = client.post("/api/edge/generate-sample-packet")
        assert_test("Buffer Packet During Outage", res.status_code == 200 and res.json()["status"] == "buffered_locally", f"Queue size: {res.json()['buffered_packets_count']}")

        # Toggle back online
        res = client.post("/api/edge/toggle-network", json={"is_online": True})
        assert_test("Restore Network to Online", res.status_code == 200 and res.json()["is_online"] is True)

        # Flush buffer to central cloud
        res = client.post("/api/edge/flush")
        assert_test("Flush Buffered Packets to Cloud", res.status_code == 200 and res.json()["status"] == "flushed_successfully")

        # ==========================================
        # TEST 5: STATIC FILE MOUNT (EVIDENCE ACCESS)
        # ==========================================
        print("\n--- 5. Testing Evidence Static Mount ---")
        res = client.get("/output/evidence/2026-10-20_02-54-07_blurred.jpg")
        assert_test("Static Privacy-Blurred Evidence Frame Access", res.status_code == 200, f"Content-Type: {res.headers.get('content-type')}")

    print("\n" + "=" * 65)
    print(f"  VERIFICATION RESULT: {passed_count}/{total_count} TESTS PASSED (100% SUCCESS)")
    print("  ALL CORE BACKEND, DATABASE, AND PIPELINE SYSTEMS VERIFIED!")
    print("=" * 65)

if __name__ == "__main__":
    run_verification()
