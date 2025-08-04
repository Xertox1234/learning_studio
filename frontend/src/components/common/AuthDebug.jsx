import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

export default function AuthDebug() {
  const { user, login } = useAuth();
  const [showDebug, setShowDebug] = useState(false);
  const [testResult, setTestResult] = useState('');

  const testAuth = async () => {
    setTestResult('Testing authentication...\n');
    
    // Check localStorage
    const token = localStorage.getItem('authToken');
    setTestResult(prev => prev + `\n1. Token in localStorage: ${token ? 'Yes (' + token.substring(0, 20) + '...)' : 'No'}\n`);
    
    // Check if user is loaded
    setTestResult(prev => prev + `\n2. User in context: ${user ? 'Yes (' + user.email + ')' : 'No'}\n`);
    
    // Test API call
    try {
      const response = await fetch('/api/v1/auth/status/', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      
      setTestResult(prev => prev + `\n3. API /auth/status/ response: ${response.status}\n`);
      
      if (response.ok) {
        const data = await response.json();
        setTestResult(prev => prev + `   Response data: ${JSON.stringify(data, null, 2)}\n`);
      } else {
        const errorText = await response.text();
        setTestResult(prev => prev + `   Error: ${errorText}\n`);
      }
    } catch (error) {
      setTestResult(prev => prev + `\n3. API call error: ${error.message}\n`);
    }
    
    // Test forum API
    try {
      const response = await fetch('/api/v1/forums/', {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });
      
      setTestResult(prev => prev + `\n4. Forum API response: ${response.status}\n`);
    } catch (error) {
      setTestResult(prev => prev + `\n4. Forum API error: ${error.message}\n`);
    }
  };

  const quickLogin = async () => {
    setTestResult('Attempting login...\n');
    const result = await login('test@pythonlearning.studio', 'testpass123');
    if (result.success) {
      setTestResult(prev => prev + 'Login successful! Refresh the page.\n');
    } else {
      setTestResult(prev => prev + `Login failed: ${result.error}\n`);
    }
  };

  if (!showDebug) {
    return (
      <button 
        onClick={() => setShowDebug(true)}
        className="fixed bottom-4 right-4 bg-purple-600 text-white px-3 py-1 rounded text-sm hover:bg-purple-700 z-50"
      >
        Debug Auth
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg p-4 max-w-md z-50">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold text-sm">Auth Debug</h3>
        <button 
          onClick={() => setShowDebug(false)}
          className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-2">
        <button 
          onClick={testAuth}
          className="w-full bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
        >
          Test Auth Status
        </button>
        
        <button 
          onClick={quickLogin}
          className="w-full bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
        >
          Quick Login (Demo User)
        </button>
        
        {testResult && (
          <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-auto max-h-64">
            {testResult}
          </pre>
        )}
      </div>
    </div>
  );
}