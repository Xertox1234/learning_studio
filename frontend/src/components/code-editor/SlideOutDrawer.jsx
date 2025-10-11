import React, { useState, useEffect, useRef } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

/**
 * SlideOutDrawer - Smooth sliding drawer component for code editor outputs
 * Features smooth animations, theme awareness, and proper accessibility
 */
const SlideOutDrawer = ({
  isOpen = false,
  onToggle = () => {},
  title = "Output",
  children,
  className = "",
  headerClassName = "",
  contentClassName = "",
  animationDuration = 300
}) => {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const contentRef = useRef(null)
  const [maxHeight, setMaxHeight] = useState(0)
  const [isAnimating, setIsAnimating] = useState(false)

  // Calculate content height for smooth animation
  useEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.scrollHeight
      setMaxHeight(height)
    }
  }, [children, isOpen])

  // Handle animation states
  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true)
      const timer = setTimeout(() => {
        setIsAnimating(false)
      }, animationDuration)
      return () => clearTimeout(timer)
    } else {
      setIsAnimating(true)
      const timer = setTimeout(() => {
        setIsAnimating(false)
      }, animationDuration - 50) // Slightly shorter for close animation
      return () => clearTimeout(timer)
    }
  }, [isOpen, animationDuration])

  return (
    <div className={`slide-out-drawer ${className}`}>
      {/* Drawer Header */}
      <button
        onClick={onToggle}
        className={`w-full flex items-center justify-between px-4 py-3 text-sm font-medium transition-colors duration-200 rounded-t-lg ${
          isDark 
            ? 'bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-600' 
            : 'bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-300'
        } ${headerClassName}`}
        aria-expanded={isOpen}
        aria-controls="drawer-content"
      >
        <span>{title}</span>
        <div className="flex items-center space-x-2">
          {isAnimating && (
            <div className={`w-2 h-2 rounded-full animate-pulse ${
              isDark ? 'bg-blue-400' : 'bg-blue-600'
            }`} />
          )}
          {isOpen ? (
            <ChevronDown className={`h-4 w-4 transition-transform duration-${animationDuration} transform`} />
          ) : (
            <ChevronRight className={`h-4 w-4 transition-transform duration-${animationDuration} transform`} />
          )}
        </div>
      </button>
      
      {/* Drawer Content */}
      <div
        className={`overflow-hidden transition-all duration-${animationDuration} ease-out ${
          isDark 
            ? 'border-l border-r border-b border-gray-600 bg-gray-800' 
            : 'border-l border-r border-b border-gray-300 bg-gray-50'
        }`}
        style={{
          maxHeight: isOpen ? `${maxHeight}px` : '0px',
          opacity: isOpen ? 1 : 0
        }}
        id="drawer-content"
        aria-hidden={!isOpen}
      >
        <div
          ref={contentRef}
          className={`px-4 py-3 transition-opacity duration-200 ${
            isOpen ? 'opacity-100' : 'opacity-0'
          } ${contentClassName}`}
          style={{
            transitionDelay: isOpen ? `${animationDuration * 0.3}ms` : '0ms'
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

export default SlideOutDrawer