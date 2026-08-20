'use client'

import * as React from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { cn } from '@/lib/utils'
import { ErrorBoundary } from '@/components/ErrorBoundary'

function DashboardContent() {
  return (
    <div className='flex h-screen bg-background'>
      <Sidebar />
      <div className={cn('flex flex-1 flex-col overflow-hidden')}>
        <Header />
        <main className='flex-1 overflow-y-auto p-4 lg:p-6 animate-fade-in'>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function DashboardLayout() {
  return (
    <ErrorBoundary>
      <DashboardContent />
    </ErrorBoundary>
  )
}
