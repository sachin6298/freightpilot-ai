# FreightPilot AI Frontend

React 18 + TypeScript + Vite UI for the FreightPilot AI FastAPI backend.

## Setup (Windows PowerShell)

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run build
npm run dev
```

Open <http://localhost:5173>.

## Environment variables

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_PAYPAL_CLIENT_ID=YOUR_SANDBOX_CLIENT_ID
```

The PayPal Client ID is public. The PayPal Client Secret belongs only in `backend/.env` and must never be exposed through a `VITE_` variable.

## Pages and backend connections

| Page | Data / actions |
|---|---|
| Overview | `/api/analytics/overview`, `/api/analytics/carriers`, `/api/shipments` |
| Shipments | Create, list, cancel and manual tracking events |
| Freight quotes | Shipment quotes, benchmark estimate and quote assessment |
| Risk manager | Re-assess selected shipment quote records |
| AI Copilot | `/api/copilot/compare` with selected stored quote IDs |
| Payments | Shipment payment history and PayPal SDK create/approve/capture flow |
| Analytics | Shipment status, captured spend by currency and carrier aggregation |
| Settings | `/health`, carrier registry and client-side config presence |

## Notes

- The app supports Guest demo access while backend `AUTH_REQUIRED=false`; login and registration are also available.
- PayPal checkout requires the PayPal Sandbox Client ID in the frontend and the Sandbox Client ID/Secret in backend configuration.
- The frontend creates a PayPal order through FastAPI, returns the provider order ID to the PayPal JavaScript SDK, then asks FastAPI to verify/capture the approved order. It never decides the amount.
- Payment history is aggregated by requesting the payment list for each visible shipment; the backend currently has no global payments endpoint.
- Live carrier adapters are not supplied by default. Quote and tracking data are labeled by provenance and manual/demo records should not be presented as live.
