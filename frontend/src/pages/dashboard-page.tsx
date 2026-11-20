import { useQuery } from '@tanstack/react-query'
import { KeyRoundIcon, ShieldCheckIcon, UserIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PageHeader } from '@/components/common/page-header'
import { StatusBadge } from '@/components/common/status-badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/context/auth-context'
import { apiKeysApi, authApi } from '@/lib/api'
import { formatDate, formatRelativeTime } from '@/lib/format'

export function DashboardPage() {
  const { user } = useAuth()

  const totpQuery = useQuery({
    queryKey: ['totp-status'],
    queryFn: authApi.totpStatus,
  })

  const apiKeysQuery = useQuery({
    queryKey: ['api-keys'],
    queryFn: apiKeysApi.list,
  })

  if (!user) return null

  const activeKeys =
    apiKeysQuery.data?.keys.filter((key) => !key.is_revoked).length ?? 0

  return (
    <div className="space-y-6">
      <PageHeader
        title={`Welcome back, ${user.username}`}
        description="Review your account, security posture, and service credentials."
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="size-4 text-muted-foreground" />
              Account profile
            </CardTitle>
            <CardDescription>
              Identity details returned by the authenticated session.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <dl className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Email
                </dt>
                <dd className="text-sm font-medium break-all">{user.email}</dd>
              </div>
              <div className="space-y-1">
                <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Username
                </dt>
                <dd className="text-sm font-medium">{user.username}</dd>
              </div>
              <div className="space-y-1">
                <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Role
                </dt>
                <dd>
                  <StatusBadge tone={user.role === 'Admin' ? 'info' : 'neutral'}>
                    {user.role}
                  </StatusBadge>
                </dd>
              </div>
              <div className="space-y-1">
                <dt className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Member since
                </dt>
                <dd className="text-sm" title={formatDate(user.created_at)}>
                  {formatRelativeTime(user.created_at)}
                </dd>
              </div>
            </dl>

            <Separator />

            <div className="flex flex-wrap gap-2">
              <StatusBadge tone={user.is_active ? 'success' : 'danger'}>
                {user.is_active ? 'Active' : 'Inactive'}
              </StatusBadge>
              <StatusBadge tone={user.is_verified ? 'success' : 'neutral'}>
                {user.is_verified ? 'Email verified' : 'Email unverified'}
              </StatusBadge>
            </div>

            <p className="text-xs text-muted-foreground">User ID: {user.id}</p>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheckIcon className="size-4 text-muted-foreground" />
                Security
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Two-factor authentication
                </p>
                {totpQuery.isLoading ? (
                  <Skeleton className="h-5 w-24" />
                ) : (
                  <StatusBadge
                    tone={totpQuery.data?.enabled ? 'success' : 'neutral'}
                  >
                    {totpQuery.data?.enabled ? 'Enabled' : 'Not enabled'}
                  </StatusBadge>
                )}
              </div>
              <Button asChild variant="outline" size="sm">
                <Link to="/security">Manage security</Link>
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <KeyRoundIcon className="size-4 text-muted-foreground" />
                API keys
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1">
                <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                  Active keys
                </p>
                {apiKeysQuery.isLoading ? (
                  <Skeleton className="h-5 w-12" />
                ) : (
                  <p className="text-2xl font-semibold">{activeKeys}</p>
                )}
              </div>
              <Button asChild variant="outline" size="sm">
                <Link to="/api-keys">Manage API keys</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
