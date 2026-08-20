'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

const DropdownMenu = ({ children, ...props }: React.ComponentProps<'div'>) => (
  <div className='relative' {...props}>{children}</div>
)

interface DropdownMenuTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean
}

const DropdownMenuTrigger = React.forwardRef<HTMLButtonElement, DropdownMenuTriggerProps>(
  ({ className, children, asChild = false, ...props }, ref) => {
    // When `asChild` is used, render the child directly (e.g. a Button) so the
    // composability matches the Radix-style API used across the app.
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        className: cn(
          'flex items-center space-x-1 rounded-md bg-background px-3 py-2 text-sm font-medium ring-offset-background hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          className,
          (children as React.ReactElement<{ className?: string }>).props?.className
        ),
      })
    }
    return (
      <button
        ref={ref}
        className={cn(
          'flex items-center space-x-1 rounded-md bg-background px-3 py-2 text-sm font-medium ring-offset-background hover:bg-accent hover:text-accent-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
          className
        )}
        {...props}
      >
        {children}
        <ChevronDown className='h-4 w-4' />
      </button>
    )
  }
)
DropdownMenuTrigger.displayName = 'DropdownMenuTrigger'

interface DropdownMenuContentProps extends React.HTMLAttributes<HTMLDivElement> {
  align?: 'start' | 'center' | 'end'
}

const DropdownMenuContent = React.forwardRef<HTMLDivElement, DropdownMenuContentProps>(
  ({ className, children, align = 'end', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'absolute right-0 mt-2 z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-scale-in',
        align === 'start' && 'left-0 right-auto',
        align === 'center' && 'left-1/2 -translate-x-1/2 right-auto',
        align === 'end' && 'right-0',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
)
DropdownMenuContent.displayName = 'DropdownMenuContent'

interface DropdownMenuItemProps extends React.HTMLAttributes<HTMLDivElement> {
  inset?: boolean
  asChild?: boolean
  disabled?: boolean
}

const DropdownMenuItem = React.forwardRef<HTMLDivElement, DropdownMenuItemProps>(
  ({ className, inset, asChild = false, disabled, children, ...props }, ref) => {
    const cls = cn(
      'relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground',
      inset && 'pl-8',
      disabled && 'pointer-events-none opacity-50',
      className
    )
    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{ className?: string }>
      return React.cloneElement(child, { className: cn(cls, child.props.className) })
    }
    return (
      <div ref={ref} className={cls} aria-disabled={disabled} {...props}>
        {children}
      </div>
    )
  }
)
DropdownMenuItem.displayName = 'DropdownMenuItem'

const DropdownMenuSeparator = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('-mx-1 my-1 h-px bg-muted', className)}
      {...props}
    />
  )
)
DropdownMenuSeparator.displayName = 'DropdownMenuSeparator'

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator }
