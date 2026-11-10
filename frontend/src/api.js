const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const TOKEN_KEY = 'freightpilot_access_token';
export function getAuthToken() {
    return window.localStorage.getItem(TOKEN_KEY);
}
export function setAuthToken(token) {
    if (token)
        window.localStorage.setItem(TOKEN_KEY, token);
    else
        window.localStorage.removeItem(TOKEN_KEY);
}
async function request(path, init = {}) {
    const headers = new Headers(init.headers || {});
    headers.set('Accept', 'application/json');
    if (init.body && !headers.has('Content-Type'))
        headers.set('Content-Type', 'application/json');
    const token = getAuthToken();
    if (token)
        headers.set('Authorization', `Bearer ${token}`);
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
    }
    catch {
        throw new Error(`Cannot reach the API at ${API_BASE_URL}. Confirm that the FastAPI server is running.`);
    }
    if (!response.ok) {
        let message = `Request failed (${response.status}).`;
        try {
            const payload = (await response.json());
            const detail = payload.error || payload.detail;
            if (typeof detail === 'string')
                message = detail;
            else if (detail?.message)
                message = detail.message;
        }
        catch {
            // Keep status-based fallback when a server returns non-JSON content.
        }
        throw new Error(message);
    }
    if (response.status === 204)
        return undefined;
    return response.json();
}
export const fetchHealth = () => request('/health');
export const fetchShipments = () => request('/api/shipments?limit=100');
export const fetchShipment = (id) => request(`/api/shipments/${encodeURIComponent(id)}`);
export const createShipment = (payload) => request('/api/shipments', { method: 'POST', body: JSON.stringify(payload) });
export const cancelShipment = (id) => request(`/api/shipments/${encodeURIComponent(id)}/cancel`, { method: 'POST' });
export const fetchShipmentQuotes = (id) => request(`/api/shipments/${encodeURIComponent(id)}/quotes`);
export const fetchShipmentEstimate = (id) => request(`/api/shipments/${encodeURIComponent(id)}/estimate`);
export const assessQuote = (id) => request(`/api/quotes/${encodeURIComponent(id)}/assess`, { method: 'POST' });
export const fetchAnalyticsOverview = () => request('/api/analytics/overview');
export const fetchCarrierPerformance = () => request('/api/analytics/carriers');
export const fetchCarrierCatalog = () => request('/api/carriers');
export const refreshCarrierQuotes = (shipmentId, carrierCode) => request(`/api/shipments/${encodeURIComponent(shipmentId)}/refresh-quotes?carrier_code=${encodeURIComponent(carrierCode)}`, { method: 'POST' });
export const fetchTracking = (shipmentId) => request(`/api/shipments/${encodeURIComponent(shipmentId)}/tracking`);
export const addTrackingEvent = (shipmentId, payload) => request(`/api/shipments/${encodeURIComponent(shipmentId)}/tracking`, { method: 'POST', body: JSON.stringify(payload) });
export const fetchNotifications = () => request('/api/notifications?limit=30');
export const markNotificationRead = (id) => request(`/api/notifications/${encodeURIComponent(id)}/read`, { method: 'POST' });
export const fetchShipmentPayments = (shipmentId) => request(`/api/shipments/${encodeURIComponent(shipmentId)}/payments`);
export const createPaymentOrder = (quoteId, idempotencyKey) => request('/api/payments/create-order', { method: 'POST', body: JSON.stringify({ quote_id: quoteId, idempotency_key: idempotencyKey }) });
export const capturePayment = (paymentId, providerOrderId) => request(`/api/payments/${encodeURIComponent(paymentId)}/capture`, { method: 'POST', body: JSON.stringify({ provider_order_id: providerOrderId }) });
export const compareQuotesWithCopilot = (shipmentId, quoteIds) => request('/api/copilot/compare', { method: 'POST', body: JSON.stringify({ shipment_id: shipmentId, quote_ids: quoteIds }) });
export const fetchCopilotHistory = (shipmentId) => request(`/api/copilot/history${shipmentId ? `?shipment_id=${encodeURIComponent(shipmentId)}` : ''}`);
export const login = (email, password) => request('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
export const register = (email, password) => request('/api/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) });
export const registerBuyer = (payload) => request('/api/auth/register/buyer', { method: 'POST', body: JSON.stringify(payload) });
export const registerSeller = (payload) => request('/api/auth/register/seller', { method: 'POST', body: JSON.stringify(payload) });
export const sendEmailVerification = () => request('/api/auth/send-email-verification', { method: 'POST', body: JSON.stringify({}) });
export const verifyEmail = (token) => request('/api/auth/verify-email', { method: 'POST', body: JSON.stringify({ token }) });
export const sendPhoneVerification = (phoneNumber) => request('/api/auth/send-phone-verification', { method: 'POST', body: JSON.stringify({ phone_number: phoneNumber }) });
export const verifyPhone = (phoneNumber, otp) => request('/api/auth/verify-phone', { method: 'POST', body: JSON.stringify({ phone_number: phoneNumber, otp }) });
export const editQuotePrice = (quoteId, payload) => request(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/price`, { method: 'PUT', body: JSON.stringify(payload) });
export const fetchQuotePriceHistory = (quoteId) => request(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/price-history`);
export const createCounterOffer = (quoteId, payload) => request(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/counter-offer`, { method: 'POST', body: JSON.stringify(payload) });
export const respondCounterOffer = (counterId, decision, responseNotes) => request(`/api/marketplace/counter-offers/${encodeURIComponent(counterId)}/respond`, { method: 'POST', body: JSON.stringify({ decision, response_notes: responseNotes }) });
export const fetchCounterOffers = (quoteId) => request(`/api/marketplace/quotes/${encodeURIComponent(quoteId)}/counter-offers`);
export const fetchSettlements = () => request('/api/settlements');
export const calculateFreightEstimate = (payload) => request('/api/calculator/estimate', { method: 'POST', body: JSON.stringify(payload) });
export const sendAiSupportChat = (message, shipmentId, roleContext) => request('/api/copilot/chat', { method: 'POST', body: JSON.stringify({ message, shipment_id: shipmentId, role_context: roleContext }) });
export const fetchCurrentUser = () => request('/api/auth/me');
export const resetDemoData = () => request('/api/demo/reset', { method: 'POST' });
export const apiBaseUrl = API_BASE_URL;
export const paypalClientId = import.meta.env.VITE_PAYPAL_CLIENT_ID || '';
export const oauthSignIn = (provider, idToken, nonce, authorizationCode) => request(`/api/auth/oauth/${provider}`, {
    method: 'POST',
    body: JSON.stringify(provider === 'apple'
        ? { authorization_code: authorizationCode, nonce }
        : { id_token: idToken, nonce }),
});
export const requestPhoneLoginOtp = (phoneNumber) => request('/api/auth/phone/request', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
});
export const verifyPhoneLoginOtp = (phoneNumber, otp) => request('/api/auth/phone/verify', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp }),
});
export const updateAccountPhone = (phoneNumber) => request('/api/auth/me/phone', {
    method: 'PUT',
    body: JSON.stringify({ phone_number: phoneNumber }),
});
export const sendAccountPhoneVerification = (phoneNumber) => request('/api/auth/send-phone-verification', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber }),
});
export const verifyAccountPhone = (phoneNumber, otp) => request('/api/auth/verify-phone', {
    method: 'POST',
    body: JSON.stringify({ phone_number: phoneNumber, otp }),
});
// Firebase Phone Authentication endpoints
export const verifyFirebasePhone = (idToken, phoneNumber) => request('/api/auth/firebase/verify-phone', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken, phone_number: phoneNumber }),
});
export const linkFirebasePhone = (idToken, phoneNumber) => request('/api/auth/firebase/link-phone', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken, phone_number: phoneNumber }),
});
