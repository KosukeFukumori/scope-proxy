import { apiClient } from './client'
import type { UsageSummary } from '../types/api'

export function getUsageSummary(days = 7): Promise<UsageSummary> {
  return apiClient.get<UsageSummary>(`/_admin/api/usage/summary?days=${days}`)
}
