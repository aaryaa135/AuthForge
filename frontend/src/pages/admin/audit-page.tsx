import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertCircleIcon, ScrollTextIcon, SearchIcon } from 'lucide-react'

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
import { auditApi, getErrorMessage } from '@/lib/api'
import { AUDIT_ACTIONS } from '@/lib/constants'
import { formatDateTime } from '@/lib/format'

export function AdminAuditPage() {
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [action, setAction] = useState('all')
  const [success, setSuccess] = useState('all')
  const [userIdInput, setUserIdInput] = useState('')
  const [userId, setUserId] = useState('')
  const [sortBy, setSortBy] = useState('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setSearch(searchInput.trim())
      setUserId(userIdInput.trim())
      setPage(1)
    }, 350)

    return () => window.clearTimeout(timer)
  }, [searchInput, userIdInput])

  const auditQuery = useQuery({
    queryKey: [
      'admin-audit',
      { page, pageSize, search, action, success, userId, sortBy, sortOrder },
    ],
    queryFn: () =>
      auditApi.list({
        page,
        page_size: pageSize,
        search: search || undefined,
        action: action === 'all' ? undefined : action,
        success: success === 'all' ? undefined : success === 'success',
        user_id: userId || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      }),
  })

  const logs = auditQuery.data?.items ?? []

  function resetFilters() {
    setSearchInput('')
    setSearch('')
    setAction('all')
    setSuccess('all')
    setUserIdInput('')
    setUserId('')
    setSortBy('created_at')
    setSortOrder('desc')
    setPage(1)
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit log"
        description="Immutable security events recorded by the authentication service."
        actions={
          <Button variant="outline" onClick={resetFilters}>
            Reset filters
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Security events</CardTitle>
          <CardDescription>
            Filter by action, outcome, or user. Newest events appear first by default.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-3">
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="relative flex-1">
                <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  className="pl-8"
                  placeholder="Search action text"
                  value={searchInput}
                  onChange={(event) => setSearchInput(event.target.value)}
                />
              </div>
              <Input
                className="sm:max-w-80"
                placeholder="Filter by user UUID"
                value={userIdInput}
                onChange={(event) => setUserIdInput(event.target.value)}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <Select
                value={action}
                onValueChange={(value) => {
                  setAction(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-56">
                  <SelectValue placeholder="Action" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All actions</SelectItem>
                  {AUDIT_ACTIONS.map((item) => (
                    <SelectItem key={item} value={item}>
                      {item}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={success}
                onValueChange={(value) => {
                  setSuccess(value)
                  setPage(1)
                }}
              >
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Outcome" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All outcomes</SelectItem>
                  <SelectItem value="success">Success</SelectItem>
                  <SelectItem value="failure">Failure</SelectItem>
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
                  <SelectItem value="action">Action</SelectItem>
                  <SelectItem value="success">Outcome</SelectItem>
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

          {auditQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : null}

          {auditQuery.isError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{getErrorMessage(auditQuery.error)}</AlertDescription>
            </Alert>
          ) : null}

          {!auditQuery.isLoading && !auditQuery.isError && logs.length === 0 ? (
            <EmptyState
              icon={ScrollTextIcon}
              title="No audit events found"
              description="Adjust the filters or wait for new authentication activity."
              action={
                <Button variant="outline" onClick={resetFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : null}

          {logs.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>IP address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="whitespace-nowrap">
                      {formatDateTime(log.created_at)}
                    </TableCell>
                    <TableCell>
                      <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                        {log.action}
                      </code>
                    </TableCell>
                    <TableCell>
                      {log.user_id ? (
                        <span className="font-mono text-xs text-muted-foreground">
                          {log.user_id}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusBadge tone={log.success ? 'success' : 'danger'}>
                        {log.success ? 'Success' : 'Failure'}
                      </StatusBadge>
                    </TableCell>
                    <TableCell>
                      {log.ip_address ?? (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : null}

          <Pagination
            page={auditQuery.data?.page ?? page}
            pages={auditQuery.data?.pages ?? 0}
            total={auditQuery.data?.total ?? 0}
            onPageChange={setPage}
            disabled={auditQuery.isFetching}
          />
        </CardContent>
      </Card>
    </div>
  )
}
