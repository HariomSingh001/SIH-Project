import React from 'react';
import {
  LayoutDashboard,
  MapPin,
  AlertTriangle,
  Building2,
  ShieldCheck,
  Eye,
  Radio,
  Cpu
} from 'lucide-react';
import { translations } from '../utils/translations';

export default function Sidebar({
  activeTab,
  setActiveTab,
  lang,
  setLang,
  openAlertsCount = 0
}) {
  const t = translations[lang];

  const navItems = [
    { id: 'dashboard', label: t.dashboard, icon: LayoutDashboard },
    { id: 'map', label: t.nationalMap, icon: MapPin },
    {
      id: 'discrepancies',
      label: t.discrepancyFeed,
      icon: AlertTriangle,
      badge: openAlertsCount > 0 ? openAlertsCount : null
    },
    { id: 'centres', label: t.trainingCentres, icon: Building2 },
    { id: 'evidence', label: t.evidencePrivacy, icon: ShieldCheck },
    { id: 'pipeline', label: t.pipelineSync, icon: Cpu }
  ];

  return (
    <aside className="sidebar">
      <div>
        {/* Brand / Logo */}
        <div className="brand-section">
          <div className="brand-logo-badge">
            <Eye size={24} strokeWidth={2.4} />
          </div>
          <div className="brand-info">
            <h1>
              Pramaan AI <span>(प्रमाण)</span>
            </h1>
            <p>{t.brandTagline}</p>
          </div>
        </div>

        {/* Navigation items - Modern pills */}
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                <div className="nav-icon">
                  <Icon size={19} strokeWidth={isActive ? 2.3 : 1.9} />
                </div>
                <span>{item.label}</span>
                {item.badge && (
                  <span className={`nav-badge ${isActive ? 'active-alert' : 'alert'}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer & Language Selector */}
      <div className="sidebar-footer">
        <div className="language-selector">
          <span className="lang-label">{t.language}</span>
          <div className="lang-toggle-group">
            <button
              id="lang-en"
              className={`lang-btn ${lang === 'en' ? 'active' : ''}`}
              onClick={() => setLang('en')}
            >
              <Radio size={12} strokeWidth={2.5} /> English
            </button>
            <button
              id="lang-hi"
              className={`lang-btn ${lang === 'hi' ? 'active' : ''}`}
              onClick={() => setLang('hi')}
            >
              <Radio size={12} strokeWidth={2.5} /> हिंदी
            </button>
          </div>
        </div>

        <div className="org-credit">
          <strong>{t.teamCredit}</strong>
          <span>{t.subCredit}</span>
        </div>
      </div>
    </aside>
  );
}
