import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { startRegistration } from '@simplewebauthn/browser';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import { getApiErrorMessage } from '@inator/shared/types';
import { totpApi, webauthnApi } from '../api';
import type { WebAuthnCredential } from '../types';

/**
 * Security Settings page.
 * Uses useAuth for user data; manages TOTP + WebAuthn credentials.
 */
export function Security(): React.JSX.Element {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // TOTP state
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [showTotpSetup, setShowTotpSetup] = useState(false);
  const [showTotpDisable, setShowTotpDisable] = useState(false);
  const [totpQrCode, setTotpQrCode] = useState('');
  const [totpToken, setTotpToken] = useState('');
  const [totpDisableToken, setTotpDisableToken] = useState('');
  const [totpLoading, setTotpLoading] = useState(false);

  // WebAuthn state
  const [webauthnCredentials, setWebauthnCredentials] = useState<WebAuthnCredential[]>([]);
  const [showWebauthnAdd, setShowWebauthnAdd] = useState(false);
  const [webauthnName, setWebauthnName] = useState('');
  const [webauthnLoading, setWebauthnLoading] = useState(false);

  const [dataLoading, setDataLoading] = useState(true);

  useEffect(() => {
    const loadSecurityData = async (): Promise<void> => {
      try {
        const [totpStatus, credentials] = await Promise.all([
          totpApi.status().catch(() => ({ enabled: false })),
          webauthnApi.listCredentials().catch(() => [] as WebAuthnCredential[]),
        ]);
        setTotpEnabled(totpStatus.enabled);
        setWebauthnCredentials(credentials);
      } catch {
        setError('Failed to load security settings');
      } finally {
        setDataLoading(false);
      }
    };
    void loadSecurityData();
  }, []);

  // ─── TOTP handlers ──────────────────────────────────────────────────

  const handleTotpSetup = async (): Promise<void> => {
    setTotpLoading(true);
    setError('');
    setMessage('');
    try {
      const data = await totpApi.setup();
      setTotpQrCode(data.qr_code);
      setShowTotpSetup(true);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to initialize TOTP setup'));
    }
    setTotpLoading(false);
  };

  const handleTotpConfirm = async (): Promise<void> => {
    if (!totpToken) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }
    setTotpLoading(true);
    setError('');
    try {
      await totpApi.confirm(totpToken);
      setTotpEnabled(true);
      setShowTotpSetup(false);
      setTotpToken('');
      setMessage('Two-factor authentication enabled successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Invalid verification code'));
    }
    setTotpLoading(false);
  };

  const handleTotpDisable = async (): Promise<void> => {
    if (!totpDisableToken) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }
    setTotpLoading(true);
    setError('');
    setMessage('');
    try {
      await totpApi.disable(totpDisableToken);
      setTotpEnabled(false);
      setShowTotpDisable(false);
      setTotpDisableToken('');
      setMessage('Two-factor authentication disabled successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to disable TOTP'));
    }
    setTotpLoading(false);
  };

  // ─── WebAuthn handlers ──────────────────────────────────────────────

  const handleWebauthnAdd = async (): Promise<void> => {
    if (!webauthnName.trim()) {
      setError('Please enter a name for this security key');
      return;
    }
    setWebauthnLoading(true);
    setError('');
    setMessage('');
    try {
      const { options } = await webauthnApi.registerBegin(webauthnName);
      const credential = await startRegistration(
        options as Parameters<typeof startRegistration>[0],
      );
      await webauthnApi.registerComplete(credential);
      const updatedList = await webauthnApi.listCredentials();
      setWebauthnCredentials(updatedList);
      setShowWebauthnAdd(false);
      setWebauthnName('');
      setMessage('Security key added successfully');
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Failed to add security key'));
    }
    setWebauthnLoading(false);
  };

  const handleWebauthnDelete = async (credentialId: number): Promise<void> => {
    if (!confirm('Are you sure you want to remove this security key?')) return;
    try {
      await webauthnApi.deleteCredential(credentialId);
      setWebauthnCredentials((prev) => prev.filter((c) => c.id !== credentialId));
      setMessage('Security key removed successfully');
    } catch {
      setError('Failed to remove security key');
    }
  };

  // ─── Render ─────────────────────────────────────────────────────────

  if (authLoading || dataLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-bold text-gray-900">🔐 Security Settings</h1>
          <button
            onClick={() => navigate('/')}
            className="rounded-lg bg-gray-100 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-200"
          >
            ← Back
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
        {message && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4">
            <p className="text-sm text-green-800">{message}</p>
          </div>
        )}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* Profile Info */}
        <section className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-xl font-semibold text-gray-900">Account Information</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-500">Username</span>
              <p className="mt-1 text-gray-900">{user?.username}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Email</span>
              <p className="mt-1 text-gray-900">{user?.email}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Role</span>
              <p className="mt-1 text-gray-900">{user?.role}</p>
            </div>
            <div>
              <span className="font-medium text-gray-500">Organization</span>
              <p className="mt-1 text-gray-900">{user?.customer?.name ?? 'N/A'}</p>
            </div>
          </div>
        </section>

        {/* TOTP Section */}
        <TotpSection
          enabled={totpEnabled}
          loading={totpLoading}
          showSetup={showTotpSetup}
          showDisable={showTotpDisable}
          qrCode={totpQrCode}
          token={totpToken}
          disableToken={totpDisableToken}
          onSetup={() => void handleTotpSetup()}
          onConfirm={() => void handleTotpConfirm()}
          onDisable={() => void handleTotpDisable()}
          onTokenChange={setTotpToken}
          onDisableTokenChange={setTotpDisableToken}
          onShowDisable={() => setShowTotpDisable(true)}
          onCancelSetup={() => {
            setShowTotpSetup(false);
            setTotpToken('');
          }}
          onCancelDisable={() => {
            setShowTotpDisable(false);
            setTotpDisableToken('');
          }}
        />

        {/* WebAuthn Section */}
        <WebAuthnSection
          credentials={webauthnCredentials}
          loading={webauthnLoading}
          showAdd={showWebauthnAdd}
          name={webauthnName}
          onNameChange={setWebauthnName}
          onAdd={() => void handleWebauthnAdd()}
          onDelete={(id) => void handleWebauthnDelete(id)}
          onShowAdd={() => setShowWebauthnAdd(true)}
          onCancelAdd={() => {
            setShowWebauthnAdd(false);
            setWebauthnName('');
          }}
        />
      </main>
    </div>
  );
}

