import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { 
  ChevronLeft, ChevronRight, Clock, BookOpen, CheckCircle,
  ArrowLeft, Code, FileText, Video, AlertCircle, Info,
  User, Calendar, Target, PlayCircle, Award
} from 'lucide-react'
import { api } from '../utils/api'
import { useAuth } from '../contexts/AuthContext'
import { ReadOnlyCodeBlock, RunButtonCodeEditor, MinimalFillBlankEditor, MinimalMultipleChoiceBlanks } from '../components/code-editor'
import ConfettiCelebration from '../components/common/ConfettiCelebration'
import clsx from 'clsx'

// Content Block Components
function TextBlock({ content }) {
  return (
    <div 
      className="prose prose-lg dark:prose-invert max-w-none mb-6"
      dangerouslySetInnerHTML={{ __html: content }}
    />
  )
}

function HeadingBlock({ content }) {
  return (
    <h2 className="text-2xl font-bold mb-4 mt-8">{content}</h2>
  )
}

function CodeExampleBlock({ content }) {
  const { title, language, code, explanation } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      {title && (
        <div className="flex items-center space-x-2 mb-4">
          <Code className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div className="mb-4">
        <ReadOnlyCodeBlock
          code={code}
          language={language}
          showLineNumbers={true}
          theme="light"
        />
      </div>
      
      {explanation && (
        <div 
          className="prose dark:prose-invert text-sm"
          dangerouslySetInnerHTML={{ __html: explanation }}
        />
      )}
    </div>
  )
}

function VideoBlock({ content }) {
  const { title, video_url, description } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      {title && (
        <div className="flex items-center space-x-2 mb-4">
          <Video className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div className="aspect-video bg-muted rounded-lg flex items-center justify-center mb-4">
        <div className="text-center">
          <PlayCircle className="h-16 w-16 text-muted-foreground mx-auto mb-2" />
          <p className="text-muted-foreground">Video Player</p>
          <a 
            href={video_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-primary hover:underline text-sm mt-2 inline-block"
          >
            Watch Video →
          </a>
        </div>
      </div>
      
      {description && (
        <div 
          className="prose dark:prose-invert text-sm"
          dangerouslySetInnerHTML={{ __html: description }}
        />
      )}
    </div>
  )
}

function CalloutBlock({ content }) {
  const { type, title, text } = content
  
  const getCalloutStyles = (type) => {
    switch (type) {
      case 'warning':
        return 'border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20 text-yellow-800 dark:text-yellow-200'
      case 'error':
        return 'border-red-200 bg-red-50 dark:bg-red-950/20 text-red-800 dark:text-red-200'
      case 'success':
        return 'border-green-200 bg-green-50 dark:bg-green-950/20 text-green-800 dark:text-green-200'
      default:
        return 'border-blue-200 bg-blue-50 dark:bg-blue-950/20 text-blue-800 dark:text-blue-200'
    }
  }
  
  const getIcon = (type) => {
    switch (type) {
      case 'warning':
        return <AlertCircle className="h-5 w-5" />
      case 'error':
        return <AlertCircle className="h-5 w-5" />
      case 'success':
        return <CheckCircle className="h-5 w-5" />
      default:
        return <Info className="h-5 w-5" />
    }
  }
  
  return (
    <div className={clsx('border rounded-lg p-4 mb-6', getCalloutStyles(type))}>
      <div className="flex items-start space-x-3">
        {getIcon(type)}
        <div className="flex-1">
          {title && <h4 className="font-semibold mb-2">{title}</h4>}
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: text }}
          />
        </div>
      </div>
    </div>
  )
}

function RunnableCodeExampleBlock({ content }) {
  const { title, language, code, mock_output, ai_explanation } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      {title && (
        <div className="flex items-center space-x-2 mb-4">
          <PlayCircle className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div className="mb-4">
        <RunButtonCodeEditor
          code={code}
          language={language}
          title={title}
          mockOutput={mock_output}
          aiExplanation={ai_explanation}
          showLineNumbers={true}
        />
      </div>
    </div>
  )
}

function FillBlankCodeBlock({ content }) {
  const { title, template, solutions, alternative_solutions, ai_hints, language } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      {title && (
        <div className="flex items-center space-x-2 mb-4">
          <Target className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div className="mb-4">
        <MinimalFillBlankEditor
          template={template}
          solutions={solutions || {}}
          alternativeSolutions={alternative_solutions || {}}
          aiHints={ai_hints || {}}
          language={language || 'python'}
          showLineNumbers={true}
        />
      </div>
    </div>
  )
}

function MultipleChoiceCodeBlock({ content }) {
  const { title, template, choices, solutions, ai_explanations, language } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      {title && (
        <div className="flex items-center space-x-2 mb-4">
          <Award className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">{title}</h3>
        </div>
      )}
      
      <div className="mb-4">
        <MinimalMultipleChoiceBlanks
          template={template}
          choices={choices || {}}
          solutions={solutions || {}}
          aiExplanations={ai_explanations || {}}
          language={language || 'python'}
          showLineNumbers={true}
        />
      </div>
    </div>
  )
}

function InteractiveExerciseBlock({ content }) {
  const { title, instructions, starter_code, hints } = content
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      <div className="flex items-center space-x-2 mb-4">
        <Target className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">{title}</h3>
      </div>
      
      <div 
        className="prose dark:prose-invert mb-4"
        dangerouslySetInnerHTML={{ __html: instructions }}
      />
      
      {starter_code && (
        <div className="mb-4">
          <h4 className="font-medium mb-2">Starter Code:</h4>
          <ReadOnlyCodeBlock
            code={starter_code}
            language="python"
            showLineNumbers={true}
          />
        </div>
      )}
      
      <button className="btn-primary">
        Start Exercise
      </button>
      
      {hints && hints.length > 0 && (
        <div className="mt-4 pt-4 border-t">
          <details className="group">
            <summary className="cursor-pointer font-medium text-muted-foreground hover:text-foreground">
              View Hints ({hints.length})
            </summary>
            <div className="mt-3 space-y-2">
              {hints.map((hint, index) => (
                <div key={index} className="text-sm text-muted-foreground bg-muted p-3 rounded">
                  <strong>Hint {index + 1}:</strong> {hint}
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  )
}

function QuizBlock({ content, onQuizComplete = null }) {
  const { question, options, explanation, correct_answer } = content
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  
  const handleSubmit = () => {
    if (selectedAnswer !== null) {
      setShowExplanation(true)
      
      // Check if answer is correct and trigger confetti
      if (selectedAnswer === correct_answer) {
        setShowConfetti(true)
        if (onQuizComplete) {
          onQuizComplete(true) // Pass success status
        }
      } else if (onQuizComplete) {
        onQuizComplete(false) // Pass failure status
      }
    }
  }
  
  const handleConfettiComplete = () => {
    setShowConfetti(false)
  }
  
  return (
    <div className="bg-card border rounded-lg p-6 mb-6">
      <div className="flex items-center space-x-2 mb-4">
        <Award className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">Knowledge Check</h3>
      </div>
      
      <div className="mb-4">
        <h4 className="font-medium mb-3">{question}</h4>
        
        <div className="space-y-2">
          {options.map((option, index) => (
            <label key={index} className="flex items-center space-x-3 cursor-pointer">
              <input
                type="radio"
                name="quiz-option"
                value={index}
                checked={selectedAnswer === index}
                onChange={(e) => setSelectedAnswer(parseInt(e.target.value))}
                className="form-radio"
                disabled={showExplanation}
              />
              <span>{option}</span>
            </label>
          ))}
        </div>
      </div>
      
      {!showExplanation ? (
        <button 
          onClick={handleSubmit}
          disabled={selectedAnswer === null}
          className="btn-primary disabled:opacity-50"
        >
          Submit Answer
        </button>
      ) : (
        <div className="bg-muted p-4 rounded-lg">
          <h5 className="font-medium mb-2">Explanation:</h5>
          <div 
            className="prose prose-sm dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: explanation }}
          />
        </div>
      )}
      
      {/* Confetti Celebration for Correct Answers */}
      <ConfettiCelebration
        isVisible={showConfetti}
        onComplete={handleConfettiComplete}
        title="Correct! 🎉"
        message="Great job! You got that question right!"
        type="quiz"
        autoHide={true}
        autoHideDelay={3000}
      />
    </div>
  )
}

function LessonContent({ content, onQuizComplete = null }) {
  if (!content || content.length === 0) {
    return (
      <div className="text-center py-12">
        <BookOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-medium mb-2">Content Coming Soon</h3>
        <p className="text-muted-foreground">This lesson content is being developed.</p>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {content.map((block, index) => {
        switch (block.type) {
          case 'text':
            return <TextBlock key={index} content={block.value} />
          case 'heading':
            return <HeadingBlock key={index} content={block.value} />
          case 'code_example':
            return <CodeExampleBlock key={index} content={block.value} />
          case 'runnable_code_example':
            return <RunnableCodeExampleBlock key={index} content={block.value} />
          case 'fill_blank_code':
            return <FillBlankCodeBlock key={index} content={block.value} />
          case 'multiple_choice_code':
            return <MultipleChoiceCodeBlock key={index} content={block.value} />
          case 'interactive_exercise':
            return <InteractiveExerciseBlock key={index} content={block.value} />
          case 'video':
            return <VideoBlock key={index} content={block.value} />
          case 'callout':
            return <CalloutBlock key={index} content={block.value} />
          case 'quiz':
            return <QuizBlock 
              key={index} 
              content={block.value} 
              onQuizComplete={(isCorrect) => onQuizComplete && onQuizComplete(index, isCorrect)}
            />
          default:
            return (
              <div key={index} className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  Unsupported content type: {block.type}
                </p>
              </div>
            )
        }
      })}
    </div>
  )
}

export default function WagtailLessonPage() {
  const { courseSlug, lessonSlug } = useParams()
  const { user, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [completed, setCompleted] = useState(false)
  const [quizResults, setQuizResults] = useState({})
  const [showCourseComplete, setShowCourseComplete] = useState(false)

  useEffect(() => {
    fetchLesson()
  }, [courseSlug, lessonSlug])

  const fetchLesson = async () => {
    try {
      setLoading(true)
      console.log('Fetching lesson:', { courseSlug, lessonSlug })
      console.log('API URL will be:', `/courses/${courseSlug}/lessons/${lessonSlug}/`)
      
      const response = await api.get(`/courses/${courseSlug}/lessons/${lessonSlug}/`)
      console.log('Lesson response:', response)
      setLesson(response.data)
      setError(null)
    } catch (err) {
      console.error('Error fetching lesson:', err)
      console.error('Error details:', {
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        message: err.message
      })
      
      if (err.response?.status === 404) {
        setError('Lesson not found.')
      } else if (err.response?.status === 403) {
        setError('You need to be enrolled in this course to access this lesson.')
      } else {
        setError(`Failed to load lesson: ${err.message}. Please try again later.`)
      }
    } finally {
      setLoading(false)
    }
  }

  // Handle individual quiz completion
  const handleQuizComplete = useCallback((quizIndex, isCorrect) => {
    setQuizResults(prev => {
      const newResults = { ...prev, [quizIndex]: isCorrect }
      
      // Check if this is the final lesson and all quizzes are completed correctly
      if (lesson && lesson.title.includes('Final Assessment') || lesson.title.includes('Quiz')) {
        const totalQuizzes = lesson.content.filter(block => block.type === 'quiz').length
        const completedQuizzes = Object.keys(newResults).length
        const allCorrect = Object.values(newResults).every(result => result === true)
        
        if (completedQuizzes === totalQuizzes && allCorrect && totalQuizzes > 0) {
          // Trigger course completion confetti after a short delay
          setTimeout(() => {
            setShowCourseComplete(true)
          }, 1000)
        }
      }
      
      return newResults
    })
  }, [lesson])

  const handleCourseCompleteConfetti = () => {
    setShowCourseComplete(false)
  }

  const handleMarkComplete = () => {
    setCompleted(true)
    // TODO: Update progress via API
  }

  if (loading) {
    return (
      <div className="container-custom py-8">
        <div className="animate-pulse max-w-4xl mx-auto">
          <div className="h-6 bg-muted rounded w-32 mb-4"></div>
          <div className="h-8 bg-muted rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-muted rounded w-1/2 mb-8"></div>
          <div className="space-y-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-muted rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container-custom py-8">
        <div className="max-w-4xl mx-auto text-center">
          <AlertCircle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Error Loading Lesson</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Link to={`/courses/${courseSlug}`} className="btn-primary">
            Back to Course
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container-custom py-8">
      <div className="max-w-4xl mx-auto">
        {/* Breadcrumb Navigation */}
        <nav className="flex items-center space-x-2 text-sm text-muted-foreground mb-6">
          <Link to={`/courses/${lesson.course.slug}`} className="hover:text-primary transition-colors">
            {lesson.course.title}
          </Link>
          <ChevronRight className="h-4 w-4" />
          <span className="text-foreground">{lesson.title}</span>
        </nav>

        {/* Lesson Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-primary/10 text-primary rounded-full flex items-center justify-center text-sm font-medium">
              {lesson.lesson_number}
            </div>
            <div>
              <h1 className="text-3xl font-bold">{lesson.title}</h1>
              {lesson.estimated_duration && (
                <div className="flex items-center space-x-2 text-muted-foreground mt-2">
                  <Clock className="h-4 w-4" />
                  <span>{lesson.estimated_duration}</span>
                </div>
              )}
            </div>
          </div>

          {lesson.intro && (
            <p className="text-lg text-muted-foreground">{lesson.intro}</p>
          )}
        </div>

        {/* Learning Objectives */}
        {lesson.objectives && lesson.objectives.length > 0 && (
          <div className="bg-card border rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Learning Objectives</span>
            </h2>
            <ul className="space-y-2">
              {lesson.objectives.map((objective, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <span>{objective}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Main Content */}
        <div className="mb-8">
          <LessonContent content={lesson.content} onQuizComplete={handleQuizComplete} />
        </div>

        {/* Resources */}
        {lesson.resources && lesson.resources.length > 0 && (
          <div className="bg-card border rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Additional Resources</span>
            </h2>
            <div className="space-y-3">
              {lesson.resources.map((resource, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="text-2xl">
                    {resource.type === 'video' ? '🎥' : 
                     resource.type === 'documentation' ? '📚' : 
                     resource.type === 'article' ? '📄' : '🔗'}
                  </div>
                  <div>
                    <a 
                      href={resource.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="font-medium text-primary hover:underline"
                    >
                      {resource.title}
                    </a>
                    {resource.description && (
                      <p className="text-sm text-muted-foreground mt-1">{resource.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lesson Completion */}
        <div className="bg-card border rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold mb-1">Mark as Complete</h3>
              <p className="text-sm text-muted-foreground">
                {completed ? 'Great job! You\'ve completed this lesson.' : 'Click when you\'ve finished studying this lesson.'}
              </p>
            </div>
            <button 
              onClick={handleMarkComplete}
              disabled={completed}
              className={clsx(
                'px-6 py-2 rounded-lg font-medium transition-colors',
                completed 
                  ? 'bg-green-600 text-white cursor-default' 
                  : 'bg-primary text-primary-foreground hover:bg-primary/90'
              )}
            >
              {completed ? (
                <>
                  <CheckCircle className="h-4 w-4 inline mr-2" />
                  Completed
                </>
              ) : (
                'Mark Complete'
              )}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <div>
            {lesson.navigation?.previous && (
              <Link 
                to={`/courses/${courseSlug}/lessons/${lesson.navigation.previous.slug}`}
                className="btn-secondary flex items-center space-x-2"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Previous: {lesson.navigation.previous.title}</span>
              </Link>
            )}
          </div>
          
          <Link 
            to={`/courses/${courseSlug}`}
            className="btn-secondary"
          >
            Back to Course
          </Link>
          
          <div>
            {lesson.navigation?.next && (
              <Link 
                to={`/courses/${courseSlug}/lessons/${lesson.navigation.next.slug}`}
                className="btn-primary flex items-center space-x-2"
              >
                <span>Next: {lesson.navigation.next.title}</span>
                <ChevronRight className="h-4 w-4" />
              </Link>
            )}
          </div>
        </div>
        
        {/* Course Completion Confetti */}
        <ConfettiCelebration
          isVisible={showCourseComplete}
          onComplete={handleCourseCompleteConfetti}
          title="🎓 Course Complete!"
          message="Congratulations! You've successfully completed the Interactive Python Fundamentals course!"
          type="course"
          autoHide={false}
        />
      </div>
    </div>
  )
}