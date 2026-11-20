import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { ShieldAlertIcon } from 'lucide-react'

import { FullPageLoader } from '@/components/common/loader'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'

export function RequireAuth() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === 'loading') {
    return <FullPageLoader />
  }

  if (status === 'anonymous') {
    const redirectTo = `${location.pathname}${location.search}`
    return <Navigate to="/login" replace state={{ from: redirectTo }} />
  }

  return <Outlet />
}

export function PublicOnly() {
  const { status } = useAuth()

  if (status === 'loading') {
    return <FullPageLoader />
  }

  if (status === 'authenticated') {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}

export function RequireAdmin() {
  const { user } = useAuth()

  if (user?.role !== 'Admin') {
    return (
      <Card className="mx-auto max-w-lg">
        <CardHeader>
          <div className="flex size-10 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <ShieldAlertIcon className="size-5" />
          </div>
          <CardTitle>Admin access required</CardTitle>
          <CardDescription>
            Your account does not have permission to view this area.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline">
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return <Outlet />
}
