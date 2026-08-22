export interface User {
  id: number
  email: string
}

export interface BackendConfig {
  id: number
  endpoint_url: string
  openapi_url: string
  last_fetched_at: string | null
}

export interface Operation {
  operation_id: string
  method: string
  path: string
  summary: string | null
  is_active: boolean
}

export interface SchemaSnapshot {
  id: number
  fetched_at: string
  spec_hash: string
  diff_summary: string
}

export interface TokenSummary {
  id: string
  name: string
  created_at: string
  expires_at: string | null
  revoked_at: string | null
  last_used_at: string | null
}

export interface TokenDetail extends TokenSummary {
  operation_ids: string[]
}

export interface TokenCreateResponse extends TokenDetail {
  raw_token: string
}

export interface RequestLog {
  id: number
  token_id: string | null
  operation_id: string | null
  method: string
  path: string
  status: number
  latency_ms: number
  created_at: string
}

export interface UsageSummary {
  period_days: number
  total_requests: number
  denied_requests: number
  forwarded_requests: number
}
