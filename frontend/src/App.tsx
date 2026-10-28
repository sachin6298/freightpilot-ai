import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { KpiCards } from './components/KpiCards';
import { ShipmentDetailCard } from './components/ShipmentDetailCard';
import { RateEstimateCard } from './components/RateEstimateCard';
import { QuoteComparisonView } from './components/QuoteComparisonView';
import { QuoteDetailModal } from './components/QuoteDetailModal';
import { NewShipmentModal } from './components/NewShipmentModal';
import { SelectedQuoteBanner } from './components/SelectedQuoteBanner';
import {
  fetchShipments,
  fetchShipmentQuotes,
  fetchShipmentEstimate,
  createShipment,
  resetDemoData,
} from './api';
import { Shipment, Quote, RateEstimate, ShipmentCreatePayload } from './types';

export default function App(): React.ReactElement {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [activeShipment, setActiveShipment] = useState<Shipment | null>(null);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [rateEstimate, setRateEstimate] = useState<RateEstimate | null>(null);
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null);
  const [inspectingQuote, setInspectingQuote] = useState<Quote | null>(null);

  const [isLoadingShipments, setIsLoadingShipments] = useState<boolean>(true);
  const [isLoadingQuotes, setIsLoadingQuotes] = useState<boolean>(false);
  const [isResetting, setIsResetting] = useState<boolean>(false);
  const [isNewShipmentOpen, setIsNewShipmentOpen] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => {
      setNotification((curr) => (curr === msg ? null : curr));
    }, 4500);
  };

  // Load quotes and statistical rate estimate for a shipment
  const loadQuotesAndEstimate = useCallback(async (shipmentId: string) => {
    setIsLoadingQuotes(true);
    try {
      const [quotesData, estimateData] = await Promise.all([
        fetchShipmentQuotes(shipmentId),
        fetchShipmentEstimate(shipmentId),
      ]);
      setQuotes(quotesData);
      setRateEstimate(estimateData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch quotes or rate estimate';
      setErrorMessage(msg);
      setQuotes([]);
      setRateEstimate(null);
    } finally {
      setIsLoadingQuotes(false);
    }
  }, []);

  // Initial load of shipments
  const loadShipments = useCallback(async (preserveActiveId?: string) => {
    setIsLoadingShipments(true);
    setErrorMessage(null);
    try {
      const data = await fetchShipments();
      setShipments(data);

      if (data.length > 0) {
        const target = preserveActiveId
          ? data.find((s) => s.id === preserveActiveId) || data[0]
          : data.find((s) => s.id === 'demo-shipment-001') || data[0];
        setActiveShipment(target);
        await loadQuotesAndEstimate(target.id);
      } else {
        setActiveShipment(null);
        setQuotes([]);
        setRateEstimate(null);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Cannot connect to backend API';
      setErrorMessage(msg);
    } finally {
      setIsLoadingShipments(false);
    }
  }, [loadQuotesAndEstimate]);

  useEffect(() => {
    loadShipments();
  }, [loadShipments]);

  // Handle switching active shipment
  const handleSelectShipment = async (shipmentId: string) => {
    const target = shipments.find((s) => s.id === shipmentId);
    if (target) {
      setActiveShipment(target);
      setSelectedQuote(null);
      await loadQuotesAndEstimate(target.id);
    }
  };

  // Handle creating a new shipment
  const handleCreateShipment = async (payload: ShipmentCreatePayload) => {
    const newShipment = await createShipment(payload);
    showNotification(`Shipment "${newShipment.cargo_type}" created successfully.`);
    await loadShipments(newShipment.id);
  };

  // Handle demo data reset
  const handleResetDemo = async () => {
    if (!window.confirm('Reset database to initial synthetic demo quotes?')) return;
    setIsResetting(true);
    try {
      await resetDemoData();
      setSelectedQuote(null);
      showNotification('Demo data reset to initial 3 synthetic quotes.');
      await loadShipments('demo-shipment-001');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Reset failed';
      setErrorMessage(msg);
    } finally {
      setIsResetting(false);
    }
  };

  const handleSelectQuote = (quote: Quote) => {
    if (selectedQuote?.id === quote.id) {
      setSelectedQuote(null);
      showNotification('Quote selection cleared.');
    } else {
      setSelectedQuote(quote);
      showNotification(`Selected quote ${quote.provider_label} (${quote.reference}).`);
    }
  };

  return (
    <div className="app-container">
      <Header
        onOpenNewShipment={() => setIsNewShipmentOpen(true)}
        onResetDemo={handleResetDemo}
        isResetting={isResetting}
      />

      {/* Global Notification Toast */}
      {notification && (
        <div className="toast-notification">
          <span>{notification}</span>
          <button className="toast-close" onClick={() => setNotification(null)}>×</button>
        </div>
      )}

      <main className="main-content">
        {/* Error Banner */}
        {errorMessage && (
          <div className="alert alert-error">
            <div className="alert-content">
              <strong>API Error:</strong> {errorMessage}
            </div>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => loadShipments(activeShipment?.id)}
            >
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoadingShipments && (
          <div className="card loading-card">
            <div className="spinner"></div>
            <p>Loading freight shipments, baseline estimates and risk signals...</p>
          </div>
        )}

        {/* Dashboard Content */}
        {!isLoadingShipments && activeShipment && (
          <>
            {/* KPI Statistics Bar */}
            <KpiCards shipment={activeShipment} quotes={quotes} />

            {/* Shipment Specifications Summary */}
            <ShipmentDetailCard
              shipment={activeShipment}
              allShipments={shipments}
              onSelectShipment={handleSelectShipment}
            />

            {/* Rate Estimate Baseline Card */}
            <RateEstimateCard
              estimate={rateEstimate}
              shipment={activeShipment}
            />

            {/* Quotes Comparison & Risk Section */}
            {isLoadingQuotes ? (
              <div className="card loading-card">
                <div className="spinner"></div>
                <p>Normalizing quotes and assessing risk indicators...</p>
              </div>
            ) : (
              <QuoteComparisonView
                quotes={quotes}
                shipment={activeShipment}
                selectedQuoteId={selectedQuote?.id || null}
                onSelectQuote={handleSelectQuote}
                onInspectQuote={(quote) => setInspectingQuote(quote)}
              />
            )}
          </>
        )}

        {/* Empty State when no shipments exist */}
        {!isLoadingShipments && !activeShipment && (
          <div className="card empty-state">
            <div className="empty-icon">🚢</div>
            <h3 className="empty-title">No Active Shipments</h3>
            <p className="empty-text">
              There are no shipments in the database. You can restore the demo dataset or create a new shipment.
            </p>
            <div className="empty-actions">
              <button className="btn btn-primary" onClick={handleResetDemo}>
                Restore Seeded Demo Shipment
              </button>
              <button className="btn btn-secondary" onClick={() => setIsNewShipmentOpen(true)}>
                + Create New Shipment
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Selected Quote Fixed Action Banner */}
      <SelectedQuoteBanner
        quote={selectedQuote}
        onClear={() => setSelectedQuote(null)}
        onInspect={(quote) => setInspectingQuote(quote)}
      />

      {/* Quote Detail Modal */}
      <QuoteDetailModal
        quote={inspectingQuote}
        shipment={activeShipment}
        isSelected={selectedQuote?.id === inspectingQuote?.id}
        onSelect={handleSelectQuote}
        onClose={() => setInspectingQuote(null)}
      />

      {/* New Shipment Modal */}
      <NewShipmentModal
        isOpen={isNewShipmentOpen}
        onClose={() => setIsNewShipmentOpen(false)}
        onSubmit={handleCreateShipment}
      />

      <footer className="footer">
        <p>
          FreightPilot AI &bull; PayPal AI Hackathon 2026 &bull; Milestone 4: Forecasting &amp; Explainable Risk Engine &bull; Sandbox Mode
        </p>
      </footer>
    </div>
  );
}
