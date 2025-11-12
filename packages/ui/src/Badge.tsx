'use client'

import * as React from 'react'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'primary' | 'accent' | 'success' | 'warning' | 'destructive' | 'outline'
}

const variantStyles = {
  default: 'bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-slate-100',
  primary: 'bg-primary-100 dark:bg-primary-900 text-primary-900 dark:text-primary-100',
  accent: 'bg-accent-100 dark:bg-accent-900 text-accent-900 dark:text-accent-100',
  success: 'bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100',
  warning: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100',
  destructive: 'bg-red-100 dark:bg-red-900 text-red-900 dark:text-red-100',
  outline: 'border border-border text-foreground',
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => (
    <div
      ref={ref}
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors ${variantStyles[variant]} ${className}`}
      {...props}
    />
  ),
)
Badge.displayName = 'Badge'

export { Badge }
