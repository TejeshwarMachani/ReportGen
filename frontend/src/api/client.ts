import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private client: AxiosInstance
  private refreshTokenPromise: Promise<string> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    })

    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const accessToken = localStorage.getItem('access_token')
        if (accessToken && config.headers) {
          config.headers.Authorization = \Bearer \\
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true
          
          try {
            const newAccessToken = await this.refreshAccessToken()
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = \Bearer \\
            }
            return this.client(originalRequest)
          } catch (refreshError) {
            this.clearAuth()
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }
        
        return Promise.reject(error)
      }
    )
  }

  private async refreshAccessToken(): Promise<string> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise
    }

    this.refreshTokenPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token')
      }

      const response = await axios.post(\\/auth/refresh\, {
        refresh_token: refreshToken,
      })

      const { access_token } = response.data
      localStorage.setItem('access_token', access_token)
      return access_token
    })()

    try {
      const token = await this.refreshTokenPromise
      return token
    } finally {
      this.refreshTokenPromise = null
    }
  }

  private clearAuth() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async get<T>(url: string, params?: Record<string, unknown>) {
    const response = await this.client.get<T>(url, { params })
    return response.data
  }

  async post<T>(url: string, data?: unknown) {
    const response = await this.client.post<T>(url, data)
    return response.data
  }

  async patch<T>(url: string, data?: unknown) {
    const response = await this.client.patch<T>(url, data)
    return response.data
  }

  async delete<T>(url: string) {
    const response = await this.client.delete<T>(url)
    return response.data
  }

  async upload<T>(url: string, file: File, onProgress?: (progress: number) => void) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
    return response.data
  }
}

export const api = new ApiClient()
