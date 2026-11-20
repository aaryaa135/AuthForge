import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import {
  ArrowDownIcon,
  ArrowRightIcon,
  CheckIcon,
  CodeIcon,
  DatabaseIcon,
  FingerprintIcon,
  GaugeIcon,
  KeyRoundIcon,
  LayersIcon,
  LockKeyholeIcon,
  MenuIcon,
  ScrollTextIcon,
  ServerIcon,
  ShieldCheckIcon,
  TerminalIcon,
  UsersIcon,
  XIcon,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

const GITHUB_URL = 'https://github.com/aaryaa135/AuthForge'

interface HealthResponse {
  status: string
  version?: string
  environment?: string
}

const features = [
  {
    icon: KeyRoundIcon,
    title: 'JWT authentication',
    description:
      'Short-lived access tokens with refresh-token rotation, revocation, and single-flight renewal.',
  },
  {
    icon: FingerprintIcon,
    title: 'TOTP two-factor authentication',
    description:
      'Time-based one-time passwords with backup codes and a dedicated login challenge.',
  },
  {
    icon: UsersIcon,
    title: 'Role-based access control',
    description:
      'Admin, Manager, and User roles enforced by server-side authorization dependencies.',
  },
  {
    icon: LockKeyholeIcon,
    title: 'API key management',
    description:
      'Create scoped service credentials with optional expiry and one-time key disclosure.',
  },
  {
    icon: ScrollTextIcon,
    title: 'Audit logging',
    description:
      'Track authentication and security events with searchable, filterable logs.',
  },
  {
    icon: GaugeIcon,
    title: 'Redis-backed rate limiting',
    description:
      'Protect login endpoints with request throttling backed by Redis.',
  },
]

const stackGroups = [
  {
    title: 'Frontend',
    items: [
      'React 19',
      'TypeScript',
      'Vite',
      'Tailwind CSS',
      'React Router',
      'TanStack Query',
      'Axios',
      'Lucide',
    ],
  },
  {
    title: 'Backend & infrastructure',
    items: [
      'Python 3.11',
      'FastAPI',
      'Pydantic',
      'SQLAlchemy',
      'Alembic',
      'PostgreSQL',
      'Redis',
      'python-jose',
      'Passlib + bcrypt',
      'Uvicorn',
    ],
  },
]

const securityPoints = [
  'JWT access tokens with refresh-token rotation',
  'TOTP two-factor authentication with backup codes',
  'Role-based access control enforced server-side',
  'API keys with scopes, expiry, and revocation',
  'Audit logging for authentication events',
  'Redis-backed rate limiting on login',
  'bcrypt password hashing',
  'Security headers and configurable CORS',
]

function useHealthStatus() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const { data } = await axios.get<HealthResponse>(`${API_BASE_URL}/health`, {
        timeout: 5000,
      })
      return data
    },
    retry: 1,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

function ApiStatus() {
  const { data, isPending, isError } = useHealthStatus()
  const isOnline = !isPending && !isError && data?.status === 'healthy'
  const label = isPending ? 'API loading' : isOnline ? 'API online' : 'API offline'

  return (
    <span className="inline-flex items-center gap-2" aria-live="polite">
      <span
        className={
          isPending
            ? 'size-1.5 rounded-full bg-zinc-400'
            : isOnline
              ? 'size-1.5 rounded-full bg-zinc-950'
              : 'size-1.5 rounded-full bg-white ring-1 ring-zinc-400'
        }
      />
      {label}
    </span>
  )
}

