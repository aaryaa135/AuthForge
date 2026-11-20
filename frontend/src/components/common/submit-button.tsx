import { Loader2Icon } from 'lucide-react'
import type { ComponentProps, ReactNode } from 'react'


import { Button } from '@/components/ui/button'

interface SubmitButtonProps extends ComponentProps<typeof Button> {
  loading?: boolean
  children: ReactNode
}

export function SubmitButton({
  loading = false,
  children,
  disabled,
  ...props
}: SubmitButtonProps) {
  return (
    <Button type="submit" disabled={disabled || loading} {...props}>
      {loading ? <Loader2Icon className="animate-spin" /> : null}
      {children}
    </Button>
  )
}
