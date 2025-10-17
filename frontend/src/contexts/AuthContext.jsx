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

// 🔒 SECURITY: Enable credentials for cookie-based authentication (CVE-2024-JWT-003)
// This ensures httpOnly cookies are sent with all requests
axios.defaults.withCredentials = true

// Get CSRF token from cookie for mutation requests
function getCsrfToken() {
  const name = 'csrftoken'
  const cookies = document.cookie.split(';')

  for (let cookie of cookies) {
    cookie = cookie.trim()
    if (cookie.startsWith(name + '=')) {
      return decodeURIComponent(cookie.substring(name.length + 1))
    }
  }
  return null
}

// Add CSRF token to mutation requests (POST, PUT, PATCH, DELETE)
axios.interceptors.request.use(
  (config) => {
    // Add CSRF token for mutation requests
    if (['post', 'put', 'patch', 'delete'].includes(config.method?.toLowerCase())) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken
      }
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

      // Try to refresh the token (reads from httpOnly cookie automatically)
      try {
        await axios.post('/auth/refresh/')

        // Token refreshed successfully (new token set in httpOnly cookie)
        // Retry the original request
        return axios(originalRequest)
      } catch (refreshError) {
        // Refresh failed, redirect to login
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
      // 🔒 SECURITY: No need to check localStorage
      // Authentication cookies are sent automatically with withCredentials: true
      const response = await axios.get('/auth/user/')
      setUser(response.data.user || response.data)
    } catch (err) {
      // 🔒 SECURITY: Only log errors in development to avoid exposing internals
      if (import.meta.env.DEV) {
        console.error('Auth check failed:', err)
      }
      // Only log the error, don't crash the app
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email, password) => {
    try {
      setError(null)
      const response = await axios.post('/auth/login/', { email, password })
      const { user } = response.data

      // 🔒 SECURITY: No localStorage! Tokens are in httpOnly cookies
      // Cookies are set automatically by the server and sent with subsequent requests
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
      const { user } = response.data

      // 🔒 SECURITY: No localStorage! Tokens are in httpOnly cookies
      // Cookies are set automatically by the server and sent with subsequent requests
      setUser(user)

      return { success: true }
    } catch (err) {
      const message = err.response?.data?.error || err.response?.data?.message || 'Registration failed'
      setError(message)
      return { success: false, error: message }
    }
  }

  const logout = async () => {
    try {
      // Call logout endpoint to clear httpOnly cookies
      await axios.post('/auth/logout/')
    } catch (err) {
      // 🔒 SECURITY: Only log errors in development to avoid exposing internals
      if (import.meta.env.DEV) {
        console.error('Logout request failed:', err)
      }
      // Continue with client-side logout even if server logout fails
    } finally {
      // 🔒 SECURITY: No localStorage to clear!
      // Cookies are cleared by the server's logout endpoint
      setUser(null)
    }
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
