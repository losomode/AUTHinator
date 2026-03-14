/** Registered inator service from the service registry. */
export interface Service {
  id: number;
  name: string;
  description: string;
  ui_url: string;
  ui_path: string;
  icon: string;
  is_active: boolean;
  is_core: boolean;
  last_registered_at: string;
}

/** WebAuthn (passkey / security key) credential. */
export interface WebAuthnCredential {
  id: number;
  name: string;
  created_at: string;
}

/** TOTP setup response with QR code. */
export interface TotpSetupResponse {
  qr_code: string;
  secret: string;
}

/** TOTP enrollment status. */
export interface TotpStatusResponse {
  enabled: boolean;
}

/** SSO provider available for login. */
export interface SSOProvider {
  id: string;
  name: string;
  login_url: string;
}
