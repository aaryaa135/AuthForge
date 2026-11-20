import { useState, type FormEvent } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircleIcon,
  CheckCircle2Icon,
  KeyRoundIcon,
  ShieldCheckIcon,
} from 'lucide-react'
import { toast } from 'sonner'

import { CopyButton } from '@/components/common/copy-button'
import { PageHeader } from '@/components/common/page-header'
import { PasswordInput } from '@/components/common/password-input'
import { StatusBadge } from '@/components/common/status-badge'
import { SubmitButton } from '@/components/common/submit-button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/context/auth-context'
import { authApi, getErrorMessage } from '@/lib/api'
import type { TotpEnableResponse } from '@/lib/types'

export function SecurityPage() {
  const { resetSession } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const totpQuery = useQuery({
    queryKey: ['totp-status'],
    queryFn: authApi.totpStatus,
  })

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [changingPassword, setChangingPassword] = useState(false)

  const [enrollment, setEnrollment] = useState<TotpEnableResponse | null>(null)
  const [enrollmentError, setEnrollmentError] = useState<string | null>(null)
  const [startingEnrollment, setStartingEnrollment] = useState(false)
  const [setupCode, setSetupCode] = useState('')
  const [setupError, setSetupError] = useState<string | null>(null)
  const [verifyingSetup, setVerifyingSetup] = useState(false)

  const [disableCode, setDisableCode] = useState('')
  const [disableError, setDisableError] = useState<string | null>(null)
  const [disabling, setDisabling] = useState(false)

  async function handlePasswordChange(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPasswordError(null)

    if (newPassword.length < 8 || newPassword.length > 128) {
      setPasswordError('New password must be between 8 and 128 characters.')
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.')
      return
    }

    setChangingPassword(true)

    try {
      await authApi.changePassword(currentPassword, newPassword)
      toast.success('Password changed. Please sign in again.')
      resetSession()
      navigate('/login', { replace: true })
    } catch (error) {
      setPasswordError(getErrorMessage(error))
    } finally {
      setChangingPassword(false)
    }
  }

  async function handleStartEnrollment() {
    setEnrollmentError(null)
    setStartingEnrollment(true)

    try {
      const response = await authApi.enableTotp()
      setEnrollment(response)
    } catch (error) {
      setEnrollmentError(getErrorMessage(error))
      await queryClient.invalidateQueries({ queryKey: ['totp-status'] })
    } finally {
      setStartingEnrollment(false)
    }
  }

  async function handleVerifySetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSetupError(null)
    setVerifyingSetup(true)

    try {
      await authApi.verifyTotpSetup(setupCode.trim())
      toast.success('Two-factor authentication enabled.')
      setEnrollment(null)
      setSetupCode('')
      await queryClient.invalidateQueries({ queryKey: ['totp-status'] })
    } catch (error) {
      setSetupError(getErrorMessage(error))
    } finally {
      setVerifyingSetup(false)
    }
  }

  async function handleDisable(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setDisableError(null)
    setDisabling(true)

    try {
      await authApi.disableTotp(disableCode.trim())
      toast.success('Two-factor authentication disabled.')
      setDisableCode('')
      await queryClient.invalidateQueries({ queryKey: ['totp-status'] })
    } catch (error) {
      setDisableError(getErrorMessage(error))
    } finally {
      setDisabling(false)
    }
  }

  const totpEnabled = totpQuery.data?.enabled ?? false

  return (
    <div className="space-y-6">
      <PageHeader
        title="Security settings"
        description="Change your password and manage two-factor authentication."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <KeyRoundIcon className="size-4 text-muted-foreground" />
              Change password
            </CardTitle>
            <CardDescription>
              Changing your password revokes every refresh token for your account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handlePasswordChange}>
              {passwordError ? (
                <Alert variant="destructive">
                  <AlertCircleIcon />
                  <AlertDescription>{passwordError}</AlertDescription>
                </Alert>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="current-password">Current password</Label>
                <PasswordInput
                  id="current-password"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New password</Label>
                <PasswordInput
                  id="new-password"
                  autoComplete="new-password"
                  minLength={8}
                  maxLength={128}
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm new password</Label>
                <PasswordInput
                  id="confirm-password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                />
              </div>

              <SubmitButton loading={changingPassword}>
                Update password
              </SubmitButton>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2">
                <ShieldCheckIcon className="size-4 text-muted-foreground" />
                Two-factor authentication
              </CardTitle>
              {totpQuery.isLoading ? (
                <Skeleton className="h-5 w-16" />
              ) : (
                <StatusBadge tone={totpEnabled ? 'success' : 'neutral'}>
                  {totpEnabled ? 'Enabled' : 'Disabled'}
                </StatusBadge>
              )}
            </div>
            <CardDescription>
              Protect your account with a TOTP authenticator app and single-use
              backup codes.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {totpQuery.isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-8 w-32" />
              </div>
            ) : null}

            {totpQuery.isError ? (
              <Alert variant="destructive">
                <AlertCircleIcon />
                <AlertDescription>
                  {getErrorMessage(totpQuery.error)}
                </AlertDescription>
              </Alert>
            ) : null}

            {!totpQuery.isLoading && !totpEnabled ? (
              <div className="space-y-4">
                {enrollmentError ? (
                  <Alert variant="destructive">
                    <AlertCircleIcon />
                    <AlertDescription>{enrollmentError}</AlertDescription>
                  </Alert>
                ) : null}

                {!enrollment ? (
                  <>
                    <p className="text-sm text-muted-foreground">
                      Two-factor authentication is not active. Start enrollment to
                      generate a QR code and backup codes.
                    </p>
                    <Button
                      onClick={handleStartEnrollment}
                      disabled={startingEnrollment}
                    >
                      {startingEnrollment ? 'Preparing…' : 'Enable two-factor'}
                    </Button>
                  </>
                ) : (
                  <div className="space-y-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
                      <img
                        src={enrollment.qr_code}
                        alt="TOTP enrollment QR code"
                        className="size-40 rounded-lg border bg-white p-2"
                      />
                      <div className="space-y-2 text-sm">
                        <p className="font-medium">1. Scan the QR code</p>
                        <p className="text-muted-foreground">
                          Use Google Authenticator, 1Password, Authy, or any TOTP
                          app. If you cannot scan it, enter this secret manually.
                        </p>
                        <div className="flex flex-wrap items-center gap-2">
                          <code className="rounded bg-muted px-2 py-1 text-xs break-all">
                            {enrollment.secret}
                          </code>
                          <CopyButton value={enrollment.secret} label="Copy secret" />
                        </div>
                      </div>
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-medium">Backup codes</p>
                        <CopyButton
                          value={enrollment.backup_codes.join('\n')}
                          label="Copy all"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Store these codes securely. Each code can be used once. They
                        will not be shown again after you leave this page.
                      </p>
                      <div className="grid gap-2 rounded-lg border bg-muted/40 p-3 sm:grid-cols-2">
                        {enrollment.backup_codes.map((code) => (
                          <code key={code} className="text-xs">
                            {code}
                          </code>
                        ))}
                      </div>
                    </div>

                    <Separator />

                    <form className="space-y-3" onSubmit={handleVerifySetup}>
                      <div className="space-y-2">
                        <Label htmlFor="setup-code">
                          2. Enter a code to activate
                        </Label>
                        <Input
                          id="setup-code"
                          inputMode="numeric"
                          autoComplete="one-time-code"
                          placeholder="123456"
                          value={setupCode}
                          onChange={(event) => setSetupCode(event.target.value)}
                          required
                        />
                      </div>
                      {setupError ? (
                        <Alert variant="destructive">
                          <AlertCircleIcon />
                          <AlertDescription>{setupError}</AlertDescription>
                        </Alert>
                      ) : null}
                      <SubmitButton loading={verifyingSetup}>
                        Activate two-factor
                      </SubmitButton>
                    </form>
                  </div>
                )}
              </div>
            ) : null}

            {!totpQuery.isLoading && totpEnabled ? (
              <div className="space-y-4">
                <Alert>
                  <CheckCircle2Icon />
                  <AlertTitle>Two-factor is active</AlertTitle>
                  <AlertDescription>
                    You will be asked for an authenticator code on every new sign-in.
                  </AlertDescription>
                </Alert>

                <form className="space-y-3" onSubmit={handleDisable}>
                  <div className="space-y-2">
                    <Label htmlFor="disable-code">
                      Authenticator code to disable
                    </Label>
                    <Input
                      id="disable-code"
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      placeholder="123456"
                      value={disableCode}
                      onChange={(event) => setDisableCode(event.target.value)}
                      required
                    />
                  </div>
                  {disableError ? (
                    <Alert variant="destructive">
                      <AlertCircleIcon />
                      <AlertDescription>{disableError}</AlertDescription>
                    </Alert>
                  ) : null}
                  <Button type="submit" variant="destructive" disabled={disabling}>
                    {disabling ? 'Disabling…' : 'Disable two-factor'}
                  </Button>
                </form>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
