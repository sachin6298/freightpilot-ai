import React from 'react';

interface HeaderProps {
  onOpenNewShipment: () => void;
  onResetDemo: () => void;
  isResetting: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  onOpenNewShipment,
  onResetDemo,
  isResetting,
}) => {
  return (
    <header className="header">
      <div className="brand">
        <div className="logo-icon">FP</div>
        <div>
          <div className="brand-header-row">
            <h1 className="brand-title">FreightPilot AI</h1>
            <span className="badge badge-demo">SANDBOX DEMO</span>
          </div>
          <p className="brand-subtitle">
            AI-Assisted Freight Procurement &amp; PayPal Risk Review
          </p>
        </div>
      </div>

      <div className="header-actions">
        <button
          className="btn btn-secondary btn-sm"
          onClick={onResetDemo}
          disabled={isResetting}
          title="Reset database to initial synthetic demo dataset"
        >
          {isResetting ? 'Resetting...' : '↺ Reset Demo Data'}
        </button>

        <button
          className="btn btn-primary btn-sm"
          onClick={onOpenNewShipment}
        >
          + New Shipment Request
        </button>
      </div>
    </header>
  );
};
