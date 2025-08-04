import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext-simple'
import Layout from './components/common/Layout'
import HomePage from './pages/HomePage'

// Simple test components for other pages
function TestPage({ name }) {
  return (
    <div className="container-custom py-8">
      <h1 className="text-3xl font-bold mb-4">{name} Page</h1>
      <p className="text-gray-600 dark:text-gray-400">This is the {name.toLowerCase()} page - coming soon!</p>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="forum" element={<TestPage name="Forum" />} />
            <Route path="courses" element={<TestPage name="Courses" />} />
            <Route path="playground" element={<TestPage name="Playground" />} />
            <Route path="dashboard" element={<TestPage name="Dashboard" />} />
          </Route>
          <Route path="/login" element={<TestPage name="Login" />} />
          <Route path="/register" element={<TestPage name="Register" />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App