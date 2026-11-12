import { useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Bot,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  CreditCard,
  FileText,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  MoreHorizontal,
  Package,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Truck,
  Wallet,
  X,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useDashboardData } from "../../hooks/useDashboardData";
import { useAuth } from "../../context/AuthContext";
import type { Shipment, PaymentRecord } from "../../types";
import "./freight-dashboard.css";

type ShipmentStatus = "In transit" | "Delivered" | "Delayed" | "Booked";
type PaymentStatus = "Completed" | "Pending" | "Failed";
type NavigationId =
  | "dashboard"
  | "shipments"
  | "marketplace"
  | "quotes"
  | "payments"
  | "documents"
  | "analytics"
  | "copilot"
  | "risk"
  | "carriers"
  | "settings";

function mapShipmentStatus(status: string): ShipmentStatus {
  const statusMap: Record<string, ShipmentStatus> = {
    "DRAFT": "Booked", "QUOTED": "Booked", "BOOKED": "Booked", "PAYMENT_PENDING": "Booked",
    "PAYMENT_FAILED": "Delayed", "PAID": "In transit", "IN_TRANSIT": "In transit", "EXCEPTION": "Delayed",
    "DELIVERED": "Delivered", "CANCELLED": "Delayed",
  };
  return statusMap[status] || "Booked";
}

function mapPaymentStatus(status: string): PaymentStatus {
  const statusMap: Record<string, PaymentStatus> = {
    "CREATED": "Pending", "APPROVED": "Pending", "CAPTURED": "Completed", "FAILED": "Failed", "REFUNDED": "Completed",
  };
  return statusMap[status] || "Pending";
}

function formatAmount(amount: string | number | null | undefined, currency: string): string {
  const num = typeof amount === "string" ? parseFloat(amount) : (amount ?? 0);
  if (currency === "USD") return "$" + num.toLocaleString("en-US", { minimumFractionDigits: 2 });
  if (currency === "EUR") return "€" + num.toLocaleString("de-DE", { minimumFractionDigits: 2 });
  if (currency === "GBP") return "£" + num.toLocaleString("en-GB", { minimumFractionDigits: 2 });
  return num.toLocaleString("en-IN", { minimumFractionDigits: 2 });
}

function formatDate(dateStr: string): string {
  try { return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(dateStr)); } catch { return dateStr; }
}

const navigation: {
  group: string;
  items: { id: NavigationId; label: string; href: string; icon: LucideIcon }[];
}[] = [
  { group: "WORKSPACE", items: [
    { id: "dashboard", label: "Overview", href: "/dashboard", icon: LayoutDashboard },
    { id: "shipments", label: "Shipments", href: "/shipments", icon: Package },
    { id: "marketplace", label: "Marketplace", href: "/marketplace", icon: Truck },
    { id: "quotes", label: "Quotes", href: "/quotes", icon: FileText },
  ]},
  { group: "MANAGE", items: [
    { id: "payments", label: "Payments", href: "/payments", icon: Wallet },
    { id: "documents", label: "Documents", href: "/documents", icon: ShieldCheck },
    { id: "analytics", label: "Analytics", href: "/analytics", icon: Activity },
    { id: "copilot", label: "AI Copilot", href: "/copilot", icon: Bot },
    { id: "risk", label: "Risk engine", href: "/risk", icon: ShieldCheck },
    { id: "carriers", label: "Carriers", href: "/carriers", icon: Truck },
  ]},
  { group: "PREFERENCES", items: [{ id: "settings", label: "Settings", href: "/settings", icon: Settings }]},
];

const statusClass: Record<ShipmentStatus, string> = { "In transit": "fpd-status-blue", Delivered: "fpd-status-green", Delayed: "fpd-status-amber", Booked: "fpd-status-purple" };
const paymentStatusClass: Record<PaymentStatus, string> = { Completed: "fpd-status-green", Pending: "fpd-status-amber", Failed: "fpd-status-red" };

function StatusPill({ status }: { status: ShipmentStatus }) { return <span className={"fpd-status " + statusClass[status]}>{status}</span>; }
function PaymentPill({ status }: { status: PaymentStatus }) { return <span className={"fpd-status " + paymentStatusClass[status]}>{status}</span>; }
function getGreeting() { const hour = new Date().getHours(); if (hour < 12) return "Good morning"; if (hour < 17) return "Good afternoon"; return "Good evening"; }

export type FreightDashboardProps = {
  activePage?: NavigationId;
  onNavigate?: (path: string) => void;
  onCreateShipment?: () => void;
  onGetQuote?: () => void;
  onSignOut?: () => void;
};