function LandingNav() {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm font-semibold tracking-tight text-zinc-950"
        >
          <ShieldCheckIcon className="size-5" strokeWidth={1.75} />
          AuthForge
        </Link>

        <nav className="hidden items-center gap-7 text-sm text-zinc-600 md:flex">
          <a href="#features" className="transition-colors hover:text-zinc-950">
            Features
          </a>
          <a href="#architecture" className="transition-colors hover:text-zinc-950">
            Architecture
          </a>
          <Link to="/docs" className="transition-colors hover:text-zinc-950">
            Documentation
          </Link>
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Button
            asChild
            variant="ghost"
            className="text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
          >
            <Link to="/login">Sign in</Link>
          </Button>
          <Button asChild className="bg-zinc-950 text-white hover:bg-zinc-800">
            <Link to="/register">Get started</Link>
          </Button>
        </div>

        <button
          type="button"
          className="inline-flex size-9 items-center justify-center rounded-md border border-zinc-200 text-zinc-950 md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls="mobile-navigation"
          aria-label={open ? 'Close navigation' : 'Open navigation'}
        >
          {open ? <XIcon className="size-4" /> : <MenuIcon className="size-4" />}
        </button>
      </div>

      {open ? (
        <div id="mobile-navigation" className="border-t border-zinc-200 bg-white md:hidden">
          <nav className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-3 text-sm sm:px-6">
            <a
              href="#features"
              onClick={() => setOpen(false)}
              className="rounded-md px-2 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
            >
              Features
            </a>
            <a
              href="#architecture"
              onClick={() => setOpen(false)}
              className="rounded-md px-2 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
            >
              Architecture
            </a>
            <Link
              to="/docs"
              onClick={() => setOpen(false)}
              className="rounded-md px-2 py-2 text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950"
            >
              Documentation
            </Link>
            <Separator className="my-2" />
            <Button
              asChild
              variant="outline"
              className="border-zinc-300 bg-white text-zinc-950 hover:bg-zinc-100"
            >
              <Link to="/login" onClick={() => setOpen(false)}>
                Sign in
              </Link>
            </Button>
            <Button asChild className="bg-zinc-950 text-white hover:bg-zinc-800">
              <Link to="/register" onClick={() => setOpen(false)}>
                Get started
              </Link>
            </Button>
          </nav>
        </div>
      ) : null}
    </header>
  )
}

function CodePreview() {
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 text-zinc-300">
      <div className="flex items-center justify-between border-b border-zinc-800 px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <TerminalIcon className="size-3.5" />
          auth.http
        </div>
        <span className="rounded border border-zinc-700 px-1.5 py-0.5 font-mono text-[10px] text-zinc-400">
          200 OK
        </span>
      </div>
      <pre className="overflow-x-auto p-5 font-mono text-[12px] leading-6 sm:text-[13px]">
        <code>{`POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=ada@authforge.dev
password=••••••••••••

200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_9f2c...",
  "token_type": "bearer"
}`}</code>
      </pre>
    </div>
  )
}

function SectionHeading({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string
  title: string
  description: string
}) {
  return (
    <div className="max-w-2xl">
      <p className="text-xs font-medium tracking-[0.18em] text-zinc-500 uppercase">
        {eyebrow}
      </p>
      <h2 className="mt-3 text-2xl font-semibold tracking-tight text-zinc-950 sm:text-3xl">
        {title}
      </h2>
      <p className="mt-3 text-sm leading-6 text-zinc-600">{description}</p>
    </div>
  )
}

function ArchitectureNode({
  icon: Icon,
  title,
  description,
  meta,
}: {
  icon: typeof CodeIcon
  title: string
  description: string
  meta: string
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon className="size-4 text-zinc-500" />
          <h3 className="text-sm font-semibold text-zinc-950">{title}</h3>
        </div>
        <span className="font-mono text-[10px] tracking-wider text-zinc-400 uppercase">
          {meta}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-zinc-600">{description}</p>
    </div>
  )
}

function Connector({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-center gap-2 lg:flex-col">
      <ArrowDownIcon className="size-4 text-zinc-400 lg:hidden" />
      <ArrowRightIcon className="hidden size-4 text-zinc-400 lg:block" />
      <span className="font-mono text-[10px] tracking-wider text-zinc-400 uppercase">
        {label}
      </span>
    </div>
  )
}

