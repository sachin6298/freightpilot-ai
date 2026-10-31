/** Domain types returned by the FreightPilot AI FastAPI backend. */
export interface Shipment {
  id: string;
  cargo_type: string;
  quantity_tonnes: number | string;
  origin: string;
  destination: string;
  ready_date: string;
  required_arrival_date?: string | null;
  currency: string;
  mode: string;
  status: string;
  created_at: string;
  updated_at: string;
  quotes_count?: number;
}

export interface QuoteTerms {
  fuel_surcharge?: number;
  port_dues?: number;
  payment_terms?: string;
  advance_pct?: number;
  itemized?: boolean;
  demurrage_rate_daily?: number;
  [key: string]: unknown;
}

export interface RiskFlag {
  code: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW' | string;
  title: string;
  evidence: string;
  recommended_check: string;
}

export interface RiskAssessment {
  score: number;
  label: 'LOWER_CONCERN' | 'REVIEW' | 'HIGH_ATTENTION' | 'INSUFFICIENT_DATA' | string;
  flags: RiskFlag[];
  method_version: string;
  benchmark_variance_pct?: number | null;
  assessed_at?: string | null;
}

export interface RateEstimate {
  currency: string;
  median_rate?: number | null;
  min_rate?: number | null;
  max_rate?: number | null;
  sample_size: number;
  coverage_status: 'REPRESENTATIVE_DEMO' | 'INSUFFICIENT_DATA' | string;
  method: string;
  disclaimer: string;
}

export interface Quote {
  id: string;
  shipment_id: string;
  provider_label: string;
  reference: string;
  base_amount: number | string;
  surcharge_amount: number | string;
  total_amount: number | string;
  currency: string;
  transit_days?: number | null;
  validity_until?: string | null;
  vessel_class?: string | null;
  cargo_capacity_tonnes?: number | string | null;
  terms?: QuoteTerms | null;
  source_kind: string;
  created_at: string;
  assessment?: RiskAssessment | null;
  benchmark_variance_pct?: number | null;
}

export interface ShipmentCreatePayload {
  cargo_type: string;
  quantity_tonnes: number;
  origin: string;
  destination: string;
  ready_date: string;
  required_arrival_date?: string | null;
  currency: string;
}

export interface AnalyticsOverview {
  shipment_count: number;
  active_shipments: number;
  delivered_shipments: number;
  shipment_status_counts: Record<string, number>;
  quote_count: number;
  high_attention_quotes: number;
  payment_attempts: number;
  captured_payments: number;
  captured_spend_by_currency: Array<{ currency: string; amount: string }>;
  data_scope: string;
}

export interface CarrierPerformance {
  carrier: string;
  currency: string;
  quote_count: number;
  average_quote?: string | null;
  lowest_quote?: string | null;
  average_transit_days?: number | null;
  data_source: string;
}

export interface TrackingEvent {
  id: string;
  shipment_id: string;
  status: string;
  location?: string | null;
  description: string;
  source_kind: string;
  occurred_at: string;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  shipment_id?: string | null;
  kind: string;
  title: string;
  message: string;
  read_at?: string | null;
  created_at: string;
}

export interface PaymentRecord {
  payment_id: string;
  shipment_id: string;
  quote_id: string;
  provider: string;
  provider_order_id: string;
  provider_capture_id?: string | null;
  provider_refund_id?: string | null;
  status: string;
  amount: string;
  currency: string;
  last_verified_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CarrierCatalogItem {
  code: string;
  name: string;
  status?: string;
  description?: string;
  [key: string]: unknown;
}

export interface CarrierCatalog {
  items: CarrierCatalogItem[];
  live_integrations_available: boolean;
  note?: string | null;
}

export interface CopilotComparison {
  quote_id: string;
  advantages: string[];
  concerns: string[];
}

export interface CopilotResult {
  summary: string;
  comparison: CopilotComparison[];
  missing_information: string[];
  next_questions: string[];
  disclaimer: string;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserProfile;
}

export interface PaymentOrderResponse extends PaymentRecord {}

export interface ApiError {
  error?: { code?: string; message?: string };
  detail?: string | { code?: string; message?: string };
}
