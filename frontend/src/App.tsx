import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ConfirmationResult, RecaptchaVerifier } from 'firebase/auth';
import { NewShipmentModal } from './components/NewShipmentModal';
import { PayPalCheckout } from './components/PayPalCheckout';
import { SvgDonutChart, SvgAreaChart, SvgRiskGauge, SvgBarComparison } from './components/SvgCharts';
import Contact5Section from './components/Contact5';
import { FreightWorkspaceShell, type WorkspacePage } from './components/workspace/FreightWorkspaceShell';
import { FreightOverview } from './components/workspace/FreightOverview';
import { ThemeToggleButton } from './components/workspace/ThemeToggleButton';
import { FamilyReceiveComponent } from './components/ui/FamilyReceiveComponent';
import { AiCopilotChat } from './components/ai/AiCopilotChat';
import {
  addTrackingEvent, apiBaseUrl, assessQuote, cancelShipment, compareQuotesWithCopilot,
  createShipment, fetchAnalyticsOverview, fetchCarrierCatalog, fetchCarrierPerformance,
  fetchCurrentUser, fetchHealth, fetchNotifications, fetchShipmentPayments,
  fetchShipmentQuotes, fetchShipmentEstimate, fetchShipments, fetchTracking,
  getAuthToken, login, registerBuyer, registerSeller, paypalClientId, refreshCarrierQuotes,
  resetDemoData, setAuthToken, oauthSignIn, requestPhoneLoginOtp, verifyPhoneLoginOtp, updateAccountPhone,
  linkFirebasePhone, verifyFirebasePhone, deleteAccount, requestPasswordReset, resetPassword,
  clearAuthTokens, setRefreshToken,
} from './api';
import {
  AnalyticsOverview, CarrierCatalog, CarrierPerformance, CopilotResult, NotificationItem,
  PaymentRecord, Quote, RateEstimate, Shipment, ShipmentCreatePayload, TrackingEvent, UserProfile,
} from './types';

type Page = 'landing' | 'overview' | 'shipments' | 'quotes' | 'payments' | 'copilot' | 'risk' | 'analytics' | 'carriers' | 'documents' | 'settings';
type IconName = 'overview' | 'shipments' | 'quotes' | 'risk' | 'copilot' | 'payments' | 'analytics' | 'settings' | 'bell' | 'plus' | 'search' | 'arrow' | 'refresh' | 'clock' | 'check' | 'warning' | 'external' | 'menu' | 'logout' | 'shield' | 'truck' | 'wallet' | 'spark' | 'calendar' | 'filter' | 'close' | 'route' | 'file' | 'database' | 'activity' | 'chevron';

function Icon({ name, size = 18 }: { name: IconName; size?: number }): React.ReactElement {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true as const };
  const paths: Record<IconName, React.ReactNode> = {
    overview: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="4" rx="1.5"/><rect x="14" y="10" width="7" height="11" rx="1.5"/><rect x="3" y="13" width="7" height="8" rx="1.5"/></>,
    shipments: <><path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9M7.5 5.25l9 4.5"/></>,
    quotes: <><path d="M4 5h16M4 12h16M4 19h16"/><path d="M8 3v4M16 10v4M11 17v4"/></>,
    risk: <><path d="M12 3 20 6v5c0 5-3.4 8.2-8 10-4.6-1.8-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/></>,
    copilot: <><path d="M12 3v3M5.6 6.6l2.1 2.1M3 13h3M18 13h3M16.3 8.7l2.1-2.1"/><rect x="5" y="10" width="14" height="10" rx="3"/><path d="M9 14h.01M15 14h.01M9 17h6"/></>,
    payments: <><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M7 15h4"/></>,
    analytics: <><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a7.5 7.5 0 0 1-1.6.9l-.3 1.8h-2.8l-.3-1.8a7.5 7.5 0 0 1-1.6-.9l-1.7.6-1.4-2.4 1.4-1.1a7 7 0 0 1 0-1.9l-1.4-1.1 1.4-2.4 1.7.6a7.5 7.5 0 0 1 1.6-.9l.3-1.8h2.8l.3 1.8a7.5 7.5 0 0 1 1.6.9l1.7-.6 1.4 2.4-1.4 1.1a7 7 0 0 1 0 1.8z" transform="translate(-1 -1) scale(1.08)"/></>,
    bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>,
    arrow: <><path d="M5 12h14M13 6l6 6-6 6"/></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.5 9a7 7 0 0 1 11.8-2L20 12M4 12l2.7 5a7 7 0 0 0 11.8-2"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    check: <path d="m5 12 4 4L19 6"/>,
    warning: <><path d="m12 3 10 18H2z"/><path d="M12 9v5M12 17h.01"/></>,
    external: <><path d="M14 3h7v7M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/></>,
    shield: <><path d="M12 3 20 6v5c0 5-3.4 8.2-8 10-4.6-1.8-8-5-8-10V6z"/><path d="m9 12 2 2 4-4"/></>,
    truck: <><path d="M3 6h11v11H3zM14 10h4l3 3v4h-7z"/><circle cx="7.5" cy="19" r="1.5"/><circle cx="17.5" cy="19" r="1.5"/></>,
    wallet: <><rect x="3" y="5" width="18" height="15" rx="2"/><path d="M3 9h18M16 14h2"/></>,
    spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7zM19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>,
    filter: <><path d="M4 5h16l-6 7v6l-4 2v-8z"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    route: <><circle cx="6" cy="18" r="2"/><circle cx="18" cy="6" r="2"/><path d="M8 18h3a3 3 0 0 0 3-3V9a3 3 0 0 1 3-3"/></>,
    file: <><path d="M6 3h8l4 4v14H6zM14 3v5h5M9 13h6M9 17h6"/></>,
    database: <><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></>,
    activity: <><path d="M3 12h4l3-8 4 16 3-8h4"/></>,
    chevron: <path d="m9 18 6-6-6-6"/>,
  };
  return <svg {...common}>{paths[name]}</svg>;
}

function money(value: number | string | null | undefined, currency = 'USD'): string {
  if (value === null || value === undefined || value === '') return '—';
  try { return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(Number(value)); }
  catch { return `${currency} ${Number(value).toLocaleString()}`; }
}
function shortDate(value?: string | null): string {
  if (!value) return 'Not specified';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
}
function dateTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date);
}
function statusTone(status: string): string {
  const normalized = status.toUpperCase();
  if (['DELIVERED', 'PAID', 'CAPTURED', 'COMPLETED', 'VERIFIED'].includes(normalized)) return 'cream';
  if (['IN_TRANSIT', 'BOOKED', 'QUOTED', 'APPROVED'].includes(normalized)) return 'coral-subtle';
  if (['EXCEPTION', 'FAILED', 'REVIEW_REQUIRED', 'CANCELLED', 'REFUNDED'].includes(normalized)) return 'coral-bold';
  return 'coral-outline';
}
function riskTone(label?: string): string {
  if (label === 'LOWER_CONCERN') return 'cream';
  if (label === 'HIGH_ATTENTION') return 'coral-bold';
  if (label === 'REVIEW') return 'coral-subtle';
  return 'coral-outline';
}
function riskLabel(label?: string): string {
  return (label || 'NOT ASSESSED').replace(/_/g, ' ');
}
function routeName(shipment: Shipment): string {
  return `${shipment.origin} → ${shipment.destination}`;
}

function StatCard({ label, value, caption, icon, tint }: { label: string; value: string | number; caption: string; icon: IconName; tint: string }): React.ReactElement {
  return <div className="stat-card"><div className={`stat-icon ${tint}`}><Icon name={icon} size={19} /></div><div className="stat-copy"><span className="eyebrow">{label}</span><strong>{value}</strong><span className="stat-caption">{caption}</span></div></div>;
}

function StatusBadge({ value }: { value: string }): React.ReactElement {
  return <span className={`status-badge ${statusTone(value)}`}><span className="status-dot" />{value.replace(/_/g, ' ')}</span>;
}

function EmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }): React.ReactElement {
  return <div className="empty-panel"><div className="empty-symbol"><Icon name="file" size={23}/></div><h3>{title}</h3><p>{description}</p>{action}</div>;
}

function createAuthNonce(): string {
  const bytes = new Uint8Array(32);
  window.crypto.getRandomValues(bytes);
  return Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
}

function GoogleBrandIcon(): React.ReactElement {
  return (
    <svg aria-hidden="true" viewBox="0 0 48 48" width="20" height="20" focusable="false">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5Z"/>
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.91c-.58 2.96-2.25 5.47-4.72 7.16l7.62 5.91c4.45-4.11 7.17-10.16 7.17-17.54Z"/>
      <path fill="#FBBC05" d="M10.53 28.59A14.4 14.4 0 0 1 9.75 24c0-1.59.27-3.13.76-4.59l-7.98-6.19A23.9 23.9 0 0 0 0 24c0 3.87.93 7.52 2.56 10.78l7.97-6.19Z"/>
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.91l-7.62-5.91c-2.12 1.44-4.84 2.29-8.28 2.29-6.26 0-11.57-4.22-13.46-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48Z"/>
    </svg>
  );
}

function AppleBrandIcon(): React.ReactElement {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" focusable="false">
      <path fill="currentColor" d="M16.37 12.1c.02 2.18 1.91 2.9 1.93 2.91-.02.05-.3 1.04-1 2.06-.6.88-1.22 1.76-2.2 1.78-.96.02-1.27-.57-2.37-.57s-1.45.55-2.34.59c-.94.03-1.65-.95-2.25-1.83-1.23-1.78-2.17-5.02-.91-7.22a3.47 3.47 0 0 1 2.94-1.81c.92-.02 1.79.62 2.36.62.56 0 1.58-.76 2.67-.65.46.02 1.73.19 2.55 1.38-.07.04-1.52.89-1.38 2.74ZM14.62 6.3c.5-.6.83-1.43.74-2.26-.72.03-1.58.48-2.1 1.08-.46.53-.85 1.37-.74 2.17.79.06 1.61-.4 2.1-.99Z"/>
    </svg>
  );
}

function PhoneBrandIcon(): React.ReactElement {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" focusable="false">
      <rect x="6.5" y="2" width="11" height="20" rx="2.2" />
      <path d="M10 5h4M11 18.5h2" />
    </svg>
  );
}

