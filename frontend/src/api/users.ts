import { apiClient } from './client'
import type { UserSummary } from '../types/api'

export function listUsers(): Promise<UserSummary[]> {
  return apiClient.get<UserSummary[]>('/_admin/api/users')
}

export interface CreateUserInput {
  email: string
  password: string
}

export function createUser(input: CreateUserInput): Promise<UserSummary> {
  return apiClient.post<UserSummary>('/_admin/api/users', input)
}

export function deleteUser(id: number): Promise<void> {
  return apiClient.delete<void>(`/_admin/api/users/${id}`)
}