export function LandingPage() {
  return (
    <div className="min-h-svh bg-white text-zinc-950">
      <LandingNav />

      <section className="border-b border-zinc-200">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:py-28">
          <div>
            <p className="text-xs font-medium tracking-[0.2em] text-zinc-500 uppercase">
              Authentication infrastructure
            </p>
            <h1 className="mt-4 max-w-xl text-4xl font-semibold tracking-tight text-zinc-950 sm:text-5xl">
              Authentication infrastructure, built for developers.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-zinc-600">
              AuthForge is a secure, modular authentication backend for teams that need
              JWT sessions, two-factor authentication, role-based access control, API
              keys, and audit trails without rebuilding the plumbing from scratch.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="h-11 bg-zinc-950 px-5 text-white hover:bg-zinc-800"
              >
                <Link to="/dashboard">
                  Explore dashboard
                  <ArrowRightIcon />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="h-11 border-zinc-300 bg-white px-5 text-zinc-950 hover:bg-zinc-100"
              >
                <Link to="/docs">View API docs</Link>
              </Button>
            </div>
            <div className="mt-6 flex flex-wrap items-center gap-3 text-xs text-zinc-500">
              <ApiStatus />
              <span className="h-3 w-px bg-zinc-200" />
              <span>FastAPI · PostgreSQL · Redis</span>
            </div>
          </div>

          <CodePreview />
        </div>
      </section>

      <section id="features" className="scroll-mt-20 border-b border-zinc-200">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <SectionHeading
            eyebrow="Capabilities"
            title="Everything you need to ship authentication."
            description="A focused set of primitives that cover the full account lifecycle, from first registration to long-lived service credentials."
          />
          <div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-zinc-200 bg-zinc-200 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="bg-white p-6">
                <div className="flex size-9 items-center justify-center rounded-lg border border-zinc-200 text-zinc-950">
                  <Icon className="size-4" />
                </div>
                <h3 className="mt-4 text-sm font-semibold text-zinc-950">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-zinc-600">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section
        id="architecture"
        className="scroll-mt-20 border-b border-zinc-200 bg-zinc-50"
      >
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <SectionHeading
            eyebrow="Architecture"
            title="A small, deliberate system."
            description="A React client talks to a FastAPI backend over a versioned REST API. PostgreSQL stores durable state while Redis handles short-lived authentication concerns."
          />
          <div className="mt-10 rounded-xl border border-zinc-200 bg-white p-4 sm:p-6">
            <div className="grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1.1fr] lg:items-center">
              <ArchitectureNode
                icon={CodeIcon}
                title="React frontend"
                description="Vite, TypeScript, Tailwind CSS, and TanStack Query consume the versioned REST API."
                meta="Client"
              />
              <Connector label="HTTPS" />
              <ArchitectureNode
                icon={ServerIcon}
                title="FastAPI backend"
                description="JWT issuance, RBAC, TOTP, API keys, audit logging, and security middleware."
                meta="API"
              />
              <Connector label="SQL / cache" />
              <div className="grid gap-3">
                <ArchitectureNode
                  icon={DatabaseIcon}
                  title="PostgreSQL"
                  description="Users, roles, refresh tokens, API keys, and audit records."
                  meta="Durable"
                />
                <ArchitectureNode
                  icon={LayersIcon}
                  title="Redis"
                  description="Rate limiting and short-lived authentication session state."
                  meta="Ephemeral"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-zinc-200">
        <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
          <SectionHeading
            eyebrow="Stack"
            title="Built with tools you already know."
            description="No proprietary runtime or hosted auth service. AuthForge is a normal web stack you can run, inspect, and extend."
          />
          <div className="mt-10 grid gap-6 lg:grid-cols-2">
            {stackGroups.map((group) => (
              <div key={group.title} className="rounded-xl border border-zinc-200 p-6">
                <h3 className="text-sm font-semibold text-zinc-950">{group.title}</h3>
                <div className="mt-4 flex flex-wrap gap-2">
                  {group.items.map((item) => (
                    <span
                      key={item}
                      className="rounded-md border border-zinc-200 bg-zinc-50 px-2.5 py-1 text-xs font-medium text-zinc-700"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-zinc-200 bg-zinc-50">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 py-20 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
          <div>
            <SectionHeading
              eyebrow="Security"
              title="Security is part of the foundation."
              description="Authentication decisions are enforced by the backend. The frontend reflects permissions, but never replaces server-side checks."
            />
            <Button
              asChild
              variant="outline"
              className="mt-6 border-zinc-300 bg-white text-zinc-950 hover:bg-zinc-100"
            >
              <Link to="/docs">Read the API documentation</Link>
            </Button>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {securityPoints.map((point) => (
              <li
                key={point}
                className="flex items-start gap-2 rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-700"
              >
                <CheckIcon className="mt-0.5 size-4 shrink-0 text-zinc-950" />
                {point}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <footer className="bg-white">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <Link
                to="/"
                className="flex items-center gap-2 text-sm font-semibold tracking-tight text-zinc-950"
              >
                <ShieldCheckIcon className="size-5" strokeWidth={1.75} />
                AuthForge
              </Link>
              <p className="mt-2 max-w-xs text-sm leading-6 text-zinc-600">
                A secure, modular authentication backend for developer teams.
              </p>
            </div>
            <nav className="flex flex-wrap gap-x-8 gap-y-3 text-sm text-zinc-600">
              <Link to="/docs" className="transition-colors hover:text-zinc-950">
                Documentation
              </Link>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer"
                className="transition-colors hover:text-zinc-950"
              >
                GitHub
              </a>
              <Link to="/login" className="transition-colors hover:text-zinc-950">
                Sign in
              </Link>
            </nav>
          </div>
          <Separator className="my-6" />
          <div className="flex flex-col gap-2 text-xs text-zinc-500 sm:flex-row sm:items-center sm:justify-between">
            <p>Built with FastAPI, PostgreSQL, Redis, and React.</p>
            <p>AuthForge</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
