/**
 * Export utilities for moderation reports and data
 */

/**
 * Convert data to CSV format
 * @param {Array} data - Array of objects to convert
 * @param {Array} columns - Column definitions [{key, header}]
 * @returns {string} CSV string
 */
export const convertToCSV = (data, columns) => {
  if (!data || data.length === 0) {
    return ''
  }

  // Create header row
  const headers = columns.map(col => col.header).join(',')

  // Create data rows
  const rows = data.map(item => {
    return columns.map(col => {
      let value = item[col.key]

      // Handle nested objects
      if (col.key.includes('.')) {
        const keys = col.key.split('.')
        value = keys.reduce((obj, key) => obj?.[key], item)
      }

      // Format value
      if (value === null || value === undefined) {
        return ''
      }

      // Convert to string and escape
      value = String(value)

      // Escape quotes and wrap in quotes if contains comma, newline, or quote
      if (value.includes(',') || value.includes('\n') || value.includes('"')) {
        value = `"${value.replace(/"/g, '""')}"`
      }

      return value
    }).join(',')
  })

  return [headers, ...rows].join('\n')
}

/**
 * Download CSV file
 * @param {string} csvContent - CSV string content
 * @param {string} filename - Name of the file to download
 */
export const downloadCSV = (csvContent, filename) => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')

  if (navigator.msSaveBlob) {
    // IE 10+
    navigator.msSaveBlob(blob, filename)
  } else {
    const url = URL.createObjectURL(blob)
    link.href = url
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }
}

/**
 * Export moderation queue data to CSV
 * @param {Array} queueItems - Queue items to export
 * @param {Object} filters - Applied filters
 */
export const exportModerationQueue = (queueItems, filters = {}) => {
  const columns = [
    { key: 'id', header: 'ID' },
    { key: 'content_type', header: 'Content Type' },
    { key: 'created_at', header: 'Created At' },
    { key: 'author.username', header: 'Author' },
    { key: 'author.trust_level.level', header: 'Author Trust Level' },
    { key: 'priority_score', header: 'Priority Score' },
    { key: 'flags_count', header: 'Flags Count' },
    { key: 'preview', header: 'Content Preview' },
    { key: 'status', header: 'Status' },
  ]

  // Format data for export
  const formattedData = queueItems.map(item => ({
    ...item,
    created_at: new Date(item.created_at).toLocaleString(),
    status: item.status || 'pending',
    preview: item.content?.substring(0, 100) || '',
  }))

  const csv = convertToCSV(formattedData, columns)

  // Generate filename with timestamp and filters
  const timestamp = new Date().toISOString().split('T')[0]
  const filterSuffix = filters.contentType ? `_${filters.contentType}` : ''
  const filename = `moderation_queue${filterSuffix}_${timestamp}.csv`

  downloadCSV(csv, filename)
}

/**
 * Export moderation analytics to CSV
 * @param {Object} analytics - Analytics data
 * @param {number} timeRange - Time range in days
 */
export const exportModerationAnalytics = (analytics, timeRange) => {
  if (!analytics) return

  // Create summary section
  const summaryColumns = [
    { key: 'metric', header: 'Metric' },
    { key: 'value', header: 'Value' },
    { key: 'trend', header: 'Trend' },
  ]

  const summaryData = [
    {
      metric: 'Total Reviews',
      value: analytics.total_reviews || 0,
      trend: analytics.total_reviews_trend ? `${analytics.total_reviews_trend > 0 ? '+' : ''}${analytics.total_reviews_trend}%` : 'N/A',
    },
    {
      metric: 'Approval Rate',
      value: `${analytics.approval_rate || 0}%`,
      trend: analytics.approval_rate_trend ? `${analytics.approval_rate_trend > 0 ? '+' : ''}${analytics.approval_rate_trend}%` : 'N/A',
    },
    {
      metric: 'Average Response Time',
      value: analytics.avg_response_time || 'N/A',
      trend: analytics.avg_response_time_trend ? `${analytics.avg_response_time_trend > 0 ? '+' : ''}${analytics.avg_response_time_trend}%` : 'N/A',
    },
    {
      metric: 'Pending Items',
      value: analytics.pending_items || 0,
      trend: analytics.pending_items_trend ? `${analytics.pending_items_trend > 0 ? '+' : ''}${analytics.pending_items_trend}%` : 'N/A',
    },
  ]

  let csvContent = '# Moderation Analytics Summary\n'
  csvContent += `# Period: Last ${timeRange} days\n`
  csvContent += `# Generated: ${new Date().toLocaleString()}\n\n`
  csvContent += convertToCSV(summaryData, summaryColumns)

  // Add content type breakdown
  if (analytics.by_content_type) {
    csvContent += '\n\n# Content Type Breakdown\n'
    const contentTypeColumns = [
      { key: 'type', header: 'Content Type' },
      { key: 'count', header: 'Count' },
      { key: 'percentage', header: 'Percentage' },
    ]

    const total = Object.values(analytics.by_content_type).reduce((a, b) => a + b, 0)
    const contentTypeData = Object.entries(analytics.by_content_type).map(([type, count]) => ({
      type,
      count,
      percentage: total > 0 ? `${((count / total) * 100).toFixed(1)}%` : '0%',
    }))

    csvContent += '\n' + convertToCSV(contentTypeData, contentTypeColumns)
  }

  // Add daily activity
  if (analytics.daily_activity && analytics.daily_activity.length > 0) {
    csvContent += '\n\n# Daily Activity\n'
    const activityColumns = [
      { key: 'date', header: 'Date' },
      { key: 'approved', header: 'Approved' },
      { key: 'rejected', header: 'Rejected' },
      { key: 'total', header: 'Total' },
    ]

    csvContent += '\n' + convertToCSV(analytics.daily_activity, activityColumns)
  }

  // Add top moderators
  if (analytics.top_moderators && analytics.top_moderators.length > 0) {
    csvContent += '\n\n# Top Moderators\n'
    const moderatorColumns = [
      { key: 'username', header: 'Username' },
      { key: 'reviews', header: 'Total Reviews' },
      { key: 'approved', header: 'Approved' },
      { key: 'rejected', header: 'Rejected' },
      { key: 'approval_rate', header: 'Approval Rate' },
    ]

    const moderatorData = analytics.top_moderators.map(mod => ({
      ...mod,
      approval_rate: `${mod.approval_rate}%`,
    }))

    csvContent += '\n' + convertToCSV(moderatorData, moderatorColumns)
  }

  const timestamp = new Date().toISOString().split('T')[0]
  const filename = `moderation_analytics_${timeRange}days_${timestamp}.csv`

  downloadCSV(csvContent, filename)
}

/**
 * Format date for export
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
export const formatDateForExport = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}
