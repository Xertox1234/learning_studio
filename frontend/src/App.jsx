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
import CoursesPage from './pages/CoursesPage'
import CourseDetailPage from './pages/CourseDetailPage'
import LessonPage from './pages/LessonPage'
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
import CodeMirrorDemoPage from './pages/CodeMirrorDemoPage'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'

function App() {
  return (
    <ErrorBoundary
      title="Application Error"
      message="Something went wrong with the Python Learning Studio application."
      showDetails={true}
    >
      <BrowserRouter>
        <ThemeProvider>
          <AuthProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              
              {/* Protected routes with Layout */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<HomePage />} />
                <Route path="forum" element={<ForumPage />} />
                <Route path="forum/:forumSlug/:forumId" element={<ForumDetailPage />} />
                <Route path="forum/topics/:forumSlug/:forumId/:topicSlug/:topicId" element={<ForumTopicPage />} />
                <Route path="forum/topics/create" element={<TopicCreatePage />} />
                <Route path="forum/topics/:forumSlug/:forumId/:topicSlug/:topicId/reply" element={<TopicReplyPage />} />
                <Route path="courses" element={<CoursesPage />} />
                <Route path="courses/:courseId" element={<CourseDetailPage />} />
                <Route path="courses/:courseId/lessons/:lessonId" element={<LessonPage />} />
                <Route path="learning/courses" element={<WagtailCoursesPage />} />
                <Route path="learning/courses/:courseSlug" element={<WagtailCourseDetailPage />} />
                <Route path="blog" element={<BlogPage />} />
                <Route path="blog/:slug" element={<BlogPostPage />} />
                <Route path="exercises/:exerciseId" element={<ExercisePage />} />
                <Route path="playground" element={<WagtailPlaygroundPage />} />
                <Route path="playground-legacy" element={<CodePlaygroundPage />} />
                <Route path="exercise-demo" element={<ExercisePage />} />
                <Route path="codemirror-demo" element={<CodeMirrorDemoPage />} />
                <Route path="dashboard" element={<DashboardPage />} />
              </Route>
            </Routes>
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App