import React, { useState } from 'react'
import { apiRequest } from '../../utils/api'

const SimpleLogin = () => {
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const response = await apiRequest('/api/v1/auth/login/', {
        method: 'POST',
        body: JSON.stringify(credentials)
      })

      if (response.ok) {
        const data = await response.json()
        if (data.token) {
          localStorage.setItem('authToken', data.token)
          setMessage('✅ Login successful! Token saved.')
          // Refresh the page to update auth state
          setTimeout(() => window.location.reload(), 1000)
        }
      } else {
        const errorData = await response.json()
        setMessage(`❌ Login failed: ${errorData.error || 'Unknown error'}`)
      }
    } catch (error) {
      setMessage(`❌ Network error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleQuickDemo = () => {
    setCredentials({ email: 'test@pythonlearning.studio', password: 'testpass123' })
  }

  return (
    <div className="fixed top-20 left-4 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 p-4 rounded-lg shadow-lg text-sm font-mono z-40 max-w-sm">
      <h4 className="font-bold mb-3 text-gray-900 dark:text-gray-100">🔐 Quick Login</h4>
      
      <form onSubmit={handleLogin} className="space-y-3">
        <div>
          <input
            type="email"
            placeholder="Email"
            value={credentials.email}
            onChange={(e) => setCredentials({...credentials, email: e.target.value})}
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            required
          />
        </div>
        
        <div>
          <input
            type="password"
            placeholder="Password"
            value={credentials.password}
            onChange={(e) => setCredentials({...credentials, password: e.target.value})}
            className="w-full px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            required
          />
        </div>
        
        <div className="flex space-x-2">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
          
          <button
            type="button"
            onClick={handleQuickDemo}
            className="px-3 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700"
          >
            Demo
          </button>
        </div>
      </form>
      
      {message && (
        <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs text-gray-800 dark:text-gray-200">
          {message}
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-600 dark:text-gray-400">
        <p>For testing: Use any email/password or click Demo to populate fields.</p>
        <p>Real auth would check against Django users.</p>
      </div>
    </div>
  )
}

export default SimpleLogin