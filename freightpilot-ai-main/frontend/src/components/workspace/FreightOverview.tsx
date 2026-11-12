import { Activity, AlertTriangle, ArrowUpRight, CheckCircle2, FileText, Package, Plus, Sparkles, Wallet } from 'lucide-react';
import type { AnalyticsOverview, PaymentRecord, Quote, Shipment } from '../../types';

type Props = {
  analytics: AnalyticsOverview | null;
  shipments: Shipment[];
  payments: PaymentRecord[];
  quotes: Quote[];
  loading: boolean;
  onNavigate: (page: 'shipments' | 'quotes' | 'payments' | 'copilot' | 'risk' | 'analytics') => void;
  onCreateShipment: () => void;
  onSelectShipment: (shipment: Shipment) => void;
};

function money(value: string | number, currency: string) {
  try { return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(Number(value)); }
  catch { return `${currency} ${Number(value).toLocaleString()}`; }
}
function dateLabel(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(date);
}
function metricValue(value: number | null | undefined) { return value == null ? '—' : value.toLocaleString(); }
function statusClass(status: string) {
  const normalized = status.toUpperCase();
  if (['DELIVERED', 'CAPTURED', 'PAID', 'COMPLETED'].includes(normalized)) return 'success';
  if (['EXCEPTION', 'FAILED', 'CANCELLED', 'REVIEW_REQUIRED'].includes(normalized)) return 'danger';
  if (['IN_TRANSIT', 'BOOKED', 'QUOTED', 'APPROVED'].includes(normalized)) return 'info';
  return 'neutral';
}
function recentMonths(shipments: Shipment[]) {
  const now = new Date();
  const monthStarts = Array.from({ length: 6 }, (_, index) => new Date(now.getFullYear(), now.getMonth() - 5 + index, 1));
  const counts = monthStarts.map((month) => ({ label: new Intl.DateTimeFormat('en', { month: 'short' }).format(month), value: shipments.filter((shipment) => {
    const created = new Date(shipment.created_at);
    return !Number.isNaN(created.getTime()) && created.getFullYear() === month.getFullYear() && created.getMonth() === month.getMonth();
  }).length }));
  return counts;
}

