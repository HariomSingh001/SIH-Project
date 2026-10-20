"""
Automated End-to-End Test Suite for Parman AI Backend API.
Tests:
1. Lifespan startup and mock data seeding
2. /health and root endpoints
3. /api/centres (Listing & ID lookup)
4. /api/attendance (Listing & filtering)
5. /api/inventory (Inventory listing per centre)
6. /api/dashboard/stats & /api/dashboard/map
7. /api/discrepancies (List & status update)
8. /api/telemetry (Edge AI telemetry ingestion with automatic discrepancy trigger)
"""

import asyncio
from fastapi.testclient import TestClient
from main import app

def run_tests():
    print("========================================")
    print("Starting Parman AI Backend Tests...")
    print("========================================")

    # Use TestClient with context manager to trigger lifespan (startup/shutdown)
    with TestClient(app) as client:
        # 1. Health check
        res = client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.text}"
        print("[PASS] /health -> OK:", res.json())

        # 2. Root endpoint
        res = client.get("/")
        assert res.status_code == 200, f"Root check failed: {res.text}"
        print("[PASS] / -> OK:", res.json()["project"])

        # 3. Centres endpoint
        res = client.get("/api/centres")
        assert res.status_code == 200, f"Centres list failed: {res.text}"
        centres = res.json()
        assert len(centres) >= 5, f"Expected at least 5 centres seeded, got {len(centres)}"
        print(f"[PASS] /api/centres -> Found {len(centres)} seeded centres.")

        # Centre detail
        c_id = centres[0]["centre_id"]
        res = client.get(f"/api/centres/{c_id}")
        assert res.status_code == 200, f"Centre detail failed: {res.text}"
        detail = res.json()
        print(f"[PASS] /api/centres/{c_id} -> {detail['centre_name']} ({len(detail['batches'])} batches, {len(detail['cameras'])} cameras)")

        # 4. Attendance endpoint
        res = client.get("/api/attendance")
        assert res.status_code == 200, f"Attendance list failed: {res.text}"
        att_records = res.json()
        assert len(att_records) > 0, "Expected attendance records"
        print(f"[PASS] /api/attendance -> Found {len(att_records)} attendance records.")

        # 5. Inventory endpoint
        res = client.get(f"/api/inventory?centre_id={c_id}")
        assert res.status_code == 200, f"Inventory list failed: {res.text}"
        items = res.json()
        print(f"[PASS] /api/inventory -> Found {len(items)} equipment items for {c_id}.")

        # 6. Dashboard Stats
        res = client.get("/api/dashboard/stats")
        assert res.status_code == 200, f"Dashboard stats failed: {res.text}"
        stats = res.json()
        print(f"[PASS] /api/dashboard/stats -> {stats['total_centres']} centres, {stats['total_open_alerts']} open alerts, Avg Trust Score: {stats['national_average_trust_score']}")

        # 7. Dashboard Map Markers
        res = client.get("/api/dashboard/map")
        assert res.status_code == 200, f"Map markers failed: {res.text}"
        markers = res.json()
        print(f"[PASS] /api/dashboard/map -> {len(markers)} geo markers.")

        # 8. Discrepancies Listing & Status Update
        res = client.get("/api/discrepancies")
        assert res.status_code == 200, f"Discrepancies list failed: {res.text}"
        alerts = res.json()
        print(f"[PASS] /api/discrepancies -> Found {len(alerts)} discrepancy alerts.")
        if alerts:
            test_alert = alerts[0]
            alt_id = test_alert["alert_id"]
            # Test status update
            patch_res = client.patch(f"/api/discrepancies/{alt_id}/status", json={"status": "Acknowledged"})
            assert patch_res.status_code == 200, f"Status patch failed: {patch_res.text}"
            print(f"[PASS] /api/discrepancies/{alt_id}/status -> Status updated to Acknowledged.")

        # 9. AI Telemetry Ingestion (Simulating edge camera sending detection result)
        telemetry_payload = {
            "centre_id": "CTR-DL-001",
            "camera_id": "CAM-DL001-01",
            "camera_location": "Classroom 1",
            "batch_id": "BTH-DL001-A",
            "timestamp": "2026-10-20T14:30:00+05:30",
            "frame_index": 120,
            "total_detected_persons": 14,
            "confidence_avg": 0.88,
            "roi_area": "classroom_seating",
            "equipment_detected": {
                "items_detected": [
                    {"class": "desktop_computer", "count": 25, "confidence_avg": 0.92},
                    {"class": "chair", "count": 28, "confidence_avg": 0.89}
                ]
            },
            "evidence_frame_path": "output/evidence/2026-10-20_02-54-07_blurred.jpg",
            "privacy_masked": True
        }

        ingest_res = client.post("/api/telemetry", json=telemetry_payload)
        assert ingest_res.status_code == 201, f"Telemetry ingestion failed: {ingest_res.text}"
        ingest_data = ingest_res.json()
        print(f"[PASS] /api/telemetry (POST) -> Successfully ingested! Generated alerts: {ingest_data['alerts_generated']}")

    print("========================================")
    print("*** ALL BACKEND API TESTS PASSED! ***")
    print("========================================")

if __name__ == "__main__":
    run_tests()
