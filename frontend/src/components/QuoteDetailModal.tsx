import React from 'react';
import { Quote, Shipment, RiskFlag } from '../types';

interface QuoteDetailModalProps {
  quote: Quote | null;
  shipment: Shipment | null;
  isSelected: boolean;
  onSelect: (quote: Quote) => void;
  onClose: () => void;
}

export const QuoteDetailModal: React.FC<QuoteDetailModalProps> = ({
  quote,
  shipment,
  isSelected,
  onSelect,
  onClose,
}) => {
  if (!quote) return null;

  const formatCurrency = (val: number | string, cur = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cur,
    }).format(Number(val));
  };

  const terms = quote.terms || {};
  const assessment = quote.assessment;
  const flags: RiskFlag[] = assessment?.flags || [];

  const getRiskLabelBadge = (label?: string) => {
    switch (label) {
      case 'LOWER_CONCERN':
        return <span className="risk-pill risk-pill-green">✓ LOWER CONCERN</span>;
      case 'REVIEW':
        return <span className="risk-pill risk-pill-amber">⚠️ REVIEW REQUIRED</span>;
      case 'HIGH_ATTENTION':
        return <span className="risk-pill risk-pill-red">🚨 HIGH ATTENTION</span>;
      case 'INSUFFICIENT_DATA':
        return <span className="risk-pill risk-pill-blue">ℹ️ LIMITED DATA</span>;
      default:
        return <span className="risk-pill risk-pill-muted">UNASSESSED</span>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-md" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="source-tag">{quote.source_kind}</span>
            <h3 className="modal-title">{quote.provider_label}</h3>
            <p className="modal-subtitle">
              Quote Reference: <code>{quote.reference}</code>
              {shipment && ` • ${shipment.cargo_type} (${shipment.origin.split(',')[0]} → ${shipment.destination.split(',')[0]})`}
            </p>
          </div>
          <button className="btn-close" onClick={onClose} aria-label="Close modal">×</button>
        </div>

        <div className="modal-body">
          {/* Price Breakdown Box */}
          <div className="detail-section">
            <h4 className="detail-section-title">Authoritative Cost Breakdown</h4>
            <div className="cost-breakdown-table">
              <div className="cost-row">
                <span>Base Ocean Freight:</span>
                <span className="cost-val">{formatCurrency(quote.base_amount, quote.currency)}</span>
              </div>
              <div className="cost-row">
                <span>Surcharges &amp; Port Fees:</span>
                <span className="cost-val">{formatCurrency(quote.surcharge_amount, quote.currency)}</span>
              </div>

              {terms.fuel_surcharge !== undefined && (
                <div className="cost-subrow">
                  <span>↳ Bunker Adjustment (BAF / Fuel):</span>
                  <span>{formatCurrency(Number(terms.fuel_surcharge), quote.currency)}</span>
                </div>
              )}

              {terms.port_dues !== undefined && (
                <div className="cost-subrow">
                  <span>↳ Port Terminal Dues:</span>
                  <span>{formatCurrency(Number(terms.port_dues), quote.currency)}</span>
                </div>
              )}

              <div className="cost-row cost-total-row">
                <span>Verified Total:</span>
                <span className="cost-total-val">{formatCurrency(quote.total_amount, quote.currency)}</span>
              </div>
            </div>
          </div>

          {/* Explainable Risk Assessment Section */}
          <div className="detail-section">
            <div className="risk-modal-header">
              <h4 className="detail-section-title">Explainable Risk Analysis</h4>
              <div className="risk-score-badge-row">
                {getRiskLabelBadge(assessment?.label)}
                <span className="score-meter">
                  Priority Score: <strong>{assessment?.score ?? 0}</strong>/100
                </span>
              </div>
            </div>

            {flags.length > 0 ? (
              <div className="risk-flags-list modal-flags-list">
                {flags.map((flag) => (
                  <div key={flag.code} className="risk-flag-entry">
                    <div className="flag-title-row">
                      <span className={`flag-severity-pill severity-${flag.severity.toLowerCase()}`}>
                        {flag.severity}
                      </span>
                      <strong className="flag-title">{flag.title}</strong>
                    </div>
                    <p className="flag-evidence">
                      <strong>Factual Evidence:</strong> {flag.evidence}
                    </p>
                    <p className="flag-check">
                      <strong>Recommended Verification:</strong> {flag.recommended_check}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="risk-clean-notice">
                ✓ No anomalies, date conflicts, or fee discrepancies detected.
              </div>
            )}
          </div>

          {/* Operational & Vessel Specs */}
          <div className="detail-section">
            <h4 className="detail-section-title">Operational &amp; Vessel Specifications</h4>
            <div className="spec-grid">
              <div className="spec-tile">
                <span className="tile-label">Transit Duration</span>
                <span className="tile-val">{quote.transit_days ? `${quote.transit_days} Days` : 'Not specified'}</span>
              </div>
              <div className="spec-tile">
                <span className="tile-label">Vessel Class</span>
                <span className="tile-val">{quote.vessel_class || 'Standard'}</span>
              </div>
              <div className="spec-tile">
                <span className="tile-label">Vessel Cargo Capacity</span>
                <span className="tile-val">
                  {quote.cargo_capacity_tonnes
                    ? `${Number(quote.cargo_capacity_tonnes).toLocaleString()} MT`
                    : 'Unstated'}
                </span>
              </div>
              <div className="spec-tile">
                <span className="tile-label">Quote Validity Expiry</span>
                <span className="tile-val">
                  {quote.validity_until
                    ? new Date(quote.validity_until).toLocaleDateString()
                    : 'Open validity'}
                </span>
              </div>
            </div>
          </div>

          {/* Payment Terms & Conditions */}
          <div className="detail-section">
            <h4 className="detail-section-title">Commercial &amp; Payment Terms</h4>
            <div className="terms-container">
              <div className="term-entry">
                <strong>Payment Schedule:</strong>{' '}
                {typeof terms.payment_terms === 'string' ? terms.payment_terms : 'Standard commercial terms'}
              </div>
              {terms.advance_pct !== undefined && (
                <div className="term-entry">
                  <strong>Advance Requirement:</strong> {String(terms.advance_pct)}% upfront
                </div>
              )}
              {terms.demurrage_rate_daily !== undefined && (
                <div className="term-entry">
                  <strong>Demurrage Daily Rate:</strong> {formatCurrency(Number(terms.demurrage_rate_daily), quote.currency)} / day
                </div>
              )}
            </div>
          </div>

          {/* Notice */}
          <div className="notice-box">
            <span className="notice-icon">ℹ️</span>
            <span className="notice-text">
              Risk analysis is an explainable decision-support tool. It does not replace buyer due diligence and does not automatically authorize payment.
            </span>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button
            className={`btn ${isSelected ? 'btn-success' : 'btn-primary'}`}
            onClick={() => {
              onSelect(quote);
              onClose();
            }}
          >
            {isSelected ? '✓ Currently Selected' : 'Select this Quote'}
          </button>
        </div>
      </div>
    </div>
  );
};
