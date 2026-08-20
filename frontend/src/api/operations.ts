import { apiClient } from './client'
import type { Operation, SchemaSnapshot } from '../types/api'

export function listOperations(isActive?: boolean): Promise<Operation[]> {
  const query = isActive === undefined ? '' : `?is_active=${isActive}`
  return apiClient.get<Operation[]>(`/_admin/api/operations${query}`)
}

export function listSchemaSnapshots(): Promise<SchemaSnapshot[]> {
  return apiClient.get<SchemaSnapshot[]>('/_admin/api/schema-snapshots')
}