export function FreightOverview({ analytics, shipments, payments, quotes, loading, onNavigate, onCreateShipment, onSelectShipment }: Props) {
  const activeCount = analytics?.active_shipments ?? shipments.filter((item) => !['DELIVERED', 'CANCELLED'].includes(item.status.toUpperCase())).length;
  const quoteCount = analytics?.quote_count ?? shipments.reduce((total, item) => total + (item.quotes_count || 0), 0);
  const capturedCount = analytics?.captured_payments ?? payments.filter((item) => ['CAPTURED', 'COMPLETED', 'PAID'].includes(item.status.toUpperCase())).length;
  const riskCount = analytics?.high_attention_quotes ?? quotes.filter((item) => ['HIGH_ATTENTION', 'REVIEW'].includes(item.assessment?.label || '')).length;
  const monthData = recentMonths(shipments);
  const maxMonth = Math.max(1, ...monthData.map((item) => item.value));
  const capturedPayments = payments.filter((item) => ['CAPTURED', 'COMPLETED', 'PAID'].includes(item.status.toUpperCase())).slice(0, 5);

  return <div className="fp-overview">
    <div className="fp-overview-welcome"><div><span className="fp-overview-kicker">YOUR OPERATIONS AT A GLANCE</span><h2>Good to see you.</h2><p>Monitor shipments, compare freight offers and keep settlement activity in view.</p></div><button className="fpw-secondary-button" onClick={() => onNavigate('analytics')}>View analytics <ArrowUpRight size={15}/></button></div>

    <div className="fp-overview-metrics">
      <article className="fp-metric-card"><div className="fp-metric-top"><span>Total shipments</span><span className="fp-metric-icon blue"><Package size={18}/></span></div><strong>{loading ? '…' : metricValue(analytics?.shipment_count ?? shipments.length)}</strong><small>Stored shipment requests</small></article>
      <article className="fp-metric-card"><div className="fp-metric-top"><span>Active shipments</span><span className="fp-metric-icon violet"><Activity size={18}/></span></div><strong>{loading ? '…' : metricValue(activeCount)}</strong><small>Not delivered or cancelled</small></article>
      <article className="fp-metric-card"><div className="fp-metric-top"><span>Quote offers</span><span className="fp-metric-icon amber"><FileText size={18}/></span></div><strong>{loading ? '…' : metricValue(quoteCount)}</strong><small>Offers recorded by the backend</small></article>
      <article className="fp-metric-card"><div className="fp-metric-top"><span>Captured payments</span><span className="fp-metric-icon green"><Wallet size={18}/></span></div><strong>{loading ? '…' : metricValue(capturedCount)}</strong><small>Verified captures only</small></article>
    </div>

    <div className="fp-overview-grid">
      <section className="fp-card fp-volume-card"><div className="fp-card-heading"><div><span className="fp-section-label">SHIPMENT ACTIVITY</span><h3>Shipment creation</h3><p>Monthly count based on stored creation dates.</p></div><span className="fp-card-icon"><Activity size={17}/></span></div>
        {shipments.length === 0 ? <div className="fp-chart-empty">Shipment activity will appear here after records are created.</div> : <div className="fp-volume-chart">{monthData.map((item) => <div className="fp-volume-column" key={item.label}><div className="fp-volume-track"><div className="fp-volume-bar" style={{ height: `${Math.max(6, item.value / maxMonth * 100)}%` }} title={`${item.value} shipments`}/></div><span>{item.label}</span><strong>{item.value}</strong></div>)}</div>}
      </section>
      <section className="fp-card fp-status-card"><div className="fp-card-heading"><div><span className="fp-section-label">RISK REVIEW</span><h3>Attention required</h3><p>Based on available quote assessments.</p></div><span className="fp-card-icon warning"><AlertTriangle size={17}/></span></div><div className="fp-risk-highlight"><strong>{metricValue(riskCount)}</strong><span>Quotes marked for review or high attention</span></div><button className="fp-card-link" onClick={() => onNavigate('risk')}>Open risk engine <ArrowUpRight size={15}/></button><div className="fp-card-divider"/><div className="fp-quick-status"><span><i className="dot green"/> Captured payments</span><strong>{capturedCount}</strong></div><div className="fp-quick-status"><span><i className="dot blue"/> Active shipments</span><strong>{activeCount}</strong></div></section>
    </div>

    <div className="fp-overview-grid fp-lower-grid">
      <section className="fp-card fp-table-card"><div className="fp-card-heading"><div><span className="fp-section-label">RECENT ACTIVITY</span><h3>Recent shipments</h3><p>Latest shipment records from your workspace.</p></div><button className="fp-text-action" onClick={() => onNavigate('shipments')}>View all <ArrowUpRight size={14}/></button></div>
        {shipments.length === 0 ? <div className="fp-empty-state"><Package size={25}/><strong>No shipments yet</strong><span>Create your first shipment to begin.</span><button className="fpw-primary-button" onClick={onCreateShipment}><Plus size={15}/> Create shipment</button></div> : <div className="fp-table-scroll"><table className="fp-table"><thead><tr><th>Shipment</th><th>Route</th><th>Status</th><th>Created</th></tr></thead><tbody>{shipments.slice(0, 6).map((shipment) => <tr key={shipment.id} onClick={() => onSelectShipment(shipment)}><td><strong>{shipment.cargo_type}</strong><small>{shipment.id.slice(0, 12)}</small></td><td>{shipment.origin} <span className="fp-route-arrow">→</span> {shipment.destination}</td><td><span className={`fp-status-pill ${statusClass(shipment.status)}`}>{shipment.status.replace(/_/g, ' ')}</span></td><td>{dateLabel(shipment.created_at)}</td></tr>)}</tbody></table></div>}
      </section>
      <section className="fp-card fp-payment-card"><div className="fp-card-heading"><div><span className="fp-section-label">SETTLEMENT</span><h3>Recent payments</h3><p>PayPal transaction records verified by the API.</p></div><span className="fp-card-icon green"><Wallet size={17}/></span></div>
        {capturedPayments.length === 0 ? <div className="fp-empty-compact"><CreditCardMini/><strong>No captured payments</strong><span>Successful captures will appear here.</span></div> : <div className="fp-payments-list">{capturedPayments.map((payment) => <div className="fp-payment-row" key={payment.payment_id}><div className="fp-payment-logo"><Wallet size={16}/></div><div className="fp-payment-copy"><strong>{payment.provider.includes('paypal') ? 'PayPal' : payment.provider}</strong><small>{dateLabel(payment.created_at)} · {payment.payment_id.slice(0, 9)}</small></div><div className="fp-payment-amount"><strong>{money(payment.amount, payment.currency)}</strong><small><CheckCircle2 size={12}/> Captured</small></div></div>)}</div>}
        <button className="fp-card-link" onClick={() => onNavigate('payments')}>Open payment ledger <ArrowUpRight size={15}/></button>
      </section>
    </div>

    <section className="fp-quick-actions"><div><span className="fp-section-label">QUICK ACCESS</span><h3>Move work forward</h3></div><div className="fp-quick-action-list"><button onClick={onCreateShipment}><Plus size={16}/><span>New shipment</span></button><button onClick={() => onNavigate('quotes')}><FileText size={16}/><span>Compare quotes</span></button><button onClick={() => onNavigate('copilot')}><Sparkles size={16}/><span>Ask AI Copilot</span></button><button onClick={() => onNavigate('payments')}><Wallet size={16}/><span>Payments</span></button></div></section>
  </div>;
}

function CreditCardMini() { return <Wallet size={24}/>; }
