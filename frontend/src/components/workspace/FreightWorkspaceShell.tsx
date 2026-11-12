import { useMemo, useState, type ReactNode } from 'react';
import {
  AlertTriangle, Anchor, Bell, BookOpen, ChevronDown, ChevronLeft,
  FileText, LayoutDashboard, LogOut, Menu, Search, Settings, ShieldCheck,
  Ship, Truck, UserRound, Wallet, X,
  Plus, Sparkles, ChartNoAxesCombined,
} from 'lucide-react';
import type { NotificationItem, Shipment, UserProfile } from '../../types';
import { ThemeToggleButton } from './ThemeToggleButton';

export type WorkspacePage = 'overview' | 'shipments' | 'quotes' | 'payments' | 'copilot' | 'risk' | 'analytics' | 'carriers' | 'documents' | 'settings';

type Props = {
  page: WorkspacePage;
  title: string;
  subtitle: string;
  currentUser: UserProfile | null;
  notifications: NotificationItem[];
  shipments: Shipment[];
  activeShipmentId?: string | null;
  backendOnline: boolean;
  error?: string | null;
  onNavigate: (page: WorkspacePage) => void;
  onSelectShipment: (id: string) => void;
  onSignIn: () => void;
  onSignOut: () => void;
  onPublicSite: () => void;
  onNewShipment: () => void;
  onSearchChange: (value: string) => void;
  onRetry: () => void;
  onDismissError: () => void;
  children: ReactNode;
};

const navigation = [
  { label: 'WORKSPACE', items: [
    { id: 'overview' as const, label: 'Overview', icon: LayoutDashboard },
    { id: 'shipments' as const, label: 'Shipments', icon: Ship },
    { id: 'quotes' as const, label: 'Freight quotes', icon: FileText },
    { id: 'payments' as const, label: 'Payments', icon: Wallet },
  ] },
  { label: 'INTELLIGENCE', items: [
    { id: 'copilot' as const, label: 'AI Copilot', icon: Sparkles },
    { id: 'risk' as const, label: 'Risk engine', icon: ShieldCheck },
    { id: 'analytics' as const, label: 'Analytics', icon: ChartNoAxesCombined },
  ] },
  { label: 'MANAGEMENT', items: [
    { id: 'carriers' as const, label: 'Carriers', icon: Truck },
    { id: 'documents' as const, label: 'Documents', icon: BookOpen },
    { id: 'settings' as const, label: 'Settings', icon: Settings },
  ] },
];

function formatTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Recently' : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date);
}

