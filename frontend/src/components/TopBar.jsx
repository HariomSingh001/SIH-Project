import React from 'react';
import { Shield, Activity, Wifi, Sparkles } from 'lucide-react';
import { translations } from '../utils/translations';

export default function TopBar({
  activeTab,
  lang,
  onSimulate,
  simulating
}) {
  const t = translations[lang];

  const pageHeadings = {
    dashboard: {
      title: lang === 'en' ? 'National Overview Dashboard' : 'राष्ट्रीय समीक्षा डैशबोर्ड',
      sub: lang === 'en' ? 'Real-time telemetry and AI vision compliance monitoring' : 'रीयल-टाइम टेलीमेट्री एवं AI विज़न अनुपालन निगरानी'
    },
    map: {
      title: t.nationalMap,
      sub: t.geographicSubtitle
    },
    discrepancies: {
      title: t.discrepancyFeed,
      sub: t.liveAlertsSubtitle
    },
    centres: {
      title: t.trainingCentres,
      sub: lang === 'en' ? 'Directory of empanelled vocational training institutes' : 'पंजीकृत व्यावसायिक प्रशिक्षण संस्थानों की निर्देशिका'
    },
    evidence: {
      title: t.evidencePrivacy,
      sub: lang === 'en' ? 'Cryptographically hashed, DPDP 2023 compliant blurred audit frames' : 'क्रिप्टोग्राफ़िक हैश युक्त DPDP 2023 अनुपालक धुंधले साक्ष्य'
    }
  };

  const current = pageHeadings[activeTab] || pageHeadings.dashboard;

  return (
    <header className="top-header">
      <div className="header-title-box">
        <h2>{current.title}</h2>
        <p>{current.sub}</p>
      </div>

      <div className="header-actions">
        {/* Bandwidth Savings Badge */}
        <div className="system-status-pill">
          <Wifi size={14} className="text-green-600" />
          <span>{t.bandwidthSaved}</span>
        </div>

        {/* Live Status Pulse */}
        <div className="system-status-pill">
          <div className="pulse-dot"></div>
          <span>{t.telemetryActive}</span>
        </div>

        {/* DPDP Compliance Badge */}
        <div className="dpdp-badge">
          <Shield size={14} />
          <span>{t.dpdpBadge}</span>
        </div>

        {/* Simulate Edge Packet Button */}
        <button
          id="btn-simulate-packet"
          className="btn-primary"
          onClick={onSimulate}
          disabled={simulating}
        >
          <Sparkles size={16} />
          <span>{simulating ? 'Processing...' : t.simulateEdge}</span>
        </button>
      </div>
    </header>
  );
}
