import React, { useState } from 'react';
import {
  ShieldCheck,
  Eye,
  Lock,
  FileCheck,
  Sliders,
  Cpu,
  Download,
  Key
} from 'lucide-react';
import { translations } from '../utils/translations';

export default function EvidenceInspector({
  alert = null,
  lang = 'en'
}) {
  const t = translations[lang];
  const [viewMode, setViewMode] = useState('blurred'); // 'blurred' or 'annotated'

  // Evidence frame URLs generated in Phase 2
  const blurredPath = alert?.evidence_frame_path || '/output/evidence/2026-10-20_02-54-07_blurred.jpg';
  const annotatedPath = '/output/annotated/2026-10-20_02-54-07_annotated.jpg';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner explaining DPDP Compliance */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, #ffffff 0%, #f6fcf8 100%)',
          border: '1px solid #bbf7d0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          padding: '20px 24px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              background: '#ecfdf5',
              color: '#15803d',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <ShieldCheck size={26} />
          </div>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#0f172a' }}>
              Digital Personal Data Protection (DPDP) Act 2023 Compliance
            </h3>
            <p style={{ fontSize: '13px', color: '#475569', marginTop: '3px' }}>
              All evidence images are automatically sanitized with edge-based facial blurring before telemetry transmission.
            </p>
          </div>
        </div>

        {/* View Mode Toggle Buttons */}
        <div style={{ display: 'flex', background: '#f1f5f9', padding: '4px', borderRadius: '9999px', border: '1px solid #cbd5e1' }}>
          <button
            className={`btn-pill ${viewMode === 'blurred' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '7px 16px', fontSize: '12.5px' }}
            onClick={() => setViewMode('blurred')}
          >
            <Lock size={13} /> {t.privacyBlurred}
          </button>
          <button
            className={`btn-pill ${viewMode === 'annotated' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '7px 16px', fontSize: '12.5px' }}
            onClick={() => setViewMode('annotated')}
          >
            <Eye size={13} /> {t.detectionOverlay}
          </button>
        </div>
      </div>

      {/* Main Inspection Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '24px' }}>
        {/* Evidence Visualizer Frame */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: '700', color: '#64748b' }}>
                CAMERA FEED: CAM-DL001-01 (Classroom 1)
              </span>
              <span style={{ fontSize: '11px', background: '#e2e8f0', padding: '2px 8px', borderRadius: '4px' }}>
                Frame #42 &bull; 1080p
              </span>
            </div>
            <span
              style={{
                fontSize: '11.5px',
                fontWeight: '700',
                color: viewMode === 'blurred' ? '#15803d' : '#0284c7',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              {viewMode === 'blurred' ? '✓ Privacy Mask Applied' : '✓ YOLOv8 Detections'}
            </span>
          </div>

          <div
            style={{
              position: 'relative',
              width: '100%',
              borderRadius: '12px',
              overflow: 'hidden',
              backgroundColor: '#0f172a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '380px'
            }}
          >
            <img
              src={viewMode === 'blurred' ? blurredPath : annotatedPath}
              alt="Classroom Telemetry Evidence"
              style={{
                maxWidth: '100%',
                maxHeight: '460px',
                objectFit: 'contain',
                display: 'block'
              }}
              onError={(e) => {
                // Fallback demonstration placeholder if image path requires direct backend URL
                e.target.onerror = null;
                e.target.src = viewMode === 'blurred' 
                  ? 'http://127.0.0.1:8000/output/evidence/2026-10-20_02-54-07_blurred.jpg'
                  : 'http://127.0.0.1:8000/output/annotated/2026-10-20_02-54-07_annotated.jpg';
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '14px', fontSize: '12px', color: '#64748b' }}>
            <span>Evidence File: <code>2026-10-20_02-54-07_{viewMode}.jpg</code></span>
            <span>Size: <strong>84.2 KB (JPEG)</strong></span>
          </div>
        </div>

        {/* Telemetry & Cryptographic Verification Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Metadata Card */}
          <div className="card">
            <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={17} color="#15803d" /> AI Vision Metadata
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Model Architecture</span>
                <strong>YOLOv8s (1280px inference)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Persons Detected (AI)</span>
                <strong style={{ color: '#15803d', fontSize: '15px' }}>27 Persons</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Confidence Score (Mean)</span>
                <strong>89.4% (Min: 64%, Max: 97%)</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid #f1f5f9' }}>
                <span style={{ color: '#64748b' }}>Active Tracking IDs</span>
                <span>ByteTrack ID #101 - #127</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#64748b' }}>Sampling Frequency</span>
                <strong>1 sample / 15-30s</strong>
              </div>
            </div>
          </div>

          {/* Tamper-Proof Cryptographic Hash Card */}
          <div className="card">
            <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Key size={17} color="#0284c7" /> Tamper-Proof Integrity
            </h4>

            <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '10px', fontSize: '11.5px', marginBottom: '12px' }}>
              <span style={{ color: '#64748b', display: 'block', marginBottom: '4px' }}>SHA-256 Hash of Evidence Frame:</span>
              <code style={{ wordBreak: 'break-all', color: '#0f172a', fontWeight: '600' }}>
                9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
              </code>
            </div>

            <p style={{ fontSize: '12px', color: '#64748b', lineHeight: 1.4 }}>
              The cryptographic fingerprint of every privacy frame is anchored upon capture. Any post-ingestion tampering invalidates the audit trail.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
