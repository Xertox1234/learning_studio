import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Shield,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Users,
  MessageSquare,
  FileText,
  BarChart3,
  Activity,
  ArrowLeft,
  Download
} from 'lucide-react'
import { useModerationAnalytics } from '../hooks/useForumQuery'
import { useAuth } from '../contexts/AuthContext'
import { format, subDays } from 'date-fns'
import clsx from 'clsx'
import { exportModerationAnalytics } from '../utils/exportUtils'
import toast from 'react-hot-toast'

export default function ModerationAnalyticsPage() {
  const { user } = useAuth()
  const [timeRange, setTimeRange] = useState('7') // 7, 30, 90 days

  // Check if user can access moderation features
  const canModerate = user && (
    user.is_staff ||
    user.is_superuser ||
    (user.trust_level && user.trust_level.level >= 3)
  )

  // Fetch analytics with React Query hook
  const { data: analytics, isLoading: loading, error } = useModerationAnalytics(
    { days: timeRange },
    { enabled: canModerate } // Only fetch if user can moderate
  )

  const handleExportAnalytics = () => {
    if (!analytics) {
      toast.error('No analytics data to export')
      return
    }

    exportModerationAnalytics(analytics, parseInt(timeRange))
    toast.success(`Analytics report exported successfully`)
  }

  if (!canModerate) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <Shield className="w-16 h-16 mx-auto text-red-500 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
            <p className="text-gray-600">
              You need to be Trust Level 3 or higher to access moderation analytics.
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

  if (loading && !analytics) {
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

  const calculateTrend = (current, previous) => {
    if (previous === 0) return current > 0 ? 100 : 0
    return ((current - previous) / previous) * 100
  }

  const formatTrend = (trend) => {
    const absTrend = Math.abs(trend)
    return `${trend > 0 ? '+' : ''}${absTrend.toFixed(1)}%`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/forum/moderation/queue"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Queue</span>
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                <h1 className="text-3xl font-bold text-gray-900">Moderation Analytics</h1>
              </div>
              <p className="text-gray-600">
                Comprehensive overview of moderation activity and performance metrics
              </p>
            </div>

            {/* Time Range Selector & Export */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-white rounded-lg p-1 shadow-sm">
                {[
                  { value: '7', label: '7 Days' },
                  { value: '30', label: '30 Days' },
                  { value: '90', label: '90 Days' }
                ].map((range) => (
                  <button
                    key={range.value}
                    onClick={() => setTimeRange(range.value)}
                    className={clsx(
                      'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      timeRange === range.value
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              {/* Export Button */}
              <button
                onClick={handleExportAnalytics}
                disabled={!analytics}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm',
                  analytics
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                )}
                aria-label="Export analytics report to CSV"
                title="Export analytics report to CSV"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800">{error.message || 'Failed to load analytics'}</p>
          </div>
        )}

        {analytics && (
          <>
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {/* Total Reviews */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Activity className="w-6 h-6 text-purple-600" />
                  </div>
                  {analytics.trends?.total_reviews && (
                    <div className={clsx(
                      'flex items-center gap-1 text-sm font-medium',
                      analytics.trends.total_reviews > 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analytics.trends.total_reviews > 0 ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      <span>{formatTrend(analytics.trends.total_reviews)}</span>
                    </div>
                  )}
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Total Reviews</h3>
                <p className="text-3xl font-bold text-gray-900">{analytics.total_reviews || 0}</p>
                <p className="text-sm text-gray-500 mt-1">Last {timeRange} days</p>
              </div>

              {/* Approval Rate */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  {analytics.trends?.approval_rate && (
                    <div className={clsx(
                      'flex items-center gap-1 text-sm font-medium',
                      analytics.trends.approval_rate > 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analytics.trends.approval_rate > 0 ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      <span>{formatTrend(analytics.trends.approval_rate)}</span>
                    </div>
                  )}
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Approval Rate</h3>
                <p className="text-3xl font-bold text-gray-900">{analytics.approval_rate || 0}%</p>
                <p className="text-sm text-gray-500 mt-1">{analytics.approved_count || 0} approved</p>
              </div>

              {/* Avg Response Time */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Clock className="w-6 h-6 text-blue-600" />
                  </div>
                  {analytics.trends?.avg_response_time && (
                    <div className={clsx(
                      'flex items-center gap-1 text-sm font-medium',
                      analytics.trends.avg_response_time < 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analytics.trends.avg_response_time < 0 ? (
                        <TrendingDown className="w-4 h-4" />
                      ) : (
                        <TrendingUp className="w-4 h-4" />
                      )}
                      <span>{formatTrend(Math.abs(analytics.trends.avg_response_time))}</span>
                    </div>
                  )}
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Avg Response Time</h3>
                <p className="text-3xl font-bold text-gray-900">{analytics.avg_response_time || '0m'}</p>
                <p className="text-sm text-gray-500 mt-1">Time to review</p>
              </div>

              {/* Pending Items */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <AlertTriangle className="w-6 h-6 text-orange-600" />
                  </div>
                  {analytics.trends?.pending_count && (
                    <div className={clsx(
                      'flex items-center gap-1 text-sm font-medium',
                      analytics.trends.pending_count < 0 ? 'text-green-600' : 'text-red-600'
                    )}>
                      {analytics.trends.pending_count < 0 ? (
                        <TrendingDown className="w-4 h-4" />
                      ) : (
                        <TrendingUp className="w-4 h-4" />
                      )}
                      <span>{formatTrend(Math.abs(analytics.trends.pending_count))}</span>
                    </div>
                  )}
                </div>
                <h3 className="text-sm font-medium text-gray-600 mb-1">Pending Items</h3>
                <p className="text-3xl font-bold text-gray-900">{analytics.pending_count || 0}</p>
                <p className="text-sm text-gray-500 mt-1">Awaiting review</p>
              </div>
            </div>

            {/* Content Type Breakdown & Top Moderators */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Content Type Breakdown */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-gray-600" />
                  Content Type Breakdown
                </h3>
                <div className="space-y-4">
                  {analytics.by_content_type && Object.entries(analytics.by_content_type).map(([type, count]) => {
                    const total = Object.values(analytics.by_content_type).reduce((a, b) => a + b, 0)
                    const percentage = total > 0 ? (count / total) * 100 : 0

                    const getIcon = (type) => {
                      switch (type) {
                        case 'posts': return MessageSquare
                        case 'topics': return FileText
                        case 'users': return Users
                        default: return FileText
                      }
                    }

                    const Icon = getIcon(type)

                    return (
                      <div key={type}>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700 capitalize">{type}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-500">{count}</span>
                            <span className="text-sm font-medium text-gray-900">{percentage.toFixed(1)}%</span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Top Moderators */}
              <div className="bg-white rounded-xl shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Users className="w-5 h-5 text-gray-600" />
                  Top Moderators
                </h3>
                <div className="space-y-3">
                  {analytics.top_moderators && analytics.top_moderators.length > 0 ? (
                    analytics.top_moderators.map((moderator, index) => (
                      <div
                        key={moderator.username}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className={clsx(
                            'w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm',
                            index === 0 && 'bg-yellow-100 text-yellow-700',
                            index === 1 && 'bg-gray-200 text-gray-700',
                            index === 2 && 'bg-orange-100 text-orange-700',
                            index > 2 && 'bg-blue-100 text-blue-700'
                          )}>
                            #{index + 1}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900">{moderator.username}</p>
                            <p className="text-sm text-gray-500">
                              {moderator.approval_rate}% approval rate
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold text-gray-900">{moderator.review_count}</p>
                          <p className="text-xs text-gray-500">reviews</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-gray-500 py-8">No moderation data available</p>
                  )}
                </div>
              </div>
            </div>

            {/* Daily Activity Chart (Simple Bar Chart) */}
            <div className="bg-white rounded-xl shadow-md p-6 mb-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-600" />
                Daily Activity
              </h3>
              {analytics.daily_activity && analytics.daily_activity.length > 0 ? (
                <div className="space-y-2">
                  {analytics.daily_activity.map((day) => (
                    <div key={day.date} className="flex items-center gap-4">
                      <div className="w-24 text-sm text-gray-600">
                        {format(new Date(day.date), 'MMM dd')}
                      </div>
                      <div className="flex-1 flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-8 relative overflow-hidden">
                          <div
                            className="bg-green-500 h-full rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                            style={{
                              width: `${(day.approved / Math.max(...analytics.daily_activity.map(d => d.total), 1)) * 100}%`
                            }}
                          >
                            {day.approved > 0 && (
                              <span className="text-xs font-medium text-white">{day.approved}</span>
                            )}
                          </div>
                          <div
                            className="absolute top-0 bg-red-500 h-full rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                            style={{
                              left: `${(day.approved / Math.max(...analytics.daily_activity.map(d => d.total), 1)) * 100}%`,
                              width: `${(day.rejected / Math.max(...analytics.daily_activity.map(d => d.total), 1)) * 100}%`
                            }}
                          >
                            {day.rejected > 0 && (
                              <span className="text-xs font-medium text-white">{day.rejected}</span>
                            )}
                          </div>
                        </div>
                        <div className="w-16 text-sm font-medium text-gray-900 text-right">
                          {day.total}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span className="text-sm text-gray-600">Approved</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded"></div>
                      <span className="text-sm text-gray-600">Rejected</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-500 py-8">No activity data available</p>
              )}
            </div>

            {/* Insights & Recommendations */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                Insights & Recommendations
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analytics.insights && analytics.insights.length > 0 ? (
                  analytics.insights.map((insight, index) => (
                    <div key={index} className="bg-white rounded-lg p-4 border border-blue-100">
                      <p className="text-sm text-gray-700">{insight}</p>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="bg-white rounded-lg p-4 border border-blue-100">
                      <p className="text-sm text-gray-700">
                        📊 Moderation activity is {analytics.total_reviews > 50 ? 'high' : 'moderate'} for the selected period
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-100">
                      <p className="text-sm text-gray-700">
                        ⚡ Average response time is {analytics.avg_response_time}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-100">
                      <p className="text-sm text-gray-700">
                        ✅ Approval rate of {analytics.approval_rate}% indicates balanced moderation
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border border-blue-100">
                      <p className="text-sm text-gray-700">
                        👥 {analytics.total_moderators || 0} moderators actively reviewing content
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
