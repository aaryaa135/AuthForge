import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { AlertCircleIcon, CheckCircle2Icon, Loader2Icon } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { authApi, getErrorMessage } from '@/lib/api'

type VerifyState =
  | { status: 'verifying' }
  | { status: 'success'; message: string }
  | { status: 'error'; message: string }

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const started = useRef(false)
  const [state, setState] = useState<VerifyState>(
    token
      ? { status: 'verifying' }
      : {
          status: 'error',
          message: 'This verification link is missing its token.',
        },
  )

  useEffect(() => {
    if (!token || started.current) return
    started.current = true

    let active = true

    authApi
      .verifyEmail(token)
      .then((response) => {
        if (active) {
          setState({ status: 'success', message: response.message })
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setState({ status: 'error', message: getErrorMessage(error) })
        }
      })

    return () => {
      active = false
    }
  }, [token])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
        <CardDescription>
          We are confirming the verification token from your email.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {state.status === 'verifying' ? (
          <div className="flex items-center gap-3 rounded-lg border p-4 text-sm text-muted-foreground">
            <Loader2Icon className="size-4 animate-spin" />
            Verifying your email address…
          </div>
        ) : null}

        {state.status === 'success' ? (
          <Alert>
            <CheckCircle2Icon />
            <AlertTitle>Email verified</AlertTitle>
            <AlertDescription>{state.message}</AlertDescription>
          </Alert>
        ) : null}

        {state.status === 'error' ? (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertTitle>Verification failed</AlertTitle>
            <AlertDescription>{state.message}</AlertDescription>
          </Alert>
        ) : null}

        <div className="flex flex-col gap-2 text-sm">
          <Link
            to="/login"
            className="font-medium text-foreground underline-offset-4 hover:underline"
          >
            Continue to sign in
          </Link>
          {state.status === 'error' ? (
            <Link
              to="/resend-verification"
              className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
            >
              Resend verification email
            </Link>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
