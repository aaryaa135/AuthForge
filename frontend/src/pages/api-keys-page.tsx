import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertCircleIcon, KeyRoundIcon, PlusIcon, TriangleAlertIcon } from 'lucide-react'
import { toast } from 'sonner'

import { CopyButton } from '@/components/common/copy-button'
import { EmptyState } from '@/components/common/empty-state'
import { PageHeader } from '@/components/common/page-header'
import { StatusBadge } from '@/components/common/status-badge'
import { SubmitButton } from '@/components/common/submit-button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiKeysApi, getErrorMessage } from '@/lib/api'
import { formatDate, formatDateTime } from '@/lib/format'
import type { ApiKey, ApiKeyCreateResponse } from '@/lib/types'

export function ApiKeysPage() {
  const queryClient = useQueryClient()
  const keysQuery = useQuery({ queryKey: ['api-keys'], queryFn: apiKeysApi.list })

  const [createOpen, setCreateOpen] = useState(false)
  const [name, setName] = useState('')
  const [scopes, setScopes] = useState('')
  const [expiresInDays, setExpiresInDays] = useState('')
  const [createError, setCreateError] = useState<string | null>(null)
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null)

  const [keyToRevoke, setKeyToRevoke] = useState<ApiKey | null>(null)
  const [revokeError, setRevokeError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: apiKeysApi.create,
    onSuccess: async (response) => {
      setCreatedKey(response)
      setCreateOpen(false)
      setName('')
      setScopes('')
      setExpiresInDays('')
      await queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
    onError: (error) => setCreateError(getErrorMessage(error)),
  })

  const revokeMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess: async () => {
      toast.success('API key revoked.')
      setKeyToRevoke(null)
      setRevokeError(null)
      await queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
    onError: (error) => setRevokeError(getErrorMessage(error)),
  })

  function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCreateError(null)

    const parsedScopes = scopes
      .split(',')
      .map((scope) => scope.trim())
      .filter(Boolean)

    const parsedDays = expiresInDays.trim() ? Number(expiresInDays) : undefined

    if (parsedDays !== undefined && (!Number.isFinite(parsedDays) || parsedDays <= 0)) {
      setCreateError('Expiry must be a positive number of days.')
      return
    }

    createMutation.mutate({
      name: name.trim(),
      scopes: parsedScopes.length > 0 ? parsedScopes : undefined,
      expires_in_days: parsedDays,
    })
  }

  const keys = keysQuery.data?.keys ?? []

  return (
    <div className="space-y-6">
      <PageHeader
        title="API keys"
        description="Create service credentials for machine-to-machine access. Keys are shown once at creation."
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <PlusIcon />
            Create key
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Your keys</CardTitle>
          <CardDescription>
            Only key metadata is stored. Plaintext values cannot be retrieved later.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keysQuery.isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : null}

          {keysQuery.isError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{getErrorMessage(keysQuery.error)}</AlertDescription>
            </Alert>
          ) : null}

          {!keysQuery.isLoading && !keysQuery.isError && keys.length === 0 ? (
            <EmptyState
              icon={KeyRoundIcon}
              title="No API keys yet"
              description="Create a key to authenticate service accounts through the X-API-Key header."
              action={
                <Button onClick={() => setCreateOpen(true)}>
                  <PlusIcon />
                  Create your first key
                </Button>
              }
            />
          ) : null}

          {keys.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Prefix</TableHead>
                  <TableHead>Scopes</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Expires</TableHead>
                  <TableHead>Last used</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                        {key.key_prefix}…
                      </code>
                    </TableCell>
                    <TableCell>
                      {key.scopes && key.scopes.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {key.scopes.map((scope) => (
                            <StatusBadge key={scope} tone="neutral">
                              {scope}
                            </StatusBadge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell title={formatDateTime(key.created_at)}>
                      {formatDate(key.created_at)}
                    </TableCell>
                    <TableCell title={formatDateTime(key.expires_at)}>
                      {key.expires_at ? formatDate(key.expires_at) : 'Never'}
                    </TableCell>
                    <TableCell title={formatDateTime(key.last_used_at)}>
                      {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                    </TableCell>
                    <TableCell>
                      <StatusBadge tone={key.is_revoked ? 'danger' : 'success'}>
                        {key.is_revoked ? 'Revoked' : 'Active'}
                      </StatusBadge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="destructive"
                        size="sm"
                        disabled={key.is_revoked}
                        onClick={() => {
                          setRevokeError(null)
                          setKeyToRevoke(key)
                        }}
                      >
                        Revoke
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : null}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create API key</DialogTitle>
            <DialogDescription>
              The plaintext key is returned once. Store it before closing the next
              dialog.
            </DialogDescription>
          </DialogHeader>

          <form className="space-y-4" onSubmit={handleCreate}>
            {createError ? (
              <Alert variant="destructive">
                <AlertCircleIcon />
                <AlertDescription>{createError}</AlertDescription>
              </Alert>
            ) : null}

            <div className="space-y-2">
              <Label htmlFor="key-name">Name</Label>
              <Input
                id="key-name"
                placeholder="CI deploy bot"
                maxLength={100}
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-scopes">Scopes (optional)</Label>
              <Input
                id="key-scopes"
                placeholder="users:read, audit:read"
                value={scopes}
                onChange={(event) => setScopes(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated. Scopes are metadata for your services.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="key-expiry">Expires in days (optional)</Label>
              <Input
                id="key-expiry"
                type="number"
                min={1}
                placeholder="90"
                value={expiresInDays}
                onChange={(event) => setExpiresInDays(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Leave blank for a non-expiring key.
              </p>
            </div>

            <DialogFooter className="mt-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateOpen(false)}
              >
                Cancel
              </Button>
              <SubmitButton loading={createMutation.isPending}>
                Create key
              </SubmitButton>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={createdKey !== null}
        onOpenChange={(open) => {
          if (!open) setCreatedKey(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API key created</DialogTitle>
            <DialogDescription>
              Copy this value now. It will not be shown again.
            </DialogDescription>
          </DialogHeader>

          {createdKey ? (
            <div className="space-y-4">
              <Alert>
                <TriangleAlertIcon />
                <AlertTitle>Store it securely</AlertTitle>
                <AlertDescription>
                  Treat this key like a password. Anyone with it can act as your
                  service account.
                </AlertDescription>
              </Alert>

              <div className="space-y-2">
                <Label>API key</Label>
                <code className="block rounded-lg border bg-muted/50 p-3 text-xs break-all">
                  {createdKey.api_key}
                </code>
                <CopyButton value={createdKey.api_key} label="Copy API key" />
              </div>

              <div className="text-sm text-muted-foreground">
                Prefix: <code>{createdKey.key_prefix}</code> · Name:{' '}
                {createdKey.name}
              </div>
            </div>
          ) : null}

          <DialogFooter>
            <Button onClick={() => setCreatedKey(null)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={keyToRevoke !== null}
        onOpenChange={(open) => {
          if (!open) {
            setKeyToRevoke(null)
            setRevokeError(null)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Revoke “{keyToRevoke?.name}”?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. Requests using this key will fail immediately.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {revokeError ? (
            <Alert variant="destructive">
              <AlertCircleIcon />
              <AlertDescription>{revokeError}</AlertDescription>
            </Alert>
          ) : null}

          <AlertDialogFooter>
            <AlertDialogCancel disabled={revokeMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={revokeMutation.isPending}
              onClick={(event) => {
                event.preventDefault()
                if (keyToRevoke) revokeMutation.mutate(keyToRevoke.id)
              }}
            >
              {revokeMutation.isPending ? 'Revoking…' : 'Revoke key'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
