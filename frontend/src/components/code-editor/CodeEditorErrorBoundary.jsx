import React from 'react'
import ErrorBoundary from '../common/ErrorBoundary'
import { Code, AlertTriangle, RefreshCw } from 'lucide-react'

/**
 * Specialized error boundary for code editor components
 * Handles CodeMirror-specific errors and provides code editor recovery options
 */
const CodeEditorErrorBoundary = ({ children }) => {
  const fallback = (error, errorInfo, retry) => (
    <div className="min-h-[300px] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
          {/* Code Editor Icon and Title */}
          <div className="flex items-center mb-4">
            <div className="flex-shrink-0">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-red-100 dark:bg-red-900/40">
                <Code className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-red-800 dark:text-red-200">
                Code Editor Error
              </h3>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                The code editor encountered an unexpected error and needs to be reloaded.
              </p>
            </div>
          </div>

          {/* Common CodeMirror Issues */}
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/40 rounded border">
            <h4 className="text-sm font-medium text-red-800 dark:text-red-200 mb-2">
              Common causes:
            </h4>
            <ul className="text-xs text-red-700 dark:text-red-300 space-y-1">
              <li>• Invalid code template or widget configuration</li>
              <li>• Theme switching while editor is active</li>
              <li>• Browser extension interference</li>
              <li>• Memory constraints with large code files</li>
            </ul>
          </div>

          {/* Recovery Actions */}
          <div className="flex flex-col gap-2">
            <button
              onClick={retry}
              className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset Code Editor
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center justify-center px-4 py-2 border border-red-300 dark:border-red-600 text-sm font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
            >
              Reload Page
            </button>
          </div>

          {/* Help Text */}
          <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-800">
            <p className="text-xs text-red-600 dark:text-red-400">
              Your progress is automatically saved. Reloading will restore your work.
            </p>
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <ErrorBoundary
      fallback={fallback}
      title="Code Editor Error"
      message="The code editor encountered an error and needs to be reset."
      showDetails={true}
    >
      {children}
    </ErrorBoundary>
  )
}

export default CodeEditorErrorBoundary