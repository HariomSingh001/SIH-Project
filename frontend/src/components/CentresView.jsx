import React, { useState, useEffect } from 'react';
import {
  Building2,
  MapPin,
  Users,
  Camera,
  Shield,
  Search,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Package
} from 'lucide-react';
import { translations } from '../utils/translations';

export default function CentresView({
  centres = [],
  selectedCentreId = null,
  lang = 'en'
}) {
  const t = translations[lang];
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState('ALL');
  const [activeCentre, setActiveCentre] = useState(null);
  const [centreDetail, setCentreDetail] = useState(null);
  const [centreInventory, setCentreInventory] = useState([]);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Filter centres
  const states = ['ALL', ...new Set(centres.map((c) => c.state))];

  const filteredCentres = centres.filter((c) => {
    const matchesSearch =
      c.centre_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.centre_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.city.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesState = selectedState === 'ALL' || c.state === selectedState;
    return matchesSearch && matchesState;
  });

  // Load centre detail when selected
  const handleOpenCentre = async (centreId) => {
    setLoadingDetail(true);
    setActiveCentre(centreId);
    try {
      const res = await fetch(`/api/centres/${centreId}`);
      if (res.ok) {
        const data = await res.json();
        setCentreDetail(data);
      }

      // Load inventory for centre
      const invRes = await fetch(`/api/inventory?centre_id=${centreId}`);
      if (invRes.ok) {
        const invData = await invRes.json();
        setCentreInventory(invData);
      }
    } catch (err) {
      console.error('Failed to load centre detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  useEffect(() => {
    if (selectedCentreId) {
      handleOpenCentre(selectedCentreId);
    }
  }, [selectedCentreId]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Search and Filters */}
      <div className="card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: '240px' }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Search by centre name, ID or city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              border: 'none',
              fontSize: '13.5px',
              color: '#1e293b',
              background: 'transparent'
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: '600', color: '#64748b' }}>State:</span>
          <select
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid #cbd5e1',
              fontSize: '12.5px',
              color: '#334155',
              background: '#ffffff'
            }}
          >
            {states.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Centre Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
        {filteredCentres.map((centre) => {
          const isCritical = centre.compliance_status === 'Critical';
          const isWarning = centre.compliance_status === 'Warning';
          return (
            <div
              key={centre.centre_id}
              className="card"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                padding: '22px'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: '#64748b' }}>
                    {centre.centre_id}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: '700',
                      padding: '2px 8px',
                      borderRadius: '9999px',
                      background: isCritical ? '#fee2e2' : isWarning ? '#fef3c7' : '#dcfce7',
                      color: isCritical ? '#991b1b' : isWarning ? '#92400e' : '#166534'
                    }}
                  >
                    {centre.compliance_status}
                  </span>
                </div>

                <h3 style={{ fontSize: '15.5px', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>
                  {centre.centre_name}
                </h3>

                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#64748b', fontSize: '12px', marginBottom: '14px' }}>
                  <MapPin size={13} />
                  <span>{centre.city}, {centre.state}</span>
                </div>

                {/* Key Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
                  <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Trust Score</span>
                    <strong style={{ fontSize: '14px', color: isCritical ? '#dc2626' : isWarning ? '#d97706' : '#15803d' }}>
                      {centre.trust_score}%
                    </strong>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Batches</span>
                    <strong style={{ fontSize: '14px', color: '#0f172a' }}>{centre.active_batches}</strong>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '8px', borderRadius: '8px', textAlign: 'center' }}>
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'block' }}>Capacity</span>
                    <strong style={{ fontSize: '14px', color: '#0f172a' }}>{centre.total_capacity}</strong>
                  </div>
                </div>
              </div>

              <button
                className="btn-primary"
                style={{ width: '100%', fontSize: '12.5px', padding: '8px 14px' }}
                onClick={() => handleOpenCentre(centre.centre_id)}
              >
                Inspect Centre Details &rarr;
              </button>
            </div>
          );
        })}
      </div>

      {/* Centre Deep Dive Modal */}
      {activeCentre && centreDetail && (
        <div className="modal-overlay" onClick={() => setActiveCentre(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ padding: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#64748b' }}>
                  {centreDetail.centre_id} &bull; {centreDetail.sector}
                </span>
                <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#0f172a', marginTop: '2px' }}>
                  {centreDetail.centre_name}
                </h3>
                <p style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                  {centreDetail.address}
                </p>
              </div>
              <button
                style={{ fontSize: '20px', color: '#94a3b8', padding: '4px 8px' }}
                onClick={() => setActiveCentre(null)}
              >
                &times;
              </button>
            </div>

            {/* Centre Overview Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
              <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '10px' }}>
                <span style={{ fontSize: '11.5px', color: '#64748b' }}>Trust Score</span>
                <p style={{ fontSize: '18px', fontWeight: '700', color: '#15803d' }}>{centreDetail.trust_score}%</p>
              </div>
              <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '10px' }}>
                <span style={{ fontSize: '11.5px', color: '#64748b' }}>Compliance</span>
                <p style={{ fontSize: '15px', fontWeight: '700', color: '#0f172a' }}>{centreDetail.compliance_status}</p>
              </div>
              <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '10px' }}>
                <span style={{ fontSize: '11.5px', color: '#64748b' }}>Contact</span>
                <p style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a' }}>{centreDetail.contact_person || 'N/A'}</p>
              </div>
              <div style={{ background: '#f8fafc', padding: '10px', borderRadius: '10px' }}>
                <span style={{ fontSize: '11.5px', color: '#64748b' }}>Connectivity</span>
                <p style={{ fontSize: '12px', fontWeight: '600', color: '#0f172a' }}>{centreDetail.connectivity || '4G LTE'}</p>
              </div>
            </div>

            {/* Active Batches */}
            <div style={{ marginBottom: '24px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '10px' }}>
                Active Training Batches ({centreDetail.batches?.length || 0})
              </h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                      <th style={{ padding: '6px' }}>Batch ID</th>
                      <th style={{ padding: '6px' }}>Course</th>
                      <th style={{ padding: '6px' }}>Size</th>
                      <th style={{ padding: '6px' }}>Shift</th>
                    </tr>
                  </thead>
                  <tbody>
                    {centreDetail.batches?.map((b) => (
                      <tr key={b.batch_id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '8px 6px', fontWeight: '600' }}>{b.batch_id}</td>
                        <td style={{ padding: '8px 6px' }}>{b.course_name}</td>
                        <td style={{ padding: '8px 6px' }}>{b.batch_size} students</td>
                        <td style={{ padding: '8px 6px', color: '#64748b' }}>{b.shift}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sanctioned Equipment Manifest */}
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '10px' }}>
                Sanctioned Equipment Inventory Compliance ({centreInventory.length} items)
              </h4>
              <div style={{ overflowX: 'auto', maxHeight: '200px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #e2e8f0', color: '#64748b', textAlign: 'left' }}>
                      <th style={{ padding: '6px' }}>Item</th>
                      <th style={{ padding: '6px' }}>Category</th>
                      <th style={{ padding: '6px' }}>Sanctioned</th>
                      <th style={{ padding: '6px' }}>Min Req.</th>
                      <th style={{ padding: '6px' }}>AI Verified</th>
                      <th style={{ padding: '6px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {centreInventory.map((eq) => {
                      const isShort = eq.last_verified_count !== null && eq.last_verified_count < eq.minimum_required;
                      return (
                        <tr key={eq.item_id} style={{ borderBottom: '1px solid #f8fafc' }}>
                          <td style={{ padding: '7px 6px', fontWeight: '600' }}>{eq.item_name}</td>
                          <td style={{ padding: '7px 6px', color: '#64748b' }}>{eq.category}</td>
                          <td style={{ padding: '7px 6px' }}>{eq.sanctioned_count}</td>
                          <td style={{ padding: '7px 6px' }}>{eq.minimum_required}</td>
                          <td style={{ padding: '7px 6px', fontWeight: '700', color: isShort ? '#dc2626' : '#15803d' }}>
                            {eq.last_verified_count !== null ? eq.last_verified_count : 'Pending'}
                          </td>
                          <td style={{ padding: '7px 6px' }}>
                            <span
                              style={{
                                fontSize: '10.5px',
                                fontWeight: '700',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                background: isShort ? '#fee2e2' : '#dcfce7',
                                color: isShort ? '#991b1b' : '#166534'
                              }}
                            >
                              {isShort ? 'Deficit' : 'Compliant'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
