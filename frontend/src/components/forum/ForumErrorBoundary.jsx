import React from 'react'
import ErrorBoundary from '../common/ErrorBoundary'
import { MessageSquare, Users, RefreshCw, Home } from 'lucide-react'

/**
 * Specialized error boundary for forum components
 * Handles forum-specific errors with community-focused recovery options
 */
const ForumErrorBoundary = ({ children }) => {
  const fallback = (error, errorInfo, retry) => (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          {/* Forum Icon and Title */}
          <div className="flex items-center mb-4">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/40">
                <MessageSquare className="h-7 w-7 text-red-600 dark:text-red-400" />
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-red-800 dark:text-red-200">
                Forum Loading Error
              </h3>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                We're having trouble loading the forum content right now.
              </p>
            </div>
          </div>

          {/* Forum-specific Error Context */}
          <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/40 rounded border">
            <h4 className="text-sm font-medium text-red-800 dark:text-red-200 mb-2 flex items-center">
              <Users className="h-4 w-4 mr-2" />
              What this might affect:
            </h4>
            <ul className="text-xs text-red-700 dark:text-red-300 space-y-1">
              <li>• Forum posts and discussions</li>
              <li>• User trust levels and badges</li>
              <li>• Real-time notifications</li>
              <li>• Community features</li>
            </ul>
          </div>

          {/* Recovery Actions */}
          <div className="flex flex-col gap-3">
            <button
              onClick={retry}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reload Forum
            </button>
            
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => window.location.href = '/community'}
                className="inline-flex items-center justify-center px-3 py-2 border border-red-300 dark:border-red-600 text-xs font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
              >
                <Users className="h-3 w-3 mr-1" />
                Community
              </button>
              
              <button
                onClick={() => window.location.href = '/'}
                className="inline-flex items-center justify-center px-3 py-2 border border-red-300 dark:border-red-600 text-xs font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
              >
                <Home className="h-3 w-3 mr-1" />
                Home
              </button>
            </div>
          </div>

          {/* Community Support */}
          <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-800">
            <p className="text-xs text-red-600 dark:text-red-400">
              Having persistent issues? Ask for help in our 
              <a href="/community/support" className="ml-1 underline hover:text-red-500">
                support forum
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <ErrorBoundary
      fallback={fallback}
      title="Forum Error"
      message="We're having trouble loading the forum content."
      showDetails={false}
    >
      {children}
    </ErrorBoundary>
  )
}

export default ForumErrorBoundary