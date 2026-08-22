import { apiClient } from './client'
import type { SetupStatus, User } from '../types/api'

export function getSetupStatus(): Promise<SetupStatus> {
  return apiClient.get<SetupStatus>('/_admin/api/setup/status')
}

export function setup(username: string, password: string): Promise<User> {
  return apiClient.post<User>('/_admin/api/setup', { username, password })
}

export function login(username: string, password: string): Promise<User> {
  return apiClient.post<User>('/_admin/api/login', { username, password })
}

export function logout(): Promise<void> {
  return apiClient.post<void>('/_admin/api/logout')
}

export function getCurrentUser(): Promise<User> {
  return apiClient.get<User>('/_admin/api/me')
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return apiClient.patch<void>('/_admin/api/me/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}

export function changeUsername(username: string): Promise<User> {
  return apiClient.patch<User>('/_admin/api/me/username', { username })
}
