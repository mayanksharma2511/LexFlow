import React, { useState } from 'react';
import apiClient from '../api/client';

interface NewCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const generateDefaultCaseNumber = () => `CV-2026-${Math.floor(1000 + Math.random() * 9000)}`;

export const NewCaseModal: React.FC<NewCaseModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [title, setTitle] = useState('');
  const [caseNumber, setCaseNumber] = useState(generateDefaultCaseNumber);
  const [clientName, setClientName] = useState('');
  const [opposingParty, setOpposingParty] = useState('');
  const [court, setCourt] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await apiClient.post('/cases', {
        title,
        case_number: caseNumber,
        client_name: clientName,
        opposing_party: opposingParty,
        court,
        priority: priority.toUpperCase(),
        description,
      });

      onSuccess();
      onClose();
      // Reset form
      setTitle('');
      setCaseNumber(generateDefaultCaseNumber());
      setClientName('');
      setOpposingParty('');
      setCourt('');
      setDescription('');
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string | Array<{ msg?: string }> } }; message?: string };
      const detail = axiosError.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg || 'Validation error').join(', '));
      } else {
        setError(axiosError.message || 'Error creating case');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div style={headerStyle}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#f8fafc' }}>
              Create New Matter
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#94a3b8' }}>
              Initialize a new legal case in LexFlow
            </p>
          </div>
          <button type="button" onClick={onClose} style={closeButtonStyle}>
            ✕
          </button>
        </div>

        {error && <div style={errorStyle}>{error}</div>}

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '16px', marginTop: '16px' }}>
          <div style={gridTwoStyle}>
            <div>
              <label style={labelStyle}>Case Title *</label>
              <input
                required
                type="text"
                placeholder="e.g. Acme Corp v. Stellar Tech"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Case Number *</label>
              <input
                required
                type="text"
                placeholder="e.g. CV-2026-8841"
                value={caseNumber}
                onChange={(e) => setCaseNumber(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={gridTwoStyle}>
            <div>
              <label style={labelStyle}>Client Name *</label>
              <input
                required
                type="text"
                placeholder="e.g. Acme Holdings Inc."
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Opposing Party *</label>
              <input
                required
                type="text"
                placeholder="e.g. Stellar Technologies Ltd"
                value={opposingParty}
                onChange={(e) => setOpposingParty(e.target.value)}
                style={inputStyle}
              />
            </div>
          </div>

          <div style={gridTwoStyle}>
            <div>
              <label style={labelStyle}>Court / Jurisdiction *</label>
              <input
                required
                type="text"
                placeholder="e.g. High Court of Delhi"
                value={court}
                onChange={(e) => setCourt(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                style={inputStyle}
              >
                <option value="LOW">Low Priority</option>
                <option value="MEDIUM">Medium Priority</option>
                <option value="HIGH">High Priority</option>
              </select>
            </div>
          </div>

          <div>
            <label style={labelStyle}>Matter Overview & Description *</label>
            <textarea
              required
              rows={3}
              placeholder="Brief summary of claims, contractual disputes, or key allegations..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              style={{ ...inputStyle, resize: 'vertical' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '8px' }}>
            <button type="button" onClick={onClose} style={cancelButtonStyle}>
              Cancel
            </button>
            <button type="submit" disabled={loading} style={submitButtonStyle}>
              {loading ? 'Creating...' : 'Create Case'}
            </button>
          </div>
        </form>
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
  maxWidth: '640px',
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

const gridTwoStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '16px',
};

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '12px',
  fontWeight: 600,
  color: '#94a3b8',
  marginBottom: '6px',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  backgroundColor: '#0f172a',
  border: '1px solid #334155',
  borderRadius: '6px',
  color: '#f8fafc',
  fontSize: '14px',
  boxSizing: 'border-box',
};

const errorStyle: React.CSSProperties = {
  marginTop: '12px',
  padding: '10px',
  backgroundColor: 'rgba(239, 68, 68, 0.1)',
  border: '1px solid rgba(239, 68, 68, 0.3)',
  borderRadius: '6px',
  color: '#ef4444',
  fontSize: '13px',
};

const cancelButtonStyle: React.CSSProperties = {
  padding: '10px 16px',
  backgroundColor: 'transparent',
  border: '1px solid #334155',
  borderRadius: '6px',
  color: '#94a3b8',
  fontSize: '14px',
  fontWeight: 500,
  cursor: 'pointer',
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
