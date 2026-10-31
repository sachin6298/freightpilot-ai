import React, { useState } from 'react';
import { ShipmentCreatePayload } from '../types';

interface NewShipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (payload: ShipmentCreatePayload) => Promise<void>;
}

export const NewShipmentModal: React.FC<NewShipmentModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [cargoType, setCargoType] = useState('Containerized Electronics');
  const [quantityTonnes, setQuantityTonnes] = useState(1250);
  const [origin, setOrigin] = useState('Port of Singapore');
  const [destination, setDestination] = useState('Port of Los Angeles, USA');
  const [readyDate, setReadyDate] = useState('2026-11-20');
  const [arrivalDate, setArrivalDate] = useState('2026-12-15');
  const [currency, setCurrency] = useState('USD');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Frontend validation
    if (!cargoType.trim()) {
      setErrorMessage('Cargo description is required.');
      return;
    }
    if (quantityTonnes <= 0) {
      setErrorMessage('Quantity must be greater than zero tonnes.');
      return;
    }
    if (origin.trim().toLowerCase() === destination.trim().toLowerCase()) {
      setErrorMessage('Origin and destination ports must be different.');
      return;
    }
    if (arrivalDate && arrivalDate < readyDate) {
      setErrorMessage('Required arrival date cannot be earlier than ready date.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        cargo_type: cargoType.trim(),
        quantity_tonnes: Number(quantityTonnes),
        origin: origin.trim(),
        destination: destination.trim(),
        ready_date: readyDate,
        required_arrival_date: arrivalDate || null,
        currency,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create shipment.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePrefill = (sample: 'santos' | 'shanghai') => {
    if (sample === 'santos') {
      setCargoType('Soybean / Agricultural Bulk');
      setQuantityTonnes(30000);
      setOrigin('Port of Santos, Brazil');
      setDestination('Port of Rotterdam, Netherlands');
      setReadyDate('2026-11-12');
      setArrivalDate('2026-12-08');
      setCurrency('USD');
    } else {
      setCargoType('Industrial Machinery & Steel');
      setQuantityTonnes(8500);
      setOrigin('Port of Shanghai, China');
      setDestination('Port of Antwerp, Belgium');
      setReadyDate('2026-11-25');
      setArrivalDate('2026-12-28');
      setCurrency('USD');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content modal-md" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3 className="modal-title">Create Shipment Request</h3>
            <p className="modal-subtitle">Define cargo specifications and shipping route.</p>
          </div>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {/* Quick Prefill Bar */}
            <div className="prefill-bar">
              <span className="prefill-label">Prefill Demo Sample:</span>
              <button
                type="button"
                className="btn-prefill"
                onClick={() => handlePrefill('santos')}
              >
                Santos → Rotterdam (Grain 30k MT)
              </button>
              <button
                type="button"
                className="btn-prefill"
                onClick={() => handlePrefill('shanghai')}
              >
                Shanghai → Antwerp (Steel 8.5k MT)
              </button>
            </div>

            {errorMessage && (
              <div className="alert alert-error">
                <strong>Error:</strong> {errorMessage}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="cargo-type" className="form-label">Cargo Description / Category *</label>
              <input
                id="cargo-type"
                type="text"
                className="form-input"
                value={cargoType}
                onChange={(e) => setCargoType(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-2">
              <div className="form-group">
                <label htmlFor="quantity-tonnes" className="form-label">Quantity (Metric Tonnes) *</label>
                <input
                  id="quantity-tonnes"
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="form-input"
                  value={quantityTonnes}
                  onChange={(e) => setQuantityTonnes(parseFloat(e.target.value) || 0)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="currency-select" className="form-label">Comparison Currency *</label>
                <select
                  id="currency-select"
                  className="form-select"
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-2">
              <div className="form-group">
                <label htmlFor="origin-port" className="form-label">Origin Port / Location *</label>
                <input
                  id="origin-port"
                  type="text"
                  className="form-input"
                  value={origin}
                  onChange={(e) => setOrigin(e.target.value)}
                  placeholder="e.g. Port of Santos, Brazil"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="dest-port" className="form-label">Destination Port / Location *</label>
                <input
                  id="dest-port"
                  type="text"
                  className="form-input"
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  placeholder="e.g. Port of Rotterdam, Netherlands"
                  required
                />
              </div>
            </div>

            <div className="grid grid-2">
              <div className="form-group">
                <label htmlFor="ready-date" className="form-label">Cargo Ready Date *</label>
                <input
                  id="ready-date"
                  type="date"
                  className="form-input"
                  value={readyDate}
                  onChange={(e) => setReadyDate(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="arrival-date" className="form-label">Required Arrival Date</label>
                <input
                  id="arrival-date"
                  type="date"
                  className="form-input"
                  value={arrivalDate}
                  onChange={(e) => setArrivalDate(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating Shipment...' : 'Create Shipment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
