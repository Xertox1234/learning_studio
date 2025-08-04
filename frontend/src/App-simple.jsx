import { Routes, Route } from 'react-router-dom'

function SimpleHome() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
        Python Learning Studio - React Test
      </h1>
      <p className="text-lg text-gray-600 dark:text-gray-400">
        React app is working! 🎉
      </p>
      <div className="mt-8 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <p>If you can see this, the React app is loading correctly.</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<SimpleHome />} />
      <Route path="*" element={<SimpleHome />} />
    </Routes>
  )
}

export default App