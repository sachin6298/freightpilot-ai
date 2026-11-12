/**
 * API client service for FreightPilot AI.
 */

import { Shipment, Quote, ShipmentCreatePayload, ApiError, RateEstimate } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = (await res.json()) as ApiError;
      if (data?.error?.message) {
        errorDetail = data.error.message;
      }
    } catch {
      // Fallback to status text
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<{ status: string; app: string; mode: string }> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    headers: { Accept: 'application/json' },
  });
  return handleResponse(res);
}

export async function fetchShipments(): Promise<Shipment[]> {
  const res = await fetch(`${API_BASE_URL}/api/shipments`, {
    headers: { Accept: 'application/json' },
  });
  return handleResponse<Shipment[]>(res);
}

export async function fetchShipment(id: string): Promise<Shipment> {
  const res = await fetch(`${API_BASE_URL}/api/shipments/${id}`, {
    headers: { Accept: 'application/json' },
  });
  return handleResponse<Shipment>(res);
}

export async function fetchShipmentQuotes(shipmentId: string): Promise<Quote[]> {
  const res = await fetch(`${API_BASE_URL}/api/shipments/${shipmentId}/quotes`, {
    headers: { Accept: 'application/json' },
  });
  return handleResponse<Quote[]>(res);
}

export async function fetchShipmentEstimate(shipmentId: string): Promise<RateEstimate> {
  const res = await fetch(`${API_BASE_URL}/api/shipments/${shipmentId}/estimate`, {
    headers: { Accept: 'application/json' },
  });
  return handleResponse<RateEstimate>(res);
}

export async function recalculateQuoteAssessment(quoteId: string): Promise<Quote> {
  const res = await fetch(`${API_BASE_URL}/api/quotes/${quoteId}/assess`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  return handleResponse<Quote>(res);
}

export async function createShipment(payload: ShipmentCreatePayload): Promise<Shipment> {
  const res = await fetch(`${API_BASE_URL}/api/shipments`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse<Shipment>(res);
}

export async function resetDemoData(): Promise<{ status: string; shipment_id: string }> {
  const res = await fetch(`${API_BASE_URL}/api/demo/reset`, {
    method: 'POST',
    headers: { Accept: 'application/json' },
  });
  return handleResponse(res);
}
