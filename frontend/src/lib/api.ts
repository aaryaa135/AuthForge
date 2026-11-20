import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

import type {
  ApiKeyCreateResponse,
  ApiKeyListResponse,
  AuditListParams,
  AuditLog,
  CreateApiKeyInput,
  LoginResponse,
  MessageResponse,
  Paginated,
  TokenResponse,
  TotpEnableResponse,
  TotpStatusResponse,
  TotpVerifyResponse,
  User,
  UserListParams,
} from './types'

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)
const API_ROOT = `${API_BASE_URL}/api/v1`
const REFRESH_STORAGE_KEY = 'authforge.refresh_token'

function readStoredRefreshToken(): string | null {
  try {
    return window.localStorage.getItem(REFRESH_STORAGE_KEY)
  } catch {
    return null
  }
}

let accessToken: string | null = null
let refreshToken: string | null = readStoredRefreshToken()

export const tokenStore = {
  getAccess(): string | null {
    return accessToken
  },
  getRefresh(): string | null {
    return refreshToken
  },
  setTokens(tokens: TokenResponse): void {
    accessToken = tokens.access_token
    refreshToken = tokens.refresh_token
    try {
      window.localStorage.setItem(REFRESH_STORAGE_KEY, tokens.refresh_token)
    } catch {
      // Storage can be unavailable in private mode; the session still works in memory.
    }
  },
  clear(): void {
    accessToken = null
    refreshToken = null
    try {
      window.localStorage.removeItem(REFRESH_STORAGE_KEY)
    } catch {
      // Ignore storage failures.
    }
  },
}

export const api = axios.create({
  baseURL: API_ROOT,
  headers: { 'Content-Type': 'application/json' },
})

const PUBLIC_AUTH_PATHS = [
  '/auth/login',
  '/auth/refresh',
  '/auth/register',
  '/auth/2fa/login-verify',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/auth/verify-email',
  '/auth/resend-verification',
]

function isPublicAuthRequest(url?: string): boolean {
  if (!url) return false
  return PUBLIC_AUTH_PATHS.some((path) => url.includes(path))
}

let refreshPromise: Promise<TokenResponse> | null = null

async function performRefresh(): Promise<TokenResponse> {
  const currentRefreshToken = tokenStore.getRefresh()

  if (!currentRefreshToken) {
    throw new Error('No refresh token available.')
  }

  const { data } = await axios.post<TokenResponse>(
    `${API_ROOT}/auth/refresh`,
    { refresh_token: currentRefreshToken },
    { headers: { 'Content-Type': 'application/json' } },
  )

  tokenStore.setTokens(data)
  return data
}

export function refreshSession(): Promise<TokenResponse> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.getAccess()

  if (token && !isPublicAuthRequest(config.url)) {
    config.headers.set('Authorization', `Bearer ${token}`)
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined

    const shouldRefresh =
      error.response?.status === 401 &&
      original !== undefined &&
      !original._retry &&
      !isPublicAuthRequest(original.url) &&
      tokenStore.getRefresh() !== null

    if (shouldRefresh && original) {
      original._retry = true

      try {
        const tokens = await refreshSession()
        original.headers.set('Authorization', `Bearer ${tokens.access_token}`)
        return await api(original)
      } catch {
        tokenStore.clear()
        window.dispatchEvent(new Event('authforge:unauthorized'))
      }
    }

    return Promise.reject(error)
  },
)

let bootstrapPromise: Promise<User> | null = null

export function bootstrapSession(): Promise<User> {
  if (!bootstrapPromise) {
    bootstrapPromise = (async () => {
      await refreshSession()
      const { data } = await api.get<User>('/auth/me')
      return data
    })().finally(() => {
      bootstrapPromise = null
    })
  }

  return bootstrapPromise
}

