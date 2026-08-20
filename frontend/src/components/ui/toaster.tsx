'use client'

import { Toaster as HotToastToaster, toast } from 'react-hot-toast'
import { cn } from '@/lib/utils'

interface ToasterProps {
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right'
  theme?: 'light' | 'dark'
}

export function Toaster({ position = 'top-right', theme = 'light' }: ToasterProps) {
  return (
    <HotToastToaster
      position={position}
      toastOptions={{
        className: cn(
          'group',
          'bg-background text-foreground',
          'border border-border',
          'shadow-lg',
          'animate-slide-in'
        ),
        duration: 4000,
        style: {
          background: 'var(--background)',
          color: 'var(--foreground)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '1rem',
        },
        success: {
          iconTheme: {
            primary: '#22c55e',
            secondary: '#fff',
          },
        },
        error: {
          iconTheme: {
            primary: '#ef4444',
            secondary: '#fff',
          },
        },
      }}
    />
  )
}

export { toast }
