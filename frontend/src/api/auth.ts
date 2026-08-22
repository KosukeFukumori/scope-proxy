import { apiClient } from './client'
import type { User } from '../types/api'

export function login(email: string, password: string): Promise<User> {
  return apiClient.post<User>('/_admin/api/login', { email, password })
}

export function logout(): Promise<void> {
  return apiClient.post<void>('/_admin/api/logout')
}

export function getCurrentUser(): Promise<User> {
  return apiClient.get<User>('/_admin/api/me')
}

export interface ChangePasswordInput {
  current_password: string
  new_password: string
}

export function changePassword(input: ChangePasswordInput): Promise<void> {
  return apiClient.patch<void>('/_admin/api/me/password', input)
}
