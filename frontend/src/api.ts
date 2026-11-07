/** Typed API client. Authentication is optional in local demo mode. */
import {
  AnalyticsOverview, ApiError, AuthResponse, CarrierCatalog, CarrierPerformance,
  CopilotResult, NotificationItem, PaymentRecord, PaymentOrderResponse, Quote,
  RateEstimate, Shipment, ShipmentCreatePayload, TrackingEvent, UserProfile,
} from './types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const TOKEN_KEY = 'freightpilot_access_token';

export function getAuthToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string | null): void {
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  headers.set('Accept', 'application/json');
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const token = getAuthToken();
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new Error(`Cannot reach the API at ${API_BASE_URL}. Confirm that the FastAPI server is running.`);
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const payload = (await response.json()) as ApiError;
      const detail = payload.error || payload.detail;
      if (typeof detail === 'string') message = detail;
      else if (detail?.message) message = detail.message;
    } catch {
      // Keep status-based fallback when a server returns non-JSON content.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const fetchHealth = () => request<{ status: string; app: string; mode: string; database: string }>('/health');
export const fetchShipments = () => request<Shipment[]>('/api/shipments?limit=100');
export const fetchShipment = (id: string) => request<Shipment>(`/api/shipments/${encodeURIComponent(id)}`);
export const createShipment = (payload: ShipmentCreatePayload) => request<Shipment>('/api/shipments', { method: 'POST', body: JSON.stringify(payload) });
export const cancelShipment = (id: string) => request<Shipment>(`/api/shipments/${encodeURIComponent(id)}/cancel`, { method: 'POST' });
export const fetchShipmentQuotes = (id: string) => request<Quote[]>(`/api/shipments/${encodeURIComponent(id)}/quotes`);
export const fetchShipmentEstimate = (id: string) => request<RateEstimate>(`/api/shipments/${encodeURIComponent(id)}/estimate`);
export const assessQuote = (id: string) => request<Quote>(`/api/quotes/${encodeURIComponent(id)}/assess`, { method: 'POST' });
export const fetchAnalyticsOverview = () => request<AnalyticsOverview>('/api/analytics/overview');
export const fetchCarrierPerformance = () => request<{ items: CarrierPerformance[]; note?: string }>('/api/analytics/carriers');
export const fetchCarrierCatalog = () => request<CarrierCatalog>('/api/carriers');
export const refreshCarrierQuotes = (shipmentId: string, carrierCode: string) => request<{ created_count: number; quote_ids: string[] }>(`/api/shipments/${encodeURIComponent(shipmentId)}/refresh-quotes?carrier_code=${encodeURIComponent(carrierCode)}`, { method: 'POST' });
export const fetchTracking = (shipmentId: string) => request<TrackingEvent[]>(`/api/shipments/${encodeURIComponent(shipmentId)}/tracking`);
export const addTrackingEvent = (shipmentId: string, payload: { status: string; location?: string; description: string }) => request<TrackingEvent>(`/api/shipments/${encodeURIComponent(shipmentId)}/tracking`, { method: 'POST', body: JSON.stringify(payload) });
export const fetchNotifications = () => request<NotificationItem[]>('/api/notifications?limit=30');
export const markNotificationRead = (id: string) => request<NotificationItem>(`/api/notifications/${encodeURIComponent(id)}/read`, { method: 'POST' });
export const fetchShipmentPayments = (shipmentId: string) => request<PaymentRecord[]>(`/api/shipments/${encodeURIComponent(shipmentId)}/payments`);
export const createPaymentOrder = (quoteId: string, idempotencyKey: string) => request<PaymentOrderResponse>('/api/payments/create-order', { method: 'POST', body: JSON.stringify({ quote_id: quoteId, idempotency_key: idempotencyKey }) });
export const capturePayment = (paymentId: string, providerOrderId: string) => request<PaymentRecord>(`/api/payments/${encodeURIComponent(paymentId)}/capture`, { method: 'POST', body: JSON.stringify({ provider_order_id: providerOrderId }) });
export const compareQuotesWithCopilot = (shipmentId: string, quoteIds: string[]) => request<CopilotResult>('/api/copilot/compare', { method: 'POST', body: JSON.stringify({ shipment_id: shipmentId, quote_ids: quoteIds }) });
export const fetchCopilotHistory = (shipmentId?: string) => request<Array<{ id: string; shipment_id: string; task: string; input: unknown; response: CopilotResult; created_at: string }>>(`/api/copilot/history${shipmentId ? `?shipment_id=${encodeURIComponent(shipmentId)}` : ''}`);
export const login = (email: string, password: string) => request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
export const register = (email: string, password: string) => request<AuthResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) });
export const registerBuyer = (payload: { email: string; password: string; company_name?: string; contact_person?: string; phone_number?: string }) =>
  request<AuthResponse>('/api/auth/register/buyer', { method: 'POST', body: JSON.stringify(payload) });
