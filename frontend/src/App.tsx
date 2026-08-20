import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/toaster'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { LoginPage } from '@/pages/Login'
import { RegisterPage } from '@/pages/Register'
import { ForgotPasswordPage } from '@/pages/ForgotPassword'
import { DashboardPage } from '@/pages/Dashboard'
import { DatasetsPage } from '@/pages/Datasets'
import { ReportsPage } from '@/pages/Reports'
import { ReportDetailPage } from '@/pages/ReportDetail'
import { ChatPage } from '@/pages/Chat'
import { ForecastsPage } from '@/pages/Forecasts'
import { TeamPage } from '@/pages/Team'
import { SettingsPage } from '@/pages/Settings'
import { useAuthStore } from '@/store/authStore'
import { ThemeProvider } from '@/context/ThemeContext'
import '@/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, checkAuth } = useAuthStore()
  
  React.useEffect(() => {
    checkAuth()
  }, [checkAuth])
  
  if (!isAuthenticated) {
    return <Navigate to='/login' replace />
  }
  
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, checkAuth } = useAuthStore()
  
  React.useEffect(() => {
    checkAuth()
  }, [checkAuth])
  
  if (isAuthenticated) {
    return <Navigate to='/dashboard' replace />
  }
  
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path='/login' element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path='/register' element={
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      } />
      <Route path='/forgot-password' element={
        <PublicRoute>
          <ForgotPasswordPage />
        </PublicRoute>
      } />
      <Route element={
        <ProtectedRoute>
          <DashboardLayout />
        </ProtectedRoute>
      }>
        <Route path='/dashboard' element={<DashboardPage />} />
        <Route path='/datasets' element={<DatasetsPage />} />
        <Route path='/datasets/:id' element={<DatasetsPage />} />
        <Route path='/reports' element={<ReportsPage />} />
        <Route path='/reports/:id' element={<ReportDetailPage />} />
        <Route path='/reports/generate' element={<ReportsPage />} />
        <Route path='/chat' element={<ChatPage />} />
        <Route path='/forecasts' element={<ForecastsPage />} />
        <Route path='/team' element={<TeamPage />} />
        <Route path='/settings' element={<SettingsPage />} />
      </Route>
      <Route path='/' element={<Navigate to='/dashboard' replace />} />
      <Route path='*' element={<Navigate to='/dashboard' replace />} />
    </Routes>
  )
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AppRoutes />
          <Toaster position='top-right' />
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App
