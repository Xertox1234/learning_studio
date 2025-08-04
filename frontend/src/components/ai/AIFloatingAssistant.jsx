import React, { useState, useEffect, useRef } from 'react'
import { MessageCircle, X, Send, Loader, Bot, User, Minimize2, Maximize2 } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import DOMPurify from 'dompurify'

const AIFloatingAssistant = ({
  exerciseContext = null,
  studentCode = '',
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [quickActions, setQuickActions] = useState([])
  
  const { theme } = useTheme()
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Initialize with welcome message and context-aware quick actions
  useEffect(() => {
    if (exerciseContext && messages.length === 0) {
      const welcomeMessage = {
        id: Date.now(),
        type: 'ai',
        content: `Hi! I'm your AI programming assistant. I can help you with "${exerciseContext.title}". What would you like to know?`,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
      
      // Set context-aware quick actions
      setQuickActions([
        {
          id: 'explain_concept',
          label: 'Explain this concept',
          icon: '💡',
          prompt: 'Can you explain the main programming concept in this exercise?'
        },
        {
          id: 'real_world',
          label: 'Real-world usage',
          icon: '🌍', 
          prompt: 'How is this concept used in real-world programming?'
        },
        {
          id: 'debug_help',
          label: 'Help me debug',
          icon: '🐛',
          prompt: 'I\'m having trouble with my code. Can you help me debug it?'
        },
        {
          id: 'similar_examples',
          label: 'Show similar examples',
          icon: '📝',
          prompt: 'Can you show me similar examples of this concept?'
        },
        {
          id: 'best_practices',
          label: 'Best practices',
          icon: '⭐',
          prompt: 'What are the best practices for this concept?'
        },
        {
          id: 'career_relevance',
          label: 'Career relevance',
          icon: '💼',
          prompt: 'What jobs or careers use this programming concept?'
        }
      ])
    }
  }, [exerciseContext, messages.length])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Handle sending messages to AI
  const sendMessage = async (messageContent) => {
    if (!messageContent.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsLoading(true)

    try {
      // Call AI assistance API
      const response = await fetch('/api/v1/ai-assistance/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          assistance_type: 'contextual_chat',
          content: messageContent,
          context: JSON.stringify({
            exercise: exerciseContext,
            student_code: studentCode,
            conversation_history: messages.slice(-5) // Last 5 messages for context
          }),
          difficulty_level: exerciseContext?.difficulty || 'beginner'
        })
      })

      const data = await response.json()
      
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: data.response || 'I apologize, but I encountered an error. Please try again.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('AI chat error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: 'I\'m experiencing some technical difficulties. Please try again in a moment.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputSubmit = (e) => {
    e.preventDefault()
    sendMessage(inputMessage)
  }

  const handleQuickAction = (action) => {
    sendMessage(action.prompt)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleInputSubmit(e)
    }
  }

  const toggleAssistant = () => {
    setIsOpen(!isOpen)
    if (!isOpen) {
      // Focus input when opening
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <>
      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={toggleAssistant}
          className={`fixed bottom-6 right-6 w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-110 transition-all duration-300 z-50 flex items-center justify-center ${className}`}
        >
          <div className="relative">
            <Bot className="w-7 h-7" />
            {/* Pulse animation */}
            <div className="absolute inset-0 rounded-full bg-blue-400 opacity-30 animate-ping"></div>
          </div>
        </button>
      )}

      {/* Chat Interface */}
      {isOpen && (
        <div className={`fixed bottom-6 right-6 w-96 max-w-[calc(100vw-3rem)] h-[600px] max-h-[calc(100vh-6rem)] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex flex-col z-50 ${isMinimized ? 'h-16' : ''} transition-all duration-300`}>
          
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 rounded-t-2xl bg-gradient-to-r from-blue-500 to-purple-600 text-white">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Bot className="w-6 h-6" />
                <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
              </div>
              <div>
                <h3 className="font-semibold text-sm">AI Assistant</h3>
                <p className="text-xs opacity-90">Ready to help</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="p-1 hover:bg-white/20 rounded-full transition-colors"
              >
                {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 hover:bg-white/20 rounded-full transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {!isMinimized && (
            <>
              {/* Quick Actions */}
              {quickActions.length > 0 && messages.length <= 1 && (
                <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">Quick actions:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {quickActions.slice(0, 4).map((action) => (
                      <button
                        key={action.id}
                        onClick={() => handleQuickAction(action)}
                        className="p-2 text-xs bg-gray-100 dark:bg-gray-800 hover:bg-blue-100 dark:hover:bg-blue-900 rounded-lg transition-colors text-left flex items-center space-x-2"
                      >
                        <span>{action.icon}</span>
                        <span className="truncate">{action.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div className={`max-w-[80%] ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                      <div className={`flex items-start space-x-2 ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${message.type === 'user' ? 'bg-blue-500' : 'bg-gradient-to-r from-purple-500 to-blue-500'}`}>
                          {message.type === 'user' ? (
                            <User className="w-4 h-4 text-white" />
                          ) : (
                            <Bot className="w-4 h-4 text-white" />
                          )}
                        </div>
                        <div className={`rounded-2xl px-4 py-2 ${message.type === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'}`}>
                          <p 
                            className="text-sm whitespace-pre-wrap"
                            dangerouslySetInnerHTML={{ 
                              __html: DOMPurify.sanitize(message.content, {
                                ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'code', 'pre', 'br'],
                                ALLOWED_ATTR: []
                              })
                            }}
                          />
                          <p className="text-xs opacity-70 mt-1">{formatTime(message.timestamp)}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="flex items-start space-x-2">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-2">
                        <div className="flex items-center space-x-2 text-gray-600 dark:text-gray-400">
                          <Loader className="w-4 h-4 animate-spin" />
                          <span className="text-sm">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <form onSubmit={handleInputSubmit} className="flex space-x-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me anything about programming..."
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white text-sm"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={!inputMessage.trim() || isLoading}
                    className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full flex items-center justify-center hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </>
          )}
        </div>
      )}
    </>
  )
}

export default AIFloatingAssistant