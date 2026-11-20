import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  tone: 'success' | 'danger' | 'neutral' | 'info'
  children: string
}

const toneClasses: Record<StatusBadgeProps['tone'], string> = {
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  danger: 'border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-400',
  neutral: 'border-border bg-muted text-muted-foreground',
  info: 'border-sky-500/30 bg-sky-500/10 text-sky-700 dark:text-sky-400',
}

export function StatusBadge({ tone, children }: StatusBadgeProps) {
  return (
    <Badge variant="outline" className={cn('font-medium', toneClasses[tone])}>
      {children}
    </Badge>
  )
}
