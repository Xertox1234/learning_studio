import React from 'react'
import { getAuthToken, isAuthenticated } from '../../utils/api'

const AuthDebug = () => {
  const token = getAuthToken()
  const authenticated = isAuthenticated()
  
  return (
    <div className="fixed top-4 left-4 bg-gray-900 text-white p-3 rounded-lg text-xs font-mono z-50 max-w-md">
      <h4 className="font-bold mb-2">🔐 Auth Debug</h4>
      <div className="space-y-1">
        <div>Authenticated: <span className={authenticated ? 'text-green-400' : 'text-red-400'}>{authenticated ? 'YES' : 'NO'}</span></div>
        <div>Token exists: <span className={token ? 'text-green-400' : 'text-red-400'}>{token ? 'YES' : 'NO'}</span></div>
        {token && (
          <div>Token preview: {token.substring(0, 30)}...</div>
        )}
        <button 
          onClick={() => {
            localStorage.setItem('authToken', 'demo-token-12345')
            window.location.reload()
          }}
          className="mt-2 px-2 py-1 bg-blue-600 rounded text-xs hover:bg-blue-700"
        >
          Set Demo Token
        </button>
        <button 
          onClick={() => {
            localStorage.removeItem('authToken')
            window.location.reload()
          }}
          className="ml-2 px-2 py-1 bg-red-600 rounded text-xs hover:bg-red-700"
        >
          Clear Token
        </button>
      </div>
    </div>
  )
}

export default AuthDebug