import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircleIcon, MailCheckIcon } from 'lucide-react'

import { SubmitButton } from '@/components/common/submit-button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi, getErrorMessage } from '@/lib/api'

export function ResendVerificationPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    setSubmitting(true)

    try {
      const response = await authApi.resendVerification(email.trim())
      setMessage(response.message)
    } catch (submitError) {
      setError(getErrorMessage(submitError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Resend verification email</CardTitle>
        <CardDescription>
          Enter the email address used during registration.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {message ? (
          <Alert>
            <MailCheckIcon />
            <AlertTitle>Request received</AlertTitle>
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        ) : null}

        {error ? (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <SubmitButton className="w-full" loading={submitting}>
            Send verification email
          </SubmitButton>
        </form>

        <Link
          to="/login"
          className="block text-center text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Back to sign in
        </Link>
      </CardContent>
    </Card>
  )
}
