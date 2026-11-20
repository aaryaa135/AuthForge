import type { ReactNode } from 'react'
import { ExternalLinkIcon, ShieldCheckIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { CopyButton } from '@/components/common/copy-button'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)
const API_ROOT = `${API_BASE_URL}/api/v1`
const SWAGGER_URL = `${API_BASE_URL}/docs`
const REDOC_URL = `${API_BASE_URL}/redoc`

type Access = 'Public' | 'Bearer' | 'Admin'

const sections = [
  { id: 'overview', label: 'Overview' },
  { id: 'authentication', label: 'Authentication' },
  { id: 'two-factor', label: 'Two-factor authentication' },
  { id: 'api-keys', label: 'API key management' },
  { id: 'users', label: 'User administration' },
  { id: 'audit', label: 'Audit logs' },
  { id: 'errors', label: 'Error handling' },
]

const tokenResponseExample = `{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_9f2c...",
  "token_type": "bearer"
}`

const userResponseExample = `{
  "id": "b3f1c2d4-8e5a-4c1b-9d7e-2f6a0c3b1e84",
  "email": "ada@authforge.dev",
  "username": "ada",
  "role": "User",
  "is_active": true,
  "is_verified": true,
  "created_at": "2026-01-15T10:30:00Z"
}`

const paginatedMeta = `  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1`

function DocsHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-3 sm:h-16 sm:flex-row sm:items-center sm:justify-between sm:gap-4 sm:px-6 sm:py-0">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight text-zinc-950"
        >
          <ShieldCheckIcon className="size-5" strokeWidth={1.75} />
          AuthForge
          <span className="hidden text-zinc-300 sm:inline">/</span>
          <span className="hidden font-mono text-xs font-normal text-zinc-500 sm:inline">
            API Reference
          </span>
        </Link>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-zinc-600 sm:text-sm">
          <a
            href={SWAGGER_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 transition-colors hover:text-zinc-950"
          >
            Swagger UI
            <ExternalLinkIcon className="size-3" />
          </a>
          <a
            href={REDOC_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 transition-colors hover:text-zinc-950"
          >
            ReDoc
            <ExternalLinkIcon className="size-3" />
          </a>
          <Button
            asChild
            variant="outline"
            className="h-8 border-zinc-300 bg-white px-3 text-zinc-950 hover:bg-zinc-100"
          >
            <Link to="/">Back to site</Link>
          </Button>
        </div>
      </div>
    </header>
  )
}

function DocsSidebar() {
  return (
    <aside className="hidden lg:block">
      <div className="sticky top-24 py-14">
        <p className="text-[11px] font-medium tracking-[0.16em] text-zinc-400 uppercase">
          On this page
        </p>
        <nav className="mt-4 space-y-1">
          {sections.map((section) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              className="block rounded-md px-2 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-950"
            >
              {section.label}
            </a>
          ))}
        </nav>

        <div className="mt-8 border-t border-zinc-200 pt-6">
          <p className="text-[11px] font-medium tracking-[0.16em] text-zinc-400 uppercase">
            Live reference
          </p>
          <div className="mt-3 space-y-2 text-sm">
            <a
              href={SWAGGER_URL}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-zinc-600 transition-colors hover:text-zinc-950"
            >
              Swagger UI
              <ExternalLinkIcon className="size-3" />
            </a>
            <a
              href={REDOC_URL}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 text-zinc-600 transition-colors hover:text-zinc-950"
            >
              ReDoc
              <ExternalLinkIcon className="size-3" />
            </a>
          </div>
        </div>
      </div>
    </aside>
  )
}

function MobileSectionNav() {
  return (
    <div className="-mx-4 mb-8 overflow-x-auto border-b border-zinc-200 px-4 pb-3 lg:hidden">
      <div className="flex w-max gap-2">
        {sections.map((section) => (
          <a
            key={section.id}
            href={`#${section.id}`}
            className="rounded-md border border-zinc-200 bg-white px-2.5 py-1.5 text-xs text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-950"
          >
            {section.label}
          </a>
        ))}
      </div>
    </div>
  )
}

function MethodBadge({ method }: { method: string }) {
  const solid = method !== 'GET'

  return (
    <span
      className={
        solid
          ? 'rounded border border-zinc-950 bg-zinc-950 px-2 py-0.5 font-mono text-[10px] font-semibold tracking-wide text-white'
          : 'rounded border border-zinc-300 bg-white px-2 py-0.5 font-mono text-[10px] font-semibold tracking-wide text-zinc-700'
      }
    >
      {method}
    </span>
  )
}

