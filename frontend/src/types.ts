/**
 * TypeScript types for FreightPilot AI frontend.
 */

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
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  evidence: string;
  recommended_check: string;
}

export interface RiskAssessment {
  score: number;
  label: 'LOWER_CONCERN' | 'REVIEW' | 'HIGH_ATTENTION' | 'INSUFFICIENT_DATA';
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
  coverage_status: 'REPRESENTATIVE_DEMO' | 'INSUFFICIENT_DATA';
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

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
