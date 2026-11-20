import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircleIcon, ShieldCheckIcon } from 'lucide-react'
import { toast } from 'sonner'

import { SubmitButton } from '@/components/common/submit-button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/context/auth-context'
import { getErrorMessage } from '@/lib/api'

const PENDING_USER_KEY = 'authforge.pending_2fa_user'
const PENDING_REDIRECT_KEY = 'authforge.pending_2fa_redirect'

export function TwoFactorPage() {
  const { completeTwoFactorLogin } = useAuth()
  const navigate = useNavigate()

  const userId = sessionStorage.getItem(PENDING_USER_KEY)
  const redirectTo = sessionStorage.getItem(PENDING_REDIRECT_KEY) ?? '/dashboard'

  const [token, setToken] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (!userId) {
      setError('No pending two-factor sign-in was found. Please sign in again.')
      return
    }

    setSubmitting(true)

    try {
      await completeTwoFactorLogin(userId, token.trim())
      sessionStorage.removeItem(PENDING_USER_KEY)
      sessionStorage.removeItem(PENDING_REDIRECT_KEY)
      toast.success('Two-factor verification complete.')
      navigate(redirectTo, { replace: true })
    } catch (submitError) {
      setError(getErrorMessage(submitError))
    } finally {
      setSubmitting(false)
    }
  }

  if (!userId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Two-factor verification</CardTitle>
          <CardDescription>No pending sign-in was found.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertDescription>
              Start from the sign-in page so AuthForge can create a pending
              two-factor session.
            </AlertDescription>
          </Alert>
          <Link
            to="/login"
            className="text-sm font-medium text-foreground underline-offset-4 hover:underline"
          >
            Return to sign in
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex size-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600">
          <ShieldCheckIcon className="size-5" />
        </div>
        <CardTitle>Two-factor verification</CardTitle>
        <CardDescription>
          Enter the 6-digit code from your authenticator app, or use one of your
          single-use backup codes.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {error ? (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="totp-token">Authentication code</Label>
            <Input
              id="totp-token"
              inputMode="numeric"
              autoComplete="one-time-code"
              placeholder="123456 or backup code"
              value={token}
              onChange={(event) => setToken(event.target.value)}
              required
            />
          </div>

          <SubmitButton className="w-full" loading={submitting}>
            Verify and sign in
          </SubmitButton>
        </form>

        <div className="flex flex-col gap-2 text-sm">
          <Link
            to="/login"
            className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
          >
            Use a different account
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