function AccessBadge({ access }: { access: Access }) {
  return (
    <Badge
      variant="outline"
      className="h-5 border-zinc-300 bg-white px-2 text-[10px] font-medium tracking-wide text-zinc-600 uppercase"
    >
      {access}
    </Badge>
  )
}

function Endpoint({
  method,
  path,
  access,
  description,
  children,
}: {
  method: string
  path: string
  access: Access
  description: string
  children: ReactNode
}) {
  return (
    <article className="border-t border-zinc-200 py-8 first:border-t-0 first:pt-0">
      <div className="flex flex-wrap items-center gap-2">
        <MethodBadge method={method} />
        <h3 className="min-w-0 break-all font-mono text-sm font-medium text-zinc-950">
          {path}
        </h3>
        <span className="sm:ml-auto">
          <AccessBadge access={access} />
        </span>
      </div>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-600">{description}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </article>
  )
}

function CodeBlock({ title, code }: { title: string; code: string }) {
  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <div className="flex items-center justify-between gap-3 border-b border-zinc-200 bg-zinc-50 px-3 py-2">
        <span className="font-mono text-[11px] tracking-wide text-zinc-500 uppercase">
          {title}
        </span>
        <CopyButton
          value={code}
          className="h-7 border-zinc-300 bg-white text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
        />
      </div>
      <pre className="overflow-x-auto bg-white p-4 font-mono text-[12px] leading-6 text-zinc-800">
        <code>{code}</code>
      </pre>
    </div>
  )
}

interface Param {
  name: string
  type: string
  required?: boolean
  description: string
}

function ParamTable({
  title = 'Parameters',
  params,
}: {
  title?: string
  params: Param[]
}) {
  const hasRequired = params.some((param) => param.required)

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <div className="border-b border-zinc-200 bg-zinc-50 px-3 py-2 text-[10px] font-medium tracking-wider text-zinc-500 uppercase">
        {title}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] border-collapse text-left text-sm">
          <thead className="bg-white text-[10px] tracking-wider text-zinc-500 uppercase">
            <tr>
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Type</th>
              <th className="px-3 py-2 font-medium">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {params.map((param) => (
              <tr key={param.name}>
                <td className="px-3 py-2 align-top font-mono text-xs text-zinc-950">
                  {param.name}
                  {param.required ? <span className="ml-1 text-zinc-400">*</span> : null}
                </td>
                <td className="px-3 py-2 align-top font-mono text-xs text-zinc-500">
                  {param.type}
                </td>
                <td className="px-3 py-2 align-top text-xs leading-5 text-zinc-600">
                  {param.description}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasRequired ? (
        <div className="border-t border-zinc-200 bg-zinc-50 px-3 py-2 text-[11px] text-zinc-500">
          * Required field
        </div>
      ) : null}
    </div>
  )
}

function Note({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs leading-5 text-zinc-600">
      {children}
    </div>
  )
}

function MetaCard({
  label,
  value,
  mono = false,
}: {
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div className="rounded-lg border border-zinc-200 p-4">
      <p className="text-[11px] font-medium tracking-wider text-zinc-500 uppercase">
        {label}
      </p>
      <p
        className={
          mono
            ? 'mt-2 break-all font-mono text-xs text-zinc-950'
            : 'mt-2 text-sm font-medium text-zinc-950'
        }
      >
        {value}
      </p>
    </div>
  )
}

function AccessCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 p-4">
      <p className="text-sm font-semibold text-zinc-950">{title}</p>
      <p className="mt-1 text-xs leading-5 text-zinc-600">{description}</p>
    </div>
  )
}

function DocsSection({
  id,
  title,
  description,
  children,
}: {
  id: string
  title: string
  description?: string
  children: ReactNode
}) {
  return (
    <section
      id={id}
      className="scroll-mt-24 border-t border-zinc-200 py-12 first:border-t-0 first:pt-0"
    >
      <h2 className="text-xl font-semibold tracking-tight text-zinc-950">{title}</h2>
      {description ? (
        <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">{description}</p>
      ) : null}
      <div className="mt-6">{children}</div>
    </section>
  )
}

