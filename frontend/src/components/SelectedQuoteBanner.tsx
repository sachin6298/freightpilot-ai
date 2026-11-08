import React from 'react';
import { Quote } from '../types';

interface SelectedQuoteBannerProps {
  quote: Quote | null;
  onClear: () => void;
  onInspect: (quote: Quote) => void;
}

export const SelectedQuoteBanner: React.FC<SelectedQuoteBannerProps> = ({
  quote,
  onClear,
  onInspect,
}) => {
  if (!quote) return null;

  const formatCurrency = (val: number | string, cur = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cur,
    }).format(Number(val));
  };

  return (
    <aside className="selected-quote-banner" aria-label="Selected Quote Summary">
      <div className="banner-content">
        <div className="banner-info">
          <span className="banner-status-badge">✓ Selected Quote</span>
          <div className="banner-details">
            <span className="banner-carrier">{quote.provider_label}</span>
            <span className="banner-ref">({quote.reference})</span>
            <span className="banner-amount">
              {formatCurrency(quote.total_amount, quote.currency)}
            </span>
          </div>
        </div>

        <div className="banner-workflow-status">
          <span className="workflow-pill">
            Server Amount Locked &bull; Ready for Sandbox Review (Milestone 5)
          </span>
        </div>

        <div className="banner-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => onInspect(quote)}
          >
            Review Breakdown
          </button>
          <button
            className="btn btn-outline-danger btn-sm"
            onClick={onClear}
            title="Deselect this quote"
          >
            Clear Selection
          </button>
        </div>
      </div>
    </aside>
  );
};
