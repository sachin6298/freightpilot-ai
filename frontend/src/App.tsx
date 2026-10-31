import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { NewShipmentModal } from './components/NewShipmentModal';
import { PayPalCheckout } from './components/PayPalCheckout';
import {
  addTrackingEvent, apiBaseUrl, assessQuote, cancelShipment, compareQuotesWithCopilot,
  createShipment, fetchAnalyticsOverview, fetchCarrierCatalog, fetchCarrierPerformance,
  fetchCurrentUser, fetchHealth, fetchNotifications, fetchShipmentPayments,
  fetchShipmentQuotes, fetchShipmentEstimate, fetchShipments, fetchTracking,
  getAuthToken, login, markNotificationRead, paypalClientId, refreshCarrierQuotes,
  register, resetDemoData, setAuthToken,
} from './api';
import {
  AnalyticsOverview, CarrierCatalog, CarrierPerformance, CopilotResult, NotificationItem,
  PaymentRecord, Quote, RateEstimate, Shipment, ShipmentCreatePayload, TrackingEvent, UserProfile,
} from './types';

type Page = 'overview' | 'shipments' | 'quotes' | 'risk' | 'copilot' | 'payments' | 'analytics' | 'settings';
type IconName = 'overview' | 'shipments' | 'quotes' | 'risk' | 'copilot' | 'payments' | 'analytics' | 'settings' | 'bell' | 'plus' | 'search' | 'arrow' | 'refresh' | 'clock' | 'check' | 'warning' | 'external' | 'menu' | 'logout' | 'shield' | 'truck' | 'wallet' | 'spark' | 'calendar' | 'filter' | 'close' | 'route' | 'file' | 'database' | 'activity' | 'chevron';

const NAV_ITEMS: Array<{ id: Page; label: string; icon: IconName; group: string }> = [
  { id: 'overview', label: 'Overview', icon: 'overview', group: 'WORKSPACE' },
  { id: 'shipments', label: 'Shipments', icon: 'shipments', group: 'WORKSPACE' },
  { id: 'quotes', label: 'Freight quotes', icon: 'quotes', group: 'WORKSPACE' },
  { id: 'risk', label: 'Risk manager', icon: 'risk', group: 'INTELLIGENCE' },
  { id: 'copilot', label: 'AI copilot', icon: 'copilot', group: 'INTELLIGENCE' },
  { id: 'payments', label: 'Payments', icon: 'payments', group: 'FINANCE' },
  { id: 'analytics', label: 'Analytics', icon: 'analytics', group: 'FINANCE' },
  { id: 'settings', label: 'Settings', icon: 'settings', group: 'SYSTEM' },
];

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
  if (['DELIVERED', 'PAID', 'CAPTURED', 'COMPLETED'].includes(normalized)) return 'green';
  if (['IN_TRANSIT', 'BOOKED', 'QUOTED', 'APPROVED'].includes(normalized)) return 'blue';
  if (['EXCEPTION', 'FAILED', 'REVIEW_REQUIRED', 'CANCELLED', 'REFUNDED'].includes(normalized)) return 'red';
  return 'amber';
}
function riskTone(label?: string): string {
  if (label === 'LOWER_CONCERN') return 'green';
  if (label === 'HIGH_ATTENTION') return 'red';
  if (label === 'REVIEW') return 'amber';
  return 'blue';
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

function AuthModal({ onClose, onAuthenticated }: { onClose: () => void; onAuthenticated: (user: UserProfile, token: string) => void }): React.ReactElement {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null);
    try {
      const response = mode === 'login' ? await login(email, password) : await register(email, password);
      onAuthenticated(response.user, response.access_token);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Authentication failed.'); }
    finally { setBusy(false); }
  };
  return <div className="modal-backdrop" onMouseDown={onClose}><div className="modal-card auth-card" onMouseDown={(event) => event.stopPropagation()}><div className="modal-head"><div><span className="eyebrow">FREIGHTPILOT ACCOUNT</span><h3>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h3><p>Sign in to keep shipment activity tied to your account.</p></div><button className="icon-button" onClick={onClose} aria-label="Close"><Icon name="close"/></button></div><form onSubmit={submit} className="form-stack"><label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" placeholder="name@company.com"/></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={mode === 'register' ? 10 : 1} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder={mode === 'register' ? 'At least 10 characters' : 'Your password'}/></label>{error && <div className="inline-alert inline-alert-danger">{error}</div>}<button className="btn btn-primary btn-full" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button><button type="button" className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null); }}>{mode === 'login' ? 'New to FreightPilot? Create an account' : 'Already have an account? Sign in'}</button></form><p className="fine-print">Local demo access remains available without signing in while backend AUTH_REQUIRED=false.</p></div></div>;
}

