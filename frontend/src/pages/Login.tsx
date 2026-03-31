/**
 * Login Page — MYC3LIUM ACCESS TERMINAL
 *
 * Teletext-styled authentication screen.
 * Shown when require_auth is enabled and user is not authenticated.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import TeletextPanel from '../components/TeletextPanel';
import TeletextText from '../components/TeletextText';
import TeletextInput from '../components/TeletextInput';
import useAuthStore from '../store/authStore';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading, error, clearError } = useAuthStore();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/p/100', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async () => {
    if (!username || !password || submitting) return;
    clearError();
    setSubmitting(true);
    try {
      await login(username, password);
      navigate('/p/100', { replace: true });
    } catch {
      // Error is set in the store
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', display: 'flex', justifyContent: 'center' }}>
        <TeletextPanel title="MYC3LIUM" borderColor="cyan" width={38}>
          <TeletextText color="cyan">VERIFYING CREDENTIALS...</TeletextText>
        </TeletextPanel>
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '2rem',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '80vh',
      }}
    >
      <TeletextPanel title="MYC3LIUM ACCESS TERMINAL" borderColor="cyan" width={38}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <TeletextText color="cyan" bold>
            AUTHENTICATION REQUIRED
          </TeletextText>

          <TeletextText color="white" size="small">
            Enter your credentials to access the mesh network dashboard.
          </TeletextText>

          <div>
            <TeletextText color="yellow" size="small">
              USERNAME
            </TeletextText>
            <TeletextInput
              value={username}
              onChange={setUsername}
              placeholder="operator"
              maxLength={32}
              onKeyDown={handleKeyDown}
            />
          </div>

          <div>
            <TeletextText color="yellow" size="small">
              PASSWORD
            </TeletextText>
            <TeletextInput
              value={password}
              onChange={setPassword}
              placeholder="********"
              maxLength={128}
              type="password"
              onKeyDown={handleKeyDown}
            />
          </div>

          {error && (
            <TeletextText color="red" size="small">
              ACCESS DENIED: {error}
            </TeletextText>
          )}

          <button
            onClick={handleSubmit}
            disabled={submitting || !username || !password}
            style={{
              background: 'transparent',
              border: '1px solid cyan',
              color: submitting ? '#666' : 'cyan',
              padding: '0.5rem 1rem',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              cursor: submitting ? 'wait' : 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            {submitting ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
          </button>

          <TeletextText color="#666" size="small">
            Contact your mesh administrator if you need access credentials.
          </TeletextText>
        </div>
      </TeletextPanel>
    </div>
  );
};

export default Login;
