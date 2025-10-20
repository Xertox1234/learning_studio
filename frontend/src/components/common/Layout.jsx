import React, { useRef } from 'react'
import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'
import Footer from './Footer'
import AuthDebug from './AuthDebug'

export default function Layout() {
  const mainContentRef = useRef(null)

  const handleSkipToContent = (e) => {
    e.preventDefault()
    mainContentRef.current?.focus()
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Skip to main content link for keyboard users (WCAG 2.4.1) */}
      <a
        href="#main-content"
        className="skip-link"
        onClick={handleSkipToContent}
      >
        Skip to main content
      </a>

      <Navbar />

      <main
        id="main-content"
        ref={mainContentRef}
        tabIndex={-1}
        className="flex-1 outline-none"
      >
        <Outlet />
      </main>

      <Footer />
      <AuthDebug />
    </div>
  )
}