export const registerSeller = (payload: { email: string; password: string; business_name: string; business_address: string; country: string; contact_person: string; contact_phone: string; registration_number?: string }) =>
  request<AuthResponse>('/api/auth/register/seller', { method: 'POST', body: JSON.stringify(payload) });

export const sendEmailVerification = () => request<{ code: string; message: string; verification_token?: string }>('/api/auth/send-email-verification', { method: 'POST', body: JSON.stringify({}) });
export const verifyEmail = (token: string) => request<{ code: string; message: string }>('/api/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) });
export const sendPhoneVerification = (phoneNumber: string) => request<{ code: string; message: string; otp?: string }>('/api/auth/send-phone-verification', { method: 'POST', body: JSON.stringify({ phone_number: phoneNumber }) });
export const verifyPhone = (phoneNumber: string, otp: string) => request<{ code: string; message: string }>('/api/auth/verify-phone', { method: 'POST', body: JSON.stringify({ phone_number: phoneNumber, otp }) });

export const editQuotePrice = (quoteId: string, payload: { base_amount: number; surcharge_amount: number; currency: string; revision_reason: string }) =>
  request<{ message: string; quote_id: string; revision_number: number; revised_amount: number }>(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/price`, { method: 'PUT', body: JSON.stringify(payload) });
export const fetchQuotePriceHistory = (quoteId: string) => request<any[]>(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/price-history`);

export const createCounterOffer = (quoteId: string, payload: { counter_amount: number; currency: string; notes?: string }) =>
  request<any>(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/counter-offer`, { method: 'POST', body: JSON.stringify(payload) });
export const respondCounterOffer = (counterId: string, decision: 'ACCEPT' | 'REJECT', responseNotes?: string) =>
  request<any>(`/api/marketplace/counter-offers/${encodeURIComponent(counterId)}/respond`, { method: 'POST', body: JSON.stringify({ decision, response_notes: responseNotes }) });
export const fetchCounterOffers = (quoteId: string) => request<any[]>(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/counter-offers`);

export const fetchSettlements = () => request<any[]>('/api/settlements');

export const calculateFreightEstimate = (payload: { cargo_type: string; quantity_tonnes: number; distance_km: number; transport_mode: string; currency: string }) =>
  request<any>('/api/calculator/estimate', { method: 'POST', body: JSON.stringify(payload) });

export const sendAiSupportChat = (message: string, shipmentId?: string, roleContext?: string) =>
  request<{ reply: string; disclaimer: string }>('/api/copilot/chat', { method: 'POST', body: JSON.stringify({ message, shipment_id: shipmentId, role_context: roleContext }) });

export const fetchCurrentUser = () => request<UserProfile>('/api/auth/me');
export const resetDemoData = () => request<{ status: string; shipment_id: string }>('/api/demo/reset', { method: 'POST' });

export const apiBaseUrl = API_BASE_URL;
export const paypalClientId = import.meta.env.VITE_PAYPAL_CLIENT_ID || '';