function AlertCircle({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

export default function FreightDashboard({ activePage = "dashboard", onNavigate, onCreateShipment, onGetQuote, onSignOut }: FreightDashboardProps) {
  const { user, loading: authLoading } = useAuth();
  const { analytics, shipments: apiShipments, payments: apiPayments, notifications: apiNotifications, loading, error, refresh } = useDashboardData();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("All statuses");
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [sidebarAccountOpen, setSidebarAccountOpen] = useState(false);
  const [aiExpanded, setAiExpanded] = useState(false);

  interface DisplayShipment {
    id: string;
    route: string;
    customer: string;
    carrier: string;
    status: ShipmentStatus;
    eta: string;
    amount: string;
    progress: number;
  }

  const displayShipments = useMemo(() => apiShipments.map((s: Shipment): DisplayShipment => ({
    id: s.id,
    route: s.origin + " → " + s.destination,
    customer: s.cargo_type || "Cargo not specified",
    carrier: "Not assigned",
    status: mapShipmentStatus(s.status),
    eta: s.required_arrival_date ? formatDate(s.required_arrival_date) : "TBD",
    amount: Number(s.quantity_tonnes).toLocaleString("en-IN") + " MT",
    progress: s.status === "DELIVERED" ? 100 : s.status === "IN_TRANSIT" ? 72 : s.status === "QUOTED" ? 25 : 12,
  })), [apiShipments]);

  const weeklyVolumes = useMemo(() => {
    const today = new Date();
    const start = new Date(today);
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - 6);
    const counts = Array.from({ length: 7 }, (_, index) => {
      const date = new Date(start);
      date.setDate(start.getDate() + index);
      const key = date.toDateString();
      const count = apiShipments.filter((shipment) => {
        const created = new Date(shipment.created_at);
        return !Number.isNaN(created.getTime()) && created.toDateString() === key;
      }).length;
      return { day: new Intl.DateTimeFormat("en", { weekday: "short" }).format(date), count };
    });
    const max = Math.max(1, ...counts.map((item) => item.count));
    return counts.map((item) => ({ day: item.day, value: item.count ? Math.max(8, (item.count / max) * 100) : 0, count: item.count }));
  }, [apiShipments]);

  const displayPayments = useMemo(() => apiPayments.map((p: PaymentRecord) => ({
    id: p.payment_id,
    shipmentId: p.shipment_id,
    amount: formatAmount(p.amount, p.currency),
    date: formatDate(p.created_at),
    status: mapPaymentStatus(p.status),
  })), [apiPayments]);

  const filteredShipments = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return displayShipments.filter((shipment) => {
      const matchesQuery = !query || [shipment.id, shipment.route, shipment.customer, shipment.carrier].some((f) => f.toLowerCase().includes(query));
      const matchesStatus = statusFilter === "All statuses" || shipment.status === statusFilter;
      return matchesQuery && matchesStatus;
    });
  }, [searchQuery, statusFilter, displayShipments]);

  function navigate(path: string) {
    if (onNavigate) onNavigate(path);
    else window.location.assign(path);
    setMobileMenuOpen(false);
    setAccountOpen(false);
  }
  function createShipment() { if (onCreateShipment) onCreateShipment(); else navigate("/shipments/new"); }
  function getQuote() { if (onGetQuote) onGetQuote(); else navigate("/quotes/new"); }
  function exportShipments() {
    const header = ["Shipment ID","Route","Customer","Carrier","Status","ETA","Amount","Progress"];
    const rows = filteredShipments.map((s) => [s.id, s.route, s.customer, s.carrier, s.status, s.eta, s.amount, s.progress + "%"]);
    const csv = [header, ...rows].map((line) => line.map((v) => '"' + String(v).replaceAll('"', '""') + '"').join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "freight-shipments.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  const formattedDate = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" }).format(new Date());
  const userName = user?.email?.split("@")[0] || "User";
  const userEmail = user?.email || "Signed-in account";

  if (authLoading) return <div className="fpd-shell"><div className="fpd-loading">Loading dashboard...</div></div>;

  return (
    <div className="fpd-shell">
      {mobileMenuOpen && <button className="fpd-mobile-backdrop" type="button" aria-label="Close navigation menu" onClick={() => setMobileMenuOpen(false)} />}
      <aside className={"fpd-sidebar " + (mobileMenuOpen ? "fpd-sidebar-open" : "")}>
        <div className="fpd-brand-row"><div className="fpd-brand-mark" aria-hidden="true"><Truck size={20} strokeWidth={2.1} /></div><span className="fpd-brand-name">FreightPilot</span><button type="button" className="fpd-icon-button fpd-sidebar-close" aria-label="Close navigation" onClick={() => setMobileMenuOpen(false)}><X size={18} /></button></div>
        <div className="fpd-workspace-switcher"><div className="fpd-workspace-avatar">FP</div><div className="fpd-workspace-copy"><strong>My workspace</strong><span>Logistics account</span></div><ChevronDown size={15} /></div>
        <nav className="fpd-navigation" aria-label="Main navigation">{navigation.map((group) => (<div className="fpd-nav-group" key={group.group}><p className="fpd-nav-label">{group.group}</p>{group.items.map((item) => { const Icon = item.icon; const selected = activePage === item.id; return (<button className={"fpd-nav-item " + (selected ? "fpd-nav-item-active" : "")} type="button" key={item.id} aria-current={selected ? "page" : undefined} onClick={() => navigate(item.href)}><Icon size={18} strokeWidth={1.8} /><span>{item.label}</span>{item.id === "shipments" && displayShipments.length > 0 && <span className="fpd-nav-count">{displayShipments.length}</span>}</button>); })}</div>))}</nav>
        <div className="fpd-sidebar-bottom">
          <div className="fpd-help-card"><div className="fpd-help-icon"><Zap size={16} /></div><div><strong>Need a hand?</strong><span>Visit the help centre</span></div><ChevronRight size={15} /></div>
          <div className="fpd-sidebar-profile"><div className="fpd-avatar">{userName.slice(0, 1).toUpperCase()}</div><div className="fpd-profile-copy"><strong>{userName}</strong><span>{userEmail}</span></div><button type="button" className="fpd-icon-button fpd-profile-menu" aria-label="Open account menu" onClick={() => setSidebarAccountOpen((open) => !open)}><MoreHorizontal size={19} /></button></div>
          {sidebarAccountOpen && (<div className="fpd-account-popover fpd-account-popover-sidebar"><button type="button" onClick={() => navigate("/settings/profile")}><Settings size={15} /> Account settings</button>{onSignOut && <button type="button" onClick={onSignOut}><LogOut size={15} /> Sign out</button>}</div>)}
        </div>
      </aside>
      <main className="fpd-main">
        <header className="fpd-topbar">
          <div className="fpd-topbar-left"><button type="button" className="fpd-icon-button fpd-mobile-menu" aria-label="Open navigation menu" onClick={() => setMobileMenuOpen(true)}><Menu size={20} /></button><div className="fpd-breadcrumb"><span>Workspace</span><ChevronRight size={14} /><strong>Overview</strong></div></div>
          <div className="fpd-topbar-actions">
            <label className="fpd-search-box"><Search size={17} /><input type="search" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search shipments..." aria-label="Search shipments" /><kbd>⌘ K</kbd></label>
            <div className="fpd-popover-wrap"><button type="button" className={"fpd-icon-button fpd-notification-button " + (notificationsOpen ? "fpd-icon-button-active" : "")} aria-label="Notifications" aria-expanded={notificationsOpen} onClick={() => { setNotificationsOpen((open) => !open); setAccountOpen(false); }}><Bell size={18} /><span className="fpd-notification-dot" /></button>{notificationsOpen && (<div className="fpd-popover fpd-notifications-popover"><div className="fpd-popover-heading"><strong>Notifications</strong><span>{apiNotifications.filter((n) => !n.read_at).length} new</span></div>{apiNotifications.slice(0, 5).map((n) => (<div key={n.id} className="fpd-notification-item"><span className={"fpd-notification-symbol fpd-symbol-" + (n.kind === "warning" ? "amber" : n.kind === "success" ? "green" : "blue")}><Clock3 size={15} /></span><div><strong>{n.title}</strong><p>{n.message}</p><small>{formatDate(n.created_at)}</small></div></div>))}{apiNotifications.length === 0 && <div className="fpd-notification-item"><span className="fpd-notification-symbol fpd-symbol-blue"><Bell size={15} /></span><div>No notifications yet</div></div>}</div>)}</div>
            <div className="fpd-popover-wrap fpd-top-account-wrap"><button type="button" className="fpd-top-account" aria-expanded={accountOpen} onClick={() => { setAccountOpen((open) => !open); setNotificationsOpen(false); }}><span className="fpd-avatar fpd-avatar-top">{userName.slice(0, 1).toUpperCase()}</span><span className="fpd-top-account-name">{userName}</span><ChevronDown size={15} /></button>{accountOpen && (<div className="fpd-popover fpd-account-popover"><div className="fpd-account-popover-user"><strong>{userName}</strong><span>{userEmail}</span></div><button type="button" onClick={() => navigate("/settings/profile")}><Settings size={15} /> Account settings</button>{onSignOut && <button type="button" onClick={onSignOut}><LogOut size={15} /> Sign out</button>}</div>)}</div>
          </div>
        </header>
        <div className="fpd-content">
          {loading && <div className="fpd-loading-overlay">Loading dashboard data...</div>}
          {error && <div className="fpd-error-banner" role="alert"><span className="fpd-error-icon"><AlertCircle size={16} /></span><span>{error}</span><button type="button" className="fpd-text-button" onClick={refresh}>Retry</button></div>}
          <section className="fpd-page-heading"><div><div className="fpd-date-line"><CalendarDays size={14} /> {formattedDate}</div><h1>{getGreeting()}, {userName}</h1><p>Here is what is happening with your freight today.</p></div><div className="fpd-heading-actions"><button type="button" className="fpd-button fpd-button-secondary" onClick={getQuote}>Get a quote</button><button type="button" className="fpd-button fpd-button-primary" onClick={createShipment}><Plus size={17} /> New shipment</button></div></section>
          {!analytics && !loading && !error && <div className="fpd-demo-notice"><span className="fpd-demo-notice-dot" />No data available. Create your first shipment to get started.</div>}
          <section className="fpd-metrics-grid" aria-label="Shipment summary">
            <article className="fpd-metric-card"><div className="fpd-metric-top"><span>Active shipments</span><span className="fpd-metric-icon fpd-icon-blue"><Package size={18} /></span></div><div className="fpd-metric-value">{analytics?.active_shipments ?? displayShipments.filter((s) => s.status !== "Delivered").length}</div><div className="fpd-metric-foot"><span className="fpd-neutral-trend">Backend total</span><span>current records</span></div></article>
            <article className="fpd-metric-card"><div className="fpd-metric-top"><span>In transit</span><span className="fpd-metric-icon fpd-icon-violet"><Truck size={18} /></span></div><div className="fpd-metric-value">{displayShipments.filter((s) => s.status === "In transit").length}</div><div className="fpd-metric-foot"><span className="fpd-neutral-trend">On schedule</span><span>{displayShipments.length > 0 ? Math.round(displayShipments.filter((s) => s.status === "In transit").length / displayShipments.length * 100) : 0}% of active</span></div></article>
            <article className="fpd-metric-card"><div className="fpd-metric-top"><span>Pending quotes</span><span className="fpd-metric-icon fpd-icon-amber"><FileText size={18} /></span></div><div className="fpd-metric-value">{analytics?.quote_count ?? 0}</div><div className="fpd-metric-foot"><span className="fpd-trend-warning"><Clock3 size={13} /> {analytics?.high_attention_quotes ?? 0} need review</span><span>Awaiting response</span></div></article>
            <article className="fpd-metric-card"><div className="fpd-metric-top"><span>Payments processed</span><span className="fpd-metric-icon fpd-icon-green"><CircleDollarSign size={18} /></span></div><div className="fpd-metric-value">{analytics?.captured_spend_by_currency?.[0]?.amount ? analytics.captured_spend_by_currency[0].currency + " " + analytics.captured_spend_by_currency[0].amount : "₹0.00"}</div><div className="fpd-metric-foot"><span className="fpd-neutral-trend">{analytics?.captured_payments ?? 0} captured</span><span>recorded payments</span></div></article>
          </section>
          <section className="fpd-primary-grid">
            <article className="fpd-panel fpd-volume-panel"><div className="fpd-panel-heading"><div><h2>Shipment activity</h2><p>Shipment volume over the last 7 days</p></div><span className="fpd-select-button" aria-label="Chart period">This week <ChevronDown size={14} /></span></div><div className="fpd-chart-summary"><strong>{analytics?.shipment_count ?? displayShipments.length}</strong><span>shipments created</span><span className="fpd-chart-change"><ArrowUpRight size={14} /> {analytics?.shipment_count ? "live" : "demo"}</span></div><div className="fpd-bar-chart" role="img" aria-label="Bar chart showing shipment activity from Monday to Sunday">{weeklyVolumes.map((item) => (<div className="fpd-bar-column" key={item.day} title={`${item.count} shipments`}><div className="fpd-bar-track"><div className="fpd-bar" style={{ height: item.value + "%" }} /></div><span>{item.day}</span></div>))}</div></article>
            <article className="fpd-panel fpd-ai-panel"><div className="fpd-ai-heading"><span className="fpd-ai-icon"><Sparkles size={18} /></span><span className="fpd-ai-label">GEMINI AI</span><span className="fpd-preview-pill">Preview</span></div><h2>Logistics insights</h2><p className="fpd-ai-intro">A quick summary of what may need your attention.</p><div className="fpd-ai-insight"><span className="fpd-ai-insight-icon"><Clock3 size={16} /></span><div><strong>{displayShipments.filter((s) => s.status === "Delayed").length} shipments may need attention</strong><p>One carrier ETA is delayed. Confirm the revised delivery window before updating the customer.</p></div></div>{aiExpanded && (<div className="fpd-ai-extra"><div><Check size={14} /><span>Review delayed shipments for revised ETA.</span></div><div><Check size={14} /><span>Check route updates before dispatch confirmation.</span></div><small>Illustrative recommendation. Gemini API connection is not active yet.</small></div>)}<button type="button" className="fpd-text-button" onClick={() => setAiExpanded((expanded) => !expanded)}>{aiExpanded ? "Hide recommendations" : "View recommendations"} <ArrowRight size={15} /></button><div className="fpd-ai-footnote"><Bot size={13} /> Powered by Gemini when API integration is enabled</div></article>
          </section>
          <section className="fpd-panel fpd-shipments-panel"><div className="fpd-panel-heading fpd-shipments-heading"><div><h2>Recent shipments</h2><p>Track and manage your latest freight movements</p></div><div className="fpd-table-actions"><label className="fpd-filter-select"><span className="fpd-sr-only">Filter shipments by status</span><select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option>All statuses</option><option>In transit</option><option>Delivered</option><option>Delayed</option><option>Booked</option></select><ChevronDown size={14} /></label><button type="button" className="fpd-button fpd-button-small fpd-button-secondary" onClick={exportShipments}><ArrowDownRight size={15} /> Export</button></div></div><div className="fpd-table-scroll"><table className="fpd-table"><thead><tr><th>SHIPMENT</th><th>ROUTE</th><th>CARRIER</th><th>STATUS</th><th>ETA</th><th className="fpd-th-amount">CARGO</th><th aria-label="Details" /></tr></thead><tbody>{filteredShipments.length === 0 ? (<tr><td className="fpd-empty-state" colSpan={7}>No shipments match your search or filter. {displayShipments.length === 0 && "Create a shipment to get started."}</td></tr>) : filteredShipments.map((shipment) => {
            const originalShipment = apiShipments.find(s => s.id === shipment.id);
            const handleSelect = () => { if (originalShipment) setSelectedShipment(originalShipment); };
            return (<tr key={shipment.id} onClick={handleSelect} tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter") handleSelect(); }}><td><strong className="fpd-shipment-id">{shipment.id}</strong><span className="fpd-table-subtext">{shipment.customer}</span></td><td><span className="fpd-route-cell"><MapPin size={14} /> {shipment.route}</span></td><td>{shipment.carrier}</td><td><StatusPill status={shipment.status} /></td><td>{shipment.eta}</td><td className="fpd-amount-cell">{shipment.amount}</td><td><button type="button" className="fpd-row-arrow" aria-label={"View " + shipment.id + " details"} onClick={(e) => { e.stopPropagation(); handleSelect(); }}><ChevronRight size={17} /></button></td></tr>);
          })}</tbody></table></div><div className="fpd-table-footer"><span>Showing {filteredShipments.length} of {displayShipments.length} shipments</span><button type="button" className="fpd-text-button" onClick={() => navigate("/shipments")}>View all shipments <ArrowRight size={14} /></button></div></section>
          <section className="fpd-bottom-grid">
            <article className="fpd-panel fpd-payments-panel"><div className="fpd-panel-heading"><div><div className="fpd-payment-title"><h2>Recent payments</h2><span className="fpd-sandbox-pill">PayPal Sandbox</span></div><p>Test transactions from the payment gateway</p></div><button type="button" className="fpd-icon-button fpd-light-more" aria-label="More payment options" onClick={() => navigate("/payments")}><MoreHorizontal size={19} /></button></div><div className="fpd-payment-list">{displayPayments.length === 0 ? <div className="fpd-empty-state">No payments yet. Create a shipment and process a payment to see history.</div> : displayPayments.map((payment) => (<div className="fpd-payment-row" key={payment.id}><span className="fpd-payment-method"><CreditCard size={17} /></span><div className="fpd-payment-info"><strong>{payment.id}</strong><span>{payment.shipmentId} · {payment.date}</span></div><div className="fpd-payment-amount"><strong>{payment.amount}</strong><PaymentPill status={payment.status} /></div></div>))}</div><div className="fpd-payment-footer"><span><ShieldCheck size={14} /> Sandbox only — no real money is charged</span><button type="button" className="fpd-text-button" onClick={() => navigate("/payments")}>View all <ArrowRight size={14} /></button></div></article>
            <article className="fpd-panel fpd-quick-panel"><div className="fpd-panel-heading"><div><h2>Quick actions</h2><p>Get common tasks done faster</p></div></div><button type="button" className="fpd-quick-action" onClick={createShipment}><span className="fpd-quick-icon fpd-icon-blue"><Plus size={18} /></span><span><strong>Create a shipment</strong><small>Start a new freight request</small></span><ChevronRight size={17} /></button><button type="button" className="fpd-quick-action" onClick={getQuote}><span className="fpd-quick-icon fpd-icon-violet"><FileText size={18} /></span><span><strong>Request a quote</strong><small>Compare carrier pricing</small></span><ChevronRight size={17} /></button><button type="button" className="fpd-quick-action" onClick={() => navigate("/documents")}><span className="fpd-quick-icon fpd-icon-green"><ShieldCheck size={18} /></span><span><strong>Upload documents</strong><small>Manage shipment paperwork</small></span><ChevronRight size={17} /></button></article>
          </section>
          <footer className="fpd-footer"><span>© {new Date().getFullYear()} FreightPilot</span><span>Dashboard · {analytics ? "Live data" : "Demo mode"}</span></footer>
        </div>
      </main>
      {selectedShipment && (<div className="fpd-modal-backdrop" role="presentation" onMouseDown={(e) => { if (e.target === e.currentTarget) setSelectedShipment(null); }}><aside className="fpd-detail-drawer" role="dialog" aria-modal="true" aria-labelledby="fpd-detail-title"><div className="fpd-drawer-header"><div><span className="fpd-drawer-eyebrow">SHIPMENT DETAILS</span><h2 id="fpd-detail-title">{selectedShipment.id}</h2></div><button type="button" className="fpd-icon-button" aria-label="Close shipment details" onClick={() => setSelectedShipment(null)}><X size={18} /></button></div><StatusPill status={mapShipmentStatus(selectedShipment.status)} /><div className="fpd-drawer-route"><div className="fpd-route-point"><span className="fpd-route-dot fpd-route-origin" /><div><small>ORIGIN</small><strong>{selectedShipment.origin}</strong></div></div><div className="fpd-route-line" /><div className="fpd-route-point"><span className="fpd-route-dot fpd-route-destination" /><div><small>DESTINATION</small><strong>{selectedShipment.destination}</strong></div></div></div><div className="fpd-detail-progress"><div><span>Delivery progress</span><strong>{selectedShipment.status === "DELIVERED" ? 100 : selectedShipment.status === "IN_TRANSIT" ? 72 : selectedShipment.status === "QUOTED" ? 25 : 12}%</strong></div><div className="fpd-progress-track"><span style={{ width: (selectedShipment.status === "DELIVERED" ? 100 : selectedShipment.status === "IN_TRANSIT" ? 72 : selectedShipment.status === "QUOTED" ? 25 : 12) + "%" }} /></div></div><div className="fpd-detail-grid"><div><small>CARGO TYPE</small><strong>{selectedShipment.cargo_type}</strong></div><div><small>QUANTITY</small><strong>{Number(selectedShipment.quantity_tonnes).toLocaleString()} MT</strong></div><div><small>ESTIMATED DELIVERY</small><strong>{selectedShipment.required_arrival_date ? formatDate(selectedShipment.required_arrival_date) : "TBD"}</strong></div><div><small>COMPARISON CURRENCY</small><strong>{selectedShipment.currency}</strong></div></div><div className="fpd-drawer-note"><Activity size={16} /><div><strong>Tracking connection</strong><p>Carrier tracking events will appear here when the shipment tracking API is connected.</p></div></div><button type="button" className="fpd-button fpd-button-primary fpd-drawer-button" onClick={() => { setSelectedShipment(null); navigate("/shipments"); }}>Open shipment page <ArrowRight size={16} /></button></aside></div>)}
    </div>
  );
}