function AuthModal({ onClose, onAuthenticated, initialMode = 'login', resetToken = null }: { onClose: () => void; onAuthenticated: (user: UserProfile, token: string, refreshToken?: string | null) => void; initialMode?: 'login' | 'register' | 'reset-password'; resetToken?: string | null }): React.ReactElement {
  const [mode, setMode] = useState<'login' | 'register' | 'forgot' | 'reset-password'>(initialMode);
  const [newPassword, setNewPassword] = useState('');
  const [newPasswordConfirm, setNewPasswordConfirm] = useState('');
  const [method, setMethod] = useState<'password' | 'phone'>('password');
  const [role, setRole] = useState<'BUYER' | 'SELLER'>('BUYER');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [businessAddress, setBusinessAddress] = useState('');
  const [contactPerson, setContactPerson] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [otpRequested, setOtpRequested] = useState(false);
  const firebaseConfirmationRef = useRef<ConfirmationResult | null>(null);
  const firebaseRecaptchaRef = useRef<RecaptchaVerifier | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [nonce] = useState(createAuthNonce);
  const googleButtonRef = useRef<HTMLDivElement>(null);
  const onAuthenticatedRef = useRef(onAuthenticated);
  useEffect(() => { onAuthenticatedRef.current = onAuthenticated; }, [onAuthenticated]);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';
  const appleClientId = import.meta.env.VITE_APPLE_CLIENT_ID || '';
  const appleRedirectUri = import.meta.env.VITE_APPLE_REDIRECT_URI || '';
  const firebasePhoneAuthEnabled = Boolean(import.meta.env.VITE_FIREBASE_API_KEY && import.meta.env.VITE_FIREBASE_AUTH_DOMAIN && import.meta.env.VITE_FIREBASE_PROJECT_ID && import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID && import.meta.env.VITE_FIREBASE_APP_ID);

  useEffect(() => () => {
    firebaseRecaptchaRef.current?.clear();
    firebaseRecaptchaRef.current = null;
    firebaseConfirmationRef.current = null;
  }, []);

  const completeOAuth = useCallback(async (provider: 'google' | 'apple', idToken: string) => {
    setBusy(true);
    setError(null);
    try {
      const response = await oauthSignIn(provider, idToken, nonce);
      onAuthenticatedRef.current(response.user, response.access_token, response.refresh_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : `${provider} sign-in failed.`);
    } finally {
      setBusy(false);
    }
  }, [nonce]);

  useEffect(() => {
    if (!googleClientId) return;
    let active = true;
    const initializeGoogle = () => {
      if (!active || !window.google?.accounts?.id || !googleButtonRef.current) return;
      const target = googleButtonRef.current;
      target.replaceChildren();
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        nonce,
        auto_select: false,
        callback: (response) => {
          if (!response.credential) {
            setError('Google did not return an identity token. Please retry.');
            return;
          }
          void completeOAuth('google', response.credential);
        },
      });
      window.google.accounts.id.renderButton(target, {
        theme: 'outline',
        size: 'large',
        shape: 'rectangular',
        text: 'continue_with',
        width: Math.min(420, Math.max(260, target.clientWidth || 320)),
        logo_alignment: 'left',
      });
    };
    const script = document.getElementById('google-identity-sdk');
    if (window.google?.accounts?.id) initializeGoogle();
    else script?.addEventListener('load', initializeGoogle);
    return () => {
      active = false;
      script?.removeEventListener('load', initializeGoogle);
    };
  }, [completeOAuth, googleClientId, nonce]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      let response;
      if (mode === 'login') {
        response = await login(email, password);
      } else if (role === 'BUYER') {
        response = await registerBuyer({
          email,
          password,
          company_name: businessName || undefined,
          contact_person: contactPerson || undefined,
          phone_number: contactPhone || undefined,
        });
      } else {
        response = await registerSeller({
          email,
          password,
          business_name: businessName,
          business_address: businessAddress,
          country: 'US',
          contact_person: contactPerson,
          contact_phone: contactPhone,
        });
      }
      onAuthenticated(response.user, response.access_token, response.refresh_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Authentication failed.');
    } finally {
      setBusy(false);
    }
  };

  const requestPhoneCode = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (firebasePhoneAuthEnabled) {
        const { createRecaptchaVerifier, sendPhoneOtp } = await import('./lib/firebaseAuth');
        firebaseRecaptchaRef.current?.clear();
        const verifier = createRecaptchaVerifier('recaptcha-container');
        firebaseRecaptchaRef.current = verifier;
        const result = await sendPhoneOtp(phoneNumber.trim(), verifier);
        firebaseConfirmationRef.current = result.confirmationResult;
      } else {
        // Local development fallback: backend/.env may use SMS_PROVIDER=console.
        // Production Firebase deployments must provide the public Firebase web config.
        await requestPhoneLoginOtp(phoneNumber.trim());
      }
      setOtpRequested(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not request an SMS code.');
    } finally {
      setBusy(false);
    }
  };

  const verifyPhoneCode = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (firebaseConfirmationRef.current) {
        const { verifyPhoneOtp } = await import('./lib/firebaseAuth');
        const verified = await verifyPhoneOtp(firebaseConfirmationRef.current, otp.trim());
        const response = await verifyFirebasePhone(verified.idToken, verified.phoneNumber);
        firebaseConfirmationRef.current = null;
        firebaseRecaptchaRef.current?.clear();
        firebaseRecaptchaRef.current = null;
        onAuthenticated(response.user, response.access_token, response.refresh_token);
      } else {
        const response = await verifyPhoneLoginOtp(phoneNumber.trim(), otp.trim());
        onAuthenticated(response.user, response.access_token, response.refresh_token);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The SMS code could not be verified.');
    } finally {
      setBusy(false);
    }
  };

  const signInWithApple = async () => {
    if (!appleClientId || !appleRedirectUri) {
      setError('Add VITE_APPLE_CLIENT_ID and the registered HTTPS VITE_APPLE_REDIRECT_URI to frontend/.env.local before enabling Apple sign-in.');
      return;
    }
    if (!window.AppleID?.auth) {
      setError('Apple Sign In is still loading. Please retry in a moment.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      window.AppleID.auth.init({
        clientId: appleClientId,
        scope: 'name email',
        redirectURI: appleRedirectUri,
        state: nonce,
        nonce,
        usePopup: true,
      });
      const result = await window.AppleID.auth.signIn();
      const authorizationCode = result.authorization?.code;
      if (!authorizationCode) throw new Error('Apple did not return an authorization code.');
      const response = await oauthSignIn('apple', '', nonce, authorizationCode);
      onAuthenticatedRef.current(response.user, response.access_token, response.refresh_token);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Apple sign-in failed.');
    } finally {
      setBusy(false);
    }
  };

  return <div className="modal-backdrop auth-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div className="auth-split-card" role="dialog" aria-modal="true" aria-label={mode === 'login' ? 'Sign in' : mode === 'register' ? 'Create account' : 'Reset password'} onMouseDown={(event) => event.stopPropagation()}>

      {/* Left Brand Panel */}
      <div className="auth-split-left">
        <div className="auth-split-brand">
          <div className="brand-mark">FP</div>
          <div className="auth-brand-info"><strong>FreightPilot AI</strong><span>Global Logistics, Redefined</span></div>
        </div>
        <div className="auth-split-benefits">
          <div className="benefit-item">
            <div className="benefit-icon"><Icon name="shield" size={18}/></div>
            <div className="benefit-text"><strong>Secure &amp; Multi-Provider Login</strong><p>Google, Apple &amp; SMS (OTP)</p></div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon"><Icon name="check" size={18}/></div>
            <div className="benefit-text"><strong>Enterprise-Grade Security</strong><p>Your data is always protected</p></div>
          </div>
          <div className="benefit-item">
            <div className="benefit-icon"><Icon name="truck" size={18}/></div>
            <div className="benefit-text"><strong>One Account, Full Platform</strong><p>Ship, Track, Pay &amp; Analyze</p></div>
          </div>
        </div>
        <div className="auth-split-foot">© {new Date().getFullYear()} FreightPilot AI · Enterprise Platform</div>
      </div>

      {/* Right Form Panel */}
      <div className="auth-split-right">
        <div className="auth-form-brand" aria-label="FreightPilot">FREIGHT<span>PILOT</span></div>
        <button className="auth-close-btn" onClick={onClose} aria-label="Close"><Icon name="close" size={16}/></button>

        <div className="auth-toggle-pill">
          <button className={mode === 'login' ? 'active' : ''} type="button" onClick={() => { setMode('login'); setMethod('password'); setError(null); setSuccessMsg(null); setOtpRequested(false); }}>Sign In</button>
          <button className={mode === 'register' ? 'active' : ''} type="button" onClick={() => { setMode('register'); setMethod('password'); setError(null); setSuccessMsg(null); }}>Create Account</button>
        </div>

        <div className="auth-right-head">
          <h3>{mode === 'forgot' ? 'Reset Password' : mode === 'login' ? 'Welcome Back' : `Create ${role.toLowerCase()} account`}</h3>
          <p>{mode === 'forgot' ? 'Enter your account email to receive reset instructions.' : mode === 'login' ? 'Sign in to your FreightPilot AI account' : 'Join FreightPilot AI — the intelligent freight platform.'}</p>
        </div>

        {mode === 'forgot' && (
          <form onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError(null);
            setSuccessMsg(null);
            try {
              await requestPasswordReset(email);
              setSuccessMsg('If an account exists for this email, a password reset link has been sent. Check your inbox.');
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to send reset email. Please try again.');
            } finally {
              setBusy(false);
            }
          }} className="form-stack auth-fields">
            <div className="auth-input-group">
              <span className="input-icon-slot"><Icon name="external" size={15}/></span>
              <input className="auth-input-field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" placeholder="Enter your registered email"/>
            </div>
            {error && <div className="inline-alert inline-alert-danger">{error}</div>}
            {successMsg && <div className="inline-alert" style={{background:'rgba(244,237,224,0.1)',color:'#F4EDE0',border:'1px solid rgba(244,237,224,0.2)'}}>{successMsg}</div>}
            <button className="btn-auth-submit" disabled={busy}>{busy ? 'Submitting…' : 'Send Reset Instructions'}</button>
            <button type="button" className="auth-forgot-link" style={{display:'block',marginTop:8,textAlign:'center'}} onClick={() => { setMode('login'); setError(null); setSuccessMsg(null); }}>← Back to Sign In</button>
          </form>
        )}

        {mode === 'reset-password' && (
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (!resetToken) {
              setError('Invalid or missing reset token. Please request a new password reset link.');
              return;
            }
            if (newPassword !== newPasswordConfirm) {
              setError('Passwords do not match.');
              return;
            }
            if (newPassword.length < 10) {
              setError('Password must be at least 10 characters.');
              return;
            }
            setBusy(true);
            setError(null);
            setSuccessMsg(null);
            try {
              await resetPassword(resetToken, newPassword);
              setSuccessMsg('Password has been reset successfully. You can now sign in with your new password.');
              setTimeout(() => { setMode('login'); setSuccessMsg(null); }, 3000);
            } catch (err) {
              setError(err instanceof Error ? err.message : 'Failed to reset password. Please try again.');
            } finally {
              setBusy(false);
            }
          }} className="form-stack auth-fields">
            <div className="auth-input-group">
              <span className="input-icon-slot"><Icon name="shield" size={15}/></span>
              <input className="auth-input-field" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} required minLength={10} autoComplete="new-password" placeholder="Enter new password (min 10 characters)"/>
            </div>
            <div className="auth-input-group">
              <span className="input-icon-slot"><Icon name="check" size={15}/></span>
              <input className="auth-input-field" type="password" value={newPasswordConfirm} onChange={(event) => setNewPasswordConfirm(event.target.value)} required minLength={10} autoComplete="new-password" placeholder="Confirm new password"/>
            </div>
            {error && <div className="inline-alert inline-alert-danger">{error}</div>}
            {successMsg && <div className="inline-alert" style={{background:'rgba(244,237,224,0.1)',color:'#F4EDE0',border:'1px solid rgba(244,237,224,0.2)'}}>{successMsg}</div>}
            <button className="btn-auth-submit" disabled={busy}>{busy ? 'Resetting…' : 'Reset Password'}</button>
            <button type="button" className="auth-forgot-link" style={{display:'block',marginTop:8,textAlign:'center'}} onClick={() => { setMode('login'); setError(null); setSuccessMsg(null); }}>← Back to Sign In</button>
          </form>
        )}

        {mode === 'register' && <div className="role-selector auth-role-selector">
          <button type="button" className={`btn btn-sm ${role === 'BUYER' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setRole('BUYER')}>Buyer account</button>
          <button type="button" className={`btn btn-sm ${role === 'SELLER' ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setRole('SELLER')}>Seller / Carrier</button>
        </div>}

        {mode === 'login' && method === 'password' && <div className="auth-social-stack">
          <div className="google-signin-slot">
            {googleClientId ? <div ref={googleButtonRef} className="google-signin-button"/> : <button type="button" className="btn-social" disabled><span className="social-symbol social-google"><GoogleBrandIcon /></span>Continue with Google</button>}
          </div>
          <button type="button" className="btn-social" onClick={() => void signInWithApple()} disabled={busy || !appleClientId || !appleRedirectUri}>
            <span className="social-symbol social-apple"><AppleBrandIcon /></span>Continue with Apple
          </button>
          <button type="button" className="btn-social" onClick={() => { setMethod('phone'); setError(null); }}>
            <span className="social-symbol social-phone"><PhoneBrandIcon /></span>Continue with Phone (OTP)
          </button>
          {(!googleClientId || !appleClientId) && <div className="auth-provider-note">Enable Google and Apple by adding their public client IDs to frontend/.env.local.</div>}
        </div>}

        {mode === 'login' && <div className="auth-or-divider"><span>or</span></div>}

        {mode === 'login' && method === 'phone' ? <form onSubmit={otpRequested ? verifyPhoneCode : requestPhoneCode} className="form-stack auth-fields">
          <div className="auth-input-group">
            <span className="input-icon-slot"><Icon name="route" size={15}/></span>
            <input className="auth-input-field" type="tel" value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} required pattern="\+[1-9]\d{7,14}" placeholder="+919876543210" autoComplete="tel"/>
          </div>
          {otpRequested && <div className="auth-input-group">
            <span className="input-icon-slot"><Icon name="check" size={15}/></span>
            <input className="auth-input-field" value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))} required inputMode="numeric" pattern="\d{6}" placeholder="6-digit SMS code" autoComplete="one-time-code"/>
          </div>}
          {error && <div className="inline-alert inline-alert-danger">{error}</div>}
          <button className="btn-auth-submit" disabled={busy}>{busy ? 'Please wait…' : otpRequested ? 'Verify code & sign in' : 'Send SMS code'}</button>
          {otpRequested && <button type="button" className="text-button" onClick={() => { setOtpRequested(false); setOtp(''); firebaseConfirmationRef.current = null; firebaseRecaptchaRef.current?.clear(); firebaseRecaptchaRef.current = null; }}>Use a different number</button>}
          <button type="button" className="auth-forgot-link" style={{display:'block',marginTop:8}} onClick={() => { setMethod('password'); setError(null); }}>← Back to email login</button>
        </form> : (mode === 'register' || method === 'password') && <form onSubmit={submit} className="form-stack auth-fields">
          <div className="auth-input-group">
            <span className="input-icon-slot"><Icon name="external" size={15}/></span>
            <input className="auth-input-field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" placeholder="Enter your email"/>
          </div>
          <div className="auth-input-group">
            <span className="input-icon-slot"><Icon name="shield" size={15}/></span>
            <input className="auth-input-field" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={mode === 'register' ? 10 : 1} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder="Enter your password"/>
          </div>
          {mode === 'register' && <>
            {role === 'SELLER' && <>
              <label>Company / Business name<input value={businessName} onChange={(event) => setBusinessName(event.target.value)} required placeholder="Apex Marine Freight Ltd."/></label>
              <label>Business address<input value={businessAddress} onChange={(event) => setBusinessAddress(event.target.value)} required placeholder="Business address"/></label>
              <label>Contact person<input value={contactPerson} onChange={(event) => setContactPerson(event.target.value)} required placeholder="Full name"/></label>
            </>}
            {role === 'BUYER' && <label>Company name <span className="optional-label">Optional</span><input value={businessName} onChange={(event) => setBusinessName(event.target.value)} placeholder="Company / organization"/></label>}
            <label>Phone number {role === 'BUYER' && <span className="optional-label">Optional · E.164 format</span>}<input type="tel" value={contactPhone} onChange={(event) => setContactPhone(event.target.value)} required={role === 'SELLER'} pattern="\+[1-9]\d{7,14}" placeholder="+919876543210" autoComplete="tel"/></label>
          </>}
          {mode === 'login' && <div className="auth-forgot-row"><button type="button" className="auth-forgot-link" onClick={() => { setMode('forgot'); setError(null); setSuccessMsg(null); }}>Forgot password?</button></div>}
          {error && <div className="inline-alert inline-alert-danger">{error}</div>}
          <button className="btn-auth-submit" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create account'}</button>
        </form>}

        <p className="fine-print auth-security-note" style={{marginTop:14}}>Social sign-in is verified by the FreightPilot API. Seller access remains subject to administrator approval.</p>
      </div>
    </div>
  </div>;
}

