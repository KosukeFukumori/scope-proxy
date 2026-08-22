import { apiClient } from './client'
import type { BackendConfig, BackendConfigEnvPreset, SchemaRefreshResult } from '../types/api'

export function getBackendConfig(): Promise<BackendConfig> {
  return apiClient.get<BackendConfig>('/_admin/api/backend-config')
}

export function getBackendConfigEnvPreset(): Promise<BackendConfigEnvPreset> {
  return apiClient.get<BackendConfigEnvPreset>('/_admin/api/backend-config/env-preset')
}

export function upsertBackendConfig(
  endpointUrl: string,
  openapiUrl: string,
  schemaSyncIntervalSeconds: number | null,
): Promise<BackendConfig> {
  return apiClient.put<BackendConfig>('/_admin/api/backend-config', {
    endpoint_url: endpointUrl,
    openapi_url: openapiUrl,
    schema_sync_interval_seconds: schemaSyncIntervalSeconds,
  })
}

export function refreshBackendConfig(): Promise<SchemaRefreshResult> {
  return apiClient.post<SchemaRefreshResult>('/_admin/api/backend-config/refresh')
}
