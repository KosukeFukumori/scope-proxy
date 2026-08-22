export interface User {
  id: number
  username: string
}

export interface SetupStatus {
  needs_setup: boolean
}

export interface BackendConfig {
  id: number
  endpoint_url: string
  openapi_url: string
  last_fetched_at: string | null
  last_sync_status: 'success' | 'error' | null
  last_sync_error: string | null
  schema_sync_interval_seconds: number | null
  effective_schema_sync_interval_seconds: number
  endpoint_url_locked: boolean
  openapi_url_locked: boolean
}

/** The raw ENDPOINT_URL / OPENAPI_URL env var values, if set. */
export interface BackendConfigEnvPreset {
  endpoint_url: string | null
  openapi_url: string | null
}

export interface Operation {
  operation_id: string
  method: string
  path: string
  openapi_operation_id: string | null
  summary: string | null
  is_active: boolean
}

export interface SchemaSnapshot {
  id: number
  fetched_at: string
  spec_hash: string
  diff_summary: string
}

export interface SchemaRefreshResult {
  snapshot: SchemaSnapshot
  /** Diff of this refresh run (snapshot.diff_summary may belong to an older run). */
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
