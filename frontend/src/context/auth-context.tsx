import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { authApi, bootstrapSession, tokenStore } from '@/lib/api'
import { isTwoFactorChallenge, type User } from '@/lib/types'

type AuthStatus = 'loading' | 'authenticated' | 'anonymous'

interface SignInResult {
  twoFactorRequired: boolean
  userId: string | null
}

interface AuthContextValue {
  user: User | null
  status: AuthStatus
  signIn: (identifier: string, password: string) => Promise<SignInResult>
  completeTwoFactorLogin: (userId: string, token: string) => Promise<void>
  signOut: () => Promise<void>
  resetSession: () => void
  refreshUser: () => Promise<User>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  useEffect(() => {
    let active = true

    async function restoreSession() {
      if (!tokenStore.getRefresh()) {
        if (active) setStatus('anonymous')
        return
      }

      try {
        const currentUser = await bootstrapSession()
        if (active) {
          setUser(currentUser)
          setStatus('authenticated')
        }
      } catch {
        tokenStore.clear()
        if (active) {
          setUser(null)
          setStatus('anonymous')
        }
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    function handleUnauthorized() {
      setUser(null)
      setStatus('anonymous')
    }

    window.addEventListener('authforge:unauthorized', handleUnauthorized)
    return () => {
      window.removeEventListener('authforge:unauthorized', handleUnauthorized)
    }
  }, [])

  const signIn = useCallback(
    async (identifier: string, password: string): Promise<SignInResult> => {
      const result = await authApi.login(identifier, password)

      if (isTwoFactorChallenge(result)) {
        return { twoFactorRequired: true, userId: result.user_id }
      }

      tokenStore.setTokens(result)

      try {
        const currentUser = await authApi.me()
        setUser(currentUser)
        setStatus('authenticated')
      } catch (error) {
        tokenStore.clear()
        throw error
      }

      return { twoFactorRequired: false, userId: null }
    },
    [],
  )

  const completeTwoFactorLogin = useCallback(async (userId: string, token: string) => {
    const tokens = await authApi.completeTwoFactorLogin(userId, token)
    tokenStore.setTokens(tokens)

    try {
      const currentUser = await authApi.me()
      setUser(currentUser)
      setStatus('authenticated')
    } catch (error) {
      tokenStore.clear()
      throw error
    }
  }, [])

  const signOut = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      tokenStore.clear()
      setUser(null)
      setStatus('anonymous')
    }
  }, [])

  const resetSession = useCallback(() => {
    tokenStore.clear()
    setUser(null)
    setStatus('anonymous')
  }, [])

  const refreshUser = useCallback(async () => {
    const currentUser = await authApi.me()
    setUser(currentUser)
    return currentUser
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      signIn,
      completeTwoFactorLogin,
      signOut,
      resetSession,
      refreshUser,
    }),
    [user, status, signIn, completeTwoFactorLogin, signOut, resetSession, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider.')
  }
  return context
}
