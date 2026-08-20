import { apiClient } from './client'
import type { BackendConfig, SchemaSnapshot } from '../types/api'

export function getBackendConfig(): Promise<BackendConfig> {
  return apiClient.get<BackendConfig>('/_admin/api/backend-config')
}

export function upsertBackendConfig(endpointUrl: string, openapiUrl: string): Promise<BackendConfig> {
  return apiClient.put<BackendConfig>('/_admin/api/backend-config', {
    endpoint_url: endpointUrl,
    openapi_url: openapiUrl,
  })
}

export function refreshBackendConfig(): Promise<SchemaSnapshot> {
  return apiClient.post<SchemaSnapshot>('/_admin/api/backend-config/refresh')
}
