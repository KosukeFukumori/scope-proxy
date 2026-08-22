import { apiClient } from './client'
import type { TokenCreateResponse, TokenDetail, TokenSummary } from '../types/api'

export function listTokens(): Promise<TokenSummary[]> {
  return apiClient.get<TokenSummary[]>('/_admin/api/tokens')
}

export function getToken(id: string): Promise<TokenDetail> {
  return apiClient.get<TokenDetail>(`/_admin/api/tokens/${id}`)
}

export interface CreateTokenInput {
  name: string
  expires_at?: string | null
  operation_ids: string[]
}

export function createToken(input: CreateTokenInput): Promise<TokenCreateResponse> {
  return apiClient.post<TokenCreateResponse>('/_admin/api/tokens', input)
}

export interface UpdateTokenInput {
  name?: string
  expires_at?: string | null
  operation_ids?: string[]
}

export function updateToken(id: string, input: UpdateTokenInput): Promise<TokenDetail> {
  return apiClient.patch<TokenDetail>(`/_admin/api/tokens/${id}`, input)
}

export function revokeToken(id: string): Promise<TokenSummary> {
  return apiClient.post<TokenSummary>(`/_admin/api/tokens/${id}/revoke`)
}

export function deleteToken(id: string): Promise<void> {
  return apiClient.delete<void>(`/_admin/api/tokens/${id}`)
}
