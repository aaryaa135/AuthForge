import {
  ChevronDownIcon,
  KeyRoundIcon,
  LayoutDashboardIcon,
  LogOutIcon,
  ScrollTextIcon,
  ShieldCheckIcon,
  UsersIcon,
} from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuth } from '@/context/auth-context'
import { getInitials } from '@/lib/format'
import { cn } from '@/lib/utils'

const baseLinks = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboardIcon },
  { to: '/security', label: 'Security', icon: ShieldCheckIcon },
  { to: '/api-keys', label: 'API keys', icon: KeyRoundIcon },
]

const adminLinks = [
  { to: '/admin/users', label: 'Users', icon: UsersIcon },
  { to: '/admin/audit', label: 'Audit log', icon: ScrollTextIcon },
]

function navLinkClass({ isActive }: { isActive: boolean }): string {
  return cn(
    'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors',
    isActive
      ? 'bg-primary text-primary-foreground'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
  )
}

export function AppShell() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const links = user.role === 'Admin' ? [...baseLinks, ...adminLinks] : baseLinks

  async function handleSignOut() {
    await signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-svh bg-muted/20">
      <header className="sticky top-0 z-40 border-b bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4">
          <Link to="/dashboard" className="flex items-center gap-2 font-semibold">
            <ShieldCheckIcon className="size-5 text-emerald-600" />
            AuthForge
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {links.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navLinkClass}>
                <Icon className="size-4" />
                {label}
              </NavLink>
            ))}
          </nav>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-9 gap-2 px-2">
                <Avatar size="sm">
                  <AvatarFallback className="text-[10px]">
                    {getInitials(user.email)}
                  </AvatarFallback>
                </Avatar>
                <span className="hidden max-w-40 truncate text-sm sm:inline">
                  {user.email}
                </span>
                <ChevronDownIcon className="size-4 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60">
              <DropdownMenuLabel className="space-y-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {user.username}
                </p>
                <p className="truncate text-xs font-normal">{user.email}</p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs uppercase tracking-wide">
                {user.role}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {links.map(({ to, label, icon: Icon }) => (
                <DropdownMenuItem key={to} asChild>
                  <Link to={to}>
                    <Icon />
                    {label}
                  </Link>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onSelect={handleSignOut}>
                <LogOutIcon />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <nav className="flex items-center gap-1 overflow-x-auto border-t px-2 py-1 md:hidden">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={navLinkClass}>
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
