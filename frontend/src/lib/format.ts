const dateFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return dateFormatter.format(date)
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return dateTimeFormatter.format(date)
}

export function formatRelativeTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'

  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000)
  const formatter = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' })
  const thresholds: Array<{ limit: number; unit: Intl.RelativeTimeFormatUnit; divisor: number }> = [
    { limit: 60, unit: 'second', divisor: 1 },
    { limit: 3600, unit: 'minute', divisor: 60 },
    { limit: 86400, unit: 'hour', divisor: 3600 },
    { limit: 604800, unit: 'day', divisor: 86400 },
    { limit: 2629800, unit: 'week', divisor: 604800 },
    { limit: 31557600, unit: 'month', divisor: 2629800 },
    { limit: Number.POSITIVE_INFINITY, unit: 'year', divisor: 31557600 },
  ]

  const absolute = Math.abs(diffSeconds)
  const threshold = thresholds.find((item) => absolute < item.limit) ?? thresholds[0]

  return formatter.format(Math.round(diffSeconds / threshold.divisor), threshold.unit)
}

export function getInitials(email: string): string {
  const localPart = email.split('@')[0] ?? email
  const parts = localPart.split(/[._-]/).filter(Boolean)
  const initials = parts.slice(0, 2).map((part) => part[0])
  return (initials.join('') || localPart.slice(0, 2)).toUpperCase()
}

export async function copyToClipboard(value: string): Promise<void> {
  await navigator.clipboard.writeText(value)
}
