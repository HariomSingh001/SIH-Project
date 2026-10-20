"""
Live Server Comprehensive Integration Test.
Runs HTTP client against http://127.0.0.1:8000 and tests all endpoints.
"""

import httpx
from app.services.discrepancy import evaluate_attendance_discrepancy

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=" * 65)
    print("  PRAMAAN AI: LIVE API & PIPELINE INTEGRATION TEST")
    print(f"  Target: {BASE_URL}")
    print("=" * 65)

    with httpx.Client(base_url=BASE_URL, timeout=15.0) as client:
        # 1. Health
        r = client.get("/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        print("[PASS] 1. Health Check -> Status: 200 OK |", r.json()["status"])

        # 2. Root
        r = client.get("/")
        assert r.status_code == 200
        print("[PASS] 2. Root Documentation -> Status: 200 OK |", r.json()["project"])

        # 3. Centres
        r = client.get("/api/centres")
        assert r.status_code == 200
        centres = r.json()
        assert len(centres) >= 5
        print(f"[PASS] 3. Centres Registry -> Found {len(centres)} centres")

        c_id = centres[0]["centre_id"]
        r = client.get(f"/api/centres/{c_id}")
        assert r.status_code == 200
        detail = r.json()
        print(f"[PASS] 4. Centre Detail ({c_id}) -> {detail['centre_name']} ({len(detail['batches'])} batches)")

        # 4. Attendance
        r = client.get("/api/attendance")
        assert r.status_code == 200
        print(f"[PASS] 5. Attendance Records -> Found {len(r.json())} records")

        # 5. Inventory
        r = client.get(f"/api/inventory?centre_id={c_id}")
        assert r.status_code == 200
        print(f"[PASS] 6. Inventory Records -> Found {len(r.json())} items for {c_id}")

        # 6. Dashboard Stats
        r = client.get("/api/dashboard/stats")
        assert r.status_code == 200
        stats = r.json()
        print(f"[PASS] 7. Dashboard Stats -> Avg Trust Score: {stats['national_average_trust_score']}% | Open Alerts: {stats['total_open_alerts']}")

        # 7. Dashboard Map Markers
        r = client.get("/api/dashboard/map")
        assert r.status_code == 200
        print(f"[PASS] 8. Geo-Map Markers -> {len(r.json())} centres mapped across India")

        # 8. State Summary
        r = client.get("/api/dashboard/state-summary")
        assert r.status_code == 200
        print(f"[PASS] 9. State Performance -> {len(r.json())} states monitored")

        # 9. Discrepancies
        r = client.get("/api/discrepancies")
        assert r.status_code == 200
        alerts = r.json()
        print(f"[PASS] 10. Discrepancy Alerts -> Found {len(alerts)} alerts")

        if alerts:
            alt_id = alerts[0]["alert_id"]
            r = client.patch(f"/api/discrepancies/{alt_id}/status", json={"status": "Acknowledged"})
            assert r.status_code == 200
            print(f"[PASS] 11. Discrepancy Status Update -> Alert {alt_id} updated to Acknowledged")

        # 10. Live Edge Telemetry Ingestion
        payload = {
            "centre_id": "CTR-DL-001",
            "camera_id": "CAM-DL001-01",
            "camera_location": "Classroom 1",
            "batch_id": "BTH-DL001-A",
            "timestamp": "2026-10-20T16:00:00+05:30",
            "frame_index": 200,
            "total_detected_persons": 14,
            "confidence_avg": 0.92,
            "roi_area": "classroom_seating",
            "equipment_detected": {
                "items_detected": [
                    {"class": "desktop_computer", "count": 27, "confidence_avg": 0.93},
                    {"class": "chair", "count": 30, "confidence_avg": 0.90}
                ]
            },
            "evidence_frame_path": "/output/evidence/2026-10-20_02-54-07_blurred.jpg",
            "privacy_masked": True
        }
        r = client.post("/api/telemetry", json=payload)
        assert r.status_code == 201
        print(f"[PASS] 12. Edge Telemetry Ingest -> Generated {len(r.json()['alerts_generated'])} alert(s)")

        # 11. Edge Store-and-Forward: Offline Outage Simulation
        r = client.post("/api/edge/toggle-network", json={"is_online": False})
        assert r.status_code == 200 and r.json()["is_online"] is False
        print("[PASS] 13. Network Toggle to Offline -> Simulated 2G/network outage")

        r = client.post("/api/edge/generate-sample-packet")
        assert r.status_code == 200 and r.json()["status"] == "buffered_locally"
        print(f"[PASS] 14. Offline Buffering -> Telemetry packet successfully queued locally ({r.json()['buffered_packets_count']} in buffer)")

        r = client.post("/api/edge/toggle-network", json={"is_online": True})
        assert r.status_code == 200 and r.json()["is_online"] is True
        print("[PASS] 15. Network Restored to Online -> Edge connection back up")

        r = client.post("/api/edge/flush")
        assert r.status_code == 200
        print(f"[PASS] 16. Store-and-Forward Cloud Flush -> Synchronized {r.json()['synced_count']} packet(s) to central database!")

        # 12. Static Evidence Access
        r = client.get("/output/evidence/2026-10-20_02-54-07_blurred.jpg")
        assert r.status_code == 200
        print(f"[PASS] 17. Static Evidence Frame -> Accessed successfully ({len(r.content)} bytes)")

    print("=" * 65)
    print("  *** ALL 17 SYSTEM & INTEGRATION TESTS PASSED (100%) ***")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
