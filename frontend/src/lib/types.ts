export interface User {
  id: string
  email: string
  username: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type?: string
}

export interface MessageResponse {
  message: string
}

export interface TwoFactorChallenge {
  two_factor_required: true
  user_id: string | null
  message: string
}

export type LoginResponse = TokenResponse | TwoFactorChallenge

export function isTwoFactorChallenge(
  response: LoginResponse,
): response is TwoFactorChallenge {
  return 'two_factor_required' in response && response.two_factor_required === true
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface TotpStatusResponse {
  enabled: boolean
  has_backup_codes: boolean
}

export interface TotpEnableResponse {
  secret: string
  qr_code: string
  backup_codes: string[]
}

export interface TotpVerifyResponse {
  message: string
  verified: boolean
}

export interface ApiKey {
  id: string
  name: string
  key_prefix: string
  scopes: string[] | null
  expires_at: string | null
  last_used_at: string | null
  is_revoked: boolean
  created_at: string
}

export interface ApiKeyListResponse {
  keys: ApiKey[]
}

export interface ApiKeyCreateResponse {
  id: string
  name: string
  key_prefix: string
  scopes: string[] | null
  expires_at: string | null
  api_key: string
}

export interface CreateApiKeyInput {
  name: string
  scopes?: string[]
  expires_in_days?: number
}

export interface AuditLog {
  id: string
  user_id: string | null
  action: string
  success: boolean
  ip_address: string | null
  created_at: string
}

export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  role?: string
  is_active?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface AuditListParams {
  page?: number
  page_size?: number
  search?: string
  action?: string
  user_id?: string
  success?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}
