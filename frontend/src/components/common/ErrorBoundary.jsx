import React from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      eventId: null
    }
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log the error for debugging and monitoring
    console.error('Error caught by boundary:', error, errorInfo)
    
    this.setState({
      error: error,
      errorInfo: errorInfo,
      eventId: this.generateEventId()
    })
    
    // Report to error monitoring service (e.g., Sentry)
    if (process.env.NODE_ENV === 'production') {
      this.reportError(error, errorInfo)
    }
  }

  generateEventId = () => {
    return `err_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  reportError = (error, errorInfo) => {
    // Integration with error reporting service
    // Example: Sentry, LogRocket, or custom endpoint
    try {
      fetch('/api/v1/error-report/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            name: error.name,
            message: error.message,
            stack: error.stack,
          },
          errorInfo: errorInfo,
          eventId: this.state.eventId,
          userAgent: navigator.userAgent,
          url: window.location.href,
          timestamp: new Date().toISOString(),
        }),
      })
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError)
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, eventId } = this.state
      const { fallback, showDetails = false, title, message } = this.props

      // If a custom fallback is provided, use it
      if (fallback) {
        return fallback(error, errorInfo, this.handleRetry)
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <div className="max-w-2xl w-full">
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
              {/* Error Icon and Title */}
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <AlertTriangle className="h-8 w-8 text-red-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-lg font-medium text-red-800 dark:text-red-200">
                    {title || 'Something went wrong'}
                  </h3>
                  <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                    {message || 'An unexpected error occurred while loading this content.'}
                  </p>
                </div>
              </div>

              {/* Error Details (Development Mode) */}
              {process.env.NODE_ENV === 'development' && showDetails && (
                <div className="mb-6">
                  <details className="group">
                    <summary className="cursor-pointer text-sm font-medium text-red-800 dark:text-red-200 flex items-center gap-2 hover:text-red-900 dark:hover:text-red-100">
                      <Bug className="h-4 w-4" />
                      Error Details (Development)
                      <span className="text-xs bg-red-200 dark:bg-red-800 px-2 py-1 rounded">
                        {eventId}
                      </span>
                    </summary>
                    <div className="mt-3 text-xs bg-red-100 dark:bg-red-900/40 p-3 rounded border">
                      <div className="mb-2">
                        <strong>Error:</strong> {error?.toString()}
                      </div>
                      {error?.stack && (
                        <div className="mb-2">
                          <strong>Stack Trace:</strong>
                          <pre className="mt-1 text-xs overflow-auto max-h-40 whitespace-pre-wrap">
                            {error.stack}
                          </pre>
                        </div>
                      )}
                      {errorInfo?.componentStack && (
                        <div>
                          <strong>Component Stack:</strong>
                          <pre className="mt-1 text-xs overflow-auto max-h-32 whitespace-pre-wrap">
                            {errorInfo.componentStack}
                          </pre>
                        </div>
                      )}
                    </div>
                  </details>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={this.handleRetry}
                  className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </button>
                
                <button
                  onClick={this.handleReload}
                  className="inline-flex items-center justify-center px-4 py-2 border border-red-300 dark:border-red-600 text-sm font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reload Page
                </button>
                
                <button
                  onClick={this.handleGoHome}
                  className="inline-flex items-center justify-center px-4 py-2 border border-red-300 dark:border-red-600 text-sm font-medium rounded-md text-red-700 dark:text-red-200 bg-white dark:bg-red-900/20 hover:bg-red-50 dark:hover:bg-red-900/40 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors"
                >
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </button>
              </div>

              {/* Help Text */}
              <div className="mt-4 pt-4 border-t border-red-200 dark:border-red-800">
                <p className="text-xs text-red-600 dark:text-red-400">
                  If this problem persists, please contact support
                  {eventId && (
                    <span className="ml-1">
                      with error ID: <code className="bg-red-200 dark:bg-red-800 px-1 rounded">{eventId}</code>
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary