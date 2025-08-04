import React from 'react'
import ErrorBoundary from '../common/ErrorBoundary'
import { Bot, Zap, RefreshCw, MessageSquare } from 'lucide-react'

/**
 * Specialized error boundary for AI components
 * Handles AI assistant and chat-specific errors with graceful degradation
 */
const AIErrorBoundary = ({ children }) => {
  const fallback = (error, errorInfo, retry) => (
    <div className="min-h-[250px] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          {/* AI Assistant Icon and Title */}
          <div className="flex items-center mb-4">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/40">
                <Bot className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-red-800 dark:text-red-200">
                AI Assistant Error
              </h3>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                The AI assistant encountered an error and is temporarily unavailable.
              </p>
            </div>
          </div>

          {/* AI Service Status */}
          <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded">
            <div className="flex items-center">
              <Zap className="h-4 w-4 text-amber-600 dark:text-amber-400 mr-2" />
              <div>
                <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200">
                  Alternative Options
                </h4>
                <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                  You can still access all learning content and exercises while we restore AI features.
                </p>
              </div>
            </div>
          </div>

          {/* Recovery Actions */}
          <div className="flex flex-col gap-2">
            <button
              onClick={retry}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry AI Assistant
            </button>
            
            <button
              onClick={() => window.location.href = '/community'}
              className="inline-flex items-center justify-center px-4 py-2 border border-red-300 dark:border-red-600 text-sm font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Ask Community Instead
            </button>
          </div>

          {/* Fallback Options */}
          <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-800">
            <p className="text-xs text-red-600 dark:text-red-400">
              Need help right now? Check our 
              <a href="/docs" className="ml-1 underline hover:text-red-500">
                documentation
              </a> or visit the 
              <a href="/community" className="ml-1 underline hover:text-red-500">
                community forum
              </a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <ErrorBoundary
      fallback={fallback}
      title="AI Assistant Error"
      message="The AI assistant is temporarily unavailable due to an error."
      showDetails={false}
    >
      {children}
    </ErrorBoundary>
  )
}

export default AIErrorBoundary