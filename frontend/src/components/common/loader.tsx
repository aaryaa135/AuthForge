import { Loader2Icon } from 'lucide-react'

export function FullPageLoader({ label = 'Loading AuthForge…' }: { label?: string }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2Icon className="size-6 animate-spin" />
      <p className="text-sm">{label}</p>
    </div>
  )
}