export default function App(): React.ReactElement {
  const [page, setPage] = useState<Page>('overview');
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
  const [authOpen, setAuthOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [health, setHealth] = useState<{ status: string; app: string; mode: string; database: string } | null>(null);
  const [search, setSearch] = useState('');
  const [trackingStatus, setTrackingStatus] = useState('IN_TRANSIT');
  const [trackingLocation, setTrackingLocation] = useState('');
  const [trackingDescription, setTrackingDescription] = useState('Shipment status updated by operations.');
  const [trackingBusy, setTrackingBusy] = useState(false);
  const [assessmentBusy, setAssessmentBusy] = useState<string | null>(null);
  const [carrierBusy, setCarrierBusy] = useState(false);

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

  useEffect(() => { void loadPortfolio(); }, []); // initial API hydration
  useEffect(() => {
    if (page === 'payments' && shipments.length) void loadPayments(shipments);
  }, [page, shipments, loadPayments]);
  useEffect(() => {
    const token = getAuthToken();
    if (!token) return;
    fetchCurrentUser().then(setCurrentUser).catch(() => { setAuthToken(null); setCurrentUser(null); });
  }, []);

  const unreadCount = notifications.filter((notification) => !notification.read_at).length;
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

  const handleAuthSuccess = (user: UserProfile, token: string) => {
    setAuthToken(token); setCurrentUser(user); setAuthOpen(false); showToast(`Signed in as ${user.email}.`); void loadPortfolio();
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
    overview: { title: 'Overview', subtitle: 'A live view of your freight procurement operations.' },
    shipments: { title: 'Shipments', subtitle: 'Manage freight requests, operational status and tracking history.' },
    quotes: { title: 'Freight quotes', subtitle: 'Compare carrier offers using normalized cost, transit and risk data.' },
    risk: { title: 'Risk manager', subtitle: 'Review explainable quote-level signals before committing spend.' },
    copilot: { title: 'AI copilot', subtitle: 'Use shipment and quote records to generate a structured procurement review.' },
    payments: { title: 'Payments', subtitle: 'Review payment activity and complete Sandbox checkout for a selected quote.' },
    analytics: { title: 'Analytics', subtitle: 'Understand shipment volume, quote coverage and captured spend by currency.' },
    settings: { title: 'Settings', subtitle: 'Review connected services, environment configuration and account access.' },
  };

  const currentPage = pageMeta[page];
  const topHeader = <header className="topbar"><div className="topbar-mobile-brand"><div className="brand-mark">FP</div><span>FreightPilot <b>AI</b></span></div><div className="topbar-breadcrumb"><span>Workspace</span><Icon name="chevron" size={14}/><strong>{currentPage.title}</strong></div><div className="topbar-actions"><div className="environment-pill"><span className="environment-dot"/> {health?.mode === 'production' ? 'LIVE ENVIRONMENT' : 'SANDBOX DEMO'}</div><div className="notification-anchor"><button className={`icon-button topbar-icon ${showNotifications ? 'active' : ''}`} onClick={() => setShowNotifications(!showNotifications)} aria-label="Notifications"><Icon name="bell"/><span className="notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span></button>{showNotifications && <div className="notification-popover"><div className="popover-title"><strong>Notifications</strong><span>{unreadCount} unread</span></div>{notifications.length === 0 ? <p className="popover-empty">No notifications yet.</p> : notifications.slice(0, 6).map((item) => <button className={`notification-row ${item.read_at ? 'read' : ''}`} key={item.id} onClick={async () => { await markNotificationRead(item.id); setNotifications((rows) => rows.map((row) => row.id === item.id ? { ...row, read_at: new Date().toISOString() } : row)); if (item.shipment_id) { const target = shipments.find((shipment) => shipment.id === item.shipment_id); if (target) { await selectShipment(target.id); setPage('shipments'); } } }}><strong>{item.title}</strong><span>{item.message}</span><small>{dateTime(item.created_at)}</small></button>)}</div>}</div><button className="profile-button" onClick={() => { if (currentUser) { setAuthToken(null); setCurrentUser(null); showToast('Signed out.'); void loadPortfolio(); } else { setAuthOpen(true); } }}><span className="avatar">{currentUser ? currentUser.email.slice(0, 1).toUpperCase() : 'G'}</span><span className="profile-copy"><b>{currentUser ? currentUser.email.split('@')[0] : 'Guest user'}</b><small>{currentUser ? currentUser.role : 'Demo access'}</small></span><Icon name="chevron" size={14}/></button></div></header>;

  const renderOverview = () => <>
    <div className="welcome-row"><div><div className="eyebrow">OPERATIONS SNAPSHOT · {new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()).toUpperCase()}</div><h2>Good operations start with clear decisions.</h2><p>Monitor your shipment portfolio, compare freight offers and control procurement risk.</p></div><button className="btn btn-primary" onClick={() => setNewShipmentOpen(true)}><Icon name="plus" size={17}/> New shipment</button></div>
    <div className="stats-grid">
      <StatCard label="Total shipments" value={analytics?.shipment_count ?? shipments.length} caption={`${analytics?.delivered_shipments ?? 0} delivered`} icon="shipments" tint="tint-blue"/>
      <StatCard label="Active shipments" value={analytics?.active_shipments ?? shipments.filter((item) => !['DELIVERED', 'CANCELLED'].includes(item.status)).length} caption="Across current portfolio" icon="truck" tint="tint-purple"/>
      <StatCard label="Quotes received" value={totalQuoteCount} caption="Stored carrier offers" icon="quotes" tint="tint-teal"/>
      <StatCard label="High-attention quotes" value={analytics?.high_attention_quotes ?? 0} caption="Require human review" icon="risk" tint="tint-amber"/>
    </div>
    <div className="dashboard-grid">
      <section className="panel panel-main"><div className="panel-header"><div><span className="eyebrow">PORTFOLIO</span><h3>Recent shipments</h3><p>Latest records stored in your database.</p></div><button className="link-button" onClick={() => setPage('shipments')}>View all <Icon name="arrow" size={15}/></button></div>
        {shipments.length === 0 ? <EmptyState title="No shipments yet" description="Create a shipment request to start comparing freight offers." action={<button className="btn btn-primary" onClick={() => setNewShipmentOpen(true)}>Create shipment</button>}/> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Shipment / route</th><th>Ready date</th><th>Quotes</th><th>Status</th><th/></tr></thead><tbody>{shipments.slice(0, 6).map((shipment) => <tr key={shipment.id} onClick={() => { void selectShipment(shipment.id); setPage('shipments'); }} className="clickable-row"><td><strong>{shipment.cargo_type}</strong><span className="table-secondary">{shipment.origin} <span className="route-arrow">→</span> {shipment.destination}</span></td><td>{shortDate(shipment.ready_date)}</td><td><span className="count-pill">{shipment.quotes_count ?? '—'}</span></td><td><StatusBadge value={shipment.status}/></td><td><Icon name="chevron" size={16}/></td></tr>)}</tbody></table></div>}
      </section>
      <section className="panel"><div className="panel-header"><div><span className="eyebrow">PAYMENT POSITION</span><h3>Captured spend</h3><p>Verified captured payments only.</p></div><div className="panel-icon"><Icon name="wallet"/></div></div>
        {capturedSpend.length ? <div className="spend-list">{capturedSpend.map((spend) => <div className="spend-row" key={spend.currency}><div><span className="spend-currency">{spend.currency}</span><strong>{money(spend.amount, spend.currency)}</strong></div><span className="spend-caption">Captured</span></div>)}</div> : <div className="empty-inline"><div className="empty-icon-soft"><Icon name="wallet"/></div><strong>No captured spend</strong><span>Payments will appear here after PayPal confirms a capture.</span></div>}
        <div className="panel-divider"/><div className="mini-metric-row"><div><span>Payment attempts</span><strong>{analytics?.payment_attempts ?? 0}</strong></div><div><span>Captured</span><strong>{analytics?.captured_payments ?? 0}</strong></div></div>
      </section>
    </div>
    <div className="dashboard-grid dashboard-grid-lower"><section className="panel"><div className="panel-header"><div><span className="eyebrow">SHIPMENT PIPELINE</span><h3>Status distribution</h3><p>Current database status by shipment.</p></div></div><StatusDistribution counts={analytics?.shipment_status_counts || {}} total={analytics?.shipment_count || 0}/></section>
      <section className="panel"><div className="panel-header"><div><span className="eyebrow">CARRIER MARKETPLACE</span><h3>Carrier quote activity</h3><p>Average quote amounts grouped by currency.</p></div><button className="link-button" onClick={() => setPage('analytics')}>Details <Icon name="arrow" size={15}/></button></div><CarrierPreview items={carrierPerformance.slice(0, 4)}/></section></div>
    <div className="source-note"><Icon name="shield" size={15}/> Data on this dashboard is read from the backend database. Synthetic demo quotes are labeled at quote level and are not live carrier offers.</div>
  </>;

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
    return <>
      <div className="risk-hero"><div className="risk-hero-icon"><Icon name="shield" size={26}/></div><div><span className="eyebrow">EXPLAINABLE RISK ENGINE</span><h3>Evaluate the offer, not just the price.</h3><p>Assessments are generated by the backend using quote terms, price benchmarks and shipment constraints. They are decision support—not a carrier credit rating.</p></div><div className="risk-hero-metrics"><div><strong>{highRisk.length}</strong><span>Review / high attention</span></div><div><strong>{unassessed.length}</strong><span>Not assessed</span></div></div></div>
      <div className="context-strip"><div className="context-icon"><Icon name="route"/></div><div className="context-copy"><span className="eyebrow">SHIPMENT SCOPE</span><strong>{activeShipment ? routeName(activeShipment) : 'No shipment selected'}</strong><span>{activeShipment?.cargo_type || 'Select a shipment to view risk assessments.'}</span></div><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.cargo_type} · {shipment.origin} → {shipment.destination}</option>)}</select></div>
      {quotes.length === 0 ? <EmptyState title="No quotes to assess" description="Select a shipment that has stored quote records."/> : <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">QUOTE RISK REGISTER</span><h3>Risk assessments <span className="subtle-count">{quotes.length}</span></h3><p>Use Re-assess to recalculate against the current shipment's peer quotes.</p></div><button className="btn btn-secondary btn-sm" onClick={async () => { for (const quote of quotes) await handleAssess(quote); }}>Assess all quotes</button></div><div className="risk-record-list">{quotes.map((quote) => <div className="risk-record" key={quote.id}><div className="risk-score-ring" data-tone={riskTone(quote.assessment?.label)}><strong>{quote.assessment?.score ?? '—'}</strong><small>/100</small></div><div className="risk-record-main"><div className="risk-record-heading"><strong>{quote.provider_label}</strong><span className={`status-badge ${riskTone(quote.assessment?.label)}`}>{riskLabel(quote.assessment?.label)}</span></div><span className="table-secondary">{quote.reference} · {money(quote.total_amount, quote.currency)} · {quote.transit_days ? `${quote.transit_days} day transit` : 'Transit time not specified'}</span>{quote.assessment?.flags?.length ? <div className="flag-chips">{quote.assessment.flags.slice(0, 3).map((flag) => <span className={`flag-chip ${flag.severity.toLowerCase()}`} key={flag.code}>{flag.severity}: {flag.title}</span>)}</div> : <span className="table-secondary">{quote.assessment ? 'No rule flags were triggered.' : 'No stored assessment. Run the risk engine to evaluate this offer.'}</span>}</div><button className="btn btn-secondary btn-sm" onClick={() => void handleAssess(quote)} disabled={assessmentBusy === quote.id}>{assessmentBusy === quote.id ? 'Assessing…' : quote.assessment ? 'Re-assess' : 'Assess quote'}</button></div>)}</div></section>}
      <div className="source-note"><Icon name="shield" size={15}/> Model output is deterministic, versioned rule-based risk assessment. Do not describe it as a trained ML prediction unless a validated model is deployed.</div>
    </>;
  };

  const renderCopilot = () => <>
    <div className="copilot-intro"><div className="copilot-orb"><Icon name="spark" size={30}/></div><div><span className="eyebrow">FREIGHTPILOT INTELLIGENCE</span><h3>Make your next freight decision with evidence.</h3><p>Copilot compares selected quote records and returns advantages, concerns, missing information and follow-up questions.</p></div></div>
    <div className="copilot-layout"><section className="panel copilot-selection"><div className="panel-header"><div><span className="eyebrow">ANALYSIS INPUT</span><h3>Select quote offers</h3><p>{activeShipment ? routeName(activeShipment) : 'Choose a shipment first.'}</p></div><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.cargo_type}</option>)}</select></div>{quotes.length ? <div className="copilot-quote-options">{quotes.map((quote) => <label key={quote.id} className="copilot-quote-option"><input type="checkbox" checked={copilotQuoteIds.includes(quote.id)} onChange={(event) => setCopilotQuoteIds((ids) => event.target.checked ? [...ids, quote.id] : ids.filter((id) => id !== quote.id))}/><span className="option-carrier"><strong>{quote.provider_label}</strong><small>{quote.reference}</small></span><strong>{money(quote.total_amount, quote.currency)}</strong></label>)}</div> : <EmptyState title="No quote records" description="Create or select a shipment with quote offers before requesting analysis."/>}<button className="btn btn-primary btn-full" onClick={() => void handleRunCopilot()} disabled={copilotBusy || copilotQuoteIds.length === 0}><Icon name="spark" size={16}/>{copilotBusy ? 'Analyzing quote data…' : 'Analyze selected quotes'}</button><p className="fine-print">Analysis is read-only. Copilot cannot create shipments, commit payments or change operational status.</p></section>
      <section className="panel copilot-output"><div className="panel-header"><div><span className="eyebrow">DECISION BRIEF</span><h3>Procurement analysis</h3><p>Evidence-based summary from the backend.</p></div><div className="ai-tag"><Icon name="spark" size={13}/> AI / RULES</div></div>{!copilotResult ? <div className="copilot-placeholder"><div className="placeholder-art"><div/><div/><div/><Icon name="spark" size={23}/></div><strong>Your analysis will appear here</strong><span>Select one or more offers and run the copilot comparison.</span></div> : <div className="analysis-content"><div className="analysis-summary"><span className="eyebrow">SUMMARY</span><p>{copilotResult.summary}</p></div><div className="analysis-section"><h4>Quote-by-quote review</h4>{copilotResult.comparison.map((detail) => { const quote = quotes.find((item) => item.id === detail.quote_id); return <div className="comparison-detail" key={detail.quote_id}><strong>{quote?.provider_label || detail.quote_id}</strong><div className="pros-cons"><div><span className="positive-label">Advantages</span>{detail.advantages.length ? detail.advantages.map((text, i) => <p key={i}><Icon name="check" size={13}/>{text}</p>) : <p>None provided.</p>}</div><div><span className="negative-label">Concerns</span>{detail.concerns.length ? detail.concerns.map((text, i) => <p key={i}><Icon name="warning" size={13}/>{text}</p>) : <p>None provided.</p>}</div></div></div>; })}</div>{copilotResult.missing_information.length > 0 && <div className="analysis-section"><h4>Missing information</h4><ul>{copilotResult.missing_information.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}{copilotResult.next_questions.length > 0 && <div className="analysis-section"><h4>Questions to resolve</h4><ul>{copilotResult.next_questions.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}<p className="fine-print">{copilotResult.disclaimer}</p></div>}</section></div>
  </>;

  const renderPayments = () => <>
    {selectedQuote ? <section className="checkout-panel"><div className="checkout-summary"><div><span className="eyebrow">SELECTED FREIGHT OFFER</span><h3>{selectedQuote.provider_label}</h3><p>{activeShipment ? routeName(activeShipment) : `Shipment ${selectedQuote.shipment_id}`}</p><span className="source-tag">{selectedQuote.source_kind}</span></div><div className="checkout-amount"><span>Quote total</span><strong>{money(selectedQuote.total_amount, selectedQuote.currency)}</strong><small>{selectedQuote.currency} · {selectedQuote.reference}</small></div></div><div className="checkout-bottom"><div className="checkout-information"><div className="checkout-info-row"><span>Base freight</span><strong>{money(selectedQuote.base_amount, selectedQuote.currency)}</strong></div><div className="checkout-info-row"><span>Surcharges</span><strong>{money(selectedQuote.surcharge_amount, selectedQuote.currency)}</strong></div><div className="checkout-info-row total"><span>Total payable</span><strong>{money(selectedQuote.total_amount, selectedQuote.currency)}</strong></div><p className="fine-print">The backend uses the saved quote total; the browser cannot override the payable amount. Synthetic quotes are for Sandbox demonstration only.</p></div><div className="checkout-action"><div className="checkout-lock"><Icon name="shield" size={17}/><div><strong>Secure PayPal Sandbox checkout</strong><span>Approval happens on PayPal; capture is verified by FastAPI.</span></div></div><PayPalCheckout key={`${selectedQuote.id}-${selectedQuote.currency}`} quote={selectedQuote} onSuccess={onPaymentSuccess} onStatus={onPaymentStatus}/><button className="text-button" onClick={() => setSelectedQuote(null)}>Clear selected quote</button></div></div></section> : <div className="payment-selection-banner"><div className="panel-icon"><Icon name="wallet"/></div><div><strong>No quote selected for checkout</strong><span>Choose a quote from Freight quotes and select “Continue to payment”.</span></div><button className="btn btn-secondary" onClick={() => setPage('quotes')}>Browse quotes <Icon name="arrow" size={15}/></button></div>}
    <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">TRANSACTION LEDGER</span><h3>Payment history <span className="subtle-count">{payments.length}</span></h3><p>Records are read from the payment tables for all visible shipments.</p></div><button className="btn btn-secondary btn-sm" onClick={() => void loadPayments(shipments)} disabled={paymentLoading}><Icon name="refresh" size={14}/>{paymentLoading ? 'Refreshing…' : 'Refresh'}</button></div>{paymentLoading ? <LoadingPanel label="Loading payment records…"/> : payments.length === 0 ? <EmptyState title="No payment transactions" description="A payment record appears here when a PayPal order has been created for a stored quote."/> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Transaction</th><th>Quote</th><th>Amount</th><th>Provider</th><th>Created</th><th>Status</th></tr></thead><tbody>{payments.map((payment) => <tr key={payment.payment_id}><td><strong className="mono">{payment.payment_id.slice(0, 12)}…</strong><span className="table-secondary">{payment.provider_order_id}</span></td><td className="mono">{payment.quote_id.slice(0, 14)}…</td><td><strong>{money(payment.amount, payment.currency)}</strong></td><td>PayPal {payment.provider.includes('sandbox') ? 'Sandbox' : ''}</td><td>{dateTime(payment.created_at)}</td><td><StatusBadge value={payment.status}/></td></tr>)}</tbody></table></div>}</section>
  </>;

  const renderAnalytics = () => <>
    <div className="stats-grid analytics-stats"><StatCard label="Shipment volume" value={analytics?.shipment_count ?? 0} caption="Total stored requests" icon="shipments" tint="tint-blue"/><StatCard label="Quote coverage" value={totalQuoteCount} caption="Offers across visible shipments" icon="quotes" tint="tint-teal"/><StatCard label="Captured transactions" value={analytics?.captured_payments ?? 0} caption={`Of ${analytics?.payment_attempts ?? 0} attempts`} icon="payments" tint="tint-purple"/><StatCard label="Risk attention" value={analytics?.high_attention_quotes ?? 0} caption="Risk assessments scoring for review" icon="risk" tint="tint-amber"/></div>
    <div className="dashboard-grid"><section className="panel"><div className="panel-header"><div><span className="eyebrow">OPERATIONAL MIX</span><h3>Shipment status breakdown</h3><p>Counts from the shipment table.</p></div></div><StatusDistribution counts={analytics?.shipment_status_counts || {}} total={analytics?.shipment_count || 0}/></section><section className="panel"><div className="panel-header"><div><span className="eyebrow">FINANCIAL RECORDS</span><h3>Captured spend by currency</h3><p>Amounts are intentionally not summed across currencies.</p></div></div>{capturedSpend.length ? <div className="spend-list">{capturedSpend.map((spend) => <div className="spend-row" key={spend.currency}><div><span className="spend-currency">{spend.currency}</span><strong>{money(spend.amount, spend.currency)}</strong></div><span className="spend-caption">Verified captures</span></div>)}</div> : <div className="empty-inline"><strong>No captured spend</strong><span>Verified payment captures will be grouped here by currency.</span></div>}</section></div>
    <section className="panel table-panel"><div className="panel-header"><div><span className="eyebrow">CARRIER COMPARISON</span><h3>Quote activity by carrier</h3><p>Grouped from stored quotes. Synthetic demo offers may be included.</p></div></div><CarrierTable items={carrierPerformance}/></section>
    <div className="source-note"><Icon name="database" size={15}/> Data scope: {analytics?.data_scope || 'Unavailable'}. Analytics are calculated from persisted records; no cross-currency total is produced.</div>
  </>;

  const renderSettings = () => <>
    <section className="panel settings-panel"><div className="panel-header"><div><span className="eyebrow">SERVICE HEALTH</span><h3>Connected services</h3><p>Configuration visibility only; secrets are never shown in the browser.</p></div></div><div className="settings-list"><SettingRow icon="activity" title="FastAPI backend" detail={apiBaseUrl} value={health?.status === 'ok' ? 'Connected' : 'Unavailable'} good={health?.status === 'ok'}/><SettingRow icon="database" title="Database" detail="SQLite / SQLAlchemy configured by backend" value={health?.database || 'Unknown'} good={health?.database === 'configured'}/><SettingRow icon="wallet" title="PayPal JavaScript SDK" detail="VITE_PAYPAL_CLIENT_ID" value={paypalClientId && !paypalClientId.toLowerCase().includes('replace') ? 'Client ID configured' : 'Not configured'} good={Boolean(paypalClientId && !paypalClientId.toLowerCase().includes('replace'))}/><SettingRow icon="spark" title="AI Copilot" detail="Provider and API key are configured on the backend" value="Backend-managed" good={null}/><SettingRow icon="truck" title="Live carrier integrations" detail={carrierCatalog?.note || 'Carrier adapter availability reported by backend.'} value={carrierCatalog?.live_integrations_available ? 'Available' : 'Not configured'} good={Boolean(carrierCatalog?.live_integrations_available)}/></div></section>
    <div className="settings-grid"><section className="panel"><div className="panel-header"><div><span className="eyebrow">APPLICATION MODE</span><h3>Environment</h3></div><span className="environment-pill"><span className="environment-dot"/>{health?.mode || 'Unknown'}</span></div><div className="setting-description"><p>Current backend mode is reported by <code>/health</code>. The demo environment should use PayPal Sandbox and clearly mark synthetic carrier data.</p><div className="detail-line"><span>API base URL</span><strong>{apiBaseUrl}</strong></div><div className="detail-line"><span>Signed-in account</span><strong>{currentUser?.email || 'Guest / demo'}</strong></div><div className="detail-line"><span>Data scope</span><strong>{analytics?.data_scope || 'Unavailable'}</strong></div></div></section><section className="panel"><div className="panel-header"><div><span className="eyebrow">DEMO CONTROLS</span><h3>Seed data</h3><p>Reset synthetic demo content for a fresh presentation.</p></div></div><div className="demo-control"><div className="demo-control-icon"><Icon name="refresh"/></div><div><strong>Restore demo dataset</strong><span>The backend prevents deleting a shipment with linked payment records.</span></div><button className="btn btn-secondary btn-sm" onClick={() => void handleReset()} disabled={resetting}>{resetting ? 'Resetting…' : 'Reset demo'}</button></div></section></div>
    <section className="panel"><div className="panel-header"><div><span className="eyebrow">CARRIER REGISTRY</span><h3>Available adapters</h3><p>These are backend adapter registrations, not a list of confirmed live shipping providers.</p></div></div>{carrierCatalog?.items.length ? <div className="adapter-grid">{carrierCatalog.items.map((item) => <div className="adapter-card" key={item.code}><div className="adapter-mark">{item.name.slice(0, 1)}</div><div><strong>{item.name}</strong><span>{item.code}</span></div><StatusBadge value={item.status === 'CONFIGURED' ? 'REGISTERED' : 'NOT CONFIGURED'}/></div>)}</div> : <div className="empty-inline"><strong>No adapter registered</strong><span>Configure a carrier connector in backend/app/services/carrier_service.py.</span></div>}</section>
  </>;

  const renderPage = () => {
    if (loading && page === 'overview') return <LoadingPanel label="Connecting to FreightPilot services…"/>;
    switch (page) {
      case 'overview': return renderOverview();
      case 'shipments': return renderShipments();
      case 'quotes': return renderQuotes();
      case 'risk': return renderRisk();
      case 'copilot': return renderCopilot();
      case 'payments': return renderPayments();
      case 'analytics': return renderAnalytics();
      case 'settings': return renderSettings();
      default: return renderOverview();
    }
  };

  return <div className="app-shell">
    <aside className="sidebar"><div className="sidebar-brand"><div className="brand-mark">FP</div><div><strong>FreightPilot <span>AI</span></strong><small>FREIGHT PROCUREMENT</small></div></div><div className="workspace-switcher"><div className="workspace-avatar">N</div><div><strong>Northstar Logistics</strong><span>Workspace</span></div><Icon name="chevron" size={15}/></div><nav className="side-nav">{(['WORKSPACE', 'INTELLIGENCE', 'FINANCE', 'SYSTEM'] as const).map((group) => <div className="nav-group" key={group}><span className="nav-group-label">{group}</span>{NAV_ITEMS.filter((item) => item.group === group).map((item) => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => setPage(item.id)}><Icon name={item.icon} size={18}/><span>{item.label}</span>{item.id === 'payments' && payments.some((payment) => payment.status === 'REVIEW_REQUIRED') && <i className="nav-alert-dot"/>}</button>)}</div>)}</nav><div className="sidebar-bottom"><div className="sidebar-help"><div className="help-icon"><Icon name="shield" size={17}/></div><strong>Procurement control</strong><p>Use verified quotes and human review before committing payments.</p><button onClick={() => setPage('risk')}>Review risk signals <Icon name="arrow" size={13}/></button></div><div className="sidebar-footer"><span className="online-dot"/> API {health?.status === 'ok' ? 'connected' : 'not connected'}<span>v0.2.0</span></div></div></aside>
    <div className="app-main">{topHeader}<main className="page-content"><div className="page-title-row"><div><div className="eyebrow">FREIGHTPILOT AI / WORKSPACE</div><h1>{currentPage.title}</h1><p>{currentPage.subtitle}</p></div>{page !== 'overview' && page !== 'settings' && <div className="page-context"><span className="context-label">ACTIVE SHIPMENT</span><select value={activeShipment?.id || ''} onChange={(event) => void selectShipment(event.target.value)} disabled={!shipments.length}>{shipments.length === 0 && <option value="">No shipments</option>}{shipments.map((shipment) => <option value={shipment.id} key={shipment.id}>{shipment.cargo_type} · {shipment.origin} → {shipment.destination}</option>)}</select></div>}</div>{pageError && <div className="error-banner"><Icon name="warning" size={17}/><span>{pageError}</span><button className="error-retry" onClick={() => void loadPortfolio(activeShipment?.id)}>Retry</button><button onClick={() => setPageError(null)} aria-label="Dismiss"><Icon name="close" size={15}/></button></div>}{renderPage()}<footer className="app-footer"><span>FreightPilot AI · PayPal AI Hackathon 2026</span><span>{health?.mode === 'production' ? 'Production environment' : 'Sandbox demo · Synthetic data is labeled'}</span></footer></main></div>
    {toast && <div className="toast"><span className="toast-check"><Icon name="check" size={15}/></span>{toast}<button onClick={() => setToast(null)}><Icon name="close" size={14}/></button></div>}
    <NewShipmentModal isOpen={newShipmentOpen} onClose={() => setNewShipmentOpen(false)} onSubmit={handleCreateShipment}/>
    {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onAuthenticated={handleAuthSuccess}/>}
  </div>;
}

