import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  MessageSquare,
  FileText,
  User,
  ChevronLeft,
  ChevronRight,
  Filter,
  Search,
  Download,
  BarChart3
} from 'lucide-react'
import { useModerationQueue, useModerationStats, useReviewModeration } from '../hooks/useForumQuery'
import { useAuth } from '../contexts/AuthContext'
import { format } from 'date-fns'
import clsx from 'clsx'
import { exportModerationQueue } from '../utils/exportUtils'
import toast from 'react-hot-toast'

export default function ModerationQueuePage() {
  const { user } = useAuth()
  const [filterType, setFilterType] = useState('all') // all, posts, topics, users
  const [filterStatus, setFilterStatus] = useState('pending') // pending, approved, rejected
  const [currentPage, setCurrentPage] = useState(1)
  const [processingId, setProcessingId] = useState(null)
  const [reviewNotes, setReviewNotes] = useState({})
  const [selectedItems, setSelectedItems] = useState([])
  const [batchProcessing, setBatchProcessing] = useState(false)
  const [focusedItemIndex, setFocusedItemIndex] = useState(0)
  const [undoAction, setUndoAction] = useState(null)
  const [undoTimer, setUndoTimer] = useState(null)
  const [showShortcutsHelp, setShowShortcutsHelp] = useState(false)

  // Use React Query hooks
  const { data: queueData, isLoading: loading, error } = useModerationQueue({
    type: filterType !== 'all' ? filterType : undefined,
    status: filterStatus,
    page: currentPage,
    page_size: 20
  })

  const { data: stats } = useModerationStats()
  const reviewMutation = useReviewModeration()

  // Extract queue and pagination from React Query data
  const queue = queueData?.results || []
  const pagination = queueData?.pagination || null

  // Clear selections when changing filters or pages
  useEffect(() => {
    setSelectedItems([])
    setFocusedItemIndex(0)
  }, [filterType, filterStatus, currentPage])

  // Cleanup undo timer on unmount
  useEffect(() => {
    return () => {
      if (undoTimer) {
        clearTimeout(undoTimer)
      }
    }
  }, [undoTimer])

  // Keyboard shortcuts for power users
  useEffect(() => {
    const handleKeyPress = (e) => {
      // Don't trigger shortcuts if user is typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

      // Handle help modal (works regardless of queue state)
      if (e.key === '?') {
        e.preventDefault()
        setShowShortcutsHelp(true)
        return
      }

      // Handle closing help modal with Escape
      if (e.key === 'Escape' && showShortcutsHelp) {
        e.preventDefault()
        setShowShortcutsHelp(false)
        return
      }

      // Only work when queue has items
      if (queue.length === 0) return

      const focusedItem = queue[focusedItemIndex]

      switch (e.key.toLowerCase()) {
        case 'a':
          // Approve focused item or selected items
          e.preventDefault()
          if (selectedItems.length > 0) {
            handleBatchReview('approve')
          } else if (focusedItem) {
            handleReview(focusedItem.id, 'approve')
          }
          break

        case 'r':
          // Reject focused item or selected items
          e.preventDefault()
          if (selectedItems.length > 0) {
            handleBatchReview('reject')
          } else if (focusedItem) {
            handleReview(focusedItem.id, 'reject')
          }
          break

        case 'j':
          // Move focus down
          e.preventDefault()
          setFocusedItemIndex(prev => Math.min(prev + 1, queue.length - 1))
          break

        case 'k':
          // Move focus up
          e.preventDefault()
          setFocusedItemIndex(prev => Math.max(prev - 1, 0))
          break

        case 'x':
          // Toggle selection on focused item
          e.preventDefault()
          if (focusedItem) {
            handleSelectItem(focusedItem.id, !selectedItems.includes(focusedItem.id))
          }
          break

        default:
          break
      }
    }

    document.addEventListener('keydown', handleKeyPress)
    return () => document.removeEventListener('keydown', handleKeyPress)
  }, [queue, focusedItemIndex, selectedItems, handleReview, handleBatchReview, showShortcutsHelp])

  const handleReview = useCallback(async (itemId, action) => {
    try {
      setProcessingId(itemId)
      const notes = reviewNotes[itemId] || ''

      // Use mutation hook - React Query handles cache invalidation
      await reviewMutation.mutateAsync({
        itemId,
        action,
        reason: notes
      })

      toast.success(`Item ${action}d successfully`)

      // Clear the notes for this item
      setReviewNotes(prev => {
        const updated = { ...prev }
        delete updated[itemId]
        return updated
      })

      // Set up undo action
      const oppositeAction = action === 'approve' ? 'reject' : 'approve'
      setUndoAction({
        itemId,
        originalAction: action,
        oppositeAction,
        timestamp: Date.now()
      })

      // Auto-clear undo after 30 seconds
      if (undoTimer) clearTimeout(undoTimer)
      const timer = setTimeout(() => {
        setUndoAction(null)
      }, 30000)
      setUndoTimer(timer)

    } catch (error) {
      console.error(`Failed to ${action} item:`, error)
      toast.error(`Failed to ${action} item: ${error.message}`)
    } finally {
      setProcessingId(null)
    }
  }, [reviewNotes, undoTimer, reviewMutation])

  const handleSelectItem = (itemId, checked) => {
    setSelectedItems(prev => {
      if (checked) {
        return [...prev, itemId]
      } else {
        return prev.filter(id => id !== itemId)
      }
    })
  }

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedItems(queue.map(item => item.id))
    } else {
      setSelectedItems([])
    }
  }

  const handleBatchReview = useCallback(async (action) => {
    if (selectedItems.length === 0) return

    try {
      setBatchProcessing(true)
      const defaultNotes = action === 'approve'
        ? 'Batch approved'
        : 'Batch rejected'

      // Process all selected items in parallel using mutation
      const promises = selectedItems.map(async itemId => {
        return reviewMutation.mutateAsync({
          itemId,
          action,
          reason: reviewNotes[itemId] || defaultNotes
        }).catch(err => {
          console.error(`Failed to ${action} item ${itemId}:`, err)
          return { error: err, itemId }
        })
      })

      const results = await Promise.all(promises)

      // Check for failures
      const failures = results.filter(r => r && r.error)
      if (failures.length > 0) {
        toast.error(`${failures.length} of ${selectedItems.length} items failed to ${action}`)
      } else {
        toast.success(`Successfully ${action}d ${selectedItems.length} items`)
      }

      // Clear selections and notes
      setSelectedItems([])
      setReviewNotes({})

    } catch (error) {
      console.error(`Failed to batch ${action}:`, error)
      toast.error(`Failed to batch ${action}: ${error.message}`)
    } finally {
      setBatchProcessing(false)
    }
  }, [selectedItems, reviewNotes, reviewMutation])

  const handleUndo = async () => {
    if (!undoAction) return

    try {
      setProcessingId(undoAction.itemId)

      // Use mutation hook to undo
      await reviewMutation.mutateAsync({
        itemId: undoAction.itemId,
        action: undoAction.oppositeAction,
        reason: 'Reverted previous action'
      })

      toast.success('Action undone successfully')

      // Clear undo action
      if (undoTimer) clearTimeout(undoTimer)
      setUndoAction(null)
      setUndoTimer(null)

    } catch (error) {
      console.error('Failed to undo action:', error)
      toast.error(`Failed to undo: ${error.message}`)
    } finally {
      setProcessingId(null)
    }
  }

  const handleDismissUndo = () => {
    if (undoTimer) clearTimeout(undoTimer)
    setUndoAction(null)
    setUndoTimer(null)
  }

  const handleExportQueue = () => {
    if (queue.length === 0) {
      toast.error('No items to export')
      return
    }

    const filters = {
      contentType: filterType !== 'all' ? filterType : null,
      status: filterStatus,
    }

    exportModerationQueue(queue, filters)
    toast.success(`Exported ${queue.length} item${queue.length === 1 ? '' : 's'} to CSV`)
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 1: return 'text-red-600 bg-red-50 border-red-200'
      case 2: return 'text-orange-600 bg-orange-50 border-orange-200'
      case 3: return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 4: return 'text-blue-600 bg-blue-50 border-blue-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getPriorityLabel = (priority) => {
    switch (priority) {
      case 1: return 'Critical'
      case 2: return 'High'
      case 3: return 'Medium'
      case 4: return 'Low'
      default: return 'Unknown'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-green-100 text-green-800'
      case 'rejected': return 'bg-red-100 text-red-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'escalated': return 'bg-purple-100 text-purple-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getContentIcon = (contentType) => {
    switch (contentType) {
      case 'post': return <MessageSquare className="w-4 h-4" />
      case 'topic': return <FileText className="w-4 h-4" />
      case 'user': return <User className="w-4 h-4" />
      default: return <AlertTriangle className="w-4 h-4" />
    }
  }

  const formatTimeAgo = (date) => {
    if (!date) return 'unknown'
    const now = new Date()
    const targetDate = new Date(date)
    const diff = now - targetDate
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'just now'
  }

  // Check if user has moderation permissions (TL3+)
  const canModerate = user && (
    user.is_staff ||
    user.is_superuser ||
    (user.trust_level && user.trust_level.level >= 3)
  )

  if (!canModerate) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <Shield className="w-16 h-16 mx-auto text-red-500 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">
              You need to be Trust Level 3 or higher to access the moderation queue.
            </p>
            <Link
              to="/forum"
              className="inline-block mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Return to Forum
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (loading && queue.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Moderation Queue</h1>
            </div>
            <Link
              to="/forum/moderation/analytics"
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
            >
              <BarChart3 className="w-4 h-4" />
              View Analytics
            </Link>
          </div>
          <p className="text-gray-600">
            Review and moderate flagged content, new user posts, and reported items
          </p>
        </div>

        {/* Statistics Dashboard */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="w-5 h-5 text-orange-500" />
                <h3 className="text-sm font-medium text-gray-600">Pending</h3>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.pending || 0}</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <h3 className="text-sm font-medium text-gray-600">Approved</h3>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.approved || 0}</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center gap-3 mb-2">
                <XCircle className="w-5 h-5 text-red-500" />
                <h3 className="text-sm font-medium text-gray-600">Rejected</h3>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.rejected || 0}</p>
            </div>
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center gap-3 mb-2">
                <User className="w-5 h-5 text-blue-500" />
                <h3 className="text-sm font-medium text-gray-600">Today's Reviews</h3>
              </div>
              <p className="text-3xl font-bold text-gray-900">{stats.today_count || 0}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
              {/* Content Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content Type
                </label>
                <div className="flex gap-2" role="group" aria-label="Filter by content type">
                  {['all', 'posts', 'topics', 'users'].map((type) => (
                    <button
                      key={type}
                      onClick={() => {
                        setFilterType(type)
                        setCurrentPage(1)
                      }}
                      aria-label={`Filter by ${type} content`}
                      aria-pressed={filterType === type}
                      className={clsx(
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        filterType === type
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      )}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <div className="flex gap-2" role="group" aria-label="Filter by status">
                  {['pending', 'approved', 'rejected'].map((status) => (
                    <button
                      key={status}
                      onClick={() => {
                        setFilterStatus(status)
                        setCurrentPage(1)
                      }}
                      aria-label={`Show ${status} items`}
                      aria-pressed={filterStatus === status}
                      className={clsx(
                        'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                        filterStatus === status
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      )}
                    >
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Export Button */}
            <div className="ml-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Actions
              </label>
              <button
                onClick={handleExportQueue}
                disabled={queue.length === 0}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  queue.length > 0
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                )}
                aria-label="Export queue data to CSV"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
          </div>

          {/* Keyboard Shortcuts Help */}
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-blue-900">
                <span className="font-medium">⌨️ Keyboard Shortcuts:</span>
                <kbd className="px-2 py-0.5 bg-white border border-blue-300 rounded text-xs">A</kbd>
                <span className="text-xs">Approve</span>
                <kbd className="px-2 py-0.5 bg-white border border-blue-300 rounded text-xs">R</kbd>
                <span className="text-xs">Reject</span>
                <kbd className="px-2 py-0.5 bg-white border border-blue-300 rounded text-xs">J/K</kbd>
                <span className="text-xs">Navigate</span>
                <kbd className="px-2 py-0.5 bg-white border border-blue-300 rounded text-xs">X</kbd>
                <span className="text-xs">Select</span>
              </div>
              <button
                onClick={() => setShowShortcutsHelp(true)}
                className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-xs font-medium"
                aria-label="Show all keyboard shortcuts"
              >
                <span>Press</span>
                <kbd className="px-1.5 py-0.5 bg-blue-700 border border-blue-800 rounded text-xs font-mono">?</kbd>
                <span>for help</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Batch Actions Bar */}
        {queue.length > 0 && (
          <div className="bg-white rounded-xl shadow-md p-4 mb-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedItems.length === queue.length && queue.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300"
                  aria-label="Select all items"
                />
                <span className="text-sm font-medium text-gray-700">
                  Select All
                </span>
              </label>
              {selectedItems.length > 0 && (
                <span className="text-sm text-gray-600">
                  {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
                </span>
              )}
            </div>
            {selectedItems.length > 0 && (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleBatchReview('approve')}
                  disabled={batchProcessing}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium"
                  aria-label={`Approve ${selectedItems.length} selected items`}
                >
                  <CheckCircle className="w-4 h-4" />
                  {batchProcessing ? 'Processing...' : `Approve (${selectedItems.length})`}
                </button>
                <button
                  onClick={() => handleBatchReview('reject')}
                  disabled={batchProcessing}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium"
                  aria-label={`Reject ${selectedItems.length} selected items`}
                >
                  <XCircle className="w-4 h-4" />
                  {batchProcessing ? 'Processing...' : `Reject (${selectedItems.length})`}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Queue Items */}
        <div className="space-y-4">
          {queue.length === 0 ? (
            <div className="bg-white rounded-xl shadow-md p-12 text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Queue is Empty
              </h3>
              <p className="text-gray-600">
                There are no {filterStatus} items in the {filterType === 'all' ? '' : filterType + ' '}queue.
              </p>
            </div>
          ) : (
            queue.map((item, index) => (
              <div
                key={item.id}
                className={clsx(
                  'bg-white rounded-xl shadow-md hover:shadow-lg transition-all',
                  focusedItemIndex === index && 'ring-2 ring-blue-500'
                )}
              >
                <div className="p-6">
                  {/* Item Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(item.id)}
                        onChange={(e) => handleSelectItem(item.id, e.target.checked)}
                        className="w-4 h-4 mt-1 rounded border-gray-300 cursor-pointer"
                        aria-label={`Select ${item.content_type} for batch action`}
                      />
                      <div className={clsx(
                        'p-2 rounded-lg border',
                        getPriorityColor(item.priority)
                      )}>
                        {getContentIcon(item.content_type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-900">
                            {item.review_type?.replace('_', ' ').toUpperCase() || 'REVIEW'}
                          </span>
                          <span className={clsx(
                            'px-2 py-0.5 rounded-full text-xs font-medium',
                            getStatusColor(item.status)
                          )}>
                            {item.status}
                          </span>
                          <span className={clsx(
                            'px-2 py-0.5 rounded-full text-xs font-medium',
                            getPriorityColor(item.priority)
                          )}>
                            {getPriorityLabel(item.priority)}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Created {formatTimeAgo(item.created_at)}
                          {item.reporter && (
                            <span> · Reported by {item.reporter.username}</span>
                          )}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Reason */}
                  {item.reason && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-4">
                      <p className="text-sm font-medium text-gray-700 mb-1">Reason:</p>
                      <p className="text-sm text-gray-900">{item.reason}</p>
                    </div>
                  )}

                  {/* Content Preview */}
                  {item.post && (
                    <div className="bg-blue-50 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-900">Post Content</span>
                      </div>
                      <p className="text-sm text-gray-700 mb-2">{item.post.content}</p>
                      <div className="text-xs text-gray-600">
                        By {item.post.poster.username} in topic "{item.post.topic.subject}"
                      </div>
                    </div>
                  )}

                  {item.topic && (
                    <div className="bg-purple-50 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-900">Topic</span>
                      </div>
                      <p className="text-sm font-semibold text-gray-900 mb-1">{item.topic.subject}</p>
                      <div className="text-xs text-gray-600">
                        By {item.topic.poster.username} in {item.topic.forum.name}
                      </div>
                    </div>
                  )}

                  {item.content_type === 'user' && item.user && (
                    <div className="bg-yellow-50 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <User className="w-4 h-4 text-yellow-600" />
                        <span className="text-sm font-medium text-yellow-900">User Report</span>
                      </div>
                      <div className="text-sm text-gray-700">
                        User: {item.user.username}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons for Pending Items */}
                  {item.status === 'pending' && (
                    <div className="border-t pt-4">
                      <div className="mb-3">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Review Notes (optional)
                        </label>
                        <textarea
                          value={reviewNotes[item.id] || ''}
                          onChange={(e) => setReviewNotes(prev => ({
                            ...prev,
                            [item.id]: e.target.value
                          }))}
                          placeholder="Add notes about your decision..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          rows="2"
                          disabled={processingId === item.id}
                        />
                      </div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => handleReview(item.id, 'approve')}
                          disabled={processingId === item.id}
                          className={clsx(
                            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                            processingId === item.id
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-green-600 text-white hover:bg-green-700'
                          )}
                        >
                          <CheckCircle className="w-4 h-4" />
                          Approve
                        </button>
                        <button
                          onClick={() => handleReview(item.id, 'reject')}
                          disabled={processingId === item.id}
                          className={clsx(
                            'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                            processingId === item.id
                              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                              : 'bg-red-600 text-white hover:bg-red-700'
                          )}
                        >
                          <XCircle className="w-4 h-4" />
                          Reject
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Resolution Info for Reviewed Items */}
                  {item.status !== 'pending' && (
                    <div className="border-t pt-4">
                      <div className="text-sm text-gray-600">
                        {item.status === 'approved' ? 'Approved' : 'Rejected'}
                        {item.assigned_moderator && <span> by {item.assigned_moderator.username}</span>}
                        {item.resolved_at && <span> on {format(new Date(item.resolved_at), 'MMM d, yyyy h:mm a')}</span>}
                      </div>
                      {item.resolution_notes && (
                        <div className="mt-2 bg-gray-50 rounded-lg p-3">
                          <p className="text-sm font-medium text-gray-700 mb-1">Resolution Notes:</p>
                          <p className="text-sm text-gray-900">{item.resolution_notes}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="mt-8 flex items-center justify-between bg-white rounded-xl shadow-md p-4">
            <div className="text-sm text-gray-600">
              Page {pagination.current_page} of {pagination.total_pages}
              {pagination.total_items && <span> · {pagination.total_items} total items</span>}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={!pagination.has_previous}
                className={clsx(
                  'flex items-center gap-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                  pagination.has_previous
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                )}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(prev => prev + 1)}
                disabled={!pagination.has_next}
                className={clsx(
                  'flex items-center gap-1 px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                  pagination.has_next
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                )}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Undo Notification */}
        {undoAction && (
          <div className="fixed bottom-6 right-6 bg-gray-900 text-white rounded-xl shadow-2xl p-4 flex items-center gap-4 z-50 animate-slide-up">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <div>
                <p className="font-medium">Action {undoAction.originalAction === 'approve' ? 'Approved' : 'Rejected'}</p>
                <p className="text-sm text-gray-300">Click undo to revert</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleUndo}
                disabled={processingId === undoAction.itemId}
                className="px-4 py-2 bg-white text-gray-900 rounded-lg hover:bg-gray-100 font-medium text-sm disabled:opacity-50"
              >
                {processingId === undoAction.itemId ? 'Undoing...' : 'Undo'}
              </button>
              <button
                onClick={handleDismissUndo}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                aria-label="Dismiss undo notification"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Keyboard Shortcuts Help Modal */}
        {showShortcutsHelp && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black/50 z-50 animate-fade-in"
              onClick={() => setShowShortcutsHelp(false)}
              aria-hidden="true"
            />

            {/* Modal */}
            <div
              className="fixed inset-0 z-50 flex items-center justify-center p-4"
              role="dialog"
              aria-modal="true"
              aria-labelledby="shortcuts-modal-title"
            >
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-slide-up">
                {/* Header */}
                <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <h2 id="shortcuts-modal-title" className="text-2xl font-bold text-gray-900 dark:text-white">
                      Keyboard Shortcuts
                    </h2>
                  </div>
                  <button
                    onClick={() => setShowShortcutsHelp(false)}
                    className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    aria-label="Close shortcuts help"
                  >
                    <XCircle className="w-6 h-6 text-gray-500 dark:text-gray-400" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6">
                  {/* Navigation Section */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <ChevronRight className="w-5 h-5 text-blue-600" />
                      Navigation
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Move focus down</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">J</kbd>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Move focus up</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">K</kbd>
                      </div>
                    </div>
                  </div>

                  {/* Selection Section */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      Selection
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Toggle selection on focused item</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">X</kbd>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Deselect all items</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">Escape</kbd>
                      </div>
                    </div>
                  </div>

                  {/* Moderation Actions Section */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <Shield className="w-5 h-5 text-purple-600" />
                      Moderation Actions
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <div>
                          <span className="text-gray-700 dark:text-gray-300 block">Approve focused/selected item(s)</span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">Works on single or multiple items</span>
                        </div>
                        <kbd className="px-3 py-1.5 bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-600 rounded-lg text-sm font-mono shadow-sm text-green-700 dark:text-green-300">A</kbd>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <div>
                          <span className="text-gray-700 dark:text-gray-300 block">Reject focused/selected item(s)</span>
                          <span className="text-sm text-gray-500 dark:text-gray-400">Works on single or multiple items</span>
                        </div>
                        <kbd className="px-3 py-1.5 bg-red-100 dark:bg-red-900 border border-red-300 dark:border-red-600 rounded-lg text-sm font-mono shadow-sm text-red-700 dark:text-red-300">R</kbd>
                      </div>
                    </div>
                  </div>

                  {/* General Section */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-orange-600" />
                      General
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Show this help</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">?</kbd>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <span className="text-gray-700 dark:text-gray-300">Close modal</span>
                        <kbd className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono shadow-sm">Escape</kbd>
                      </div>
                    </div>
                  </div>

                  {/* Pro Tips */}
                  <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-xl p-4">
                    <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-300 mb-2 flex items-center gap-2">
                      💡 Pro Tips
                    </h3>
                    <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-200">
                      <li>• Use <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded text-xs font-mono">J</kbd> and <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded text-xs font-mono">K</kbd> to quickly navigate through items</li>
                      <li>• Press <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded text-xs font-mono">X</kbd> to select multiple items, then <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded text-xs font-mono">A</kbd> or <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 border border-blue-300 dark:border-blue-600 rounded text-xs font-mono">R</kbd> for batch operations</li>
                      <li>• You have 30 seconds to undo any moderation action</li>
                      <li>• Focused item is highlighted with a blue ring</li>
                    </ul>
                  </div>
                </div>

                {/* Footer */}
                <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
                  <button
                    onClick={() => setShowShortcutsHelp(false)}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
                  >
                    Got it!
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
