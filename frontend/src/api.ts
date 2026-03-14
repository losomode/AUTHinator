import apiClient from '@inator/shared/api/client';
import type { LoginResult, LoginResponse } from '@inator/shared/types';
import type {
  Service,
  TotpStatusResponse,
  TotpSetupResponse,
  WebAuthnCredential,
  SSOProvider,
} from './types';

/** Core authentication endpoints. */
export const authApi = {
  login: async (username: string, password: string): Promise<LoginResult> => {
    const response = await apiClient.post<LoginResult>('/auth/login/', { username, password });
    return response.data;
  },

  /** Fetch SSO providers. Uses fetch() to avoid interceptor side-effects on public endpoint. */
  ssoProviders: async (): Promise<SSOProvider[]> => {
    const response = await fetch('/api/auth/sso-providers/');
    const data = (await response.json()) as { providers?: SSOProvider[] };
    return data.providers ?? [];
  },
};

/** Service registry. */
export const servicesApi = {
  list: async (): Promise<Service[]> => {
    const response = await apiClient.get<Service[]>('/services/');
    return response.data;
  },
};

/** TOTP two-factor authentication management. */
export const totpApi = {
  status: async (): Promise<TotpStatusResponse> => {
    const response = await apiClient.get<TotpStatusResponse>('/auth/totp/status/');
    return response.data;
  },
  setup: async (): Promise<TotpSetupResponse> => {
    const response = await apiClient.post<TotpSetupResponse>('/auth/totp/setup/');
    return response.data;
  },
  confirm: async (token: string): Promise<void> => {
    await apiClient.post('/auth/totp/confirm/', { token });
  },
  disable: async (token: string): Promise<void> => {
    await apiClient.post('/auth/totp/disable/', { token });
  },
};

/** MFA verification during login. */
export const mfaApi = {
  totpVerify: async (mfaToken: string, code: string): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/mfa/totp-verify/', {
      mfa_token: mfaToken,
      code,
    });
    return response.data;
  },
  webauthnBegin: async (mfaToken: string): Promise<{ options: unknown }> => {
    const response = await apiClient.post<{ options: unknown }>('/auth/mfa/webauthn-begin/', {
      mfa_token: mfaToken,
    });
    return response.data;
  },
  webauthnComplete: async (mfaToken: string, assertion: unknown): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/mfa/webauthn-complete/', {
      mfa_token: mfaToken,
      ...(assertion as Record<string, unknown>),
    });
    return response.data;
  },
};

/** WebAuthn credential management (profile page). */
export const webauthnApi = {
  listCredentials: async (): Promise<WebAuthnCredential[]> => {
    const response = await apiClient.get<WebAuthnCredential[]>('/auth/webauthn/credentials/');
    return response.data;
  },
  registerBegin: async (name: string): Promise<{ options: unknown }> => {
    const response = await apiClient.post<{ options: unknown }>('/auth/webauthn/register/begin/', {
      name,
    });
    return response.data;
  },
  registerComplete: async (credential: unknown): Promise<void> => {
    await apiClient.post('/auth/webauthn/register/complete/', credential);
  },
  deleteCredential: async (id: number): Promise<void> => {
    await apiClient.delete(`/auth/webauthn/credentials/${id}/`);
  },
};
