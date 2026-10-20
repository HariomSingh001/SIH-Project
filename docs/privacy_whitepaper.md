# Parman AI (प्रमाण AI) — Privacy-Preserving Design Note

## DPDP Act 2023 Compliance Whitepaper

### 1. What IS Identified from Footage

| Data Element | Method | Purpose | Storage |
|:------------|:-------|:--------|:--------|
| **Aggregate headcount** | YOLO bounding box counting | Attendance verification | Numeric count only (no images) |
| **Person centroids** | ByteTrack tracking | Prevent double-counting | XY coordinates, discarded after session |
| **Equipment classes** | Custom YOLO detection | Infrastructure compliance | Class name + count |
| **Motion/activity zones** | Optical flow analysis | Equipment operability | Boolean active/inactive |

### 2. What is NOT Identified

| Data Element | Why Not | Alternative Used |
|:------------|:--------|:----------------|
| **Individual faces** | Not needed for aggregate compliance; DPDP risk | Gaussian blur applied before any storage |
| **Biometric data** | No fingerprint/iris capture | Crowd counting replaces biometric verification |
| **Individual identity** | Not required for headcount discrepancy | Anonymous centroid tracking only |
| **Audio/speech** | Privacy violation risk | No audio processing at any stage |
| **Personal devices** | Not compliance-relevant | Excluded from detection classes |

### 3. Privacy Safeguards Implemented

1. **Auto Face Blurring:** Every evidence frame has Gaussian blur (kernel 51×51) applied over detected face regions before storage or transmission.
2. **Aggregate-Only Transmission:** Only numeric telemetry (`total_detected: 18, claimed: 30, delta: -12`) is transmitted to the central server. No raw video streams.
3. **Edge-First Processing:** Video frames are processed at the edge (on-premise) and never leave the training centre in raw form.
4. **Data Minimization:** Only 1 frame per 15-30 seconds is analyzed. 99.4% of footage is never processed.
5. **Retention Policy:** Evidence frames are auto-deleted after 30 days unless flagged for an active audit investigation.
6. **Access Control:** Dashboard access is role-based (National Admin, State Monitor, Centre Manager) with audit logging.

### 4. Legal Basis

- Processing is justified under **legitimate interest** for public fund accountability (DPDP Act Section 7).
- No **consent** is required for aggregate, anonymized counting in publicly funded training spaces.
- **Data fiduciary** responsibilities are met through automatic PII masking and minimal data retention.

---

*This document is part of the SIH submission for Problem Statement 26245.*
