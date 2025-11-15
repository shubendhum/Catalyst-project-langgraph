import React from 'react';
import './AuthModal.css';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onReauth: () => void;
  message?: string;
}

const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onReauth,
  message = 'Your session has expired. Please log in again to continue.'
}) => {
  if (!isOpen) return null;

  return (
    <div className="auth-modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <div className="auth-modal-header">
          <h3>🔐 Authentication Required</h3>
          <button className="auth-modal-close" onClick={onClose}>✕</button>
        </div>
        
        <div className="auth-modal-body">
          <div className="auth-modal-icon">⚠️</div>
          <p>{message}</p>
        </div>
        
        <div className="auth-modal-footer">
          <button className="button-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="button-primary" onClick={onReauth}>
            Re-authenticate
          </button>
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