function Fact({ label, value }: { label: string; value: string }): React.ReactElement { return <div className="shipment-fact"><span>{label}</span><strong>{value}</strong></div>; }
function LoadingPanel({ label }: { label: string }): React.ReactElement { return <div className="panel loading-panel"><span className="spinner"/><strong>{label}</strong></div>; }

function StatusDistribution({ counts, total }: { counts: Record<string, number>; total: number }): React.ReactElement {
  const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const colors = ['#4169e1', '#17a889', '#9b83e6', '#e3a23d', '#d76d75', '#65a4cb'];
  if (!rows.length) return <div className="empty-inline"><strong>No status records</strong><span>Shipment counts will appear after records are created.</span></div>;
  return <div className="status-distribution"><div className="distribution-bar">{rows.map(([status, count], index) => <span key={status} style={{ width: `${total ? count / total * 100 : 0}%`, background: colors[index % colors.length] }} title={`${status}: ${count}`}/>)}</div>{rows.map(([status, count], index) => <div className="distribution-row" key={status}><span className="distribution-label"><i style={{ background: colors[index % colors.length] }}/>{status.replace(/_/g, ' ')}</span><strong>{count}</strong><span>{total ? Math.round(count / total * 100) : 0}%</span></div>)}</div>;
}

function CarrierPreview({ items }: { items: CarrierPerformance[] }): React.ReactElement {
  if (!items.length) return <div className="empty-inline"><strong>No carrier quote history</strong><span>Carrier metrics appear after quote records are stored.</span></div>;
  return <div className="carrier-preview">{items.map((item) => <div className="carrier-preview-row" key={`${item.carrier}-${item.currency}`}><div className="carrier-avatar">{item.carrier.slice(0, 1).toUpperCase()}</div><div className="carrier-preview-copy"><strong>{item.carrier}</strong><span>{item.quote_count} stored quote{item.quote_count === 1 ? '' : 's'}</span></div><div className="carrier-preview-value"><strong>{money(item.average_quote, item.currency)}</strong><span>avg. {item.currency}</span></div></div>)}</div>;
}

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
