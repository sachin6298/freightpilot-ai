import React from 'react';
import { Shipment } from '../types';

interface ShipmentDetailCardProps {
  shipment: Shipment;
  allShipments: Shipment[];
  onSelectShipment: (id: string) => void;
}

export const ShipmentDetailCard: React.FC<ShipmentDetailCardProps> = ({
  shipment,
  allShipments,
  onSelectShipment,
}) => {
  return (
    <div className="card shipment-summary-card">
      <div className="card-header">
        <div className="shipment-title-block">
          <div className="route-tags">
            <span className="route-port origin-port">{shipment.origin}</span>
            <span className="route-arrow">➔</span>
            <span className="route-port destination-port">{shipment.destination}</span>
          </div>
          <span className="shipment-id-badge">ID: {shipment.id}</span>
        </div>

        {allShipments.length > 1 && (
          <div className="shipment-switcher">
            <label htmlFor="shipment-select" className="switcher-label">
              Switch Shipment:
            </label>
            <select
              id="shipment-select"
              className="form-select"
              value={shipment.id}
              onChange={(e) => onSelectShipment(e.target.value)}
            >
              {allShipments.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.cargo_type} ({s.origin.split(',')[0]} → {s.destination.split(',')[0]})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="shipment-meta-grid">
        <div className="meta-item">
          <span className="meta-label">Cargo Category</span>
          <span className="meta-value">{shipment.cargo_type}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Quantity</span>
          <span className="meta-value">
            {Number(shipment.quantity_tonnes).toLocaleString()} Metric Tonnes
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Ready Date</span>
          <span className="meta-value">{shipment.ready_date}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Required Arrival</span>
          <span className="meta-value">
            {shipment.required_arrival_date || 'Flexible / Not Specified'}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Comparison Currency</span>
          <span className="meta-value">{shipment.currency}</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Dataset Provenance</span>
          <span className="meta-value badge-pill badge-demo-tag">
            {shipment.mode} MODE
          </span>
        </div>
      </div>
    </div>
  );
};
