import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  convertToCSV,
  downloadCSV,
  exportModerationQueue,
  exportModerationAnalytics,
  formatDateForExport,
} from './exportUtils'

describe('exportUtils', () => {
  let createElementSpy
  let appendChildSpy
  let removeChildSpy
  let clickSpy

  beforeEach(() => {
    // Mock DOM methods
    createElementSpy = vi.spyOn(document, 'createElement')
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {})
    clickSpy = vi.fn()

    // Mock URL methods
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = vi.fn()

    // Mock Blob
    global.Blob = vi.fn((content, options) => ({ content, options }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('convertToCSV', () => {
    it('should convert simple data to CSV format', () => {
      const data = [
        { id: 1, name: 'John', age: 30 },
        { id: 2, name: 'Jane', age: 25 },
      ]

      const columns = [
        { key: 'id', header: 'ID' },
        { key: 'name', header: 'Name' },
        { key: 'age', header: 'Age' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('ID,Name,Age\n1,John,30\n2,Jane,25')
    })

    it('should handle values with commas by wrapping in quotes', () => {
      const data = [
        { name: 'Smith, John', city: 'New York' },
      ]

      const columns = [
        { key: 'name', header: 'Name' },
        { key: 'city', header: 'City' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('Name,City\n"Smith, John",New York')
    })

    it('should handle values with newlines by wrapping in quotes', () => {
      const data = [
        { content: 'Line 1\nLine 2' },
      ]

      const columns = [
        { key: 'content', header: 'Content' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('Content\n"Line 1\nLine 2"')
    })

    it('should handle values with quotes by escaping them', () => {
      const data = [
        { message: 'He said "Hello"' },
      ]

      const columns = [
        { key: 'message', header: 'Message' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('Message\n"He said ""Hello"""')
    })

    it('should handle nested object properties', () => {
      const data = [
        { id: 1, user: { name: 'John', email: 'john@example.com' } },
      ]

      const columns = [
        { key: 'id', header: 'ID' },
        { key: 'user.name', header: 'User Name' },
        { key: 'user.email', header: 'Email' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('ID,User Name,Email\n1,John,john@example.com')
    })

    it('should handle null and undefined values', () => {
      const data = [
        { id: 1, name: null, age: undefined },
      ]

      const columns = [
        { key: 'id', header: 'ID' },
        { key: 'name', header: 'Name' },
        { key: 'age', header: 'Age' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('ID,Name,Age\n1,,')
    })

    it('should return empty string for empty data', () => {
      const result = convertToCSV([], [])

      expect(result).toBe('')
    })

    it('should return empty string for null data', () => {
      const result = convertToCSV(null, [])

      expect(result).toBe('')
    })
  })

  describe('downloadCSV', () => {
    it('should create download link and trigger click', () => {
      const mockLink = {
        href: '',
        download: '',
        style: {},
        click: clickSpy,
      }

      createElementSpy.mockReturnValue(mockLink)

      downloadCSV('test,csv,data', 'test.csv')

      expect(global.Blob).toHaveBeenCalledWith(
        ['test,csv,data'],
        { type: 'text/csv;charset=utf-8;' }
      )

      expect(global.URL.createObjectURL).toHaveBeenCalled()
      expect(mockLink.href).toBe('blob:mock-url')
      expect(mockLink.download).toBe('test.csv')
      expect(appendChildSpy).toHaveBeenCalledWith(mockLink)
      expect(clickSpy).toHaveBeenCalled()
      expect(removeChildSpy).toHaveBeenCalledWith(mockLink)
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })

    it('should handle IE 10+ with msSaveBlob', () => {
      const mockMsSaveBlob = vi.fn()
      navigator.msSaveBlob = mockMsSaveBlob

      downloadCSV('test,data', 'test.csv')

      expect(mockMsSaveBlob).toHaveBeenCalledWith(
        expect.objectContaining({
          content: ['test,data'],
          options: { type: 'text/csv;charset=utf-8;' },
        }),
        'test.csv'
      )

      delete navigator.msSaveBlob
    })
  })

  describe('exportModerationQueue', () => {
    beforeEach(() => {
      const mockLink = {
        href: '',
        download: '',
        style: {},
        click: clickSpy,
      }
      createElementSpy.mockReturnValue(mockLink)
    })

    it('should export queue items with correct columns', () => {
      const queueItems = [
        {
          id: 1,
          content_type: 'post',
          created_at: '2025-10-15T10:00:00Z',
          author: { username: 'user1', trust_level: { level: 0 } },
          priority_score: 5,
          flags_count: 2,
          content: 'Test content',
        },
      ]

      exportModerationQueue(queueItems, {})

      expect(global.Blob).toHaveBeenCalled()
      const csvContent = global.Blob.mock.calls[0][0][0]

      expect(csvContent).toContain('ID,Content Type,Created At')
      expect(csvContent).toContain('1,post')
      expect(csvContent).toContain('user1')
      expect(csvContent).toContain('Test content')
    })

    it('should format dates in queue export', () => {
      const queueItems = [
        {
          id: 1,
          content_type: 'post',
          created_at: '2025-10-15T14:30:00Z',
          author: { username: 'user1', trust_level: { level: 0 } },
          priority_score: 5,
          flags_count: 0,
          content: 'Test',
        },
      ]

      exportModerationQueue(queueItems, {})

      const csvContent = global.Blob.mock.calls[0][0][0]
      // Should contain formatted date (not exact format but should be readable)
      expect(csvContent).toMatch(/\d{1,2}\/\d{1,2}\/\d{4}/)
    })

    it('should include filter in filename', () => {
      const queueItems = [
        {
          id: 1,
          content_type: 'post',
          created_at: '2025-10-15T10:00:00Z',
          author: { username: 'user1', trust_level: { level: 0 } },
          priority_score: 5,
          flags_count: 0,
          content: 'Test',
        },
      ]

      exportModerationQueue(queueItems, { contentType: 'posts' })

      // Access mock results AFTER calling the function
      const mockLink = createElementSpy.mock.results[0].value
      expect(mockLink.download).toMatch(/moderation_queue_posts_\d{4}-\d{2}-\d{2}\.csv/)
    })

    it('should truncate content preview to 100 characters', () => {
      const longContent = 'a'.repeat(200)
      const queueItems = [
        {
          id: 1,
          content_type: 'post',
          created_at: '2025-10-15T10:00:00Z',
          author: { username: 'user1', trust_level: { level: 0 } },
          priority_score: 5,
          flags_count: 0,
          content: longContent,
        },
      ]

      exportModerationQueue(queueItems, {})

      const csvContent = global.Blob.mock.calls[0][0][0]
      // Content should be truncated to 100 chars
      expect(csvContent).toContain('a'.repeat(100))
      expect(csvContent).not.toContain('a'.repeat(101))
    })
  })

  describe('exportModerationAnalytics', () => {
    beforeEach(() => {
      const mockLink = {
        href: '',
        download: '',
        style: {},
        click: clickSpy,
      }
      createElementSpy.mockReturnValue(mockLink)
    })

    it('should export analytics with multiple sections', () => {
      const analytics = {
        total_reviews: 150,
        approval_rate: 75.5,
        avg_response_time: '2h 30m',
        pending_items: 12,
        total_reviews_trend: 15,
        approval_rate_trend: -5.2,
        by_content_type: {
          posts: 85,
          topics: 45,
        },
        daily_activity: [
          { date: '2025-10-15', approved: 10, rejected: 5, total: 15 },
        ],
        top_moderators: [
          { username: 'mod1', reviews: 75, approved: 60, rejected: 15, approval_rate: 80 },
        ],
      }

      exportModerationAnalytics(analytics, 7)

      expect(global.Blob).toHaveBeenCalled()
      const csvContent = global.Blob.mock.calls[0][0][0]

      // Should contain summary section
      expect(csvContent).toContain('# Moderation Analytics Summary')
      expect(csvContent).toContain('# Period: Last 7 days')

      // Should contain metrics
      expect(csvContent).toContain('Total Reviews')
      expect(csvContent).toContain('150')

      // Should contain content type breakdown
      expect(csvContent).toContain('# Content Type Breakdown')
      expect(csvContent).toContain('posts')
      expect(csvContent).toContain('85')

      // Should contain daily activity
      expect(csvContent).toContain('# Daily Activity')
      expect(csvContent).toContain('2025-10-15')

      // Should contain top moderators
      expect(csvContent).toContain('# Top Moderators')
      expect(csvContent).toContain('mod1')
    })

    it('should format trends correctly', () => {
      const analytics = {
        total_reviews: 150,
        total_reviews_trend: 15,
        approval_rate: 75.5,
        approval_rate_trend: -5.2,
        avg_response_time: '2h 30m',
        pending_items: 12,
      }

      exportModerationAnalytics(analytics, 7)

      const csvContent = global.Blob.mock.calls[0][0][0]

      expect(csvContent).toContain('+15%')
      expect(csvContent).toContain('-5.2%')
    })

    it('should calculate content type percentages', () => {
      const analytics = {
        total_reviews: 100,
        by_content_type: {
          posts: 60,
          topics: 40,
        },
      }

      exportModerationAnalytics(analytics, 7)

      const csvContent = global.Blob.mock.calls[0][0][0]

      expect(csvContent).toContain('60.0%')
      expect(csvContent).toContain('40.0%')
    })

    it('should include time range in filename', () => {
      const analytics = { total_reviews: 100 }

      exportModerationAnalytics(analytics, 30)

      // Access mock results AFTER calling the function
      const mockLink = createElementSpy.mock.results[0].value
      expect(mockLink.download).toMatch(/moderation_analytics_30days_\d{4}-\d{2}-\d{2}\.csv/)
    })

    it('should handle empty analytics sections gracefully', () => {
      const analytics = {
        total_reviews: 0,
        by_content_type: null,
        daily_activity: null,
        top_moderators: null,
      }

      exportModerationAnalytics(analytics, 7)

      expect(global.Blob).toHaveBeenCalled()
      const csvContent = global.Blob.mock.calls[0][0][0]

      // Should still have summary
      expect(csvContent).toContain('# Moderation Analytics Summary')
      expect(csvContent).toContain('Total Reviews')
    })

    it('should return early if analytics is null', () => {
      exportModerationAnalytics(null, 7)

      expect(global.Blob).not.toHaveBeenCalled()
    })

    it('should return early if analytics is undefined', () => {
      exportModerationAnalytics(undefined, 7)

      expect(global.Blob).not.toHaveBeenCalled()
    })
  })

  describe('formatDateForExport', () => {
    it('should format date string correctly', () => {
      const result = formatDateForExport('2025-10-15T14:30:00Z')

      // Check date format (MM/DD/YYYY or similar)
      expect(result).toMatch(/10\/15\/2025/)
      // Check time is included (don't check exact timezone as it depends on system)
      expect(result).toMatch(/\d{1,2}:\d{2}/)
    })

    it('should format Date object correctly', () => {
      const date = new Date('2025-10-15T14:30:00Z')
      const result = formatDateForExport(date)

      expect(result).toMatch(/2025/)
    })

    it('should handle null date', () => {
      const result = formatDateForExport(null)

      expect(result).toBe('')
    })

    it('should handle undefined date', () => {
      const result = formatDateForExport(undefined)

      expect(result).toBe('')
    })

    it('should handle invalid date', () => {
      const result = formatDateForExport('invalid-date')

      expect(result).toContain('Invalid Date')
    })
  })

  describe('Edge Cases', () => {
    beforeEach(() => {
      const mockLink = {
        href: '',
        download: '',
        style: {},
        click: clickSpy,
      }
      createElementSpy.mockReturnValue(mockLink)
    })

    it('should handle missing nested properties gracefully', () => {
      const data = [
        { id: 1, author: null },
      ]

      const columns = [
        { key: 'id', header: 'ID' },
        { key: 'author.username', header: 'Username' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toBe('ID,Username\n1,')
    })

    it('should handle very long strings', () => {
      const longString = 'a'.repeat(10000)
      const data = [{ content: longString }]
      const columns = [{ key: 'content', header: 'Content' }]

      const result = convertToCSV(data, columns)

      expect(result).toContain(longString)
    })

    it('should handle special characters in content', () => {
      const data = [
        { content: 'Test\r\nWith\tTabs' },
      ]

      const columns = [
        { key: 'content', header: 'Content' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toContain('Test')
    })

    it('should handle unicode characters', () => {
      const data = [
        { name: '日本語', emoji: '😀' },
      ]

      const columns = [
        { key: 'name', header: 'Name' },
        { key: 'emoji', header: 'Emoji' },
      ]

      const result = convertToCSV(data, columns)

      expect(result).toContain('日本語')
      expect(result).toContain('😀')
    })
  })
})
