import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { AlertTriangle, ShieldCheck, Users, Eye } from 'lucide-react';

// Custom modern SVG pulse marker icons based on compliance status
const createCustomIcon = (status, trustScore) => {
  let color = '#15803d'; // Green (Normal)
  let glow = 'rgba(21, 128, 61, 0.35)';

  if (status === 'Critical') {
    color = '#dc2626'; // Red
    glow = 'rgba(220, 38, 38, 0.4)';
  } else if (status === 'Warning') {
    color = '#d97706'; // Amber
    glow = 'rgba(217, 119, 6, 0.4)';
  }

  const html = `
    <div style="
      position: relative;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        background: ${glow};
        animation: pulse 2s infinite;
      "></div>
      <div style="
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: ${color};
        border: 3px solid #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 10px;
        font-weight: 700;
      ">
        ${Math.round(trustScore)}
      </div>
    </div>
  `;

  return L.divIcon({
    html: html,
    className: 'custom-map-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -18]
  });
};

export default function NationalMap({
  markers = [],
  onSelectCentre,
  lang = 'en'
}) {
  // Center of India coordinates
  const defaultCenter = [22.9734, 78.6569];
  const defaultZoom = 5;

  return (
    <div className="map-container">
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {markers.map((centre) => {
          const icon = createCustomIcon(centre.compliance_status, centre.trust_score);
          return (
            <Marker
              key={centre.centre_id}
              position={[centre.latitude, centre.longitude]}
              icon={icon}
            >
              <Popup>
                <div style={{ minWidth: '210px', padding: '4px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '11px', fontWeight: '700', color: '#64748b' }}>
                      {centre.centre_id}
                    </span>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: '700',
                        padding: '2px 8px',
                        borderRadius: '9999px',
                        background:
                          centre.compliance_status === 'Critical'
                            ? '#fee2e2'
                            : centre.compliance_status === 'Warning'
                            ? '#fef3c7'
                            : '#dcfce7',
                        color:
                          centre.compliance_status === 'Critical'
                            ? '#991b1b'
                            : centre.compliance_status === 'Warning'
                            ? '#92400e'
                            : '#166534'
                      }}
                    >
                      {centre.compliance_status}
                    </span>
                  </div>

                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#0f172a', marginBottom: '4px' }}>
                    {centre.centre_name}
                  </h4>
                  <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '10px' }}>
                    {centre.city}, {centre.state}
                  </p>

                  <div style={{ display: 'flex', gap: '8px', fontSize: '11.5px', marginBottom: '12px' }}>
                    <div style={{ flex: 1, background: '#f8fafc', padding: '6px', borderRadius: '6px' }}>
                      <span style={{ color: '#64748b', display: 'block' }}>Trust Score</span>
                      <strong style={{ fontSize: '14px', color: '#0f172a' }}>{centre.trust_score}%</strong>
                    </div>
                    <div style={{ flex: 1, background: '#f8fafc', padding: '6px', borderRadius: '6px' }}>
                      <span style={{ color: '#64748b', display: 'block' }}>Capacity</span>
                      <strong style={{ fontSize: '14px', color: '#0f172a' }}>{centre.total_capacity}</strong>
                    </div>
                  </div>

                  {centre.critical_alerts_count > 0 && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        color: '#dc2626',
                        fontSize: '11.5px',
                        fontWeight: '600',
                        marginBottom: '10px'
                      }}
                    >
                      <AlertTriangle size={14} />
                      {centre.critical_alerts_count} Critical Alert(s)
                    </div>
                  )}

                  <button
                    style={{
                      width: '100%',
                      background: '#15803d',
                      color: 'white',
                      padding: '7px 12px',
                      borderRadius: '8px',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    onClick={() => onSelectCentre && onSelectCentre(centre.centre_id)}
                  >
                    View Centre Deep-Dive &rarr;
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
