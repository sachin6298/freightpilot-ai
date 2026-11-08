import React, { useEffect, useRef, useState } from 'react';
import { capturePayment, createPaymentOrder, paypalClientId } from '../api';
import { PaymentRecord, Quote } from '../types';

type PayPalOrderData = { orderID: string };
type PayPalActions = unknown;
type PayPalButtonsInstance = { render: (container: HTMLElement) => Promise<void>; close?: () => void };
type PayPalNamespace = {
  Buttons: (options: {
    style?: { layout?: 'vertical' | 'horizontal'; color?: 'gold' | 'blue' | 'silver' | 'black' | 'white'; shape?: 'rect' | 'pill'; label?: 'paypal'; height?: number };
    createOrder: () => Promise<string>;
    onApprove: (data: PayPalOrderData, actions: PayPalActions) => Promise<void>;
    onCancel?: () => void;
    onError?: (error: unknown) => void;
  }) => PayPalButtonsInstance;
};

declare global {
  interface Window { paypal?: PayPalNamespace; }
}

let sdkPromise: Promise<void> | null = null;
let sdkSignature = '';

function loadPayPalSdk(clientId: string, currency: string): Promise<void> {
  const signature = `${clientId}:${currency}`;
  if (window.paypal && sdkSignature === signature) return Promise.resolve();
  if (sdkPromise && sdkSignature === signature) return sdkPromise;
  sdkSignature = signature;
  sdkPromise = new Promise((resolve, reject) => {
    const previous = document.getElementById('freightpilot-paypal-sdk');
    previous?.remove();
    delete window.paypal;
    const script = document.createElement('script');
    script.id = 'freightpilot-paypal-sdk';
    script.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(clientId)}&currency=${encodeURIComponent(currency)}&intent=capture&components=buttons`;
    script.async = true;
    script.onload = () => {
      if (window.paypal) resolve();
      else {
        sdkPromise = null;
        sdkSignature = '';
        reject(new Error('PayPal SDK loaded without exposing the Buttons API.'));
      }
    };
    script.onerror = () => {
      sdkPromise = null;
      sdkSignature = '';
      reject(new Error('PayPal SDK could not be loaded. Check network access and the Sandbox Client ID.'));
    };
    document.head.appendChild(script);
  });
  return sdkPromise;
}

interface PayPalCheckoutProps {
  quote: Quote;
  onSuccess: (payment: PaymentRecord) => void;
  onStatus: (message: string) => void;
}

export const PayPalCheckout: React.FC<PayPalCheckoutProps> = ({ quote, onSuccess, onStatus }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const paymentRef = useRef<PaymentRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let buttons: PayPalButtonsInstance | undefined;
    const clientId = paypalClientId;
    if (!clientId || clientId.toLowerCase().includes('replace')) {
      setLoading(false);
      setError('Add your PayPal Sandbox Client ID to frontend/.env.local and restart Vite to enable checkout.');
      return () => { active = false; };
    }

    setLoading(true);
    setError(null);
    loadPayPalSdk(clientId, quote.currency)
      .then(() => {
        if (!active || !containerRef.current || !window.paypal) return;
        containerRef.current.innerHTML = '';
        buttons = window.paypal.Buttons({
          style: { layout: 'vertical', color: 'gold', shape: 'rect', label: 'paypal', height: 46 },
          createOrder: async () => {
            const payment = await createPaymentOrder(quote.id, `fp-${crypto.randomUUID()}`);
            paymentRef.current = payment;
            return payment.provider_order_id;
          },
          onApprove: async (data) => {
            const payment = paymentRef.current;
            if (!payment) throw new Error('Payment order reference is missing. Refresh checkout and try again.');
            onStatus('Buyer approved the order. Verifying and capturing payment with the backend…');
            const captured = await capturePayment(payment.payment_id, data.orderID);
            onSuccess(captured);
          },
          onCancel: () => onStatus('Checkout was cancelled. No successful payment has been recorded.'),
          onError: (reason) => {
            const message = reason instanceof Error ? reason.message : 'PayPal checkout encountered an error.';
            setError(message);
          },
        });
        return buttons.render(containerRef.current);
      })
      .then(() => { if (active) setLoading(false); })
      .catch((reason: unknown) => {
        if (!active) return;
        setLoading(false);
        setError(reason instanceof Error ? reason.message : 'Unable to initialize PayPal checkout.');
      });

    return () => {
      active = false;
      try { buttons?.close?.(); } catch { /* PayPal may already have disposed the iframe. */ }
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, [quote.id, quote.currency, onSuccess, onStatus]);

  return (
    <div className="paypal-checkout-wrap">
      {loading && <div className="inline-loading"><span className="spinner small" /> Preparing secure PayPal checkout…</div>}
      {error && <div className="inline-alert inline-alert-warning">{error}</div>}
      <div ref={containerRef} className="paypal-button-container" />
      <p className="fine-print">Sandbox transaction only. The backend recalculates the payable amount from the saved quote and verifies the capture before marking the shipment as paid.</p>
    </div>
  );
};
