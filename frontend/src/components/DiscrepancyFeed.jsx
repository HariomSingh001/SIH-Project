import React, { useState } from 'react';
import {
  AlertTriangle,
  AlertOctagon,
  CheckCircle2,
  Filter,
  Eye,
  ShieldAlert,
  ArrowRight
} from 'lucide-react';
import { translations } from '../utils/translations';

export default function DiscrepancyFeed({
  alerts = [],
  lang = 'en',
  onInspectEvidence,
  onUpdateAlertStatus
}) {
  const t = translations[lang];
  const [filterSeverity, setFilterSeverity] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const filteredAlerts = alerts.filter((alert) => {
    if (filterSeverity !== 'ALL' && alert.severity.toUpperCase() !== filterSeverity) {
      return false;
    }
    if (filterStatus !== 'ALL' && alert.status.toUpperCase() !== filterStatus) {
      return false;
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Filter Bar */}
      <div className="card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Filter size={16} color="#64748b" />
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#475569' }}>Filter by Severity:</span>
          {['ALL', 'CRITICAL', 'WARNING'].map((sev) => (
            <button
              key={sev}
              className={`btn-pill ${filterSeverity === sev ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilterSeverity(sev)}
            >
              {sev === 'ALL' ? t.all : sev === 'CRITICAL' ? t.critical : t.warning}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#475569' }}>Status:</span>
          {['ALL', 'OPEN', 'ACKNOWLEDGED', 'RESOLVED'].map((st) => (
            <button
              key={st}
              className={`btn-pill ${filterStatus === st ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilterStatus(st)}
            >
              {st === 'ALL' ? t.all : st === 'OPEN' ? t.open : st === 'ACKNOWLEDGED' ? t.acknowledged : t.resolved}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '18px' }}>
        {filteredAlerts.length === 0 ? (
          <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px' }}>
            <p style={{ color: '#94a3b8', fontSize: '14px' }}>No discrepancies matching the selected filter criteria.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.alert_id}
              className={`card alert-feed-card ${alert.severity.toLowerCase()}`}
              style={{ padding: '20px' }}
            >
              <div className="alert-card-header">
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '700' }}>
                      {alert.alert_id}
                    </span>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>&bull;</span>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>
                      {alert.timestamp?.slice(0, 10)} {alert.timestamp?.slice(11, 16)}
                    </span>
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a', marginTop: '4px' }}>
                    {alert.centre_name || alert.centre_id}
                  </h4>
                </div>

                <div style={{ display: 'flex', gap: '6px' }}>
                  <span className={`alert-badge ${alert.severity.toLowerCase()}`}>
                    {alert.severity}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '3px 8px',
                      borderRadius: '9999px',
                      background: alert.status === 'Open' ? '#f1f5f9' : '#e0f2fe',
                      color: alert.status === 'Open' ? '#475569' : '#0369a1'
                    }}
                  >
                    {alert.status}
                  </span>
                </div>
              </div>

              <div style={{ margin: '8px 0' }}>
                <span
                  style={{
                    display: 'inline-block',
                    fontSize: '11px',
                    fontWeight: '700',
                    color: alert.alert_type === 'GHOST_BATCH' ? '#dc2626' : '#d97706',
                    background: '#f8fafc',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    marginBottom: '6px'
                  }}
                >
                  TYPE: {alert.alert_type}
                </span>
                <p style={{ fontSize: '12.5px', color: '#334155', lineHeight: 1.5 }}>
                  {alert.description}
                </p>
              </div>

              <div className="alert-metrics-pill" style={{ justifyContent: 'space-between', margin: '8px 0' }}>
                <span>Claimed: <strong>{alert.claimed_value}</strong></span>
                <span>AI Vision: <strong>{alert.detected_value}</strong></span>
                <span style={{ color: alert.severity === 'Critical' ? '#dc2626' : '#d97706', fontWeight: '700' }}>
                  Gap: {alert.percentage_gap}%
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '12px', borderTop: '1px solid #f1f5f9' }}>
                <button
                  className="btn-secondary btn-pill"
                  onClick={() => onInspectEvidence && onInspectEvidence(alert)}
                >
                  <Eye size={13} /> {t.inspectEvidence}
                </button>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {alert.status === 'Open' && (
                    <button
                      className="btn-primary btn-pill"
                      style={{ padding: '6px 12px', fontSize: '11.5px' }}
                      onClick={() => onUpdateAlertStatus(alert.alert_id, 'Acknowledged')}
                    >
                      {t.acknowledge}
                    </button>
                  )}
                  {alert.status === 'Acknowledged' && (
                    <button
                      className="btn-primary btn-pill"
                      style={{ padding: '6px 12px', fontSize: '11.5px' }}
                      onClick={() => onUpdateAlertStatus(alert.alert_id, 'Resolved')}
                    >
                      {t.resolve}
                    </button>
                  )}
                  <button
                    className="btn-danger-outline btn-pill"
                    style={{ padding: '5px 10px', fontSize: '11.5px' }}
                    onClick={() => onUpdateAlertStatus(alert.alert_id, 'Escalated')}
                  >
                    Escalate
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
