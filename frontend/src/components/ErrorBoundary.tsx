'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw, AlertTriangle } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className='flex min-h-[400px] items-center justify-center p-8'>
          <div className='text-center space-y-4 max-w-md'>
            <div className='mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10'>
              <AlertTriangle className='h-8 w-8 text-destructive' />
            </div>
            <div>
              <h2 className='text-xl font-semibold'>Something went wrong</h2>
              <p className='mt-2 text-muted-foreground'>
                We encountered an unexpected error. Please try again.
              </p>
              {this.state.error && (
                <details className='mt-4 text-left text-sm text-muted-foreground'>
                  <summary className='cursor-pointer select-none'>Error details</summary>
                  <pre className='mt-2 p-3 overflow-auto bg-muted rounded'>
                    {this.state.error.message}
                  </pre>
                </details>
              )}
            </div>
            <Button onClick={this.handleRetry} className='mt-2'>
              <RefreshCw className='mr-2 h-4 w-4' />
              Try again
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