export const authApi = {
  async login(identifier: string, password: string): Promise<LoginResponse> {
    const body = new URLSearchParams({ username: identifier, password })
    const { data } = await api.post<LoginResponse>('/auth/login', body, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  async register(input: {
    email: string
    username: string
    password: string
  }): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>('/auth/register', input)
    return data
  },

  async me(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },

  async logout(): Promise<void> {
    const currentRefreshToken = tokenStore.getRefresh()

    try {
      if (currentRefreshToken) {
        await api.post<MessageResponse>('/auth/logout', {
          refresh_token: currentRefreshToken,
        })
      }
    } finally {
      tokenStore.clear()
    }
  },

  async forgotPassword(email: string): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>('/auth/forgot-password', {
      email,
    })
    return data
  },

  async resetPassword(token: string, newPassword: string): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>('/auth/reset-password', {
      token,
      new_password: newPassword,
    })
    return data
  },

  async changePassword(
    currentPassword: string,
    newPassword: string,
  ): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return data
  },

  async verifyEmail(token: string): Promise<MessageResponse> {
    const { data } = await api.get<MessageResponse>('/auth/verify-email', {
      params: { token },
    })
    return data
  },

  async resendVerification(email: string): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>(
      '/auth/resend-verification',
      { email },
    )
    return data
  },

  async completeTwoFactorLogin(userId: string, token: string): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>(
      '/auth/2fa/login-verify',
      { token },
      { params: { user_id: userId } },
    )
    return data
  },

  async totpStatus(): Promise<TotpStatusResponse> {
    const { data } = await api.get<TotpStatusResponse>('/auth/2fa/status')
    return data
  },

  async enableTotp(): Promise<TotpEnableResponse> {
    const { data } = await api.post<TotpEnableResponse>('/auth/2fa/enable')
    return data
  },

  async verifyTotpSetup(token: string): Promise<TotpVerifyResponse> {
    const { data } = await api.post<TotpVerifyResponse>('/auth/2fa/verify-setup', {
      token,
    })
    return data
  },

  async disableTotp(token: string): Promise<MessageResponse> {
    const { data } = await api.post<MessageResponse>('/auth/2fa/disable', { token })
    return data
  },
}

export const apiKeysApi = {
  async list(): Promise<ApiKeyListResponse> {
    const { data } = await api.get<ApiKeyListResponse>('/auth/api-keys')
    return data
  },

  async create(input: CreateApiKeyInput): Promise<ApiKeyCreateResponse> {
    const { data } = await api.post<ApiKeyCreateResponse>('/auth/api-keys', input)
    return data
  },

  async revoke(id: string): Promise<MessageResponse> {
    const { data } = await api.delete<MessageResponse>(`/auth/api-keys/${id}`)
    return data
  },
}

export const usersApi = {
  async list(params: UserListParams): Promise<Paginated<User>> {
    const { data } = await api.get<Paginated<User>>('/users/', { params })
    return data
  },

  async get(id: string): Promise<User> {
    const { data } = await api.get<User>(`/users/${id}`)
    return data
  },

  async updateRole(id: string, role: string): Promise<User> {
    const { data } = await api.patch<User>(`/users/${id}/role`, { role })
    return data
  },

  async updateStatus(id: string, isActive: boolean): Promise<User> {
    const { data } = await api.patch<User>(`/users/${id}/status`, {
      is_active: isActive,
    })
    return data
  },
}

export const auditApi = {
  async list(params: AuditListParams): Promise<Paginated<AuditLog>> {
    const { data } = await api.get<Paginated<AuditLog>>('/audit/', { params })
    return data
  },
}

interface ValidationIssue {
  msg?: unknown
  loc?: unknown[]
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as { detail?: unknown } | undefined
    const detail = payload?.detail

    if (typeof detail === 'string') {
      return detail
    }

    if (Array.isArray(detail)) {
      return detail
        .map((issue: ValidationIssue) =>
          typeof issue?.msg === 'string' ? issue.msg : 'Invalid value.',
        )
        .join(' ')
    }

    if (error.code === 'ERR_NETWORK') {
      return 'Cannot reach the AuthForge API. Make sure the backend is running.'
    }
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'Something went wrong. Please try again.'
}
