import React from 'react';
import {
  Building,
  ShieldCheck,
  AlertOctagon,
  Wifi,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Eye,
  CheckCircle2
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import NationalMap from './NationalMap';
import { translations } from '../utils/translations';

export default function DashboardOverview({
  stats,
  mapMarkers,
  alerts = [],
  stateSummary = [],
  lang = 'en',
  onSelectCentre,
  onInspectEvidence,
  onUpdateAlertStatus
}) {
  const t = translations[lang];

  // Sample historical trend data for the chart comparing claimed vs verified
  const trendData = [
    { date: '15 Oct', claimed: 118, verified: 114 },
    { date: '16 Oct', claimed: 124, verified: 119 },
    { date: '17 Oct', claimed: 120, verified: 105 },
    { date: '18 Oct', claimed: 125, verified: 92 },
    { date: '19 Oct', claimed: 130, verified: 88 },
    { date: '20 Oct (Today)', claimed: 132, verified: 86 }
  ];

  return (
    <div>
      {/* 4 Hero KPI Cards */}
      <div className="stats-grid">
        {/* Card 1: Centres */}
        <div className="card stat-card">
          <div className="stat-icon-wrapper green">
            <Building size={26} strokeWidth={2.2} />
          </div>
          <div className="stat-details">
            <h3>{stats.total_centres || 5}</h3>
            <p>{t.monitoredCentres}</p>
            <span className="stat-subtext">
              <CheckCircle2 size={13} /> {stats.active_centres || 5} active empanelled
            </span>
          </div>
        </div>

        {/* Card 2: Average Trust Score */}
        <div className="card stat-card">
          <div className="stat-icon-wrapper blue">
            <ShieldCheck size={26} strokeWidth={2.2} />
          </div>
          <div className="stat-details">
            <h3>{stats.national_average_trust_score || 85.9}%</h3>
            <p>{t.averageTrustScore}</p>
            <span className="stat-subtext" style={{ color: '#0284c7' }}>
              <TrendingUp size={13} /> High Reliability Index
            </span>
          </div>
        </div>

        {/* Card 3: Active Discrepancies */}
        <div className="card stat-card">
          <div className="stat-icon-wrapper red">
            <AlertOctagon size={26} strokeWidth={2.2} />
          </div>
          <div className="stat-details">
            <h3>{stats.total_open_alerts || alerts.length}</h3>
            <p>{t.activeAlerts}</p>
            <span className="stat-subtext" style={{ color: '#dc2626' }}>
              <TrendingDown size={13} /> {stats.critical_alerts_count || 2} Critical Attention
            </span>
          </div>
        </div>

        {/* Card 4: Bandwidth Savings */}
        <div className="card stat-card">
          <div className="stat-icon-wrapper amber">
            <Wifi size={26} strokeWidth={2.2} />
          </div>
          <div className="stat-details">
            <h3>{stats.low_bandwidth_savings_pct || 97.3}%</h3>
            <p>{t.bandwidthEconomy}</p>
            <span className="stat-subtext" style={{ color: '#b45309' }}>
              587 MB vs 21.6 GB/day
            </span>
          </div>
        </div>
      </div>

      {/* Main 2-Column Section */}
      <div className="dashboard-columns">
        {/* Left Column: Map & Chart */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Map Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '17px', fontWeight: '700' }}>{t.geographicOverview}</h3>
                <p style={{ fontSize: '12.5px', color: '#64748b' }}>{t.geographicSubtitle}</p>
              </div>
              <div style={{ display: 'flex', gap: '10px', fontSize: '11.5px', fontWeight: '600' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#15803d' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#15803d' }}></span> Normal
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#d97706' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#d97706' }}></span> Warning
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#dc2626' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#dc2626' }}></span> Critical
                </span>
              </div>
            </div>

            <NationalMap markers={mapMarkers} onSelectCentre={onSelectCentre} lang={lang} />
          </div>

          {/* Attendance Trend Chart */}
          <div className="card">
            <div style={{ marginBottom: '18px' }}>
              <h3 style={{ fontSize: '17px', fontWeight: '700' }}>{t.attendanceTrend}</h3>
              <p style={{ fontSize: '12.5px', color: '#64748b' }}>{t.attendanceTrendSubtitle}</p>
            </div>

            <div style={{ height: '240px', width: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#ffffff',
                      borderRadius: '10px',
                      border: '1px solid #e2e8f0',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.06)'
                    }}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                  <Bar dataKey="claimed" name="Claimed Attendance" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="verified" name="AI-Verified Vision Count" fill="#15803d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column: Live Discrepancy Stream & State Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Live Alerts Stream Card */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h3 style={{ fontSize: '17px', fontWeight: '700' }}>{t.liveAlerts}</h3>
                <p style={{ fontSize: '12px', color: '#64748b' }}>{alerts.length} active notifications</p>
              </div>
            </div>

            <div className="alert-feed-list">
              {alerts.length === 0 ? (
                <p style={{ textAlign: 'center', padding: '24px', color: '#94a3b8', fontSize: '13px' }}>
                  No active discrepancies. All centres compliant!
                </p>
              ) : (
                alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`alert-feed-card ${alert.severity.toLowerCase()}`}
                  >
                    <div className="alert-card-header">
                      <div>
                        <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>
                          {alert.centre_id} &bull; {alert.timestamp?.slice(11, 16) || 'Today'}
                        </span>
                        <h4 style={{ fontSize: '13.5px', fontWeight: '700', color: '#0f172a', marginTop: '2px' }}>
                          {alert.centre_name || alert.centre_id}
                        </h4>
                      </div>
                      <span className={`alert-badge ${alert.severity.toLowerCase()}`}>
                        {alert.severity}
                      </span>
                    </div>

                    <p style={{ fontSize: '12px', color: '#475569', lineHeight: 1.4 }}>
                      {alert.description}
                    </p>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <div className="alert-metrics-pill">
                        <span>Claimed: <strong>{alert.claimed_value}</strong></span>
                        <span>AI: <strong>{alert.detected_value}</strong></span>
                        <span style={{ color: alert.severity === 'Critical' ? '#dc2626' : '#d97706' }}>
                          (-{alert.percentage_gap}%)
                        </span>
                      </div>

                      <button
                        className="btn-secondary btn-pill"
                        style={{ padding: '5px 12px', fontSize: '11.5px', display: 'flex', alignItems: 'center', gap: '4px' }}
                        onClick={() => onInspectEvidence && onInspectEvidence(alert)}
                      >
                        <Eye size={13} /> {t.inspectEvidence}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* State Performance Breakdown */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '12px' }}>
              State Performance Breakdown
            </h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                    <th style={{ padding: '8px 4px', fontWeight: '600' }}>State</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600' }}>Centres</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600' }}>Trust Score</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stateSummary.map((item, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f8fafc' }}>
                      <td style={{ padding: '10px 4px', fontWeight: '600', color: '#1e293b' }}>
                        {item.state}
                      </td>
                      <td style={{ padding: '10px 4px', color: '#64748b' }}>
                        {item.total_centres}
                      </td>
                      <td style={{ padding: '10px 4px', fontWeight: '700', color: '#0f172a' }}>
                        {item.average_trust_score}%
                      </td>
                      <td style={{ padding: '10px 4px' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: '700',
                            padding: '2px 8px',
                            borderRadius: '9999px',
                            background:
                              item.average_trust_score < 60
                                ? '#fee2e2'
                                : item.average_trust_score < 85
                                ? '#fef3c7'
                                : '#dcfce7',
                            color:
                              item.average_trust_score < 60
                                ? '#991b1b'
                                : item.average_trust_score < 85
                                ? '#92400e'
                                : '#166534'
                          }}
                        >
                          {item.average_trust_score < 60 ? 'Critical' : item.average_trust_score < 85 ? 'Warning' : 'Normal'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
