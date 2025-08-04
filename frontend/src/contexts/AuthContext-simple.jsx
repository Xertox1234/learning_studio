import { createContext, useContext, useState } from 'react'

const AuthContext = createContext()

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const login = async (email, password) => {
    // Mock login for testing
    setUser({ username: 'testuser', email })
    return { success: true }
  }

  const register = async (userData) => {
    // Mock register for testing
    setUser({ username: userData.username, email: userData.email })
    return { success: true }
  }

  const logout = () => {
    setUser(null)
  }

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    checkAuth: () => {},
    isAuthenticated: !!user,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}