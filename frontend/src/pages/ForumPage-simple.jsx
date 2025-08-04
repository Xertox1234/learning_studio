export default function ForumPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="container-custom">
        <h1 className="text-4xl font-bold mb-4">Community Forum</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 mb-8">
          Connect, learn, and share with Python developers worldwide
        </p>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-semibold mb-4">Forum Categories</h2>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="text-xl font-medium mb-2">🐍 Python Basics</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get started with Python programming fundamentals
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="text-xl font-medium mb-2">🌐 Web Development</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Django, Flask, FastAPI and web development topics
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <h3 className="text-xl font-medium mb-2">📊 Data Science</h3>
              <p className="text-gray-600 dark:text-gray-400">
                Machine learning, data analysis, and visualization
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}