import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { startAuthentication } from '@simplewebauthn/browser';
import { setToken } from '@inator/shared/api/client';
import { useAuth } from '@inator/shared/auth/AuthProvider';
import { isMfaRequired, getApiErrorMessage } from '@inator/shared/types';
import { authApi, mfaApi } from '../api';
import type { SSOProvider } from '../types';

/**
 * Login page with username/password, MFA (TOTP + WebAuthn), and SSO support.
 * On success stores tokens and refreshes auth context — no cross-origin redirects.
 */
export function Login(): React.JSX.Element {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [ssoProviders, setSsoProviders] = useState<SSOProvider[]>([]);
  const navigate = useNavigate();
  const { fetchUser } = useAuth();

  // MFA state
  const [mfaStep, setMfaStep] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [mfaMethods, setMfaMethods] = useState<string[]>([]);
  const [totpCode, setTotpCode] = useState('');

  useEffect(() => {
    authApi
      .ssoProviders()
      .then(setSsoProviders)
      .catch(() => {});
  }, []);

  const completeLogin = async (access: string, refresh: string): Promise<void> => {
    setToken(access);
    localStorage.setItem('refresh_token', refresh);
    await fetchUser();
    navigate('/');
  };

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await authApi.login(username, password);

      if (isMfaRequired(result)) {
        setMfaToken(result.mfa_token);
        setMfaMethods(result.mfa_methods);
        setMfaStep(true);
      } else {
        await completeLogin(result.access, result.refresh);
      }
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Login failed. Please check your credentials.'));
    } finally {
      setLoading(false);
    }
  };

  const handleTotpVerify = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!totpCode) {
      setError('Please enter the 6-digit code from your authenticator app');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await mfaApi.totpVerify(mfaToken, totpCode);
      await completeLogin(result.access, result.refresh);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Invalid verification code'));
    } finally {
      setLoading(false);
    }
  };

  const handleWebauthnVerify = async (): Promise<void> => {
    setError('');
    setLoading(true);
    try {
      const { options } = await mfaApi.webauthnBegin(mfaToken);
      const assertion = await startAuthentication(
        options as Parameters<typeof startAuthentication>[0],
      );
      const result = await mfaApi.webauthnComplete(mfaToken, assertion);
      await completeLogin(result.access, result.refresh);
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Security key verification failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-4xl font-bold text-gray-900">🔐 AUTHinator</h1>
          <p className="text-gray-600">
            {mfaStep ? 'Two-factor authentication required' : 'Sign in to access your services'}
          </p>
        </div>

        {/* Card */}
        <div className="rounded-lg bg-white p-8 shadow-xl">
          {!mfaStep ? (
            <>
              <form onSubmit={(e) => void handleSubmit(e)}>
                <div className="mb-6">
                  <label
                    htmlFor="username"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Username
                  </label>
                  <input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                    required
                    autoFocus
                  />
                </div>

                <div className="mb-6">
                  <label
                    htmlFor="password"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                {error && (
                  <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full rounded-lg bg-blue-600 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </button>
              </form>

              {/* SSO Providers */}
              {ssoProviders.length > 0 && (
                <>
                  <div className="my-6 flex items-center">
                    <div className="flex-1 border-t border-gray-300"></div>
                    <span className="px-4 text-sm text-gray-500">Or continue with</span>
                    <div className="flex-1 border-t border-gray-300"></div>
                  </div>

                  <div className="space-y-3">
                    {ssoProviders.map((provider) => (
                      <a
                        key={provider.id}
                        href={provider.login_url}
                        className="flex w-full items-center justify-center gap-3 rounded-lg border border-gray-300 bg-white px-4 py-3 font-medium text-gray-700 transition-colors hover:bg-gray-50"
                      >
                        <SSOIcon providerId={provider.id} />
                        <span>Continue with {provider.name}</span>
                      </a>
                    ))}
                  </div>
                </>
              )}
            </>
          ) : (
            /* MFA Step */
            <div>
              <p className="mb-6 text-sm text-gray-600">
                Verify your identity to complete sign-in.
              </p>

              {error && (
                <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              )}

              {mfaMethods.includes('totp') && (
                <form onSubmit={(e) => void handleTotpVerify(e)} className="mb-6">
                  <label
                    htmlFor="totp-code"
                    className="mb-2 block text-sm font-medium text-gray-700"
                  >
                    Authenticator Code
                  </label>
                  <input
                    id="totp-code"
                    type="text"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value)}
                    placeholder="Enter 6-digit code"
                    maxLength={6}
                    className="mb-4 w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-transparent focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full rounded-lg bg-blue-600 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading ? 'Verifying...' : 'Verify Code'}
                  </button>
                </form>
              )}

              {mfaMethods.includes('totp') && mfaMethods.includes('webauthn') && (
                <div className="my-4 flex items-center">
                  <div className="flex-1 border-t border-gray-300"></div>
                  <span className="px-4 text-sm text-gray-500">or</span>
                  <div className="flex-1 border-t border-gray-300"></div>
                </div>
              )}

              {mfaMethods.includes('webauthn') && (
                <button
                  onClick={() => void handleWebauthnVerify()}
                  disabled={loading}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-gray-800 py-3 font-medium text-white transition-colors hover:bg-gray-900 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  🔑 {loading ? 'Waiting for key...' : 'Use Security Key'}
                </button>
              )}

              <button
                onClick={() => {
                  setMfaStep(false);
                  setError('');
                  setTotpCode('');
                }}
                className="mt-4 w-full text-sm text-gray-500 transition-colors hover:text-gray-700"
              >
                ← Back to login
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>Centralized authentication for all your services</p>
        </div>
      </div>
    </div>
  );
}

/** Render provider-specific icon or null. */
function SSOIcon({ providerId }: { providerId: string }): React.JSX.Element | null {
  if (providerId === 'google') {
    return (
      <svg width="20" height="20" viewBox="0 0 48 48">
        <path
          fill="#EA4335"
          d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
        />
        <path
          fill="#4285F4"
          d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
        />
        <path
          fill="#FBBC05"
          d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
        />
        <path
          fill="#34A853"
          d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
        />
      </svg>
    );
  }
  if (providerId === 'microsoft') {
    return (
      <svg width="20" height="20" viewBox="0 0 23 23">
        <path fill="#f25022" d="M0 0h11v11H0z" />
        <path fill="#00a4ef" d="M12 0h11v11H12z" />
        <path fill="#7fba00" d="M0 12h11v11H0z" />
        <path fill="#ffb900" d="M12 12h11v11H12z" />
      </svg>
    );
  }
  return null;
}
