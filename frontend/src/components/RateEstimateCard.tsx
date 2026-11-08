import React from 'react';
import { RateEstimate, Shipment } from '../types';

interface RateEstimateCardProps {
  estimate: RateEstimate | null;
  shipment: Shipment | null;
}

export const RateEstimateCard: React.FC<RateEstimateCardProps> = ({ estimate, shipment }) => {
  if (!estimate || !shipment) return null;

  const formatCurrency = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: estimate.currency || 'USD',
      maximumFractionDigits: 0,
    }).format(val);
  };

  const isInsufficient = estimate.coverage_status === 'INSUFFICIENT_DATA';

  return (
    <div className="card rate-estimate-card">
      <div className="estimate-header">
        <div>
          <div className="estimate-title-row">
            <h3 className="card-title">Freight Rate Baseline &amp; Market Context</h3>
            <span className={`badge ${isInsufficient ? 'badge-warning' : 'badge-coverage'}`}>
              {isInsufficient ? 'LIMITED DATA' : 'DEMO STATISTICAL BASELINE'}
            </span>
          </div>
          <p className="card-subtitle">
            Calculated over verified quotes for <strong>{shipment.cargo_type}</strong> ({shipment.origin.split(',')[0]} ➔ {shipment.destination.split(',')[0]}).
          </p>
        </div>

        <div className="estimate-metric-main">
          <span className="estimate-median-label">Benchmark Median:</span>
          <span className="estimate-median-val">{formatCurrency(estimate.median_rate)}</span>
        </div>
      </div>

      <div className="estimate-body">
        <div className="estimate-stats-grid">
          <div className="estimate-stat-item">
            <span className="stat-sm-label">Observed Min:</span>
            <span className="stat-sm-val">{formatCurrency(estimate.min_rate)}</span>
          </div>
          <div className="estimate-stat-item">
            <span className="stat-sm-label">Observed Max:</span>
            <span className="stat-sm-val">{formatCurrency(estimate.max_rate)}</span>
          </div>
          <div className="estimate-stat-item">
            <span className="stat-sm-label">Sample Observations:</span>
            <span className="stat-sm-val">{estimate.sample_size} Quotes</span>
          </div>
          <div className="estimate-stat-item">
            <span className="stat-sm-label">Coverage Status:</span>
            <span className="stat-sm-val">{estimate.coverage_status}</span>
          </div>
        </div>

        {/* Methodology & Strict Non-ML Disclaimer */}
        <div className="estimate-disclaimer-box">
          <div className="disclaimer-title">Methodology &amp; Transparency Notice</div>
          <p className="disclaimer-text">
            <strong>Method:</strong> {estimate.method}.
          </p>
          <p className="disclaimer-text">
            <strong>Important Framing:</strong> {estimate.disclaimer}
          </p>
        </div>
      </div>
    </div>
  );
};
