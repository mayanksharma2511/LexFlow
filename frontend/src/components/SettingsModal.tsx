import type React from 'react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={headerStyle}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
              Workspace Settings
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#94a3b8' }}>
              Manage legal environment defaults, Security & Role controls
            </p>
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle}>
            ✕
          </button>
        </div>

        <div style={{ marginTop: '20px', display: 'grid', gap: '20px' }}>
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Security & Audit Policy</h3>
            <p style={cardTextStyle}>
              Strict Row-Level Owner Isolation is active. All matter uploads and AI risk synthesis operations are recorded in the audit trail.
            </p>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <span style={badgeStyle}>Owner Isolation: Active</span>
              <span style={badgeStyle}>Auditing: Enabled</span>
              <span style={badgeStyle}>AI Engine: Llama 3.1 8B</span>
            </div>
          </div>

          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>OCR Engine Settings</h3>
            <p style={cardTextStyle}>
              PyMuPDF fast text extraction with Tesseract OCR fallback on scanned documents.
            </p>
            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input type="checkbox" defaultChecked id="ocr-auto" style={{ accentColor: '#2563eb' }} />
              <label htmlFor="ocr-auto" style={{ fontSize: '13px', color: '#cbd5e1', cursor: 'pointer' }}>
                Automatically run OCR fallback on non-selectable PDF pages
              </label>
            </div>
          </div>

          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Theme & Workspace Appearance</h3>
            <p style={cardTextStyle}>
              Dark Legal Intelligence mode (Default).
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <button onClick={onClose} style={submitButtonStyle}>
            Save & Close
          </button>
        </div>
      </div>
    </div>
  );
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(15, 23, 42, 0.75)',
  backdropFilter: 'blur(4px)',
  zIndex: 9999,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '24px',
};

const modalStyle: React.CSSProperties = {
  backgroundColor: '#1e293b',
  border: '1px solid #334155',
  borderRadius: '12px',
  width: '100%',
  maxWidth: '560px',
  padding: '24px',
  boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  borderBottom: '1px solid #334155',
  paddingBottom: '16px',
};

const closeButtonStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: '#94a3b8',
  fontSize: '18px',
  cursor: 'pointer',
  padding: '4px',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: '#0f172a',
  border: '1px solid #334155',
  borderRadius: '8px',
  padding: '16px',
};

const cardTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '14px',
  fontWeight: 600,
  color: '#f8fafc',
};

const cardTextStyle: React.CSSProperties = {
  margin: '6px 0 0',
  fontSize: '13px',
  color: '#94a3b8',
  lineHeight: 1.5,
};

const badgeStyle: React.CSSProperties = {
  display: 'inline-block',
  padding: '4px 8px',
  backgroundColor: 'rgba(37, 99, 235, 0.15)',
  border: '1px solid rgba(37, 99, 235, 0.3)',
  borderRadius: '4px',
  color: '#60a5fa',
  fontSize: '11px',
  fontWeight: 600,
};

const submitButtonStyle: React.CSSProperties = {
  padding: '10px 20px',
  backgroundColor: '#2563eb',
  border: 'none',
  borderRadius: '6px',
  color: '#ffffff',
  fontSize: '14px',
  fontWeight: 600,
  cursor: 'pointer',
};
