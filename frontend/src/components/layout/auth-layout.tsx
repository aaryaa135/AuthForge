import { ShieldCheckIcon } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'

const highlights = [
  'JWT access and refresh token rotation',
  'TOTP two-factor authentication with backup codes',
  'Role-based access control and audit trails',
  'Service account API keys with scopes and expiry',
]

export function AuthLayout() {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-zinc-950 p-10 text-zinc-50 lg:flex">
        <div className="absolute -top-24 -right-24 size-96 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute -bottom-32 -left-24 size-96 rounded-full bg-sky-500/20 blur-3xl" />

        <Link to="/" className="relative flex items-center gap-2 text-lg font-semibold">
          <ShieldCheckIcon className="size-6 text-emerald-400" />
          AuthForge
        </Link>

        <div className="relative space-y-6">
          <h2 className="max-w-md text-3xl font-semibold tracking-tight">
            A complete authentication console for your platform.
          </h2>
          <ul className="space-y-3 text-sm text-zinc-300">
            {highlights.map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-emerald-400" />
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-zinc-500">
          FastAPI · PostgreSQL · Redis · JWT rotation · RBAC · Audit logging
        </p>
      </aside>

      <main className="flex items-center justify-center bg-muted/30 p-6">
        <div className="w-full max-w-md">
          <Link
            to="/"
            className="mb-8 flex items-center justify-center gap-2 text-base font-semibold lg:hidden"
          >
            <ShieldCheckIcon className="size-5 text-emerald-600" />
            AuthForge
          </Link>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