export function FreightWorkspaceShell({
  page, title, subtitle, currentUser, notifications, shipments, activeShipmentId,
  backendOnline, error, onNavigate, onSelectShipment, onSignIn, onSignOut,
  onPublicSite, onNewShipment, onSearchChange, onRetry, onDismissError, children,
}: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const unreadCount = notifications.filter((item) => !item.read_at).length;
  const userLabel = currentUser?.email?.split('@')[0] || 'Guest workspace';
  const initials = currentUser?.email?.slice(0, 1).toUpperCase() || 'G';
  const activeShipment = useMemo(() => shipments.find((item) => item.id === activeShipmentId), [shipments, activeShipmentId]);

  const navigate = (next: WorkspacePage) => {
    onNavigate(next);
    setMobileOpen(false);
    setNotificationsOpen(false);
    setAccountOpen(false);
  };

  return (
    <div className={`fpw-root${collapsed ? ' is-collapsed' : ''}`}>
      {mobileOpen && <button className="fpw-mobile-scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
      <aside className={`fpw-sidebar${mobileOpen ? ' mobile-open' : ''}`}>
        <div className="fpw-brand-row">
          <div className="fpw-brand-mark">FP</div>
          {!collapsed && <div className="fpw-brand-copy"><strong>FreightPilot <span>AI</span></strong><small>LOGISTICS INTELLIGENCE</small></div>}
          <button className="fpw-collapse" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
            {collapsed ? <Menu size={17} /> : <ChevronLeft size={17} />}
          </button>
        </div>

        <div className="fpw-sidebar-scroll">
          {navigation.map((group) => (
            <div className="fpw-nav-group" key={group.label}>
              {!collapsed && <div className="fpw-nav-label">{group.label}</div>}
              {group.items.map(({ id, label, icon: Icon }) => (
                <button key={id} className={`fpw-nav-item${page === id ? ' active' : ''}`} onClick={() => navigate(id)} title={collapsed ? label : undefined}>
                  <Icon size={18} strokeWidth={1.8} />
                  {!collapsed && <span>{label}</span>}
                  {!collapsed && id === 'payments' && unreadCount > 0 && <i className="fpw-nav-count">{unreadCount}</i>}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="fpw-sidebar-bottom">
          <button className="fpw-utility-item" onClick={onPublicSite} title="Public website"><Anchor size={17}/>{!collapsed && <span>Public website</span>}</button>
          <ThemeToggleButton compact={collapsed}/>
          <div className="fpw-profile-card">
            <div className="fpw-avatar">{initials}</div>
            {!collapsed && <div className="fpw-profile-copy"><strong>{userLabel}</strong><small>{currentUser?.role || 'Not signed in'}</small></div>}
            {!collapsed && <button className="fpw-profile-settings" onClick={() => navigate('settings')} aria-label="Account settings"><Settings size={15}/></button>}
          </div>
          {!collapsed && <button className="fpw-signout" onClick={currentUser ? onSignOut : onSignIn}>{currentUser ? <LogOut size={16}/> : <UserRound size={16}/>}<span>{currentUser ? 'Sign out' : 'Sign in'}</span></button>}
        </div>
      </aside>

      <div className="fpw-main">
        <header className="fpw-topbar">
          <div className="fpw-topbar-left">
            <button className="fpw-mobile-menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button>
            <div className="fpw-breadcrumb"><span>Workspace</span><ChevronDown size={13} className="fpw-crumb-chevron"/><strong>{title}</strong></div>
          </div>
          <div className="fpw-topbar-actions">
            <label className="fpw-search"><Search size={16}/><input type="search" placeholder="Search shipments, quotes…" onChange={(event) => onSearchChange(event.target.value)} aria-label="Search workspace"/><kbd>⌘ K</kbd></label>
            <div className="fpw-popover-anchor">
              <button className="fpw-icon-button" onClick={() => { setNotificationsOpen((value) => !value); setAccountOpen(false); }} aria-label="Notifications"><Bell size={18}/>{unreadCount > 0 && <i className="fpw-unread-dot"/>}</button>
              {notificationsOpen && <div className="fpw-popover fpw-notifications"><div className="fpw-popover-heading"><strong>Notifications</strong><span>{notifications.length}</span></div>{notifications.length === 0 ? <div className="fpw-popover-empty">No operational notifications yet.</div> : notifications.slice(0, 7).map((item) => <div className={`fpw-notification${item.read_at ? '' : ' unread'}`} key={item.id}><span className="fpw-notification-dot"/><div><strong>{item.title}</strong><p>{item.message}</p><small>{formatTime(item.created_at)}</small></div></div>)}</div>}
            </div>
            <div className="fpw-popover-anchor">
              <button className="fpw-account-button" onClick={() => { setAccountOpen((value) => !value); setNotificationsOpen(false); }}><span className="fpw-avatar">{initials}</span><span className="fpw-account-name">{userLabel}</span><ChevronDown size={15}/></button>
              {accountOpen && <div className="fpw-popover fpw-account-popover"><div className="fpw-account-detail"><strong>{currentUser?.email || 'Guest access'}</strong><small>{currentUser?.role || 'Sign in to access your account'}</small></div><button onClick={() => navigate('settings')}><Settings size={15}/> Account settings</button><button onClick={onPublicSite}><Anchor size={15}/> Public website</button><button onClick={currentUser ? onSignOut : onSignIn}><LogOut size={15}/>{currentUser ? 'Sign out' : 'Sign in'}</button></div>}
            </div>
          </div>
        </header>

        <main className="fpw-main-content">
          <div className="fpw-page-heading">
            <div><div className="fpw-overline">FREIGHT OPERATIONS</div><h1>{title}</h1><p>{subtitle}</p></div>
            <div className="fpw-heading-actions">
              {activeShipment && page !== 'settings' && <label className="fpw-active-shipment"><span>Active shipment</span><select value={activeShipment.id} onChange={(event) => onSelectShipment(event.target.value)}>{shipments.map((shipment) => <option key={shipment.id} value={shipment.id}>{shipment.origin} → {shipment.destination}</option>)}</select></label>}
              {page !== 'settings' && <button className="fpw-primary-button" onClick={onNewShipment}><Plus size={16}/> New shipment</button>}
            </div>
          </div>
          <div className="fpw-status-row"><span className={`fpw-connection ${backendOnline ? 'online' : 'offline'}`}><i/>{backendOnline ? 'Backend connected' : 'Backend unavailable'}</span><span className="fpw-status-note">Operational records are loaded from your API</span></div>
          {error && <div className="fpw-error"><AlertTriangle size={17}/><span>{error}</span><button onClick={onRetry}>Retry</button><button className="fpw-error-close" onClick={onDismissError} aria-label="Dismiss error"><X size={15}/></button></div>}
          <div className="fpw-content-slot">{children}</div>
          <footer className="fpw-footer"><span>Freight workspace</span><span>Shipment · Quote · Risk · Settlement</span></footer>
        </main>
      </div>
    </div>
  );
}
