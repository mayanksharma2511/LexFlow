import type React from 'react';
import { formatRole, useCurrentUser } from '../api/currentUser';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const user = useCurrentUser();
  if (!isOpen) return null;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={headerStyle}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
              Account & About
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#94a3b8' }}>
              Your account and how LexFlow handles your documents
            </p>
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle}>
            ✕
          </button>
        </div>

        <div style={{ marginTop: '20px', display: 'grid', gap: '20px' }}>
          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>Your account</h3>
            <p style={cardTextStyle}>
              {user ? `${user.full_name} · ${user.email} · ${formatRole(user.role)}` : 'Loading...'}
            </p>
          </div>

          <div style={cardStyle}>
            <h3 style={cardTitleStyle}>How LexFlow works</h3>
            <p style={cardTextStyle}>
              Each account can see only its own cases and documents, and every upload and AI analysis is
              recorded in the activity log. Text is extracted with PyMuPDF, with Tesseract OCR for scanned
              pages. AI analysis uses Llama 3.1 8B through the Groq API; when it is unavailable, LexFlow
              says so and labels any rule-based result as such.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px' }}>
          <button onClick={onClose} style={submitButtonStyle}>
            Close
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
