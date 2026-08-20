import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/api/client'

export interface User {
  id: string
  email: string
  full_name: string | null
  role: string
  org_id: string
  avatar_url?: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  setUser: (user: User) => void
  checkAuth: () => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  full_name: string
  org_name: string
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await api.post<{
            access_token: string
            refresh_token: string
            user: User
          }>('/auth/login', { email, password })
          
          localStorage.setItem('access_token', response.access_token)
          localStorage.setItem('refresh_token', response.refresh_token)
          localStorage.setItem('user', JSON.stringify(response.user))
          
          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true })
        try {
          const response = await api.post<{
            access_token: string
            refresh_token: string
            user: User
          }>('/auth/register', data)
          
          localStorage.setItem('access_token', response.access_token)
          localStorage.setItem('refresh_token', response.refresh_token)
          localStorage.setItem('user', JSON.stringify(response.user))
          
          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        const refreshToken = get().refreshToken
        if (refreshToken) {
          api.post('/auth/logout', { refresh_token: refreshToken }).catch(() => {})
        }
        
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      refreshAccessToken: async () => {
        const refreshToken = get().refreshToken
        if (!refreshToken) throw new Error('No refresh token')

        try {
          const response = await api.post<{ access_token: string }>('/auth/refresh', {
            refresh_token: refreshToken,
          })
          
          localStorage.setItem('access_token', response.access_token)
          set({ accessToken: response.access_token })
        } catch (error) {
          get().logout()
          throw error
        }
      },

      setUser: (user: User) => {
        localStorage.setItem('user', JSON.stringify(user))
        set({ user })
      },

      checkAuth: async () => {
        const accessToken = localStorage.getItem('access_token')
        const refreshToken = localStorage.getItem('refresh_token')
        const userStr = localStorage.getItem('user')
        
        if (accessToken && refreshToken && userStr) {
          try {
            const user = JSON.parse(userStr)
            set({
              user,
              accessToken,
              refreshToken,
              isAuthenticated: true,
            })
          } catch {
            get().logout()
          }
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
