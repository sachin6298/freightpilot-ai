import React, { useState, useMemo } from 'react';
import { Quote, Shipment, RiskFlag } from '../types';

interface QuoteComparisonViewProps {
  quotes: Quote[];
  shipment: Shipment;
  selectedQuoteId: string | null;
  onSelectQuote: (quote: Quote) => void;
  onInspectQuote: (quote: Quote) => void;
}

type SortField = 'price-asc' | 'price-desc' | 'transit-asc' | 'risk-asc' | 'risk-desc';

export const QuoteComparisonView: React.FC<QuoteComparisonViewProps> = ({
  quotes,
  shipment,
  selectedQuoteId,
  onSelectQuote,
  onInspectQuote,
}) => {
  const [sortField, setSortField] = useState<SortField>('price-asc');
  const [expandedRiskQuoteId, setExpandedRiskQuoteId] = useState<string | null>(null);

  const sortedQuotes = useMemo(() => {
    return [...quotes].sort((a, b) => {
      const priceA = Number(a.total_amount);
      const priceB = Number(b.total_amount);
      const transitA = a.transit_days ?? 999;
      const transitB = b.transit_days ?? 999;
      const scoreA = a.assessment?.score ?? 0;
      const scoreB = b.assessment?.score ?? 0;

      if (sortField === 'price-asc') return priceA - priceB;
      if (sortField === 'price-desc') return priceB - priceA;
      if (sortField === 'transit-asc') return transitA - transitB;
      if (sortField === 'risk-asc') return scoreA - scoreB;
      if (sortField === 'risk-desc') return scoreB - scoreA;
      return 0;
    });
  }, [quotes, sortField]);

  const formatCurrency = (val: number | string, cur = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cur,
    }).format(Number(val));
  };

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

  const toggleRiskExpand = (quoteId: string) => {
    setExpandedRiskQuoteId((curr) => (curr === quoteId ? null : quoteId));
  };

  if (quotes.length === 0) {
    return (
      <div className="card empty-state">
        <div className="empty-icon">📦</div>
        <h3 className="empty-title">No Quotes Available</h3>
        <p className="empty-text">
          There are currently no freight quotes registered for this shipment.
        </p>
      </div>
    );
  }

  return (
    <div className="quote-comparison-container">
      <div className="section-toolbar">
        <div>
          <h3 className="section-title">Freight Quote Comparison &amp; Risk Review</h3>
          <p className="section-subtitle">
            Normalized quotes with transparent risk signals and benchmark variance.
          </p>
        </div>

        <div className="sort-controls">
          <label htmlFor="quote-sort" className="sort-label">Sort by:</label>
          <select
            id="quote-sort"
            className="form-select form-select-sm"
            value={sortField}
            onChange={(e) => setSortField(e.target.value as SortField)}
          >
            <option value="price-asc">Total Cost: Low to High</option>
            <option value="price-desc">Total Cost: High to Low</option>
            <option value="transit-asc">Fastest Transit Time</option>
            <option value="risk-asc">Risk: Lowest Concern First</option>
            <option value="risk-desc">Risk: Highest Priority First</option>
          </select>
        </div>
      </div>

      <div className="quote-card-grid">
        {sortedQuotes.map((quote) => {
          const isSelected = selectedQuoteId === quote.id;
          const assessment = quote.assessment;
          const flags: RiskFlag[] = assessment?.flags || [];
          const isExpanded = expandedRiskQuoteId === quote.id;
          const variance = quote.benchmark_variance_pct;

          return (
            <div
              key={quote.id}
              className={`quote-card ${isSelected ? 'quote-card-selected' : ''}`}
            >
              {isSelected && (
                <div className="selected-ribbon">
                  <span>✓ SELECTED FOR REVIEW</span>
                </div>
              )}

              {/* Card Header */}
              <div className="quote-header">
                <div>
                  <div className="carrier-badge-row">
                    <h4 className="carrier-name">{quote.provider_label}</h4>
                    <span className="source-tag">{quote.source_kind}</span>
                  </div>
                  <span className="quote-ref">Ref: {quote.reference}</span>
                </div>

                <div className="quote-total-price">
                  <span className="total-amount-display">
                    {formatCurrency(quote.total_amount, quote.currency)}
                  </span>
                  <span className="total-label">Authoritative Total</span>
                </div>
              </div>

              {/* Benchmark Variance Indicator */}
              <div className="benchmark-variance-bar">
                {variance !== null && variance !== undefined ? (
                  <span
                    className={`variance-tag ${
                      variance < -20
                        ? 'variance-low'
                        : variance > 20
                        ? 'variance-high'
                        : 'variance-neutral'
                    }`}
                  >
                    {variance === 0
                      ? 'Benchmark Median Match'
                      : variance > 0
                      ? `+${variance}% vs benchmark median`
                      : `${variance}% vs benchmark median`}
                  </span>
                ) : (
                  <span className="variance-tag variance-neutral">Benchmark Baseline N/A</span>
                )}
              </div>

              {/* Fee Breakdown Component */}
              <div className="fee-breakdown-row">
                <div className="fee-pill">
                  <span className="fee-label">Base Freight:</span>
                  <span className="fee-val">{formatCurrency(quote.base_amount, quote.currency)}</span>
                </div>
                <div className="fee-pill">
                  <span className="fee-label">Surcharges:</span>
                  <span className="fee-val">{formatCurrency(quote.surcharge_amount, quote.currency)}</span>
                </div>
              </div>

              {/* Operational Specs */}
              <div className="operational-specs">
                <div className="spec-row">
                  <span className="spec-name">Transit Time:</span>
                  <span className="spec-val">
                    {quote.transit_days ? `${quote.transit_days} Days` : 'Not specified'}
                  </span>
                </div>

                <div className="spec-row">
                  <span className="spec-name">Vessel Class:</span>
                  <span className="spec-val">
                    {quote.vessel_class || 'Standard Vessel'}
                  </span>
                </div>

                {quote.cargo_capacity_tonnes && (
                  <div className="spec-row">
                    <span className="spec-name">Vessel Capacity:</span>
                    <span className="spec-val">
                      {Number(quote.cargo_capacity_tonnes).toLocaleString()} MT
                      {Number(quote.cargo_capacity_tonnes) < Number(shipment.quantity_tonnes) && (
                        <span className="text-rose-bold"> (Deficit vs {Number(shipment.quantity_tonnes).toLocaleString()} MT)</span>
                      )}
                    </span>
                  </div>
                )}
              </div>

              {/* Risk Assessment Box */}
              <div className="risk-assessment-card-box">
                <div className="risk-badge-header">
                  {getRiskLabelBadge(assessment?.label)}
                  <span className="risk-score-display">
                    Score: <strong>{assessment?.score ?? 0}</strong>/100
                  </span>
                </div>

                {flags.length > 0 ? (
                  <div className="risk-flags-summary">
                    <button
                      type="button"
                      className="risk-accordion-toggle"
                      onClick={() => toggleRiskExpand(quote.id)}
                    >
                      <span>
                        ⚠️ {flags.length} {flags.length === 1 ? 'Risk Flag' : 'Risk Flags'} Identified
                      </span>
                      <span>{isExpanded ? '▲ Hide' : '▼ Inspect'}</span>
                    </button>

                    {isExpanded && (
                      <div className="risk-flags-list">
                        {flags.map((flag) => (
                          <div key={flag.code} className="risk-flag-entry">
                            <div className="flag-title-row">
                              <span className={`flag-severity-pill severity-${flag.severity.toLowerCase()}`}>
                                {flag.severity}
                              </span>
                              <strong className="flag-title">{flag.title}</strong>
                            </div>
                            <p className="flag-evidence">
                              <strong>Evidence:</strong> {flag.evidence}
                            </p>
                            <p className="flag-check">
                              <strong>Check:</strong> {flag.recommended_check}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="risk-clean-notice">
                    ✓ No anomalies or risk indicators triggered
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="quote-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => onInspectQuote(quote)}
                >
                  Full Breakdown &amp; Terms
                </button>

                <button
                  type="button"
                  className={`btn btn-sm ${isSelected ? 'btn-success' : 'btn-primary'}`}
                  onClick={() => onSelectQuote(quote)}
                >
                  {isSelected ? '✓ Selected' : 'Select this Quote'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
