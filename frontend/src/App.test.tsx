import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('renders the login page when unauthenticated', () => {
    render(<App />)
    expect(screen.getByText(/Welcome back/)).toBeInTheDocument()
  })
})