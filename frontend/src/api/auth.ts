import { apiClient } from './client'
import type { User } from '../types/api'

export function login(email: string, password: string): Promise<User> {
  return apiClient.post<User>('/_admin/login', { email, password })
}

export function logout(): Promise<void> {
  return apiClient.post<void>('/_admin/logout')
}
