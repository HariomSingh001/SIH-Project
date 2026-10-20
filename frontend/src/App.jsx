import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import DashboardOverview from './components/DashboardOverview';
import NationalMap from './components/NationalMap';
import DiscrepancyFeed from './components/DiscrepancyFeed';
import CentresView from './components/CentresView';
import EvidenceInspector from './components/EvidenceInspector';
import PipelineController from './components/PipelineController';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [lang, setLang] = useState('en');

  // Backend Data States
  const [stats, setStats] = useState({});
  const [mapMarkers, setMapMarkers] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stateSummary, setStateSummary] = useState([]);
  const [centres, setCentres] = useState([]);

  // WebSocket & Pipeline Progress States
  const [wsConnected, setWsConnected] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState(null);
  const wsRef = useRef(null);

  // Interaction States
  const [selectedCentreId, setSelectedCentreId] = useState(null);
  const [inspectingAlert, setInspectingAlert] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [notification, setNotification] = useState(null);

  // Fetch all initial data from FastAPI backend
  const fetchDashboardData = async () => {
    try {
      // 1. Stats
      const statsRes = await fetch('/api/dashboard/stats');
      if (statsRes.ok) setStats(await statsRes.json());

      // 2. Map Markers
      const mapRes = await fetch('/api/dashboard/map');
      if (mapRes.ok) setMapMarkers(await mapRes.json());

      // 3. Discrepancies
      const alertsRes = await fetch('/api/discrepancies');
      if (alertsRes.ok) setAlerts(await alertsRes.json());

      // 4. State Summary
      const stateRes = await fetch('/api/dashboard/state-summary');
      if (stateRes.ok) setStateSummary(await stateRes.json());

      // 5. Centres
      const centresRes = await fetch('/api/centres');
      if (centresRes.ok) setCentres(await centresRes.json());
    } catch (err) {
      console.warn('Backend fetch fallback:', err);
    }
  };

  // WebSocket Connection Lifecycle
  useEffect(() => {
    fetchDashboardData();

    // Setup WebSocket to backend port 8000
    const host = window.location.hostname || '127.0.0.1';
    const wsUrl = `ws://${host}:8000/ws`;

    const connectWebSocket = () => {
      try {
        const socket = new WebSocket(wsUrl);
        wsRef.current = socket;

        socket.onopen = () => {
          setWsConnected(true);
          console.log('[WebSocket] Connected to Pramaan AI Central Live Stream');
        };

        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data);
            const { type, data } = payload;

            if (type === 'TELEMETRY_INGESTED') {
              showNotification(`⚡ Live Edge Telemetry: ${data.persons_detected} persons verified at ${data.centre_id}`);
              fetchDashboardData();
            } else if (type === 'NEW_DISCREPANCY_ALERT') {
              showNotification(`⚠️ Discrepancy Alert: New discrepancy detected at ${data.centre_name || data.centre_id}!`);
              fetchDashboardData();
            } else if (type === 'STORE_AND_FORWARD_SYNCED') {
              showNotification(`✓ Edge Sync: ${data.packets_synced} packets synchronized from edge buffer!`);
              fetchDashboardData();
            } else if (type.startsWith('PIPELINE_')) {
              setPipelineStatus({ type, ...data });
            }
          } catch (e) {
            console.error('[WebSocket] Failed to parse message:', e);
          }
        };

        socket.onclose = () => {
          setWsConnected(false);
          // Try reconnecting after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };

        socket.onerror = (err) => {
          console.warn('[WebSocket] Connection error:', err);
          socket.close();
        };
      } catch (e) {
        console.warn('[WebSocket] Failed to initiate:', e);
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Simulate an Edge AI packet transmission
  const handleSimulateEdgePacket = async () => {
    setSimulating(true);
    try {
      const now = new Date();
      const payload = {
        centre_id: 'CTR-DL-001',
        camera_id: 'CAM-DL001-01',
        camera_location: 'Classroom 1',
        batch_id: 'BTH-DL001-A',
        timestamp: now.toISOString(),
        frame_index: Math.floor(Math.random() * 200) + 1,
        total_detected_persons: Math.floor(Math.random() * 12) + 14,
        confidence_avg: 0.89,
        roi_area: 'classroom_seating',
        equipment_detected: {
          items_detected: [
            { class: 'desktop_computer', count: 28, confidence_avg: 0.93 },
            { class: 'chair', count: 30, confidence_avg: 0.88 }
          ]
        },
        evidence_frame_path: '/output/evidence/2026-10-20_02-54-07_blurred.jpg',
        privacy_masked: true
      };

      const res = await fetch('/api/telemetry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        showNotification(`⚡ Live Edge Packet Ingested! Detected ${data.persons_detected} students.`);
        await fetchDashboardData();
      }
    } catch (err) {
      showNotification('⚡ Simulated edge telemetry packet received.');
    } finally {
      setSimulating(false);
    }
  };

  // Update alert status
  const handleUpdateAlertStatus = async (alertId, newStatus) => {
    try {
      const res = await fetch(`/api/discrepancies/${alertId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        showNotification(`Alert ${alertId} updated to ${newStatus}`);
        fetchDashboardData();
      }
    } catch (err) {
      console.error('Failed to update alert:', err);
    }
  };

  // Notification helper
  const showNotification = (msg) => {
    setNotification(msg);
    setTimeout(() => setNotification(null), 4000);
  };

  // Navigation handlers
  const handleSelectCentre = (centreId) => {
    setSelectedCentreId(centreId);
    setActiveTab('centres');
  };

  const handleInspectEvidence = (alert) => {
    setInspectingAlert(alert);
    setActiveTab('evidence');
  };

  const openAlertsCount = alerts.filter((a) => a.status === 'Open').length;

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {notification && (
        <div
          style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            background: '#0f172a',
            color: '#ffffff',
            padding: '12px 20px',
            borderRadius: '12px',
            boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
            zIndex: 999,
            fontSize: '13.5px',
            fontWeight: '600',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            animation: 'fadeIn 0.3s ease'
          }}
        >
          <span>{notification}</span>
        </div>
      )}

      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        lang={lang}
        setLang={setLang}
        openAlertsCount={openAlertsCount}
      />

      {/* Main Content View */}
      <main className="main-content">
        <TopBar
          activeTab={activeTab}
          lang={lang}
          onSimulate={handleSimulateEdgePacket}
          simulating={simulating}
        />

        {activeTab === 'dashboard' && (
          <DashboardOverview
            stats={stats}
            mapMarkers={mapMarkers}
            alerts={alerts}
            stateSummary={stateSummary}
            lang={lang}
            onSelectCentre={handleSelectCentre}
            onInspectEvidence={handleInspectEvidence}
            onUpdateAlertStatus={handleUpdateAlertStatus}
          />
        )}

        {activeTab === 'map' && (
          <div className="card" style={{ height: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '14px' }}>
              Full Interactive National Compliance Map
            </h3>
            <div style={{ flex: 1, minHeight: '400px' }}>
              <NationalMap
                markers={mapMarkers}
                onSelectCentre={handleSelectCentre}
                lang={lang}
              />
            </div>
          </div>
        )}

        {activeTab === 'discrepancies' && (
          <DiscrepancyFeed
            alerts={alerts}
            lang={lang}
            onInspectEvidence={handleInspectEvidence}
            onUpdateAlertStatus={handleUpdateAlertStatus}
          />
        )}

        {activeTab === 'centres' && (
          <CentresView
            centres={centres.length > 0 ? centres : mapMarkers}
            selectedCentreId={selectedCentreId}
            lang={lang}
          />
        )}

        {activeTab === 'evidence' && (
          <EvidenceInspector
            alert={inspectingAlert}
            lang={lang}
          />
        )}

        {activeTab === 'pipeline' && (
          <PipelineController
            lang={lang}
            wsConnected={wsConnected}
            pipelineStatus={pipelineStatus}
            onRefreshData={fetchDashboardData}
          />
        )}
      </main>
    </div>
  );
}