// ─── Sub-components ─────────────────────────────────────────────────────

interface TotpSectionProps {
  enabled: boolean;
  loading: boolean;
  showSetup: boolean;
  showDisable: boolean;
  qrCode: string;
  token: string;
  disableToken: string;
  onSetup: () => void;
  onConfirm: () => void;
  onDisable: () => void;
  onTokenChange: (v: string) => void;
  onDisableTokenChange: (v: string) => void;
  onShowDisable: () => void;
  onCancelSetup: () => void;
  onCancelDisable: () => void;
}

function TotpSection(props: TotpSectionProps): React.JSX.Element {
  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Two-Factor Authentication</h2>
          <p className="mt-1 text-sm text-gray-500">
            Add an extra layer of security with an authenticator app
          </p>
        </div>
        {!props.enabled && !props.showSetup && (
          <button
            onClick={props.onSetup}
            disabled={props.loading}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
          >
            {props.loading ? 'Loading...' : 'Enable 2FA'}
          </button>
        )}
        {props.enabled && !props.showDisable && (
          <div className="flex items-center space-x-3">
            <span className="rounded-lg bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
              ✓ Enabled
            </span>
            <button
              onClick={props.onShowDisable}
              className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-200"
            >
              Disable 2FA
            </button>
          </div>
        )}
      </div>

      {props.showSetup && (
        <div className="mt-4 rounded-lg bg-gray-50 p-5">
          <h3 className="mb-2 font-semibold text-gray-900">Scan QR Code</h3>
          <p className="mb-4 text-sm text-gray-600">
            Scan this QR code with your authenticator app, then enter the 6-digit code to verify.
          </p>
          {props.qrCode && (
            <div className="mb-4 flex justify-center rounded bg-white py-4">
              <img src={props.qrCode} alt="TOTP QR Code" className="max-w-[200px]" />
            </div>
          )}
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Verification Code
            </label>
            <input
              type="text"
              value={props.token}
              onChange={(e) => props.onTokenChange(e.target.value)}
              placeholder="Enter 6-digit code"
              maxLength={6}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={props.onCancelSetup}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={props.onConfirm}
              disabled={props.loading}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
            >
              {props.loading ? 'Verifying...' : 'Verify & Enable'}
            </button>
          </div>
        </div>
      )}

      {props.showDisable && (
        <div className="mt-4 rounded-lg bg-gray-50 p-5">
          <h3 className="mb-2 font-semibold text-gray-900">
            Disable Two-Factor Authentication
          </h3>
          <p className="mb-4 text-sm text-gray-600">
            Enter a 6-digit code from your authenticator app to confirm disabling 2FA.
          </p>
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Verification Code
            </label>
            <input
              type="text"
              value={props.disableToken}
              onChange={(e) => props.onDisableTokenChange(e.target.value)}
              placeholder="Enter 6-digit code"
              maxLength={6}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={props.onCancelDisable}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={props.onDisable}
              disabled={props.loading}
              className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
            >
              {props.loading ? 'Disabling...' : 'Disable 2FA'}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

interface WebAuthnSectionProps {
  credentials: WebAuthnCredential[];
  loading: boolean;
  showAdd: boolean;
  name: string;
  onNameChange: (v: string) => void;
  onAdd: () => void;
  onDelete: (id: number) => void;
  onShowAdd: () => void;
  onCancelAdd: () => void;
}

function WebAuthnSection(props: WebAuthnSectionProps): React.JSX.Element {
  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Security Keys (WebAuthn)</h2>
          <p className="mt-1 text-sm text-gray-500">
            Use hardware security keys or biometric authentication
          </p>
        </div>
        <button
          onClick={props.onShowAdd}
          disabled={props.showAdd}
          className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
        >
          Add Security Key
        </button>
      </div>

      {props.credentials.length > 0 && (
        <div className="mt-4 space-y-3">
          {props.credentials.map((cred) => (
            <div
              key={cred.id}
              className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4"
            >
              <div>
                <p className="font-medium text-gray-900">🔑 {cred.name}</p>
                <p className="text-xs text-gray-500">
                  Added: {new Date(cred.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => props.onDelete(cred.id)}
                className="rounded-lg bg-red-600 px-3 py-1.5 text-sm text-white transition-colors hover:bg-red-700"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {props.showAdd && (
        <div className="mt-4 rounded-lg bg-gray-50 p-5">
          <h3 className="mb-2 font-semibold text-gray-900">Add Security Key</h3>
          <p className="mb-4 text-sm text-gray-600">
            Give your security key a name, then follow your browser&apos;s prompts.
          </p>
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Security Key Name
            </label>
            <input
              type="text"
              value={props.name}
              onChange={(e) => props.onNameChange(e.target.value)}
              placeholder="e.g., YubiKey, Touch ID"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end space-x-3">
            <button
              onClick={props.onCancelAdd}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={props.onAdd}
              disabled={props.loading}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
            >
              {props.loading ? 'Adding...' : 'Add Key'}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
