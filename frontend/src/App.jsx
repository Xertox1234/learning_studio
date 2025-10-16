import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Layout from './components/common/Layout'
import ProtectedRoute from './components/auth/ProtectedRoute'
import ErrorBoundary from './components/common/ErrorBoundary'
import HomePage from './pages/HomePage'
import ForumPage from './pages/ForumPage'
import ForumDetailPage from './pages/ForumDetailPage'
import ForumTopicPage from './pages/ForumTopicPage'
import TopicCreatePage from './pages/TopicCreatePage'
import TopicReplyPage from './pages/TopicReplyPage'
import ForumUserProfilePage from './pages/ForumUserProfilePage'
import ForumSearchPage from './pages/ForumSearchPage'
import ModerationQueuePage from './pages/ModerationQueuePage'
import ModerationAnalyticsPage from './pages/ModerationAnalyticsPage'
import ExercisePage from './pages/ExercisePage'
import CodePlaygroundPage from './pages/CodePlaygroundPage'
import WagtailPlaygroundPage from './pages/WagtailPlaygroundPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import BlogPage from './pages/BlogPage'
import BlogPostPage from './pages/BlogPostPage'
import WagtailCoursesPage from './pages/WagtailCoursesPage'
import WagtailCourseDetailPage from './pages/WagtailCourseDetailPage'
import WagtailLessonPage from './pages/WagtailLessonPage'
import WagtailExerciseListPage from './pages/WagtailExerciseListPage'
import WagtailExercisePage from './pages/WagtailExercisePage'
import StepBasedExercisePage from './pages/StepBasedExercisePage'
import CodeMirrorDemoPage from './pages/CodeMirrorDemoPage'
import MinimalInteractiveDemo from './pages/MinimalInteractiveDemo'
import IntegratedContentDemo from './pages/IntegratedContentDemo'
import TestPage from './pages/TestPage'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes default
      gcTime: 10 * 60 * 1000, // 10 minutes garbage collection
    },
  },
})

function App() {
  return (
    <ErrorBoundary
      title="Application Error"
      message="Something went wrong with the Python Learning Studio application."
      showDetails={true}
    >
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider>
            <AuthProvider>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: '#363636',
                  color: '#fff',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#10b981',
                    secondary: '#fff',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                },
              }}
            />
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/test" element={<TestPage />} />
              <Route path="/integrated-content-demo" element={<IntegratedContentDemo />} />
              
              {/* Protected routes with Layout */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<HomePage />} />
                <Route path="forum" element={<ForumPage />} />
                <Route path="forum/search" element={<ForumSearchPage />} />
                <Route path="forum/users/:userId" element={<ForumUserProfilePage />} />
                <Route path="forum/moderation/queue" element={<ModerationQueuePage />} />
                <Route path="forum/moderation/analytics" element={<ModerationAnalyticsPage />} />
                <Route path="forum/:forumSlug/:forumId" element={<ForumDetailPage />} />
                <Route path="forum/topics/:forumSlug/:forumId/:topicSlug/:topicId" element={<ForumTopicPage />} />
                <Route path="forum/topics/create" element={<TopicCreatePage />} />
                <Route path="forum/topics/:forumSlug/:forumId/:topicSlug/:topicId/reply" element={<TopicReplyPage />} />
                <Route path="courses" element={<WagtailCoursesPage />} />
                <Route path="courses/:courseSlug" element={<WagtailCourseDetailPage />} />
                <Route path="courses/:courseSlug/lessons/:lessonSlug" element={<WagtailLessonPage />} />
                <Route path="blog" element={<BlogPage />} />
                <Route path="blog/:slug" element={<BlogPostPage />} />
                <Route path="exercises" element={<WagtailExerciseListPage />} />
                <Route path="exercises/:exerciseSlug" element={<WagtailExercisePage />} />
                <Route path="step-exercises/:exerciseSlug" element={<StepBasedExercisePage />} />
                <Route path="exercise-demo/:exerciseId" element={<ExercisePage />} />
                <Route path="playground" element={<WagtailPlaygroundPage />} />
                <Route path="playground-legacy" element={<CodePlaygroundPage />} />
                <Route path="exercise-demo" element={<ExercisePage />} />
                <Route path="codemirror-demo" element={<CodeMirrorDemoPage />} />
                <Route path="minimal-code-demo" element={<MinimalInteractiveDemo />} />
                <Route path="integrated-content-demo" element={<IntegratedContentDemo />} />
                <Route path="dashboard" element={<DashboardPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </ThemeProvider>
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App