import { apiClient } from './client'
import type { TokenCreateResponse, TokenDetail, TokenSummary } from '../types/api'

export function listTokens(): Promise<TokenSummary[]> {
  return apiClient.get<TokenSummary[]>('/_admin/api/tokens')
}

export function getToken(id: number): Promise<TokenDetail> {
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

export function updateToken(id: number, input: UpdateTokenInput): Promise<TokenDetail> {
  return apiClient.patch<TokenDetail>(`/_admin/api/tokens/${id}`, input)
}

export function revokeToken(id: number): Promise<TokenSummary> {
  return apiClient.post<TokenSummary>(`/_admin/api/tokens/${id}/revoke`)
}
