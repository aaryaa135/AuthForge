import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircleIcon, SearchIcon, UsersIcon } from 'lucide-react'
import { toast } from 'sonner'

import { EmptyState } from '@/components/common/empty-state'
import { PageHeader } from '@/components/common/page-header'
import { Pagination } from '@/components/common/pagination'
import { StatusBadge } from '@/components/common/status-badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useAuth } from '@/context/auth-context'
import { getErrorMessage, usersApi } from '@/lib/api'
import { ROLES } from '@/lib/constants'
import { formatDate, formatDateTime } from '@/lib/format'
import type { User } from '@/lib/types'

export function AdminUsersPage() {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [role, setRole] = useState('all')
  const [status, setStatus] = useState('all')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim())
      setPage(1)
    }, 350)

    return () => window.clearTimeout(timer)
  }, [searchInput])

  const usersQuery = useQuery({
    queryKey: ['admin-users', { page, pageSize, search, role, status, sortBy, sortOrder }],
    queryFn: () =>
      usersApi.list({
        page,
        page_size: pageSize,
        search: search || undefined,
        role: role === 'all' ? undefined : role,
        is_active: status === 'all' ? undefined : status === 'active',
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  })

  const roleMutation = useMutation({
    mutationFn: ({ id, nextRole }: { id: string; nextRole: string }) =>
      usersApi.updateRole(id, nextRole),
    onSuccess: async () => {
      toast.success('User role updated.')
      await queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })

  const statusMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      usersApi.updateStatus(id, isActive),
    onSuccess: async () => {
      toast.success('User status updated.')
      await queryClient.invalidateQueries({ queryKey: ['admin-users'] })
    },
  })

  const mutationError = roleMutation.error ?? statusMutation.error
  const actionsBusy = roleMutation.isPending || statusMutation.isPending
  const users = usersQuery.data?.items ?? []

  function handleRoleChange(user: User, nextRole: string) {
    if (nextRole === user.role) return
    roleMutation.mutate({ id: user.id, nextRole })
  }

  function handleStatusToggle(user: User) {
    statusMutation.mutate({ id: user.id, isActive: !user.is_active })
  }

  function resetFilters() {
    setSearchInput('')
    setSearch('')
    setRole('all')
    setStatus('all')
    setSortBy('created_at')
    setSortOrder('desc')
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User management"
        description="Search, filter, and administer accounts. You cannot change your own role or deactivate your own account."
        actions={
          <Button variant="outline" onClick={resetFilters}>
            Reset filters
          </Button>
        }
      />

      {mutationError ? (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertDescription>{getErrorMessage(mutationError)}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>All users</CardTitle>
          <CardDescription>
            Server-side filtering and pagination across the users table.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <div className="relative flex-1">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="Search email or username"
                value={searchInput}
                onChange={(event) => setSearchInput(event.target.value)}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Select
                value={role}
                onValueChange={(value) => {
                  setRole(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All roles</SelectItem>
                  {ROLES.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={status}
                onValueChange={(value) => {
                  setStatus(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={sortBy}
                onValueChange={(value) => {
                  setSortBy(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">Created at</SelectItem>
                  <SelectItem value="email">Email</SelectItem>
                  <SelectItem value="username">Username</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={sortOrder}
                onValueChange={(value) => {
                  setSortOrder(value === 'asc' ? 'asc' : 'desc')
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Order" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Newest first</SelectItem>
                  <SelectItem value="asc">Oldest first</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={String(pageSize)}
                onValueChange={(value) => {
                  setPageSize(Number(value))
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[10, 20, 50, 100].map((size) => (
                    <SelectItem key={size} value={String(size)}>
                      {size} / page
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {usersQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : null}

          {usersQuery.isError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{getErrorMessage(usersQuery.error)}</AlertDescription>
            </Alert>
          ) : null}

          {!usersQuery.isLoading && !usersQuery.isError && users.length === 0 ? (
            <EmptyState
              icon={UsersIcon}
              title="No users found"
              description="Try a different search term or clear the filters."
              action={
                <Button variant="outline" onClick={resetFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : null}

          {users.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Verified</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => {
                  const isSelf = currentUser?.id === user.id

                  return (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="space-y-0.5">
                          <p className="font-medium">{user.username}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                          {isSelf ? (
                            <p className="text-xs text-muted-foreground">(you)</p>
                          ) : null}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Select
                          value={user.role}
                          onValueChange={(value) => handleRoleChange(user, value)}
                          disabled={isSelf || actionsBusy}
                        >
                          <SelectTrigger className="w-32" size="sm">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {ROLES.map((item) => (
                              <SelectItem key={item} value={item}>
                                {item}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <StatusBadge tone={user.is_active ? 'success' : 'danger'}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </StatusBadge>
                      </TableCell>
                      <TableCell>
                        <StatusBadge tone={user.is_verified ? 'success' : 'neutral'}>
                          {user.is_verified ? 'Verified' : 'Pending'}
                        </StatusBadge>
                      </TableCell>
                      <TableCell title={formatDateTime(user.created_at)}>
                        {formatDate(user.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant={user.is_active ? 'destructive' : 'outline'}
                          size="sm"
                          disabled={isSelf || actionsBusy}
                          onClick={() => handleStatusToggle(user)}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : null}

          <Pagination
            page={usersQuery.data?.page ?? page}
            pages={usersQuery.data?.pages ?? 0}
            total={usersQuery.data?.total ?? 0}
            onPageChange={setPage}
            disabled={usersQuery.isFetching}
          />
        </CardContent>
      </Card>
    </div>
  )
}