function DocsFooter() {
  return (
    <footer className="border-t border-zinc-200">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>AuthForge REST API · v1</p>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          <a
            href={SWAGGER_URL}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-zinc-950"
          >
            Swagger UI
          </a>
          <a
            href={REDOC_URL}
            target="_blank"
            rel="noreferrer"
            className="transition-colors hover:text-zinc-950"
          >
            ReDoc
          </a>
          <Link to="/" className="transition-colors hover:text-zinc-950">
            Landing page
          </Link>
        </div>
      </div>
    </footer>
  )
}

export function ApiDocsPage() {
  return (
    <div className="min-h-svh bg-white text-zinc-950">
      <DocsHeader />

      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="lg:grid lg:grid-cols-[210px_minmax(0,1fr)] lg:gap-12">
          <DocsSidebar />

          <main className="min-w-0 py-10 lg:py-14">
            <MobileSectionNav />

            <header className="pb-10">
              <p className="text-xs font-medium tracking-[0.18em] text-zinc-500 uppercase">
                API Reference
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-zinc-950 sm:text-4xl">
                AuthForge REST API
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-zinc-600">
                Endpoints for account lifecycle, two-factor authentication, service
                credentials, user administration, and audit access. Every path is
                prefixed with <code className="font-mono text-sm">/api/v1</code>.
              </p>
              <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 font-mono text-zinc-600">
                  v1
                </span>
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 font-mono text-zinc-600">
                  JSON
                </span>
                <span className="rounded border border-zinc-200 bg-zinc-50 px-2 py-1 font-mono text-zinc-600">
                  Bearer access tokens
                </span>
                <a
                  href={SWAGGER_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 rounded border border-zinc-300 bg-white px-2 py-1 text-zinc-700 transition-colors hover:bg-zinc-100 hover:text-zinc-950"
                >
                  Swagger UI
                  <ExternalLinkIcon className="size-3" />
                </a>
              </div>
            </header>

            <DocsSection
              id="overview"
              title="Overview"
              description="AuthForge is a FastAPI authentication backend with JWT sessions, TOTP two-factor authentication, role-based access control, API keys, and audit logging. PostgreSQL stores durable state and Redis handles short-lived authentication concerns."
            >
              <div className="grid gap-3 sm:grid-cols-3">
                <MetaCard label="Base URL" value={API_ROOT} mono />
                <MetaCard label="API version" value="v1" />
                <MetaCard label="Authentication" value="Bearer access token" />
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-xs font-medium tracking-wider text-zinc-500 uppercase">
                    API root
                  </p>
                  <CodeBlock title="Base URL" code={API_ROOT} />
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium tracking-wider text-zinc-500 uppercase">
                    Authorized request
                  </p>
                  <CodeBlock
                    title="Authorization header"
                    code="Authorization: Bearer <access_token>"
                  />
                </div>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <AccessCard
                  title="Public"
                  description="No access token required. Used for registration, login, refresh, and recovery flows."
                />
                <AccessCard
                  title="Bearer"
                  description="Requires a valid access token in the Authorization header."
                />
                <AccessCard
                  title="Admin"
                  description="Requires a valid access token whose role is Admin."
                />
              </div>

              <div className="mt-4">
                <Note>
                  Access tokens come from <code>POST /api/v1/auth/login</code> or the
                  TOTP login verification endpoint. Refresh tokens are only used by the
                  refresh and logout endpoints.
                </Note>
              </div>
            </DocsSection>

            <DocsSection
              id="authentication"
              title="Authentication"
              description="Account creation, session issuance, email verification, password recovery, and password changes."
            >
              <Endpoint
                method="POST"
                path="/api/v1/auth/register"
                access="Public"
                description="Create a new account. Registration does not issue tokens and does not sign the user in."
              >
                <ParamTable
                  title="Request body"
                  params={[
                    {
                      name: 'email',
                      type: 'string (email)',
                      required: true,
                      description: 'Account email address.',
                    },
                    {
                      name: 'username',
                      type: 'string',
                      required: true,
                      description: 'Between 3 and 30 characters.',
                    },
                    {
                      name: 'password',
                      type: 'string',
                      required: true,
                      description: 'Between 8 and 128 characters.',
                    },
                  ]}
                />
                <CodeBlock
                  title="Request body"
                  code={`{
  "email": "ada@authforge.dev",
  "username": "ada",
  "password": "correct-horse-battery-staple"
}`}
                />
                <CodeBlock
                  title="201 Created"
                  code={`{
  "message": "Registration successful. If the account was created, a verification email has been sent."
}`}
                />
                <Note>
                  Registration does not automatically log in the user. Call{' '}
                  <code>POST /api/v1/auth/login</code> afterward. When the deployment
                  enables required email verification, the account must be verified
                  before login succeeds.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/login"
                access="Public"
                description="Authenticate with an email address or username and receive a token pair. When TOTP is enabled, login returns a challenge instead of tokens."
              >
                <ParamTable
                  title="Form fields"
                  params={[
                    {
                      name: 'username',
                      type: 'string (form)',
                      required: true,
                      description: 'Email address or username.',
                    },
                    {
                      name: 'password',
                      type: 'string (form)',
                      required: true,
                      description: 'Account password.',
                    },
                  ]}
                />
                <CodeBlock
                  title="Request body · application/x-www-form-urlencoded"
                  code="username=ada%40authforge.dev&password=correct-horse-battery-staple"
                />
                <CodeBlock title="200 OK" code={tokenResponseExample} />
                <CodeBlock
                  title="200 OK · two-factor challenge"
                  code={`{
  "two_factor_required": true,
  "user_id": "b3f1c2d4-8e5a-4c1b-9d7e-2f6a0c3b1e84",
  "message": "Two-factor verification required."
}`}
                />
                <Note>
                  The login request uses <code>application/x-www-form-urlencoded</code>,
                  not JSON. Login is rate limited to 5 requests per minute per identifier.
                </Note>
              </Endpoint>

              <Endpoint
                method="GET"
                path="/api/v1/auth/me"
                access="Bearer"
                description="Return the authenticated user's profile and role."
              >
                <CodeBlock title="200 OK" code={userResponseExample} />
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/refresh"
                access="Public"
                description="Exchange a refresh token for a new access token and refresh token."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "refresh_token": "rt_9f2c..."
}`}
                />
                <CodeBlock title="200 OK" code={tokenResponseExample} />
                <Note>
                  Refresh tokens are single-use and rotated. Reusing a revoked refresh
                  token revokes the entire token family.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/logout"
                access="Bearer"
                description="Revoke the current session. Requires a valid access token and the refresh token that belongs to the session."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "refresh_token": "rt_9f2c..."
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Logged out successfully."
}`}
                />
                <Note>
                  Logout revokes the refresh-token family and blacklists the presented
                  access token for its remaining lifetime.
                </Note>
              </Endpoint>

              <Endpoint
                method="GET"
                path="/api/v1/auth/verify-email?token=<token>"
                access="Public"
                description="Verify an email address using the token from the verification link."
              >
                <CodeBlock
                  title="Request"
                  code="GET /api/v1/auth/verify-email?token=verify_abc123"
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Email verified successfully."
}`}
                />
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/resend-verification"
                access="Public"
                description="Request another verification email for an unverified account."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "email": "ada@authforge.dev"
}`}
                />
                <Note>
                  The response is a <code>MessageResponse</code>. Wording is generic when
                  the account does not exist, to avoid account enumeration.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/forgot-password"
                access="Public"
                description="Request a password reset email."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "email": "ada@authforge.dev"
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "If the email exists, a password reset link has been sent."
}`}
                />
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/reset-password"
                access="Public"
                description="Complete a password reset with a reset token."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "token": "reset_abc123",
  "new_password": "new-correct-horse-battery-staple"
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Password reset successful."
}`}
                />
                <Note>
                  A successful reset revokes all existing refresh tokens for the user.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/change-password"
                access="Bearer"
                description="Change the authenticated user's password."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "current_password": "correct-horse-battery-staple",
  "new_password": "new-correct-horse-battery-staple"
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Password changed successfully."
}`}
                />
                <Note>
                  A successful change revokes all existing refresh tokens for the user.
                </Note>
              </Endpoint>
            </DocsSection>

            <DocsSection
              id="two-factor"
              title="Two-factor authentication"
              description="TOTP enrollment and login verification. Enrollment returns a provisioning secret, a QR code data URI, and backup codes."
            >
              <Endpoint
                method="POST"
                path="/api/v1/auth/2fa/enable"
                access="Bearer"
                description="Start TOTP enrollment. Creates an unverified device and returns the enrollment material."
              >
                <CodeBlock
                  title="200 OK"
                  code={`{
  "secret": "<base32_secret>",
  "qr_code": "data:image/png;base64,<...>",
  "backup_codes": ["<backup_code>", "<backup_code>"]
}`}
                />
                <Note>
                  The device is not active until it is confirmed with{' '}
                  <code>POST /api/v1/auth/2fa/verify-setup</code>. Treat the secret and
                  backup codes as sensitive.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/2fa/verify-setup"
                access="Bearer"
                description="Confirm the initial TOTP code and activate two-factor authentication."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "token": "123456"
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Two-factor authentication enabled.",
  "verified": true
}`}
                />
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/2fa/login-verify?user_id=<uuid>"
                access="Public"
                description="Complete a login challenge after the password step returned two_factor_required."
              >
                <ParamTable
                  title="Query parameters"
                  params={[
                    {
                      name: 'user_id',
                      type: 'string (UUID)',
                      required: true,
                      description: 'The user_id returned by the login challenge.',
                    },
                  ]}
                />
                <CodeBlock
                  title="Request body"
                  code={`{
  "token": "123456"
}`}
                />
                <CodeBlock title="200 OK" code={tokenResponseExample} />
                <Note>
                  The challenge depends on a pending two-factor session created during
                  login. If no pending session exists, the endpoint returns 400.
                </Note>
              </Endpoint>

              <Endpoint
                method="POST"
                path="/api/v1/auth/2fa/disable"
                access="Bearer"
                description="Disable TOTP after verifying a current TOTP code."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "token": "123456"
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "Two-factor authentication disabled."
}`}
                />
              </Endpoint>

              <Endpoint
                method="GET"
                path="/api/v1/auth/2fa/status"
                access="Bearer"
                description="Check whether TOTP is enabled and whether backup codes remain."
              >
                <CodeBlock
                  title="200 OK"
                  code={`{
  "enabled": true,
  "has_backup_codes": true
}`}
                />
              </Endpoint>
            </DocsSection>

            <DocsSection
              id="api-keys"
              title="API key management"
              description="Create, list, and revoke service credentials for the authenticated user."
            >
              <Endpoint
                method="POST"
                path="/api/v1/auth/api-keys"
                access="Bearer"
                description="Create an API key. The plaintext key is returned only in this response."
              >
                <ParamTable
                  title="Request body"
                  params={[
                    {
                      name: 'name',
                      type: 'string',
                      required: true,
                      description: 'Human-readable label for the key.',
                    },
                    {
                      name: 'scopes',
                      type: 'string[] | null',
                      description: 'Optional scope list stored with the key.',
                    },
                    {
                      name: 'expires_in_days',
                      type: 'integer | null',
                      description: 'Optional lifetime in days. Omit for no expiry.',
                    },
                  ]}
                />
                <CodeBlock
                  title="Request body"
                  code={`{
  "name": "CI deploy",
  "scopes": ["users:read"],
  "expires_in_days": 30
}`}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "id": "6f0c2a8e-1d4b-4f7a-8c3e-9b2d5a6f1c70",
  "name": "CI deploy",
  "key_prefix": "ak_abc12",
  "scopes": ["users:read"],
  "expires_at": "2026-12-01T00:00:00+00:00",
  "api_key": "ak_<plaintext_key>"
}`}
                />
              </Endpoint>

              <Endpoint
                method="GET"
                path="/api/v1/auth/api-keys"
                access="Bearer"
                description="List the authenticated user's API keys. Plaintext keys are never returned."
              >
                <CodeBlock
                  title="200 OK"
                  code={`{
  "keys": [
    {
      "id": "6f0c2a8e-1d4b-4f7a-8c3e-9b2d5a6f1c70",
      "name": "CI deploy",
      "key_prefix": "ak_abc12",
      "scopes": ["users:read"],
      "expires_at": "2026-12-01T00:00:00+00:00",
      "last_used_at": null,
      "is_revoked": false,
      "created_at": "2026-11-01T12:00:00+00:00"
    }
  ]
}`}
                />
              </Endpoint>

              <Endpoint
                method="DELETE"
                path="/api/v1/auth/api-keys/{api_key_id}"
                access="Bearer"
                description="Revoke one of the authenticated user's API keys."
              >
                <ParamTable
                  title="Path parameters"
                  params={[
                    {
                      name: 'api_key_id',
                      type: 'string (UUID)',
                      required: true,
                      description: 'Key ID returned by create or list.',
                    },
                  ]}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "message": "API key revoked."
}`}
                />
              </Endpoint>
            </DocsSection>

            <DocsSection
              id="users"
              title="User administration"
              description="Admin-only user search and account management. All endpoints require the Admin role."
            >
              <Endpoint
                method="GET"
                path="/api/v1/users/"
                access="Admin"
                description="List users with pagination, search, role, status, and sorting filters."
              >
                <ParamTable
                  title="Query parameters"
                  params={[
                    {
                      name: 'page',
                      type: 'integer',
                      description: 'Page number. Defaults to 1. Minimum 1.',
                    },
                    {
                      name: 'page_size',
                      type: 'integer',
                      description: 'Page size. Defaults to 20. Range 1-100.',
                    },
                    {
                      name: 'search',
                      type: 'string',
                      description: 'Search by email or username.',
                    },
                    {
                      name: 'role',
                      type: 'string',
                      description: 'Filter by role name.',
                    },
                    {
                      name: 'is_active',
                      type: 'boolean',
                      description: 'Filter by active status.',
                    },
                    {
                      name: 'sort_by',
                      type: 'string',
                      description: 'Sort field. Defaults to created_at.',
                    },
                    {
                      name: 'sort_order',
                      type: 'string',
                      description: 'Sort direction: asc or desc. Defaults to desc.',
                    },
                  ]}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "items": [
    {
      "id": "b3f1c2d4-8e5a-4c1b-9d7e-2f6a0c3b1e84",
      "email": "ada@authforge.dev",
      "username": "ada",
      "role": "User",
      "is_active": true,
      "is_verified": true,
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
${paginatedMeta}
}`}
                />
              </Endpoint>

              <Endpoint
                method="GET"
                path="/api/v1/users/{user_id}"
                access="Admin"
                description="Return one user by ID."
              >
                <ParamTable
                  title="Path parameters"
                  params={[
                    {
                      name: 'user_id',
                      type: 'string (UUID)',
                      required: true,
                      description: 'Target user ID.',
                    },
                  ]}
                />
                <CodeBlock title="200 OK" code={userResponseExample} />
              </Endpoint>

              <Endpoint
                method="PATCH"
                path="/api/v1/users/{user_id}/role"
                access="Admin"
                description="Change a user's role. Admins cannot change their own role."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "role": "Manager"
}`}
                />
                <CodeBlock title="200 OK" code={userResponseExample} />
                <Note>
                  Seed roles are <code>Admin</code>, <code>Manager</code>, and{' '}
                  <code>User</code>. Attempting to change your own role returns 403.
                </Note>
              </Endpoint>

              <Endpoint
                method="PATCH"
                path="/api/v1/users/{user_id}/status"
                access="Admin"
                description="Activate or deactivate a user account. Admins cannot deactivate their own account."
              >
                <CodeBlock
                  title="Request body"
                  code={`{
  "is_active": false
}`}
                />
                <CodeBlock title="200 OK" code={userResponseExample} />
                <Note>Attempting to deactivate your own account returns 403.</Note>
              </Endpoint>
            </DocsSection>

            <DocsSection
              id="audit"
              title="Audit logs"
              description="Admin-only access to authentication and security events recorded by the backend."
            >
              <Endpoint
                method="GET"
                path="/api/v1/audit/"
                access="Admin"
                description="List audit events with pagination, action, user, success, and sorting filters."
              >
                <ParamTable
                  title="Query parameters"
                  params={[
                    {
                      name: 'page',
                      type: 'integer',
                      description: 'Page number. Defaults to 1. Minimum 1.',
                    },
                    {
                      name: 'page_size',
                      type: 'integer',
                      description: 'Page size. Defaults to 20. Range 1-100.',
                    },
                    {
                      name: 'search',
                      type: 'string',
                      description: 'Search within action values.',
                    },
                    {
                      name: 'action',
                      type: 'string',
                      description: 'Filter by exact action value.',
                    },
                    {
                      name: 'user_id',
                      type: 'string',
                      description: 'Filter by user ID.',
                    },
                    {
                      name: 'success',
                      type: 'boolean',
                      description: 'Filter successful or failed events.',
                    },
                    {
                      name: 'sort_by',
                      type: 'string',
                      description: 'Sort field. Defaults to created_at.',
                    },
                    {
                      name: 'sort_order',
                      type: 'string',
                      description: 'Sort direction: asc or desc. Defaults to desc.',
                    },
                  ]}
                />
                <CodeBlock
                  title="200 OK"
                  code={`{
  "items": [
    {
      "id": "e9a1c3d5-7b2f-4a6c-8d1e-3f5a7c9b2d40",
      "user_id": "b3f1c2d4-8e5a-4c1b-9d7e-2f6a0c3b1e84",
      "action": "LOGIN",
      "success": true,
      "ip_address": "203.0.113.42",
      "created_at": "2026-11-20T10:15:00Z"
    }
  ],
${paginatedMeta}
}`}
                />
                <Note>
                  <code>user_id</code> and <code>ip_address</code> can be null for events
                  that are not tied to a user or request address.
                </Note>
              </Endpoint>
            </DocsSection>

            <DocsSection
              id="errors"
              title="Error handling"
              description="Errors are returned as JSON with a detail field. Validation errors use a detail array; unexpected server errors include a request_id for tracing."
            >
              <div className="overflow-hidden rounded-lg border border-zinc-200">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] border-collapse text-left text-sm">
                    <thead className="bg-zinc-50 text-[10px] tracking-wider text-zinc-500 uppercase">
                      <tr>
                        <th className="px-3 py-2 font-medium">Status</th>
                        <th className="px-3 py-2 font-medium">Meaning</th>
                        <th className="px-3 py-2 font-medium">Typical causes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-200">
                      {[
                        {
                          status: '200',
                          meaning: 'OK',
                          description: 'Request succeeded.',
                        },
                        {
                          status: '201',
                          meaning: 'Created',
                          description: 'Registration succeeded.',
                        },
                        {
                          status: '400',
                          meaning: 'Bad Request',
                          description:
                            'Registration failed, invalid reset or verification token, logout failure, or missing pending 2FA session.',
                        },
                        {
                          status: '401',
                          meaning: 'Unauthorized',
                          description:
                            'Invalid credentials, invalid or revoked access token, or invalid refresh token.',
                        },
                        {
                          status: '403',
                          meaning: 'Forbidden',
                          description:
                            'Admin access required, insufficient permissions, inactive account, or self-modification restriction.',
                        },
                        {
                          status: '404',
                          meaning: 'Not Found',
                          description: 'User or resource not found.',
                        },
                        {
                          status: '422',
                          meaning: 'Unprocessable Entity',
                          description: 'Request validation failed.',
                        },
                        {
                          status: '429',
                          meaning: 'Too Many Requests',
                          description: 'Login rate limit exceeded.',
                        },
                        {
                          status: '500',
                          meaning: 'Internal Server Error',
                          description:
                            'Unexpected error. The response includes a request_id.',
                        },
                      ].map((row) => (
                        <tr key={row.status}>
                          <td className="px-3 py-2 align-top font-mono text-xs text-zinc-950">
                            {row.status}
                          </td>
                          <td className="px-3 py-2 align-top text-xs font-medium text-zinc-700">
                            {row.meaning}
                          </td>
                          <td className="px-3 py-2 align-top text-xs leading-5 text-zinc-600">
                            {row.description}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-2">
                <div className="space-y-2">
                  <p className="text-xs font-medium tracking-wider text-zinc-500 uppercase">
                    422 validation error
                  </p>
                  <CodeBlock
                    title="Response"
                    code={`{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short",
      "ctx": {
        "min_length": 8
      }
    }
  ]
}`}
                  />
                </div>
                <div className="space-y-2">
                  <p className="text-xs font-medium tracking-wider text-zinc-500 uppercase">
                    Authentication errors
                  </p>
                  <CodeBlock
                    title="401 Unauthorized"
                    code={`{
  "detail": "Invalid credentials."
}`}
                  />
                  <CodeBlock
                    title="401 Unauthorized"
                    code={`{
  "detail": "Invalid token."
}`}
                  />
                </div>
              </div>

              <div className="mt-3 grid gap-3 lg:grid-cols-2">
                <CodeBlock
                  title="403 Forbidden"
                  code={`{
  "detail": "Insufficient permissions."
}`}
                />
                <CodeBlock
                  title="500 Internal Server Error"
                  code={`{
  "detail": "Internal server error.",
  "request_id": "<request_id>"
}`}
                />
              </div>
            </DocsSection>
          </main>
        </div>
      </div>

      <DocsFooter />
    </div>
  )
}
