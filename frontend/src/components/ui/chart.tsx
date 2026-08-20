'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config?: Record<string, { label: string; color: string }>
}

export function ChartContainer({
  children,
  config,
  className,
  ...props
}: ChartContainerProps) {
  return (
    <div
      className={cn('flex aspect-video w-full', className)}
      {...props}
    >
      <div className='w-full h-full'>{children}</div>
      {config && (
        <div className='hidden lg:flex lg:w-72 flex-col gap-2 p-4'>
          {Object.entries(config).map(([key, { label, color }]) => (
            <div key={key} className='flex items-center gap-2'>
              <div className='h-3 w-3 rounded-full' style={{ backgroundColor: color }} />
              <span className='text-sm'>{label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function createChartConfig(
  config: Record<string, { label: string; color: string }>
) {
  return config
}
