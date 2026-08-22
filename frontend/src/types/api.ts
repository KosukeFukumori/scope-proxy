export interface User {
  id: number
  email: string
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