export default function App(): React.ReactElement {
  const [page, setPageState] = useState<Page>(() => {
    const requested = window.location.hash.replace(/^#/, '') as Page;
    return (['landing', 'overview', 'shipments', 'quotes', 'payments', 'copilot', 'risk', 'analytics', 'carriers', 'documents', 'settings'] as Page[]).includes(requested)
      ? requested : 'landing';
  });
  const pageRef = useRef<Page>(page);
  const pageHistory = useRef<Page[]>([]);
  const setPage = useCallback((nextPage: Page) => {
    if (pageRef.current === nextPage) return;
    pageHistory.current.push(pageRef.current);
    pageRef.current = nextPage;
    const nextUrl = `${window.location.pathname}${window.location.search}${nextPage === 'landing' ? '' : `#${nextPage}`}`;
    window.history.pushState({ freightPilotPage: nextPage }, '', nextUrl);
    setPageState(nextPage);
  }, []);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [activeShipment, setActiveShipment] = useState<Shipment | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [estimate, setEstimate] = useState<RateEstimate | null>(null);
  const [tracking, setTracking] = useState<TrackingEvent[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [carrierPerformance, setCarrierPerformance] = useState<CarrierPerformance[]>([]);
  const [carrierCatalog, setCarrierCatalog] = useState<CarrierCatalog | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [copilotQuoteIds, setCopilotQuoteIds] = useState<string[]>([]);
  const [copilotResult, setCopilotResult] = useState<CopilotResult | null>(null);
  const [copilotBusy, setCopilotBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [newShipmentOpen, setNewShipmentOpen] = useState(false);
  const initialAuthRoute = (() => {
    const pathname = window.location.pathname.replace(/\/+$/, '').toLowerCase();
    const hash = window.location.hash.replace(/^#/, '').toLowerCase();
    if (pathname.endsWith('/register') || hash === 'register') return 'register' as const;
    if (pathname.endsWith('/login') || hash === 'login') return 'login' as const;
    if (pathname.startsWith('/reset-password') || hash.startsWith('reset-password')) return 'reset-password' as const;
    return null;
  })();
  const [authOpen, setAuthOpen] = useState(() => initialAuthRoute !== null);
  const [authInitialMode, setAuthInitialMode] = useState<'login' | 'register' | 'reset-password'>(initialAuthRoute ?? 'login');
  const [resetPasswordToken, setResetPasswordToken] = useState<string | null>(null);
  const openAuth = (mode: 'login' | 'register' = 'login') => {
    setAuthInitialMode(mode);
    setAuthOpen(true);
    const authPath = mode === 'register' ? '/register' : '/login';
    if (window.location.pathname !== authPath) window.history.pushState({ auth: mode }, '', authPath);
  };

  // Extract reset password token from URL
  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const token = searchParams.get('token');
    if (token) {
      setResetPasswordToken(token);
      if (authInitialMode === 'reset-password') {
        setAuthOpen(true);
      }
    }
  }, []);
  const closeAuth = () => {
    setAuthOpen(false);
    if (/\/(login|register)\/?$/i.test(window.location.pathname) || /^(login|register)$/i.test(window.location.hash.replace(/^#/, ''))) {
      window.history.replaceState({ freightPilotPage: 'landing' }, '', '/');
      pageRef.current = 'landing';
      setPageState('landing');
    }
  };
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [accountPhone, setAccountPhone] = useState('');
  const [accountPhoneOtp, setAccountPhoneOtp] = useState('');
  const [accountPhoneOtpSent, setAccountPhoneOtpSent] = useState(false);
  const [phoneSettingsBusy, setPhoneSettingsBusy] = useState(false);
  const [phoneSettingsMessage, setPhoneSettingsMessage] = useState('');
  const [health, setHealth] = useState<{ status: string; service: string } | null>(null);
  const [search, setSearch] = useState('');
  const [trackingStatus, setTrackingStatus] = useState('IN_TRANSIT');
  const [trackingLocation, setTrackingLocation] = useState('');
  const [trackingDescription, setTrackingDescription] = useState('Shipment status updated by operations.');
  const [trackingBusy, setTrackingBusy] = useState(false);
  const [assessmentBusy, setAssessmentBusy] = useState<string | null>(null);
  const [carrierBusy, setCarrierBusy] = useState(false);
  const [deleteAccountOpen, setDeleteAccountOpen] = useState(false);
  const [deleteAccountConfirm, setDeleteAccountConfirm] = useState('');
  const [deleteAccountPassword, setDeleteAccountPassword] = useState('');
  const [deleteAccountBusy, setDeleteAccountBusy] = useState(false);
  const [deleteAccountError, setDeleteAccountError] = useState('');

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast((current) => current === message ? null : current), 4200);
  }, []);

  const loadShipmentDetail = useCallback(async (shipment: Shipment) => {
    setDetailLoading(true); setPageError(null);
    try {
      const [quoteRows, estimateData, trackingRows] = await Promise.all([
        fetchShipmentQuotes(shipment.id), fetchShipmentEstimate(shipment.id), fetchTracking(shipment.id),
      ]);
      setQuotes(quoteRows); setEstimate(estimateData); setTracking(trackingRows);
      setCopilotQuoteIds(quoteRows.map((quote) => quote.id));
      setCopilotResult(null);
    } catch (reason) {
      setQuotes([]); setEstimate(null); setTracking([]);
      setPageError(reason instanceof Error ? reason.message : 'Unable to load shipment details.');
    } finally { setDetailLoading(false); }
  }, []);

  const loadPortfolio = useCallback(async (preserveId?: string) => {
    setLoading(true); setPageError(null);
    const [shipmentResult, analyticsResult, carrierResult, catalogResult, notificationResult, healthResult] = await Promise.allSettled([
      fetchShipments(), fetchAnalyticsOverview(), fetchCarrierPerformance(), fetchCarrierCatalog(), fetchNotifications(), fetchHealth(),
    ]);
    if (shipmentResult.status === 'fulfilled') {
      const list = shipmentResult.value; setShipments(list);
      const target = (preserveId && list.find((item) => item.id === preserveId)) || (activeShipment && list.find((item) => item.id === activeShipment.id)) || list.find((item) => item.id === 'demo-shipment-001') || list[0] || null;
      setActiveShipment(target);
      if (target) await loadShipmentDetail(target);
      else { setQuotes([]); setEstimate(null); setTracking([]); }
    } else {
      setPageError(shipmentResult.reason instanceof Error ? shipmentResult.reason.message : 'Cannot connect to the backend.');
    }
    if (analyticsResult.status === 'fulfilled') setAnalytics(analyticsResult.value);
    if (carrierResult.status === 'fulfilled') setCarrierPerformance(carrierResult.value.items || []);
    if (catalogResult.status === 'fulfilled') setCarrierCatalog(catalogResult.value);
    if (notificationResult.status === 'fulfilled') setNotifications(notificationResult.value);
    if (healthResult.status === 'fulfilled') setHealth(healthResult.value);
    setLoading(false);
  }, [activeShipment, loadShipmentDetail]);

  const loadPayments = useCallback(async (items: Shipment[]) => {
    if (!items.length) { setPayments([]); setPaymentLoading(false); return; }
    setPaymentLoading(true);
    const paymentRows: PaymentRecord[] = [];
    // Bound concurrency to avoid opening one request per shipment at once.
    for (let offset = 0; offset < items.length; offset += 8) {
      const batch = await Promise.allSettled(items.slice(offset, offset + 8).map((shipment) => fetchShipmentPayments(shipment.id)));
      for (const result of batch) if (result.status === 'fulfilled') paymentRows.push(...result.value);
    }
    paymentRows.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    setPayments(paymentRows); setPaymentLoading(false);
  }, []);

  useEffect(() => {
    const initialUrl = `${window.location.pathname}${window.location.search}${page === 'landing' ? '' : `#${page}`}`;
    window.history.replaceState({ freightPilotPage: page }, '', initialUrl);
    const syncPageFromHistory = () => {
      const requested = window.location.hash.replace(/^#/, '') as Page;
      const next = (['landing', 'overview', 'shipments', 'quotes', 'payments', 'copilot', 'risk', 'analytics', 'carriers', 'documents', 'settings'] as Page[]).includes(requested)
        ? requested : 'landing';
      const previous = pageRef.current;
      pageRef.current = next;
      if (pageHistory.current[pageHistory.current.length - 1] === next) {
        pageHistory.current.pop();
      } else if (previous !== next) {
        pageHistory.current.push(previous);
      }
      setPageState(next);
    };
    window.addEventListener('popstate', syncPageFromHistory);
    return () => window.removeEventListener('popstate', syncPageFromHistory);
  }, []);
  useEffect(() => { void loadPortfolio(); }, []); // initial API hydration
  useEffect(() => {
    if (page === 'payments' && shipments.length) void loadPayments(shipments);
  }, [page, shipments, loadPayments]);
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;
    fetchCurrentUser().then((user) => { setCurrentUser(user); setAccountPhone(user.phone_number || ''); }).catch(() => { clearAuthTokens(); setCurrentUser(null); });
  }, []);

  // Periodic health check for Settings page
  useEffect(() => {
    if (page !== 'settings') return;
    const interval = setInterval(async () => {
      try {
        const healthResult = await fetchHealth();
        setHealth(healthResult);
      } catch {
        // Health check failed, keep previous state
      }
    }, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [page]);

  const filteredShipments = useMemo(() => shipments.filter((shipment) => `${shipment.id} ${shipment.cargo_type} ${shipment.origin} ${shipment.destination} ${shipment.status}`.toLowerCase().includes(search.toLowerCase())), [shipments, search]);
  const totalQuoteCount = analytics?.quote_count ?? shipments.reduce((sum, shipment) => sum + (shipment.quotes_count || 0), 0);
  const capturedSpend = analytics?.captured_spend_by_currency || [];

  const selectShipment = async (shipmentId: string) => {
    const target = shipments.find((shipment) => shipment.id === shipmentId);
    if (!target) return;
    setActiveShipment(target); setSelectedQuote(null);
    await loadShipmentDetail(target);
  };

  const handleCreateShipment = async (payload: ShipmentCreatePayload) => {
    const created = await createShipment(payload);
    showToast(`Shipment ${created.id.slice(0, 8)} created.`);
    setNewShipmentOpen(false);
    setPage('shipments');
    await loadPortfolio(created.id);
  };

  const handleReset = async () => {
    if (!window.confirm('Reset the synthetic demo shipment and quotes? Existing payment-linked data is protected by the backend.')) return;
    setResetting(true);
    try { const result = await resetDemoData(); showToast('Demo dataset reset.'); await loadPortfolio(result.shipment_id); }
    catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Demo reset failed.'); }
    finally { setResetting(false); }
  };

  const handleAssess = async (quote: Quote) => {
    setAssessmentBusy(quote.id);
    try {
      const assessed = await assessQuote(quote.id);
      setQuotes((rows) => rows.map((row) => row.id === assessed.id ? assessed : row));
      showToast(`Risk assessment refreshed for ${quote.provider_label}.`);
    } catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Risk assessment failed.'); }
    finally { setAssessmentBusy(null); }
  };

  const handleRunCopilot = async () => {
    if (!activeShipment || copilotQuoteIds.length === 0) return;
    setCopilotBusy(true); setCopilotResult(null);
    try { setCopilotResult(await compareQuotesWithCopilot(activeShipment.id, copilotQuoteIds)); }
    catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Copilot analysis failed.'); }
    finally { setCopilotBusy(false); }
  };

  const handleAddTracking = async (event: React.FormEvent) => {
    event.preventDefault(); if (!activeShipment) return;
    setTrackingBusy(true);
    try {
      await addTrackingEvent(activeShipment.id, { status: trackingStatus, location: trackingLocation || undefined, description: trackingDescription });
      showToast('Tracking event added.'); setTrackingDescription('Shipment status updated by operations.');
      await loadShipmentDetail(activeShipment);
      await loadPortfolio(activeShipment.id);
    } catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Unable to add tracking event.'); }
    finally { setTrackingBusy(false); }
  };

  const handleCancelShipment = async () => {
    if (!activeShipment || !window.confirm('Cancel this shipment? This action changes its lifecycle status.')) return;
    try { await cancelShipment(activeShipment.id); showToast('Shipment cancelled.'); await loadPortfolio(activeShipment.id); }
    catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Unable to cancel shipment.'); }
  };

  const handleRefreshCarriers = async () => {
    if (!activeShipment || !carrierCatalog?.items.length) { showToast('No live carrier adapters are configured yet.'); return; }
    setCarrierBusy(true);
    try {
      const configured = carrierCatalog.items.find((carrier) => carrier.status === 'CONFIGURED');
      if (!configured) { showToast('No configured carrier adapter is available.'); return; }
      const result = await refreshCarrierQuotes(activeShipment.id, configured.code);
      showToast(`${result.created_count} carrier quote(s) added.`);
      await loadShipmentDetail(activeShipment);
    } catch (reason) { setPageError(reason instanceof Error ? reason.message : 'Carrier quote refresh failed.'); }
    finally { setCarrierBusy(false); }
  };

  const handleAuthSuccess = useCallback((user: UserProfile, token: string, refreshToken?: string | null) => {
    setAuthToken(token);
    setRefreshToken(refreshToken ?? null);
    setCurrentUser(user);
    setAccountPhone(user.phone_number || '');
    setAccountPhoneOtp('');
    setAccountPhoneOtpSent(false);
    setPhoneSettingsMessage('');
    setAuthOpen(false);
    if (/\/(login|register)\/?$/i.test(window.location.pathname)) {
      window.history.replaceState({ freightPilotPage: 'landing' }, '', '/');
    }
    setPage('overview');
    showToast(`Signed in as ${user.email}.`);
    void loadPortfolio();
  }, [loadPortfolio, setPage, showToast]);

  const saveAccountPhone = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!currentUser) return;
    setPhoneSettingsBusy(true);
    setPhoneSettingsMessage('');
    try {
      const updated = await updateAccountPhone(accountPhone.trim());
      setCurrentUser(updated);
      setAccountPhone(updated.phone_number || accountPhone.trim());
      setAccountPhoneOtpSent(false);
      setAccountPhoneOtp('');
      setPhoneSettingsMessage('Phone number saved. Send a verification code to confirm ownership.');
    } catch (reason) {
      setPhoneSettingsMessage(reason instanceof Error ? reason.message : 'Could not save the phone number.');
    } finally {
      setPhoneSettingsBusy(false);
    }
  };

  const sendAccountPhoneOtp = async () => {
    if (!currentUser || !accountPhone.trim()) return;
    setPhoneSettingsBusy(true);
    setPhoneSettingsMessage('');
    try {
      // Use Firebase Phone Authentication for production
      // The backend expects Firebase ID token verification
      // We need to initialize Firebase reCAPTCHA and send OTP
      const { createRecaptchaVerifier, sendPhoneOtp } = await import('./lib/firebaseAuth');
      const recaptchaVerifier = createRecaptchaVerifier('recaptcha-container');
      const { confirmationResult } = await sendPhoneOtp(accountPhone.trim(), recaptchaVerifier);
      // Store confirmationResult for verification
      (window as any).__phoneAuthConfirmationResult = confirmationResult;
      setAccountPhoneOtpSent(true);
      setPhoneSettingsMessage('Verification code sent. Check your phone.');
    } catch (reason) {
      setPhoneSettingsMessage(reason instanceof Error ? reason.message : 'Could not send the verification code.');
    } finally {
      setPhoneSettingsBusy(false);
    }
  };

  const confirmAccountPhoneOtp = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!currentUser) return;
    setPhoneSettingsBusy(true);
    setPhoneSettingsMessage('');
    try {
      // Verify OTP using Firebase
      const { verifyPhoneOtp } = await import('./lib/firebaseAuth');
      const confirmationResult = (window as any).__phoneAuthConfirmationResult;
      if (!confirmationResult) {
        throw new Error('No verification session found. Please request a new code.');
      }
      const result = await verifyPhoneOtp(confirmationResult, accountPhoneOtp.trim());
      // Link the verified phone to the user account via backend
      const userData = await linkFirebasePhone(result.idToken, result.phoneNumber);
      setCurrentUser(userData);
      setAccountPhoneOtpSent(false);
      setAccountPhoneOtp('');
      setPhoneSettingsMessage('Phone number verified successfully.');
      showToast('Phone number verified.');
    } catch (reason) {
      setPhoneSettingsMessage(reason instanceof Error ? reason.message : 'The verification code was not accepted.');
    } finally {
      setPhoneSettingsBusy(false);
    }
  };

  const goToPayment = (quote: Quote) => { setSelectedQuote(quote); setPage('payments'); };
  const onPaymentSuccess = useCallback((payment: PaymentRecord) => {
    showToast(`Payment captured and verified: ${money(payment.amount, payment.currency)}.`);
    setSelectedQuote(null);
    if (activeShipment) void loadShipmentDetail(activeShipment);
    void loadPayments(shipments);
    void loadPortfolio(activeShipment?.id);
  }, [activeShipment, loadPayments, loadPortfolio, shipments, showToast]);
  const onPaymentStatus = useCallback((message: string) => showToast(message), [showToast]);

  const pageMeta: Record<Page, { title: string; subtitle: string }> = {
    landing: { title: 'Landing', subtitle: 'Cinematic ocean logistics overview' },
    overview: { title: 'Dashboard Overview', subtitle: "Here's what's happening with your logistics today." },
    shipments: { title: 'Shipments', subtitle: 'Track and manage all your shipments in real time.' },
    quotes: { title: 'Get Quotes', subtitle: 'Compare carrier offers using normalized cost, transit and risk data.' },
    payments: { title: 'Payments', subtitle: 'Review payment activity and complete Sandbox checkout for a selected quote.' },
    copilot: { title: 'AI Copilot', subtitle: 'Your AI logistics assistant, powered by Gemini.' },
    risk: { title: 'Risk Engine', subtitle: 'Explainable rule-based assessment of carrier, route and quote risk.' },
    analytics: { title: 'Analytics', subtitle: 'Operational insights and performance trends.' },
    carriers: { title: 'Carriers', subtitle: 'Browse and compare freight carrier catalog and performance.' },
    documents: { title: 'Documents', subtitle: 'Manage shipment documents, bills of lading and customs paperwork.' },
    settings: { title: 'Settings', subtitle: 'Review connected services, environment configuration and account access.' },
  };

  const currentPage = pageMeta[page];

  const renderLanding = () => <div className="landing-page">
    <section className="landing-hero" id="home">
      <nav className="landing-nav">
        <button className="landing-brand" onClick={() => setPage('landing')} aria-label="FreightPilot AI home">
          <span className="brand-mark">FP</span>
          <span className="landing-brand-copy"><strong>FreightPilot <i>AI</i></strong><small>GLOBAL LOGISTICS INTELLIGENCE</small></span>
        </button>
        <div className="landing-nav-links">
          <a href="#home">Home</a>
          <a href="#features">Capabilities</a>
          <a href="#workflow">How it works</a>
          <a href="#contact">Contact</a>
        </div>
        <div className="landing-nav-actions">
          <ThemeToggleButton compact />
          <FamilyReceiveComponent
            triggerLabel="Workspace"
            title="Open your workspace?"
            description="Continue to your logistics workspace to manage shipments, compare carrier quotes and review payments."
            confirmLabel="Continue"
            cancelLabel="Stay here"
            onConfirm={() => { if (currentUser) setPage('overview'); else openAuth('login'); }}
          />
          <button className="landing-signin" onClick={() => openAuth('login')}>Sign in</button>
          <button className="btn btn-coral" onClick={() => openAuth('register')}>Create account <Icon name="arrow" size={15}/></button>
        </div>
      </nav>

      <div className="landing-hero-main">
        <div className="landing-content">
          <div className="landing-badge"><span className="badge-pulse"/><Icon name="spark" size={14}/> MARITIME LOGISTICS INTELLIGENCE</div>
          <h1 className="landing-title">Navigate Freight. <span className="hero-coral">Move Smarter.</span></h1>
          <p className="landing-subtitle">Plan shipments, compare carrier quotes and evaluate operational risk in one connected workspace engineered for confident maritime procurement decisions.</p>
          <div className="landing-cta-group">
            <button className="btn btn-coral" onClick={() => openAuth('register')}>Get started <Icon name="arrow" size={16}/></button>
            <button className="btn btn-glass-hero" onClick={() => openAuth('login')}>Sign in</button>
          </div>
          <div className="landing-proof-row">
            <span><i className="proof-check"><Icon name="check" size={12}/></i> Shipment status visibility</span>
            <span><i className="proof-check"><Icon name="check" size={12}/></i> Explainable risk review</span>
            <span><i className="proof-check"><Icon name="check" size={12}/></i> Secure PayPal Sandbox checkout</span>
          </div>
        </div>

        <div className="landing-hero-scene-wrap" aria-label="Yacht moving across open water">
          <div className="landing-hero-video-frame">
            <video
              className="landing-hero-video"
              autoPlay
              muted
              loop
              playsInline
              preload="auto"
              poster="/images/yacht-poster.png"
              aria-label="A yacht cruising across open ocean with moving water"
            >
              <source src="/videos/yacht-motion.mp4" type="video/mp4" />
            </video>
            <div className="landing-hero-video-shade" aria-hidden="true" />
            <div className="landing-hero-video-caption"><span className="hero-live-dot" /> LIVE OCEAN VISUAL</div>
          </div>
        </div>
      </div>

      <div className="landing-hero-footer">
        <span>ENTERPRISE MARITIME PROCUREMENT &amp; RISK MANAGEMENT</span>
        <span>INTELLIGENCE <i/> INTEGRATION <i/> CERTAINTY</span>
      </div>
    </section>

    <section className="landing-workflow" id="workflow">
      <span id="features" className="landing-anchor" aria-hidden="true"/>
      <div className="workflow-copy"><span className="eyebrow">A CLEARER PROCUREMENT WORKFLOW</span><h2>See the whole journey.<br/><em>Choose with context.</em></h2><p>FreightPilot brings the core information together so teams can evaluate options, understand risk and track what has been confirmed—without confusing estimated data with live carrier feeds.</p><button className="btn btn-coral" onClick={() => openAuth('register')}>Enter platform <Icon name="arrow" size={15}/></button></div>
      <div className="workflow-steps">
        <div className="workflow-step"><span>01</span><div><strong>Describe the shipment</strong><small>Capture cargo, route, dates and currency.</small></div></div>
        <div className="workflow-step"><span>02</span><div><strong>Compare available offers</strong><small>Review stored quote totals, terms and context.</small></div></div>
        <div className="workflow-step"><span>03</span><div><strong>Review before committing</strong><small>Use deterministic risk signals and Copilot as decision support.</small></div></div>
        <div className="workflow-step"><span>04</span><div><strong>Track confirmed outcomes</strong><small>Follow shipment events and backend-confirmed payment status.</small></div></div>
      </div>
    </section>

    <div id="contact"><Contact5Section /></div>
    <footer className="landing-footer"><div className="landing-brand"><span className="brand-mark">FP</span><span className="landing-brand-copy"><strong>FreightPilot <i>AI</i></strong><small>GLOBAL LOGISTICS INTELLIGENCE</small></span></div><p>Clearer freight decisions, from first request to final confirmation.</p><span>© {new Date().getFullYear()} FreightPilot AI</span></footer>
  </div>;

  const renderOverview = () => (
    <FreightOverview
      analytics={analytics}
      shipments={shipments}
      payments={payments}
      quotes={quotes}
      loading={loading}
      onNavigate={(nextPage) => setPage(nextPage)}
      onCreateShipment={() => setNewShipmentOpen(true)}
      onSelectShipment={(shipment) => { void selectShipment(shipment.id); setPage('shipments'); }}
    />
  );

  const renderShipments = () => <>
    <div className="toolbar-row"><div className="search-box"><Icon name="search" size={17}/><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search shipments, route or status…"/></div><button className="btn btn-primary" onClick={() => setNewShipmentOpen(true)}><Icon name="plus" size={16}/> New shipment</button></div>
    <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">SHIPMENT REGISTER</span><h3>All shipments <span className="subtle-count">{filteredShipments.length}</span></h3><p>Select a shipment to inspect its details and event history.</p></div></div>{filteredShipments.length === 0 ? <EmptyState title="No matching shipments" description="Try another search or create a new freight request."/> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Shipment</th><th>Origin / destination</th><th>Ready</th><th>Volume</th><th>Quotes</th><th>Status</th></tr></thead><tbody>{filteredShipments.map((shipment) => <tr key={shipment.id} className={`clickable-row ${activeShipment?.id === shipment.id ? 'selected-row' : ''}`} onClick={() => void selectShipment(shipment.id)}><td><strong>{shipment.cargo_type}</strong><span className="table-secondary mono">{shipment.id}</span></td><td>{shipment.origin}<span className="table-secondary">→ {shipment.destination}</span></td><td>{shortDate(shipment.ready_date)}</td><td>{Number(shipment.quantity_tonnes).toLocaleString()} MT</td><td>{shipment.quotes_count ?? 0}</td><td><StatusBadge value={shipment.status}/></td></tr>)}</tbody></table></div>}</section>
    {activeShipment && <section className="panel shipment-inspector"><div className="panel-header"><div><span className="eyebrow">SELECTED SHIPMENT</span><h3>{activeShipment.cargo_type}</h3><p>{routeName(activeShipment)}</p></div><div className="header-inline-actions"><StatusBadge value={activeShipment.status}/>{!['DELIVERED', 'CANCELLED'].includes(activeShipment.status) && <button className="btn btn-ghost-danger btn-sm" onClick={handleCancelShipment}>Cancel shipment</button>}</div></div><div className="shipment-facts"><Fact label="Reference" value={activeShipment.id}/><Fact label="Cargo volume" value={`${Number(activeShipment.quantity_tonnes).toLocaleString()} metric tonnes`}/><Fact label="Ready date" value={shortDate(activeShipment.ready_date)}/><Fact label="Required arrival" value={shortDate(activeShipment.required_arrival_date)}/><Fact label="Comparison currency" value={activeShipment.currency}/></div>
      <div className="panel-divider"/><div className="tracking-layout"><div><div className="subsection-title"><div><span className="eyebrow">OPERATIONS</span><h4>Tracking timeline</h4></div><span className="muted-text">{tracking.length} events</span></div>{tracking.length ? <div className="timeline">{tracking.map((event) => <div className="timeline-item" key={event.id}><div className="timeline-marker"><span/></div><div className="timeline-content"><div className="timeline-heading"><strong>{event.status.replace(/_/g, ' ')}</strong><time>{dateTime(event.occurred_at)}</time></div><p>{event.description}</p><span>{event.location || 'Location not provided'} · {event.source_kind}</span></div></div>)}</div> : <div className="empty-inline compact"><strong>No tracking events</strong><span>Updates added by operations will appear here.</span></div>}</div>
        <form className="tracking-form" onSubmit={handleAddTracking}><div className="subsection-title"><div><span className="eyebrow">MANUAL EVENT</span><h4>Add tracking update</h4></div></div><label>Status<select value={trackingStatus} onChange={(event) => setTrackingStatus(event.target.value)}>{['QUOTED', 'BOOKED', 'IN_TRANSIT', 'DELIVERED', 'EXCEPTION'].map((status) => <option value={status} key={status}>{status.replace(/_/g, ' ')}</option>)}</select></label><label>Location<input value={trackingLocation} onChange={(event) => setTrackingLocation(event.target.value)} placeholder="Port, city or facility"/></label><label>Description<textarea value={trackingDescription} onChange={(event) => setTrackingDescription(event.target.value)} rows={3} required minLength={3}/></label><button className="btn btn-primary btn-full" disabled={trackingBusy}>{trackingBusy ? 'Saving…' : 'Save tracking event'}</button><p className="fine-print">Manual updates are labeled USER_INPUT; this is not a live carrier tracking feed.</p></form></div></section>}
  </>;

  const renderQuotes = () => <>
    <div className="context-strip"><div className="context-icon"><Icon name="route"/></div><div className="context-copy"><span className="eyebrow">CURRENT SHIPMENT</span><strong>{activeShipment ? routeName(activeShipment) : 'No shipment selected'}</strong><span>{activeShipment ? `${activeShipment.cargo_type} · ${Number(activeShipment.quantity_tonnes).toLocaleString()} MT` : 'Create a shipment to view quotes.'}</span></div><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.cargo_type} · {shipment.origin} → {shipment.destination}</option>)}</select><button className="btn btn-secondary btn-sm" onClick={() => void handleRefreshCarriers()} disabled={carrierBusy || !carrierCatalog?.items.length}><Icon name="refresh" size={14}/>{carrierBusy ? 'Refreshing…' : 'Refresh live rates'}</button></div>
    {activeShipment && <div className="quote-summary-grid"><div className="quote-summary-item"><span>Offers received</span><strong>{quotes.length}</strong></div><div className="quote-summary-item"><span>Benchmark median</span><strong>{estimate?.median_rate ? money(estimate.median_rate, estimate.currency) : 'Not available'}</strong></div><div className="quote-summary-item"><span>Observed range</span><strong>{estimate?.min_rate != null && estimate?.max_rate != null ? `${money(estimate.min_rate, estimate.currency)} – ${money(estimate.max_rate, estimate.currency)}` : 'Not available'}</strong></div><div className="quote-summary-item"><span>Dataset coverage</span><strong className="coverage-text">{estimate?.coverage_status?.replace(/_/g, ' ') || '—'}</strong></div></div>}
    {detailLoading ? <LoadingPanel label="Loading quotes and benchmark…"/> : quotes.length === 0 ? <EmptyState title="No quotes for this shipment" description="This shipment does not have any stored offers yet. Live carrier adapters are not configured in this project."/> : <div className="quote-list">{[...quotes].sort((a, b) => Number(a.total_amount) - Number(b.total_amount)).map((quote, index) => <QuoteCard key={quote.id} quote={quote} shipment={activeShipment} index={index} selected={selectedQuote?.id === quote.id} onAssess={() => void handleAssess(quote)} assessing={assessmentBusy === quote.id} onPay={() => goToPayment(quote)} onInspect={() => setSelectedQuote(quote)}/>)}</div>}
    {estimate && <div className="source-note"><Icon name="activity" size={15}/>{estimate.disclaimer} Method: {estimate.method}. Sample size: {estimate.sample_size}.</div>}
  </>;

  const renderRisk = () => {
    const highRisk = quotes.filter((quote) => quote.assessment && ['HIGH_ATTENTION', 'REVIEW'].includes(quote.assessment.label));
    const unassessed = quotes.filter((quote) => !quote.assessment);
    const avgScore = quotes.filter(q => q.assessment?.score != null).reduce((sum, q) => sum + (q.assessment?.score || 0), 0) / (quotes.filter(q => q.assessment?.score != null).length || 1);
    return <>
      <div className="risk-hero">
        <div className="risk-hero-icon"><Icon name="shield" size={26}/></div>
        <div>
          <span className="eyebrow">EXPLAINABLE RISK ENGINE</span>
          <h3>Evaluate the offer, not just the price.</h3>
          <p>Assessments are generated by the backend using quote terms, price benchmarks and shipment constraints. They are decision support—not a carrier credit rating.</p>
        </div>
        <div className="risk-hero-metrics">
          <div><strong>{highRisk.length}</strong><span>Review / high attention</span></div>
          <div><strong>{unassessed.length}</strong><span>Not assessed</span></div>
        </div>
        <div className="risk-gauge-box">
          <SvgRiskGauge score={quotes.length ? Math.round(avgScore) : undefined} />
        </div>
      </div>
      <div className="context-strip"><div className="context-icon"><Icon name="route"/></div><div className="context-copy"><span className="eyebrow">SHIPMENT SCOPE</span><strong>{activeShipment ? routeName(activeShipment) : 'No shipment selected'}</strong><span>{activeShipment?.cargo_type || 'Select a shipment to view risk assessments.'}</span></div><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.cargo_type} · {shipment.origin} → {shipment.destination}</option>)}</select></div>
      {quotes.length === 0 ? <EmptyState title="No quotes to assess" description="Select a shipment that has stored quote records."/> : <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">QUOTE RISK REGISTER</span><h3>Risk assessments <span className="subtle-count">{quotes.length}</span></h3><p>Use Re-assess to recalculate against the current shipment's peer quotes.</p></div><button className="btn btn-secondary btn-sm" onClick={async () => { for (const quote of quotes) await handleAssess(quote); }}>Assess all quotes</button></div><div className="risk-record-list">{quotes.map((quote) => <div className="risk-record" key={quote.id}><div className="risk-score-ring" data-tone={riskTone(quote.assessment?.label)}><strong>{quote.assessment?.score ?? '—'}</strong><small>/100</small></div><div className="risk-record-main"><div className="risk-record-heading"><strong>{quote.provider_label}</strong><span className={`status-badge ${riskTone(quote.assessment?.label)}`}>{riskLabel(quote.assessment?.label)}</span></div><span className="table-secondary">{quote.reference} · {money(quote.total_amount, quote.currency)} · {quote.transit_days ? `${quote.transit_days} day transit` : 'Transit time not specified'}</span>{quote.assessment?.flags?.length ? <div className="flag-chips">{quote.assessment.flags.slice(0, 3).map((flag) => <span className={`flag-chip ${flag.severity.toLowerCase()}`} key={flag.code}>{flag.severity}: {flag.title}</span>)}</div> : <span className="table-secondary">{quote.assessment ? 'No rule flags were triggered.' : 'No stored assessment. Run the risk engine to evaluate this offer.'}</span>}</div><button className="btn btn-secondary btn-sm" onClick={() => void handleAssess(quote)} disabled={assessmentBusy === quote.id}>{assessmentBusy === quote.id ? 'Assessing…' : quote.assessment ? 'Re-assess' : 'Assess quote'}</button></div>)}</div></section>}
      <div className="source-note"><Icon name="shield" size={15}/> Model output is deterministic, versioned rule-based risk assessment. Do not describe it as a trained ML prediction unless a validated model is deployed.</div>
    </>;
  };

  const renderCopilot = () => <>
    <div className="copilot-intro"><div className="copilot-orb"><Icon name="spark" size={30}/></div><div><span className="eyebrow">FREIGHTPILOT INTELLIGENCE</span><h3>Make your next freight decision with evidence.</h3><p>Copilot compares selected quote records and returns advantages, concerns, missing information and follow-up questions.</p></div></div>
    <div className="copilot-layout"><section className="panel copilot-selection"><div className="panel-header"><div><span className="eyebrow">ANALYSIS INPUT</span><h3>Select quote offers</h3><p>{activeShipment ? routeName(activeShipment) : 'Choose a shipment first.'}</p></div><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.cargo_type}</option>)}</select></div>{quotes.length ? <div className="copilot-quote-options">{quotes.map((quote) => <label key={quote.id} className="copilot-quote-option"><input type="checkbox" checked={copilotQuoteIds.includes(quote.id)} onChange={(event) => setCopilotQuoteIds((ids) => event.target.checked ? [...ids, quote.id] : ids.filter((id) => id !== quote.id))}/><span className="option-carrier"><strong>{quote.provider_label}</strong><small>{quote.reference}</small></span><strong>{money(quote.total_amount, quote.currency)}</strong></label>)}</div> : <EmptyState title="No quote records" description="Create or select a shipment with quote offers before requesting analysis."/>}<button className="btn btn-primary btn-full" onClick={() => void handleRunCopilot()} disabled={copilotBusy || copilotQuoteIds.length === 0}><Icon name="spark" size={16}/>{copilotBusy ? 'Analyzing quote data…' : 'Analyze selected quotes'}</button><p className="fine-print">Analysis is read-only. Copilot cannot create shipments, commit payments or change operational status.</p></section>
      <section className="panel copilot-output"><div className="panel-header"><div><span className="eyebrow">DECISION BRIEF</span><h3>Procurement analysis</h3><p>Evidence-based summary from the backend.</p></div><div className="ai-tag"><Icon name="spark" size={13}/> AI / RULES</div></div>{!copilotResult ? <div className="copilot-placeholder"><div className="placeholder-art"><div/><div/><div/><Icon name="spark" size={23}/></div><strong>Your analysis will appear here</strong><span>Select one or more offers and run the copilot comparison.</span></div> : <div className="analysis-content"><div className="analysis-summary"><span className="eyebrow">SUMMARY</span><p>{copilotResult.summary}</p></div><div className="analysis-section"><h4>Quote-by-quote review</h4>{copilotResult.comparison.map((detail) => { const quote = quotes.find((item) => item.id === detail.quote_id); return <div className="comparison-detail" key={detail.quote_id}><strong>{quote?.provider_label || detail.quote_id}</strong><div className="pros-cons"><div><span className="positive-label">Advantages</span>{detail.advantages.length ? detail.advantages.map((text, i) => <p key={i}><Icon name="check" size={13}/>{text}</p>) : <p>None provided.</p>}</div><div><span className="negative-label">Concerns</span>{detail.concerns.length ? detail.concerns.map((text, i) => <p key={i}><Icon name="warning" size={13}/>{text}</p>) : <p>None provided.</p>}</div></div></div>; })}</div>{copilotResult.missing_information.length > 0 && <div className="analysis-section"><h4>Missing information</h4><ul>{copilotResult.missing_information.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}{copilotResult.next_questions.length > 0 && <div className="analysis-section"><h4>Questions to resolve</h4><ul>{copilotResult.next_questions.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}<p className="fine-print">{copilotResult.disclaimer}</p></div>}</section></div>
    <AiCopilotChat shipmentId={activeShipment?.id} role={currentUser?.role} />
  </>;

  const renderPayments = () => <>
    {selectedQuote ? <section className="checkout-panel"><div className="checkout-summary"><div><span className="eyebrow">SELECTED FREIGHT OFFER</span><h3>{selectedQuote.provider_label}</h3><p>{activeShipment ? routeName(activeShipment) : `Shipment ${selectedQuote.shipment_id}`}</p><span className="source-tag">{selectedQuote.source_kind}</span></div><div className="checkout-amount"><span>Quote total</span><strong>{money(selectedQuote.total_amount, selectedQuote.currency)}</strong><small>{selectedQuote.currency} · {selectedQuote.reference}</small></div></div><div className="checkout-bottom"><div className="checkout-information"><div className="checkout-info-row"><span>Base freight</span><strong>{money(selectedQuote.base_amount, selectedQuote.currency)}</strong></div><div className="checkout-info-row"><span>Surcharges</span><strong>{money(selectedQuote.surcharge_amount, selectedQuote.currency)}</strong></div><div className="checkout-info-row total"><span>Total payable</span><strong>{money(selectedQuote.total_amount, selectedQuote.currency)}</strong></div><p className="fine-print">The backend uses the saved quote total; the browser cannot override the payable amount. Synthetic quotes are for Sandbox demonstration only.</p></div><div className="checkout-action"><div className="checkout-lock"><Icon name="shield" size={17}/><div><strong>Secure PayPal Sandbox checkout</strong><span>Approval happens on PayPal; capture is verified by FastAPI.</span></div></div><PayPalCheckout key={`${selectedQuote.id}-${selectedQuote.currency}`} quote={selectedQuote} onSuccess={onPaymentSuccess} onStatus={onPaymentStatus}/><button className="text-button" onClick={() => setSelectedQuote(null)}>Clear selected quote</button></div></div></section> : <div className="payment-selection-banner"><div className="panel-icon"><Icon name="wallet"/></div><div><strong>No quote selected for checkout</strong><span>Choose a quote from Freight quotes and select “Continue to payment”.</span></div><button className="btn btn-secondary" onClick={() => setPage('quotes')}>Browse quotes <Icon name="arrow" size={15}/></button></div>}
    <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">TRANSACTION LEDGER</span><h3>Payment history <span className="subtle-count">{payments.length}</span></h3><p>Records are read from the payment tables for all visible shipments.</p></div><button className="btn btn-secondary btn-sm" onClick={() => void loadPayments(shipments)} disabled={paymentLoading}><Icon name="refresh" size={14}/>{paymentLoading ? 'Refreshing…' : 'Refresh'}</button></div>{paymentLoading ? <LoadingPanel label="Loading payment records…"/> : payments.length === 0 ? <EmptyState title="No payment transactions" description="A payment record appears here when a PayPal order has been created for a stored quote."/> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Transaction</th><th>Quote</th><th>Amount</th><th>Provider</th><th>Created</th><th>Status</th></tr></thead><tbody>{payments.map((payment) => <tr key={payment.payment_id}><td><strong className="mono">{payment.payment_id.slice(0, 12)}…</strong><span className="table-secondary">{payment.provider_order_id}</span></td><td className="mono">{payment.quote_id.slice(0, 14)}…</td><td><strong>{money(payment.amount, payment.currency)}</strong></td><td>PayPal {payment.provider.includes('sandbox') ? 'Sandbox' : ''}</td><td>{dateTime(payment.created_at)}</td><td><StatusBadge value={payment.status}/></td></tr>)}</tbody></table></div>}</section>
  </>;

  const renderAnalytics = () => {
    const now = new Date();
    const activityPoints = Array.from({ length: 6 }, (_, index) => {
      const month = new Date(now.getFullYear(), now.getMonth() - 5 + index, 1);
      const count = shipments.filter((shipment) => {
        const created = new Date(shipment.created_at);
        return !Number.isNaN(created.getTime()) && created.getFullYear() === month.getFullYear() && created.getMonth() === month.getMonth();
      }).length;
      return { label: new Intl.DateTimeFormat('en', { month: 'short' }).format(month), value: count };
    });
    const quoteCountsByCarrier = carrierPerformance.slice(0, 7).map((carrier) => ({ month: carrier.carrier.slice(0, 8), amount: carrier.quote_count }));
    return <>
    <div className="stats-grid analytics-stats"><StatCard label="Shipment volume" value={analytics?.shipment_count ?? 0} caption="Total stored requests" icon="shipments" tint="tint-coral"/><StatCard label="Quote coverage" value={totalQuoteCount} caption="Offers across visible shipments" icon="quotes" tint="tint-cream"/><StatCard label="Captured transactions" value={analytics?.captured_payments ?? 0} caption={`Of ${analytics?.payment_attempts ?? 0} attempts`} icon="payments" tint="tint-coral"/><StatCard label="Risk attention" value={analytics?.high_attention_quotes ?? 0} caption="Risk assessments scoring for review" icon="risk" tint="tint-coral"/></div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-header"><div><span className="eyebrow">OPERATIONAL MIX</span><h3>Shipment status breakdown</h3><p>Counts from the shipment table.</p></div></div><SvgDonutChart counts={analytics?.shipment_status_counts || {}} total={analytics?.shipment_count || 0}/></section><section className="panel"><div className="panel-header"><div><span className="eyebrow">FINANCIAL RECORDS</span><h3>Captured spend by currency</h3><p>Amounts are intentionally not summed across currencies.</p></div></div>{capturedSpend.length ? <div className="spend-list">{capturedSpend.map((spend) => <div className="spend-row" key={spend.currency}><div><span className="spend-currency">{spend.currency}</span><strong>{money(spend.amount, spend.currency)}</strong></div><span className="spend-caption">Verified captures</span></div>)}</div> : <div className="empty-inline"><strong>No captured spend</strong><span>Verified payment captures will be grouped here by currency.</span></div>}</section></div>
    <div className="dashboard-grid dashboard-grid-lower">
      <section className="panel">
        <div className="panel-header"><div><span className="eyebrow">VOLUME TREND</span><h3>Shipment creation by month</h3><p>Actual counts grouped by stored creation dates.</p></div></div>
        <SvgAreaChart points={activityPoints} />
      </section>
      <section className="panel">
        <div className="panel-header"><div><span className="eyebrow">CARRIER ACTIVITY</span><h3>Stored quote count</h3><p>Quote volumes by carrier; no cross-currency amounts are combined.</p></div></div>
        <SvgBarComparison items={quoteCountsByCarrier} />
      </section>
    </div>
    <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">CARRIER COMPARISON</span><h3>Quote activity by carrier</h3><p>Grouped from stored quotes. Synthetic demo offers may be included.</p></div></div><CarrierTable items={carrierPerformance}/></section>
    <div className="source-note"><Icon name="database" size={15}/> Data scope: {analytics?.data_scope || 'Unavailable'}. Analytics are calculated from persisted records; no cross-currency total is produced.</div>
  </>;
  };

  const renderSettings = () => <>
    <section className="panel account-verification-panel">
      <div className="panel-header">
        <div><span className="eyebrow">ACCOUNT SECURITY</span><h3>Phone verification</h3><p>Verify a mobile number for account recovery and SMS sign-in.</p></div>
        {currentUser && <StatusBadge value={currentUser.phone_verified ? 'VERIFIED' : 'NOT VERIFIED'}/>}
      </div>
      {currentUser ? <>
        <form className="account-phone-form" onSubmit={saveAccountPhone}>
          <label>Mobile number (international format)<input type="tel" value={accountPhone} onChange={(event) => setAccountPhone(event.target.value)} placeholder="+919876543210" pattern="\+[1-9]\d{7,14}" required readOnly={Boolean(currentUser.phone_verified)}/></label>
          {!currentUser.phone_verified && <button className="btn btn-secondary btn-sm" disabled={phoneSettingsBusy || !accountPhone.trim()}>{phoneSettingsBusy ? 'Saving…' : 'Save number'}</button>}
        </form>
        {currentUser.phone_number && !currentUser.phone_verified && <div className="phone-verification-actions">
          {!accountPhoneOtpSent ? <button className="btn btn-primary btn-sm" onClick={() => void sendAccountPhoneOtp()} disabled={phoneSettingsBusy}>{phoneSettingsBusy ? 'Sending…' : 'Send SMS verification code'}</button> :
            <form className="account-phone-otp-form" onSubmit={confirmAccountPhoneOtp}>
              <div id="recaptcha-container" style={{display: 'none'}} />
              <label>Six-digit verification code<input value={accountPhoneOtp} onChange={(event) => setAccountPhoneOtp(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" pattern="\d{6}" required placeholder="123456"/></label>
              <button className="btn btn-primary btn-sm" disabled={phoneSettingsBusy || accountPhoneOtp.length !== 6}>{phoneSettingsBusy ? 'Verifying…' : 'Verify phone'}</button>
              <button type="button" className="text-button" onClick={() => void sendAccountPhoneOtp()} disabled={phoneSettingsBusy}>Resend code</button>
            </form>}
        </div>}
        {currentUser.phone_verified && <p className="phone-verified-copy"><Icon name="check" size={15}/> Your mobile number is verified and cannot be changed from this screen.</p>}
        <p className="account-phone-help">Use E.164 format, including the country code. Codes expire after 10 minutes and are limited to five attempts. Production uses Firebase Phone Auth.</p>
        {phoneSettingsMessage && <div className="inline-alert phone-settings-message">{phoneSettingsMessage}</div>}
      </> : <div className="empty-inline"><strong>Sign in to manage account verification</strong><button className="text-button" onClick={() => openAuth('login')}>Open sign in</button></div>}
    </section>
    <section className="panel settings-panel"><div className="panel-header"><div><span className="eyebrow">SERVICE HEALTH</span><h3>Connected services</h3><p>Configuration visibility only; secrets are never shown in the browser.</p></div></div><div className="settings-list"><SettingRow icon="activity" title="FastAPI backend" detail={apiBaseUrl} value={health && ['healthy', 'ok', 'available'].includes(health.status.toLowerCase()) ? 'Connected' : 'Unavailable'} good={Boolean(health && ['healthy', 'ok', 'available'].includes(health.status.toLowerCase()))}/><SettingRow icon="database" title="Database" detail="PostgreSQL connection reported by backend" value={health && ['healthy', 'ok', 'available'].includes(health.status.toLowerCase()) ? 'Available' : 'Unknown'} good={Boolean(health && ['healthy', 'ok', 'available'].includes(health.status.toLowerCase()))}/><SettingRow icon="wallet" title="PayPal JavaScript SDK" detail="VITE_PAYPAL_CLIENT_ID" value={paypalClientId && !paypalClientId.toLowerCase().includes('replace') ? 'Client ID configured' : 'Not configured'} good={Boolean(paypalClientId && !paypalClientId.toLowerCase().includes('replace'))}/><SettingRow icon="spark" title="AI Copilot" detail="Provider and API key are configured on the backend" value="Backend-managed" good={null}/><SettingRow icon="truck" title="Live carrier integrations" detail={carrierCatalog?.note || 'Carrier adapter availability reported by backend.'} value={carrierCatalog?.live_integrations_available ? 'Available' : 'Not configured'} good={Boolean(carrierCatalog?.live_integrations_available)}/></div></section>
    <div className="settings-grid"><section className="panel"><div className="panel-header"><div><span className="eyebrow">APPLICATION MODE</span><h3>Environment</h3></div><span className="environment-pill"><span className="environment-dot"/>{health?.service === 'FreightPilot AI Backend' ? 'Production Ready' : 'Unknown'}</span></div><div className="setting-description"><p>Current backend mode is reported by <code>/health</code>. The demo environment should use PayPal Sandbox and clearly mark synthetic carrier data.</p><div className="detail-line"><span>API base URL</span><strong>{apiBaseUrl}</strong></div><div className="detail-line"><span>Signed-in account</span><strong>{currentUser?.email || 'Guest / demo'}</strong></div><div className="detail-line"><span>Data scope</span><strong>{analytics?.data_scope || 'Unavailable'}</strong></div></div></section><section className="panel"><div className="panel-header"><div><span className="eyebrow">DEMO CONTROLS</span><h3>Seed data</h3><p>Reset synthetic demo content for a fresh presentation.</p></div></div><div className="demo-control"><div className="demo-control-icon"><Icon name="refresh"/></div><div><strong>Restore demo dataset</strong><span>The backend prevents deleting a shipment with linked payment records.</span></div><button className="btn btn-secondary btn-sm" onClick={() => void handleReset()} disabled={resetting}>{resetting ? 'Resetting…' : 'Reset demo'}</button></div></section></div>
    <section className="panel"><div className="panel-header"><div><span className="eyebrow">CARRIER REGISTRY</span><h3>Available adapters</h3><p>These are backend adapter registrations, not a list of confirmed live shipping providers.</p></div></div>{carrierCatalog?.items.length ? <div className="adapter-grid">{carrierCatalog.items.map((item) => <div className="adapter-card" key={item.code}><div className="adapter-mark">{item.name.slice(0, 1)}</div><div><strong>{item.name}</strong><span>{item.code}</span></div><StatusBadge value={item.status === 'CONFIGURED' ? 'REGISTERED' : 'NOT CONFIGURED'}/></div>)}</div> : <div className="empty-inline"><strong>No adapter registered</strong><span>Configure a carrier connector in backend/app/services/carrier_service.py.</span></div>}</section>
    {currentUser && <>
      <section className="panel danger-zone-panel">
        <div className="panel-header">
          <div><span className="eyebrow danger-zone-label">DANGER ZONE</span><h3>Delete your account</h3><p>This action is irreversible. Your account will be permanently deleted after 30 days. During this period you can contact support to restore it.</p></div>
        </div>
        {!deleteAccountOpen ? (
          <button className="btn btn-danger" onClick={() => setDeleteAccountOpen(true)}>Delete account</button>
        ) : (
          <form className="danger-zone-form" onSubmit={async (e) => {
            e.preventDefault();
            if (deleteAccountConfirm !== 'DELETE') {
              setDeleteAccountError('Please type DELETE to confirm.');
              return;
            }
            setDeleteAccountBusy(true);
            setDeleteAccountError('');
            try {
              await deleteAccount(deleteAccountPassword, deleteAccountConfirm);
              setDeleteAccountBusy(false);
              clearAuthTokens();
              setCurrentUser(null);
              setPage('landing');
              showToast('Account deleted successfully. You can contact support within 30 days to restore it.');
            } catch (err) {
              setDeleteAccountError(err instanceof Error ? err.message : 'Failed to delete account. Please try again.');
              setDeleteAccountBusy(false);
            }
          }}>
            <div className="danger-zone-warning"><Icon name="warning" size={20}/><strong>Warning:</strong> This will permanently delete your account and all associated data.</div>
            <label>Type <strong>DELETE</strong> to confirm<input value={deleteAccountConfirm} onChange={(event) => setDeleteAccountConfirm(event.target.value)} placeholder="DELETE" required autoComplete="off"/></label>
            <label>Enter your password<input type="password" value={deleteAccountPassword} onChange={(event) => setDeleteAccountPassword(event.target.value)} required autoComplete="current-password" placeholder="Your current password"/></label>
            {deleteAccountError && <div className="inline-alert inline-alert-danger">{deleteAccountError}</div>}
            <div className="danger-zone-actions">
              <button type="button" className="btn btn-secondary" onClick={() => { setDeleteAccountOpen(false); setDeleteAccountConfirm(''); setDeleteAccountPassword(''); setDeleteAccountError(''); }}>Cancel</button>
              <button type="submit" className="btn btn-danger" disabled={deleteAccountBusy}>{deleteAccountBusy ? 'Deleting…' : 'Delete my account permanently'}</button>
            </div>
          </form>
        )}
      </section>
    </>}
  </>;

  const renderCarriers = () => <>
    <div className="stats-grid">
      <StatCard label="Total Carriers" value={carrierPerformance.length || 0} caption="In quote database" icon="truck" tint="tint-coral"/>
      <StatCard label="Quote Activity" value={carrierPerformance.reduce((s, c) => s + (c.quote_count || 0), 0)} caption="Stored carrier quotes" icon="quotes" tint="tint-cream"/>
      <StatCard label="Configured Adapters" value={carrierCatalog?.items.filter(i => i.status === 'CONFIGURED').length || 0} caption="Live API connections" icon="activity" tint="tint-coral"/>
      <StatCard label="Avg. Transit Time" value={(() => { const values = carrierPerformance.map((c) => c.average_transit_days).filter((value): value is number => value != null && Number.isFinite(value)); return values.length ? `${(values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)} days` : '—'; })()} caption="For quotes with transit details" icon="clock" tint="tint-cream"/>
    </div>
    <section className="panel table-panel">
      <div className="panel-header"><div><span className="eyebrow">CARRIER REGISTRY</span><h3>Carrier catalog <span className="subtle-count">{carrierCatalog?.items.length ?? 0}</span></h3><p>{carrierCatalog?.note || 'Backend-registered carrier adapters.'}</p></div></div>
      {carrierCatalog?.items.length ? <div className="adapter-grid">{carrierCatalog.items.map((item) => <div className="adapter-card" key={item.code}><div className="adapter-mark">{item.name.slice(0, 1)}</div><div><strong>{item.name}</strong><span>{item.code}</span></div><StatusBadge value={item.status === 'CONFIGURED' ? 'REGISTERED' : 'NOT CONFIGURED'}/></div>)}</div> : <EmptyState title="No adapter registered" description="Configure a carrier connector in backend/app/services/carrier_service.py."/>}
    </section>
    <section className="panel table-panel">
      <div className="panel-header"><div><span className="eyebrow">CARRIER PERFORMANCE</span><h3>Quote activity by carrier</h3><p>Grouped from stored quotes.</p></div></div>
      <CarrierTable items={carrierPerformance}/>
    </section>
  </>;

  const renderDocuments = () => <>
    <section className="panel">
      <div className="panel-header"><div><span className="eyebrow">DOCUMENT CENTER</span><h3>Shipment documents</h3><p>Bills of lading, customs declarations and freight paperwork are managed per shipment.</p></div></div>
      <div className="empty-panel">
        <div className="empty-symbol"><Icon name="file" size={28}/></div>
        <h3>Document management</h3>
        <p>Select a shipment from the Shipments page to view or attach its associated documents. Bills of lading, certificates of origin, and customs manifests are linked at the shipment level.</p>
        <button className="btn btn-primary" onClick={() => setPage('shipments')}><Icon name="shipments" size={16}/> Go to Shipments</button>
      </div>
    </section>
    {shipments.length > 0 && <section className="panel table-panel">
      <div className="panel-header"><div><span className="eyebrow">SHIPMENT INDEX</span><h3>Shipments with documents</h3><p>{shipments.length} shipment records in the database.</p></div></div>
      <div className="table-wrap"><table className="data-table"><thead><tr><th>Shipment</th><th>Route</th><th>Status</th><th>Documents</th></tr></thead><tbody>{shipments.slice(0, 8).map((s) => <tr key={s.id} className="clickable-row" onClick={() => { void selectShipment(s.id); setPage('shipments'); }}><td><strong>{s.cargo_type}</strong><span className="table-secondary mono">{s.id.slice(0, 10)}…</span></td><td>{s.origin} → {s.destination}</td><td><StatusBadge value={s.status}/></td><td><span className="count-pill">View</span></td></tr>)}</tbody></table></div>
    </section>}
  </>;

  const renderNotFound = () => (
    <section className="panel" style={{textAlign: 'center', padding: '60px 24px'}}>
      <div className="empty-symbol" style={{margin: '0 auto 20px', width: 56, height: 56}}><Icon name="warning" size={32}/></div>
      <span className="eyebrow">404 — ROUTE NOT FOUND</span>
      <h2 style={{fontSize: '28px', marginTop: 8, marginBottom: 12}}>The requested page does not exist</h2>
      <p style={{color: 'var(--text-secondary)', maxWidth: 480, margin: '0 auto 24px'}}>
        The navigation link or URL anchor you followed is not recognized by the FreightPilot workspace router.
      </p>
      <button className="btn btn-primary" onClick={() => setPage('overview')}>
        <Icon name="overview" size={16}/> Return to Dashboard
      </button>
    </section>
  );

  const renderPage = () => {
    if (page === 'landing') return renderLanding();
    switch (page) {
      case 'overview': return renderOverview();
      case 'shipments': return renderShipments();
      case 'quotes': return renderQuotes();
      case 'risk': return renderRisk();
      case 'copilot': return renderCopilot();
      case 'payments': return renderPayments();
      case 'analytics': return renderAnalytics();
      case 'carriers': return renderCarriers();
      case 'documents': return renderDocuments();
      case 'settings': return renderSettings();
      default: return renderNotFound();
    }
  };

  if (page === 'landing') {
    return (
      <div className="public-website-shell">
        {renderLanding()}
        {authOpen && <AuthModal onClose={closeAuth} onAuthenticated={handleAuthSuccess} initialMode={authInitialMode} resetToken={resetPasswordToken}/>}
        {toast && <div className="toast"><span className="toast-check"><Icon name="check" size={15}/></span>{toast}<button onClick={() => setToast(null)}><Icon name="close" size={14}/></button></div>}
        <NewShipmentModal isOpen={newShipmentOpen} onClose={() => setNewShipmentOpen(false)} onSubmit={handleCreateShipment}/>
      </div>
    );
  }

  return (
    <>
      <FreightWorkspaceShell
        page={page as WorkspacePage}
        title={currentPage.title}
        subtitle={currentPage.subtitle}
        currentUser={currentUser}
        notifications={notifications}
        shipments={shipments}
        activeShipmentId={activeShipment?.id}
        backendOnline={Boolean(health && ['ok', 'healthy', 'available'].includes(health.status.toLowerCase()))}
        error={pageError}
        onNavigate={(nextPage) => setPage(nextPage)}
        onSelectShipment={(id) => { void selectShipment(id); }}
        onSignIn={() => openAuth('login')}
        onSignOut={() => { clearAuthTokens(); setCurrentUser(null); setPage('landing'); showToast('Signed out.'); void loadPortfolio(); }}
        onPublicSite={() => setPage('landing')}
        onNewShipment={() => setNewShipmentOpen(true)}
        onSearchChange={setSearch}
        onRetry={() => void loadPortfolio(activeShipment?.id)}
        onDismissError={() => setPageError(null)}
      >
        {renderPage()}
      </FreightWorkspaceShell>
      {toast && <div className="toast"><span className="toast-check"><Icon name="check" size={15}/></span>{toast}<button onClick={() => setToast(null)}><Icon name="close" size={14}/></button></div>}
      <NewShipmentModal isOpen={newShipmentOpen} onClose={() => setNewShipmentOpen(false)} onSubmit={handleCreateShipment}/>
      {authOpen && <AuthModal onClose={closeAuth} onAuthenticated={handleAuthSuccess} initialMode={authInitialMode} resetToken={resetPasswordToken}/>}
    </>
  );
}

function Fact({ label, value }: { label: string; value: string }): React.ReactElement { return <div className="shipment-fact"><span>{label}</span><strong>{value}</strong></div>; }
function LoadingPanel({ label }: { label: string }): React.ReactElement { return <div className="panel loading-panel"><span className="spinner"/><strong>{label}</strong></div>; }

function CarrierTable({ items }: { items: CarrierPerformance[] }): React.ReactElement {
  if (!items.length) return <EmptyState title="No carrier data available" description="Carrier performance is calculated from quote history. The backend currently has no live carrier connector configured."/>;
  return <div className="table-wrap"><table className="data-table"><thead><tr><th>Carrier</th><th>Currency</th><th>Quotes</th><th>Average quote</th><th>Lowest quote</th><th>Avg. transit</th><th>Provenance</th></tr></thead><tbody>{items.map((item) => <tr key={`${item.carrier}-${item.currency}`}><td><strong>{item.carrier}</strong></td><td>{item.currency}</td><td>{item.quote_count}</td><td>{money(item.average_quote, item.currency)}</td><td>{money(item.lowest_quote, item.currency)}</td><td>{item.average_transit_days == null ? '—' : `${item.average_transit_days} days`}</td><td><span className="data-source">Stored quotes</span></td></tr>)}</tbody></table></div>;
}

function QuoteCard({ quote, shipment, index, selected, onAssess, assessing, onPay, onInspect }: { quote: Quote; shipment: Shipment | null; index: number; selected: boolean; onAssess: () => void; assessing: boolean; onPay: () => void; onInspect: () => void }): React.ReactElement {
  const assessment = quote.assessment;
  const flags = assessment?.flags || [];
  const expired = Boolean(quote.validity_until && new Date(quote.validity_until).getTime() < Date.now());
  return <article className={`quote-card-modern ${selected ? 'chosen' : ''}`}><div className="quote-card-top"><div className="carrier-brand-badge">{quote.provider_label.slice(0, 1).toUpperCase()}</div><div className="quote-carrier-copy"><div className="carrier-title-row"><h3>{quote.provider_label}</h3>{index === 0 && <span className="best-value-tag">LOWEST PRICE</span>}</div><span>Reference {quote.reference}</span></div><div className="quote-price-block"><strong>{money(quote.total_amount, quote.currency)}</strong><span>Quoted total</span></div></div><div className="quote-metrics"><div><span>Base freight</span><strong>{money(quote.base_amount, quote.currency)}</strong></div><div><span>Surcharges</span><strong>{money(quote.surcharge_amount, quote.currency)}</strong></div><div><span>Transit time</span><strong>{quote.transit_days ? `${quote.transit_days} days` : 'Not supplied'}</strong></div><div><span>Vessel / service</span><strong>{quote.vessel_class || 'Not supplied'}</strong></div></div><div className="quote-card-bottom"><div className="quote-provenance"><span className="data-source">{quote.source_kind.replace(/_/g, ' ')}</span>{expired && <span className="status-badge red">EXPIRED</span>}{assessment ? <span className={`status-badge ${riskTone(assessment.label)}`}>Risk {assessment.score}/100 · {riskLabel(assessment.label)}</span> : <span className="status-badge neutral">Risk not assessed</span>}{quote.benchmark_variance_pct != null && <span className="benchmark-variance">{quote.benchmark_variance_pct > 0 ? '+' : ''}{quote.benchmark_variance_pct}% vs baseline</span>}</div><div className="quote-actions-modern"><button className="btn btn-ghost btn-sm" onClick={onInspect}>Select quote</button><button className="btn btn-secondary btn-sm" onClick={onAssess} disabled={assessing}>{assessing ? 'Assessing…' : assessment ? 'Re-assess risk' : 'Assess risk'}</button><button className="btn btn-primary btn-sm" onClick={onPay} disabled={expired || (shipment?.status === 'CANCELLED')}>Continue to payment <Icon name="arrow" size={14}/></button></div></div>{flags.length > 0 && <div className="quote-flags-preview">{flags.slice(0, 2).map((flag) => <span className={`flag-chip ${flag.severity.toLowerCase()}`} key={flag.code}>{flag.severity}: {flag.title}</span>)}</div>}</article>;
}

function SettingRow({ icon, title, detail, value, good }: { icon: IconName; title: string; detail: string; value: string; good: boolean | null }): React.ReactElement {
  return <div className="setting-row"><div className="setting-icon"><Icon name={icon}/></div><div className="setting-copy"><strong>{title}</strong><span>{detail}</span></div><span className={`setting-value ${good === true ? 'good' : good === false ? 'bad' : ''}`}><i/>{value}</span></div>;
}
