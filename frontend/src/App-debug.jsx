import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', backgroundColor: '#fee', border: '1px solid #f00' }}>
          <h2>React Error Caught!</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            <summary>Error Details</summary>
            <strong>Error:</strong> {this.state.error && this.state.error.toString()}
            <br />
            <strong>Stack:</strong> {this.state.errorInfo.componentStack}
          </details>
        </div>
      )
    }

    return this.props.children
  }
}

function App() {
  console.log('App component rendering...')
  
  React.useEffect(() => {
    console.log('App component mounted successfully')
    
    // Check for common issues
    console.log('Window object:', typeof window)
    console.log('Document object:', typeof document)
    console.log('LocalStorage available:', typeof localStorage)
    
    return () => console.log('App component unmounting')
  }, [])

  return (
    <ErrorBoundary>
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
        <h1 style={{ color: '#4CAF50' }}>✅ React App Debug Mode</h1>
        <p>Current time: {new Date().toLocaleString()}</p>
        <p>If you can see this, React is working!</p>
        
        <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
          <h3>System Check:</h3>
          <ul>
            <li>React: ✅ Working</li>
            <li>JavaScript: ✅ Working</li>
            <li>DOM: ✅ Working</li>
          </ul>
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <h3>Debug Info:</h3>
          <pre style={{ backgroundColor: '#000', color: '#0f0', padding: '10px', fontSize: '12px' }}>
            User Agent: {navigator.userAgent}
            {'\n'}Location: {window.location.href}
            {'\n'}Timestamp: {Date.now()}
          </pre>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default App