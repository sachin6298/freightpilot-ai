import React from 'react';
import { Shipment, Quote } from '../types';

interface KpiCardsProps {
  shipment: Shipment | null;
  quotes: Quote[];
}

export const KpiCards: React.FC<KpiCardsProps> = ({ shipment, quotes }) => {
  const quoteCount = quotes.length;

  let minRate: number | null = null;
  let maxRate: number | null = null;

  if (quotes.length > 0) {
    const amounts = quotes.map((q) => Number(q.total_amount));
    minRate = Math.min(...amounts);
    maxRate = Math.max(...amounts);
  }

  const formatCurrency = (val: number, cur = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cur,
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="grid grid-4 kpi-grid">
      <div className="stat-box">
        <span className="stat-label">Active Route</span>
        <span className="stat-value text-highlight" title={shipment ? `${shipment.origin} → ${shipment.destination}` : 'None'}>
          {shipment ? `${shipment.origin.split(',')[0]} → ${shipment.destination.split(',')[0]}` : '—'}
        </span>
        <span className="stat-sub">
          {shipment ? shipment.cargo_type : 'Select a shipment'}
        </span>
      </div>

      <div className="stat-box">
        <span className="stat-label">Cargo Volume</span>
        <span className="stat-value text-emerald">
          {shipment ? `${Number(shipment.quantity_tonnes).toLocaleString()} MT` : '—'}
        </span>
        <span className="stat-sub">
          {shipment ? `Ready: ${shipment.ready_date}` : 'Metric Tonnes'}
        </span>
      </div>

      <div className="stat-box">
        <span className="stat-label">Quotes Available</span>
        <span className="stat-value text-indigo">
          {quoteCount} {quoteCount === 1 ? 'Offer' : 'Offers'}
        </span>
        <span className="stat-sub">Normalized comparison</span>
      </div>

      <div className="stat-box">
        <span className="stat-label">Offer Range</span>
        <span className="stat-value text-amber">
          {minRate !== null && maxRate !== null
            ? `${formatCurrency(minRate, shipment?.currency)} – ${formatCurrency(maxRate, shipment?.currency)}`
            : '—'}
        </span>
        <span className="stat-sub">Base + Surcharges Total</span>
      </div>
    </div>
  );
};
