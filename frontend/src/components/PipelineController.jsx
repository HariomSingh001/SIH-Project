import React, { useState, useEffect } from 'react';
import {
  Play,
  CheckCircle,
  AlertTriangle,
  Wifi,
  WifiOff,
  Database,
  ArrowRight,
  HardDrive,
  Cpu,
  ShieldCheck,
  RefreshCw,
  Calculator,
  Sliders,
  Sparkles
} from 'lucide-react';
import { translations } from '../utils/translations';

export default function PipelineController({
  lang = 'en',
  wsConnected = false,
  pipelineStatus = null,
  onRefreshData
}) {
  const t = translations[lang];

  // Pipeline execution state
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState(null);
  const [selectedVideo, setSelectedVideo] = useState('data/videos/15861386_1080_1920_30fps.mp4');
  const [selectedCentre, setSelectedCentre] = useState('CTR-DL-001');

  // Store-and-Forward Edge states
  const [edgeOnline, setEdgeOnline] = useState(true);
  const [bufferedCount, setBufferedCount] = useState(0);
  const [bufferedBytes, setBufferedBytes] = useState(0);
  const [edgeLoading, setEdgeLoading] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  // Bandwidth calculator states
  const [cameraCount, setCameraCount] = useState(3);
  const [dailyHours, setDailyHours] = useState(8);
  const [samplingInterval, setSamplingInterval] = useState(25); // seconds

  // Fetch initial edge status
  const fetchEdgeStatus = async () => {
    try {
      const res = await fetch('/api/edge/status');
      if (res.ok) {
        const data = await res.json();
        setEdgeOnline(data.is_online);
        setBufferedCount(data.buffered_packets_count);
        setBufferedBytes(data.buffered_size_bytes);
      }
    } catch (e) {
      console.warn('Edge status check failed:', e);
    }
  };

  useEffect(() => {
    fetchEdgeStatus();
  }, []);

  // Update pipeline progress when received from parent WebSocket
  useEffect(() => {
    if (pipelineStatus) {
      setPipelineProgress(pipelineStatus);
      if (pipelineStatus.type === 'PIPELINE_COMPLETE' || pipelineStatus.type === 'PIPELINE_ERROR') {
        setRunningPipeline(false);
        if (onRefreshData) onRefreshData();
      }
    }
  }, [pipelineStatus]);

  // Run AI Vision Pipeline on video
  const handleStartPipeline = async () => {
    setRunningPipeline(true);
    setPipelineProgress({
      type: 'PIPELINE_STARTED',
      status: 'Launching YOLOv8s Detection and Face Blur pipeline...',
      progress_percent: 5
    });

    try {
      const res = await fetch('/api/pipeline/process-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: selectedVideo,
          centre_id: selectedCentre,
          camera_id: 'CAM-DL001-01',
          sampling_interval: 2.0,
          confidence: 0.25
        })
      });

      if (!res.ok) {
        throw new Error('Failed to start pipeline execution');
      }
    } catch (err) {
      setRunningPipeline(false);
      setPipelineProgress({
        type: 'PIPELINE_ERROR',
        error: err.message
      });
    }
  };

  // Toggle network online/offline
  const handleToggleNetwork = async () => {
    setEdgeLoading(true);
    try {
      const newStatus = !edgeOnline;
      const res = await fetch('/api/edge/toggle-network', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_online: newStatus })
      });
      if (res.ok) {
        const data = await res.json();
        setEdgeOnline(data.is_online);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEdgeLoading(false);
    }
  };

  // Generate a sample edge packet
  const handleGeneratePacket = async () => {
    setEdgeLoading(true);
    try {
      const res = await fetch('/api/edge/generate-sample-packet', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setBufferedCount(data.buffered_packets_count);
        fetchEdgeStatus();
        if (onRefreshData) onRefreshData();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEdgeLoading(false);
    }
  };

  // Flush buffer to cloud
  const handleFlushBuffer = async () => {
    setEdgeLoading(true);
    try {
      const res = await fetch('/api/edge/flush', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSyncResult(data);
        setBufferedCount(0);
        setBufferedBytes(0);
        fetchEdgeStatus();
        if (onRefreshData) onRefreshData();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setEdgeLoading(false);
    }
  };

  // Bandwidth calculation math
  // Traditional RTSP continuous: 1080p @ 30fps = ~2.0 Mbps bitrate
  const rtspBytesPerHourPerCam = 2.0 * 1024 * 1024 * 3600 / 8; // ~900 MB/hr
  const rtspDailyGB = (cameraCount * dailyHours * rtspBytesPerHourPerCam) / (1024 * 1024 * 1024);
  const rtspMonthlyGB = rtspDailyGB * 30;

  // Parman AI: Samples 1 frame every `samplingInterval` seconds
  const samplesPerHour = 3600 / samplingInterval;
  const jsonPacketBytes = 2048; // ~2 KB JSON
  // Only ~15% of frames require evidence upload (on discrepancies or periodic audit)
  const evidenceJPEGsPerHour = Math.max(1, samplesPerHour * 0.15);
  const jpegBytes = 85 * 1024; // ~85 KB JPEG
  const parmanBytesPerHourPerCam = (samplesPerHour * jsonPacketBytes) + (evidenceJPEGsPerHour * jpegBytes);
  const parmanDailyMB = (cameraCount * dailyHours * parmanBytesPerHourPerCam) / (1024 * 1024);
  const parmanMonthlyGB = (parmanDailyMB * 30) / 1024;

  const savingsPercent = ((1 - (parmanDailyMB / 1024) / rtspDailyGB) * 100).toFixed(2);
  const costSavingsINR = Math.round((rtspMonthlyGB - parmanMonthlyGB) * 12); // ~₹12/GB 4G enterprise data

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* SECTION 1: End-to-End AI Video Pipeline */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#15803d', background: '#ecfdf5', padding: '3px 8px', borderRadius: '4px' }}>
                PHASE 5 CORE
              </span>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a' }}>
                {t.runPipelineTitle}
              </h3>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
              {t.runPipelineSubtitle}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontSize: '11.5px',
                fontWeight: '600',
                padding: '4px 10px',
                borderRadius: '9999px',
                background: wsConnected ? '#dcfce7' : '#fee2e2',
                color: wsConnected ? '#15803d' : '#991b1b',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: wsConnected ? '#15803d' : '#dc2626' }}></span>
              {wsConnected ? t.wsConnected : t.wsDisconnected}
            </span>
          </div>
        </div>

        {/* Pipeline Controls & Execution Form */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.6fr', gap: '24px', alignItems: 'start' }}>
          <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '14.5px', fontWeight: '700', marginBottom: '14px', color: '#1e293b' }}>
              Select Video & Inspection Parameters
            </h4>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', display: 'block', marginBottom: '4px' }}>
                  Classroom Video Source:
                </label>
                <select
                  value={selectedVideo}
                  onChange={(e) => setSelectedVideo(e.target.value)}
                  disabled={runningPipeline}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12.5px' }}
                >
                  <option value="data/videos/15861386_1080_1920_30fps.mp4">
                    Sample Classroom Lecture Hall (1080p 30fps)
                  </option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: '#64748b', display: 'block', marginBottom: '4px' }}>
                  Target Training Centre:
                </label>
                <select
                  value={selectedCentre}
                  onChange={(e) => setSelectedCentre(e.target.value)}
                  disabled={runningPipeline}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '12.5px' }}
                >
                  <option value="CTR-DL-001">CTR-DL-001 — Skill India Training Academy (Dwarka)</option>
                  <option value="CTR-RJ-002">CTR-RJ-002 — Rajasthan Vocational Training Institute (Jaipur)</option>
                  <option value="CTR-KA-003">CTR-KA-003 — Karnataka Skill Development Centre (Bengaluru)</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '11.5px', fontWeight: '600', color: '#64748b', display: 'block', marginBottom: '4px' }}>
                    Model:
                  </label>
                  <input
                    type="text"
                    disabled
                    value="YOLOv8s (1280px)"
                    style={{ width: '100%', padding: '7px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px', background: '#f1f5f9' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '11.5px', fontWeight: '600', color: '#64748b', display: 'block', marginBottom: '4px' }}>
                    Privacy Engine:
                  </label>
                  <input
                    type="text"
                    disabled
                    value="Gaussian Face Blur"
                    style={{ width: '100%', padding: '7px', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px', background: '#f1f5f9' }}
                  />
                </div>
              </div>

              <button
                id="btn-run-pipeline"
                className="btn-primary"
                style={{ marginTop: '8px', padding: '12px', width: '100%', justifyContent: 'center' }}
                onClick={handleStartPipeline}
                disabled={runningPipeline}
              >
                {runningPipeline ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    <span>Processing Video Frames...</span>
                  </>
                ) : (
                  <>
                    <Play size={16} fill="white" />
                    <span>Run End-to-End AI Vision Pipeline</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Pipeline Real-time Progress Card */}
          <div style={{ background: '#ffffff', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', minHeight: '290px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '14.5px', fontWeight: '700', color: '#0f172a' }}>
                  Live Execution & Progress Stream
                </h4>
                {pipelineProgress && (
                  <span style={{ fontSize: '12px', fontWeight: '700', color: '#15803d' }}>
                    {pipelineProgress.progress_percent || (pipelineProgress.type === 'PIPELINE_COMPLETE' ? 100 : 0)}%
                  </span>
                )}
              </div>

              {/* Progress Bar */}
              <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '9999px', overflow: 'hidden', marginBottom: '16px' }}>
                <div
                  style={{
                    height: '100%',
                    background: 'linear-gradient(90deg, #15803d, #10b981)',
                    width: `${pipelineProgress ? (pipelineProgress.progress_percent || (pipelineProgress.type === 'PIPELINE_COMPLETE' ? 100 : 0)) : 0}%`,
                    transition: 'width 0.4s ease'
                  }}
                ></div>
              </div>

              {/* Execution Status Feedback */}
              {!pipelineProgress && !runningPipeline && (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8' }}>
                  <Cpu size={36} strokeWidth={1.5} style={{ margin: '0 auto 10px', display: 'block', color: '#cbd5e1' }} />
                  <p style={{ fontSize: '13px' }}>Click <strong>"Run End-to-End AI Vision Pipeline"</strong> to sample frames, detect students, apply face blurring, and stream live telemetry.</p>
                </div>
              )}

              {pipelineProgress && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', fontSize: '12.5px' }}>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '11px' }}>Current Operation:</span>
                    <strong style={{ color: '#0f172a' }}>
                      {pipelineProgress.status || (pipelineProgress.type === 'PIPELINE_FRAME_PROCESSED' ? `Processed Frame #${pipelineProgress.frame_index} of ${pipelineProgress.total_frames}` : pipelineProgress.message || 'Pipeline in progress...')}
                    </strong>
                  </div>

                  {pipelineProgress.type === 'PIPELINE_FRAME_PROCESSED' && (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                      <div style={{ background: '#ecfdf5', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                        <span style={{ fontSize: '10.5px', color: '#065f46' }}>Detected Persons</span>
                        <p style={{ fontSize: '16px', fontWeight: '700', color: '#15803d' }}>{pipelineProgress.persons_detected}</p>
                      </div>
                      <div style={{ background: '#f1f5f9', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                        <span style={{ fontSize: '10.5px', color: '#475569' }}>Frame Index</span>
                        <p style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>#{pipelineProgress.frame_index}</p>
                      </div>
                      <div style={{ background: '#ecfdf5', padding: '8px', borderRadius: '6px', textAlign: 'center' }}>
                        <span style={{ fontSize: '10.5px', color: '#065f46' }}>Privacy Mask</span>
                        <p style={{ fontSize: '13px', fontWeight: '700', color: '#15803d' }}>Applied</p>
                      </div>
                    </div>
                  )}

                  {pipelineProgress.type === 'PIPELINE_COMPLETE' && (
                    <div style={{ background: '#ecfdf5', border: '1px solid #bbf7d0', padding: '14px', borderRadius: '8px', color: '#065f46' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '700', fontSize: '14px' }}>
                        <CheckCircle size={18} /> Analysis Complete & Verified!
                      </div>
                      <p style={{ fontSize: '12.5px', marginTop: '4px' }}>
                        Processed video successfully. Peak detection: <strong>{pipelineProgress.max_persons_detected} students</strong>. Bandwidth saving: <strong>{pipelineProgress.bandwidth_saving_pct}%</strong>. Generated <strong>{pipelineProgress.alerts_generated}</strong> telemetry discrepancy alert(s).
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '12px', borderTop: '1px solid #f1f5f9', paddingTop: '10px' }}>
              Telemetry packets automatically stream to backend database & connected WebSocket clients in real-time.
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: Store-and-Forward Offline Resilience Simulation */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '700', color: '#0284c7', background: '#f0f9ff', padding: '3px 8px', borderRadius: '4px' }}>
                OFFLINE EDGE RESILIENCE
              </span>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a' }}>
                {t.storeAndForwardTitle}
              </h3>
            </div>
            <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
              {t.storeAndForwardSubtitle}
            </p>
          </div>

          {/* Network State Toggle Button */}
          <button
            className={edgeOnline ? 'btn-primary btn-pill' : 'btn-danger-outline btn-pill'}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
            onClick={handleToggleNetwork}
            disabled={edgeLoading}
          >
            {edgeOnline ? (
              <>
                <Wifi size={15} /> Edge Network: Online
              </>
            ) : (
              <>
                <WifiOff size={15} /> Edge Network: Offline (Drop Outage)
              </>
            )}
          </button>
        </div>

        {/* Store-and-Forward Interactive Dashboard */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
          {/* Card A: Local Queue Status */}
          <div style={{ background: '#f8fafc', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <HardDrive size={20} color="#64748b" />
              <h4 style={{ fontSize: '14.5px', fontWeight: '700', color: '#1e293b' }}>
                Local Edge Queue Buffer
              </h4>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '12.5px', color: '#64748b' }}>Queued Telemetry Packets:</span>
              <strong style={{ fontSize: '18px', color: bufferedCount > 0 ? '#d97706' : '#15803d' }}>
                {bufferedCount} packets
              </strong>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <span style={{ fontSize: '12.5px', color: '#64748b' }}>Queue Payload Size:</span>
              <strong style={{ fontSize: '13.5px', color: '#0f172a' }}>
                {(bufferedBytes / 1024).toFixed(1)} KB (Encrypted)
              </strong>
            </div>

            <button
              className="btn-secondary"
              style={{ width: '100%', fontSize: '12.5px', justifyContent: 'center' }}
              onClick={handleGeneratePacket}
              disabled={edgeLoading}
            >
              <Sparkles size={14} /> Generate Camera Detection Frame
            </button>
            <p style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px', textAlign: 'center' }}>
              {edgeOnline
                ? '⚡ Network is online: packet will send directly to central cloud.'
                : '🔒 Network is offline: packet will be securely queued in edge storage.'}
            </p>
          </div>

          {/* Card B: Cloud Flush / Sync Actions */}
          <div style={{ background: '#f8fafc', padding: '18px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <Database size={20} color="#15803d" />
                <h4 style={{ fontSize: '14.5px', fontWeight: '700', color: '#1e293b' }}>
                  Cloud Synchronization Hub
                </h4>
              </div>

              <p style={{ fontSize: '12.5px', color: '#64748b', lineHeight: 1.4, marginBottom: '14px' }}>
                When connectivity is re-established, the edge agent initiates a chronological batch upload via <code>/api/telemetry/batch</code> to eliminate packet loss.
              </p>

              {syncResult && (
                <div style={{ background: '#ecfdf5', padding: '10px', borderRadius: '8px', fontSize: '12px', color: '#065f46', marginBottom: '12px' }}>
                  ✓ Successfully synchronized {syncResult.synced_count} buffered packet(s) to central database!
                </div>
              )}
            </div>

            <button
              className="btn-primary"
              style={{ width: '100%', fontSize: '12.5px', justifyContent: 'center' }}
              onClick={handleFlushBuffer}
              disabled={edgeLoading || bufferedCount === 0 || !edgeOnline}
            >
              <RefreshCw size={14} /> Flush Buffer to Central Cloud ({bufferedCount})
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 3: Bandwidth Economy & Mathematical Proof */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Calculator size={22} color="#15803d" />
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f172a' }}>
              {t.bandwidthCalcTitle}
            </h3>
            <p style={{ fontSize: '13px', color: '#64748b' }}>
              {t.bandwidthCalcSubtitle}
            </p>
          </div>
        </div>

        {/* Sliders and Configuration */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px', background: '#f8fafc', padding: '18px', borderRadius: '12px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', marginBottom: '6px' }}>
              <span style={{ color: '#64748b', fontWeight: '600' }}>CCTV Cameras:</span>
              <strong style={{ color: '#0f172a' }}>{cameraCount} Cameras</strong>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={cameraCount}
              onChange={(e) => setCameraCount(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', marginBottom: '6px' }}>
              <span style={{ color: '#64748b', fontWeight: '600' }}>Daily Active Hours:</span>
              <strong style={{ color: '#0f172a' }}>{dailyHours} Hours/Day</strong>
            </div>
            <input
              type="range"
              min="4"
              max="16"
              value={dailyHours}
              onChange={(e) => setDailyHours(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12.5px', marginBottom: '6px' }}>
              <span style={{ color: '#64748b', fontWeight: '600' }}>Sampling Frequency:</span>
              <strong style={{ color: '#0f172a' }}>1 sample / {samplingInterval}s</strong>
            </div>
            <input
              type="range"
              min="10"
              max="60"
              step="5"
              value={samplingInterval}
              onChange={(e) => setSamplingInterval(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>

        {/* Comparison Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '18px' }}>
          {/* Traditional Streaming */}
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', padding: '18px', borderRadius: '12px' }}>
            <span style={{ fontSize: '11.5px', fontWeight: '700', color: '#991b1b', textTransform: 'uppercase' }}>
              Traditional Raw Video Streaming
            </span>
            <h4 style={{ fontSize: '24px', fontWeight: '700', color: '#991b1b', margin: '8px 0 4px' }}>
              {rtspDailyGB.toFixed(1)} GB / Day
            </h4>
            <p style={{ fontSize: '12px', color: '#7f1d1d' }}>
              Continuous 1080p RTSP stream @ 2 Mbps bitrate per camera.
            </p>
            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #fee2e2', fontSize: '12px', color: '#991b1b' }}>
              Monthly Consumption: <strong>{rtspMonthlyGB.toFixed(0)} GB / month</strong>
            </div>
          </div>

          {/* Parman AI Smart Telemetry */}
          <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '18px', borderRadius: '12px' }}>
            <span style={{ fontSize: '11.5px', fontWeight: '700', color: '#065f46', textTransform: 'uppercase' }}>
              Parman AI Edge Vision Telemetry
            </span>
            <h4 style={{ fontSize: '24px', fontWeight: '700', color: '#15803d', margin: '8px 0 4px' }}>
              {parmanDailyMB.toFixed(1)} MB / Day
            </h4>
            <p style={{ fontSize: '12px', color: '#065f46' }}>
              Smart 1-per-{samplingInterval}s telemetry JSON + key blurred evidence frames.
            </p>
            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #d1fae5', fontSize: '12px', color: '#065f46' }}>
              Monthly Consumption: <strong>{(parmanMonthlyGB * 1024).toFixed(0)} MB / month</strong>
            </div>
          </div>

          {/* Net Impact & Cost Savings */}
          <div style={{ background: '#f0f9ff', border: '1px solid #bae6fd', padding: '18px', borderRadius: '12px' }}>
            <span style={{ fontSize: '11.5px', fontWeight: '700', color: '#075985', textTransform: 'uppercase' }}>
              Efficiency & Cost Savings
            </span>
            <h4 style={{ fontSize: '24px', fontWeight: '700', color: '#0284c7', margin: '8px 0 4px' }}>
              {savingsPercent}% Savings
            </h4>
            <p style={{ fontSize: '12px', color: '#0369a1' }}>
              Saves approximately <strong>{(rtspMonthlyGB - parmanMonthlyGB).toFixed(0)} GB</strong> of cellular data every month.
            </p>
            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #e0f2fe', fontSize: '12px', color: '#075985' }}>
              Estimated 4G Data Cost Saved: <strong>₹{costSavingsINR.toLocaleString('en-IN')} / centre / month</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
