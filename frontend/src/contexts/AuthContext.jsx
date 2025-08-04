import React, { createContext, useContext, useState, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Configure axios defaults - detect if we're in development
const API_BASE_URL = window.location.port === '3000' ? 'http://localhost:8000/api/v1' : '/api/v1'
axios.defaults.baseURL = API_BASE_URL
axios.defaults.headers.common['Content-Type'] = 'application/json'

// Add token to requests if available and handle token refresh
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Handle token refresh on 401 responses
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      // Try to refresh the token
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        try {
          const response = await axios.post('/auth/refresh/', {
            refresh: refreshToken
          })
          
          const newToken = response.data.access
          localStorage.setItem('authToken', newToken)
          
          // Retry the original request with new token
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          return axios(originalRequest)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('authToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
        }
      } else {
        // No refresh token, redirect to login
        localStorage.removeItem('authToken')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('authToken')
      if (!token) {
        setLoading(false)
        return
      }

      const response = await axios.get('/auth/user/')
      setUser(response.data.user || response.data)
    } catch (err) {
      console.error('Auth check failed:', err)
      // Only log the error, don't crash the app
      localStorage.removeItem('authToken')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      setError(null)
      const response = await axios.post('/auth/login/', { email, password })
      const { token, refresh, user } = response.data
      
      localStorage.setItem('authToken', token)
      if (refresh) {
        localStorage.setItem('refreshToken', refresh)
      }
      setUser(user)
      
      return { success: true }
    } catch (err) {
      const message = err.response?.data?.error || err.response?.data?.message || 'Login failed'
      setError(message)
      return { success: false, error: message }
    }
  }

  const register = async (userData) => {
    try {
      setError(null)
      const response = await axios.post('/auth/register/', userData)
      const { token, refresh, user } = response.data
      
      localStorage.setItem('authToken', token)
      if (refresh) {
        localStorage.setItem('refreshToken', refresh)
      }
      setUser(user)
      
      return { success: true }
    } catch (err) {
      const message = err.response?.data?.error || err.response?.data?.message || 'Registration failed'
      setError(message)
      return { success: false, error: message }
    }
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('refreshToken')
    setUser(null)
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    checkAuth,
    isAuthenticated: !!user,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}