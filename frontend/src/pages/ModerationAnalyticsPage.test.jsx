import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ModerationAnalyticsPage from './ModerationAnalyticsPage'
import { AuthProvider } from '../contexts/AuthContext'
import toast from 'react-hot-toast'

// Mock dependencies
vi.mock('../utils/api')
vi.mock('../utils/exportUtils')
vi.mock('react-hot-toast')

const { apiRequest } = await import('../utils/api')
const { exportModerationAnalytics } = await import('../utils/exportUtils')

// Mock data
const mockAnalytics = {
  total_reviews: 150,
  approval_rate: 75.5,
  avg_response_time: '2h 30m',
  pending_items: 12,
  trends: {
    total_reviews: 15,
    approval_rate: -5.2,
    avg_response_time: 10,
    pending_items: -20,
  },
  by_content_type: {
    posts: 85,
    topics: 45,
    users: 20,
  },
  top_moderators: [
    { id: 1, username: 'mod1', reviews: 75, approved: 60, rejected: 15, approval_rate: 80 },
    { id: 2, username: 'mod2', reviews: 45, approved: 35, rejected: 10, approval_rate: 77.8 },
    { id: 3, username: 'mod3', reviews: 30, approved: 20, rejected: 10, approval_rate: 66.7 },
  ],
  daily_activity: [
    { date: '2025-10-08', approved: 15, rejected: 5, total: 20 },
    { date: '2025-10-09', approved: 20, rejected: 8, total: 28 },
    { date: '2025-10-10', approved: 18, rejected: 3, total: 21 },
    { date: '2025-10-11', approved: 22, rejected: 6, total: 28 },
    { date: '2025-10-12', approved: 25, rejected: 4, total: 29 },
    { date: '2025-10-13', approved: 19, rejected: 7, total: 26 },
    { date: '2025-10-14', approved: 21, rejected: 5, total: 26 },
  ],
}

const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  trust_level: { level: 3, name: 'Regular' },
  is_staff: false,
  is_superuser: false,
}

const mockStaffUser = {
  id: 2,
  username: 'staffuser',
  email: 'staff@example.com',
  trust_level: { level: 0, name: 'New' },
  is_staff: true,
  is_superuser: false,
}

// Helper to render with providers
const renderWithProviders = (component, { user = mockUser } = {}) => {
  const mockAuthContext = {
    user,
    login: vi.fn(),
    logout: vi.fn(),
    loading: false,
  }

  return render(
    <BrowserRouter>
      <AuthProvider value={mockAuthContext}>
        {component}
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('ModerationAnalyticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    // Mock successful API response by default
    apiRequest.mockResolvedValue({
      ok: true,
      json: async () => mockAnalytics,
    })

    // Mock toast
    toast.error = vi.fn()
    toast.success = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Permission Checks', () => {
    it('should deny access to users below TL3', async () => {
      const lowTrustUser = {
        ...mockUser,
        trust_level: { level: 2, name: 'Member' },
        is_staff: false,
        is_superuser: false,
      }

      renderWithProviders(<ModerationAnalyticsPage />, { user: lowTrustUser })

      await waitFor(() => {
        expect(screen.getByText('Access Denied')).toBeInTheDocument()
        expect(screen.getByText(/Trust Level 3 or higher/)).toBeInTheDocument()
        expect(screen.getByText('Return to Forum')).toBeInTheDocument()
      })

      // Should not fetch analytics
      expect(apiRequest).not.toHaveBeenCalled()
    })

    it('should allow access to TL3+ users', async () => {
      renderWithProviders(<ModerationAnalyticsPage />, { user: mockUser })

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })

      expect(apiRequest).toHaveBeenCalledWith('/api/v1/moderation/analytics/?days=7')
    })

    it('should allow access to staff users regardless of trust level', async () => {
      renderWithProviders(<ModerationAnalyticsPage />, { user: mockStaffUser })

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })

      expect(apiRequest).toHaveBeenCalledWith('/api/v1/moderation/analytics/?days=7')
    })

    it('should allow access to superusers', async () => {
      const superuser = {
        ...mockUser,
        trust_level: { level: 0, name: 'New' },
        is_staff: false,
        is_superuser: true,
      }

      renderWithProviders(<ModerationAnalyticsPage />, { user: superuser })

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })
    })
  })

  describe('Data Fetching and Display', () => {
    it('should show loading state initially', () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument()
    })

    it('should fetch and display analytics data', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        // Check key metrics
        expect(screen.getByText('150')).toBeInTheDocument() // Total reviews
        expect(screen.getByText('75.5%')).toBeInTheDocument() // Approval rate
        expect(screen.getByText('2h 30m')).toBeInTheDocument() // Avg response time
        expect(screen.getByText('12')).toBeInTheDocument() // Pending items
      })
    })

    it('should display trend indicators', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('+15.0%')).toBeInTheDocument() // Positive trend
        expect(screen.getByText('-5.2%')).toBeInTheDocument() // Negative trend
      })
    })

    it('should display content type breakdown', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('Posts')).toBeInTheDocument()
        expect(screen.getByText('Topics')).toBeInTheDocument()
        expect(screen.getByText('Users')).toBeInTheDocument()
        expect(screen.getByText('85')).toBeInTheDocument()
        expect(screen.getByText('45')).toBeInTheDocument()
        expect(screen.getByText('20')).toBeInTheDocument()
      })
    })

    it('should display top moderators', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('mod1')).toBeInTheDocument()
        expect(screen.getByText('mod2')).toBeInTheDocument()
        expect(screen.getByText('mod3')).toBeInTheDocument()
        expect(screen.getByText('75 reviews')).toBeInTheDocument()
      })
    })

    it('should display daily activity chart', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        // Check for dates from daily activity
        expect(screen.getByText('Oct 08')).toBeInTheDocument()
        expect(screen.getByText('Oct 14')).toBeInTheDocument()
      })
    })

    it('should handle empty analytics data gracefully', async () => {
      const emptyAnalytics = {
        total_reviews: 0,
        approval_rate: 0,
        avg_response_time: 'N/A',
        pending_items: 0,
        by_content_type: {},
        top_moderators: [],
        daily_activity: [],
      }

      apiRequest.mockResolvedValue({
        ok: true,
        json: async () => emptyAnalytics,
      })

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument()
        expect(screen.getByText('N/A')).toBeInTheDocument()
      })
    })
  })

  describe('Time Range Selection', () => {
    it('should default to 7 days time range', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        const sevenDaysButton = screen.getByText('7 Days')
        expect(sevenDaysButton).toHaveClass('bg-blue-600')
      })

      expect(apiRequest).toHaveBeenCalledWith('/api/v1/moderation/analytics/?days=7')
    })

    it('should fetch new data when time range changes', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })

      // Click 30 days button
      const thirtyDaysButton = screen.getByText('30 Days')
      fireEvent.click(thirtyDaysButton)

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/api/v1/moderation/analytics/?days=30')
      })
    })

    it('should update active button when time range changes', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('7 Days')).toHaveClass('bg-blue-600')
      })

      // Change to 90 days
      const ninetyDaysButton = screen.getByText('90 Days')
      fireEvent.click(ninetyDaysButton)

      await waitFor(() => {
        expect(screen.getByText('90 Days')).toHaveClass('bg-blue-600')
        expect(screen.getByText('7 Days')).not.toHaveClass('bg-blue-600')
      })
    })
  })

  describe('Export Functionality', () => {
    it('should export analytics when export button is clicked', async () => {
      exportModerationAnalytics.mockImplementation(() => {})

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })

      const exportButton = screen.getByLabelText('Export analytics report to CSV')
      fireEvent.click(exportButton)

      expect(exportModerationAnalytics).toHaveBeenCalledWith(mockAnalytics, 7)
      expect(toast.success).toHaveBeenCalledWith('Analytics report exported successfully')
    })

    it('should show error toast if no analytics data to export', async () => {
      apiRequest.mockResolvedValue({
        ok: true,
        json: async () => null,
      })

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        const exportButton = screen.getByLabelText('Export analytics report to CSV')
        expect(exportButton).toBeDisabled()
      })
    })

    it('should export with correct time range parameter', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText('Moderation Analytics')).toBeInTheDocument()
      })

      // Change to 30 days
      fireEvent.click(screen.getByText('30 Days'))

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledWith('/api/v1/moderation/analytics/?days=30')
      })

      // Export with 30 days
      const exportButton = screen.getByLabelText('Export analytics report to CSV')
      fireEvent.click(exportButton)

      expect(exportModerationAnalytics).toHaveBeenCalledWith(expect.anything(), 30)
    })
  })

  describe('Error Handling', () => {
    it('should display error message when fetch fails', async () => {
      apiRequest.mockResolvedValue({
        ok: false,
        status: 500,
      })

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch analytics/)).toBeInTheDocument()
      })
    })

    it('should display permission error for 403 responses', async () => {
      apiRequest.mockResolvedValue({
        ok: false,
        status: 403,
      })

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText(/do not have permission/)).toBeInTheDocument()
      })
    })

    it('should handle network errors gracefully', async () => {
      apiRequest.mockRejectedValue(new Error('Network error'))

      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(screen.getByText(/Failed to load analytics/)).toBeInTheDocument()
      })
    })
  })

  describe('Navigation', () => {
    it('should have a back to queue link', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        const backLink = screen.getByText('Back to Queue')
        expect(backLink).toBeInTheDocument()
        expect(backLink.closest('a')).toHaveAttribute('href', '/forum/moderation/queue')
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA labels on export button', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        const exportButton = screen.getByLabelText('Export analytics report to CSV')
        expect(exportButton).toBeInTheDocument()
        expect(exportButton).toHaveAttribute('title', 'Export analytics report to CSV')
      })
    })

    it('should have role group for time range selector', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        const timeRangeButtons = screen.getAllByRole('button', { name: /Days/ })
        expect(timeRangeButtons).toHaveLength(3)
      })
    })
  })

  describe('Performance', () => {
    it('should not refetch data unnecessarily', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledTimes(1)
      })

      // Multiple re-renders shouldn't cause extra fetches
      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledTimes(1)
      })
    })

    it('should refetch only when time range changes', async () => {
      renderWithProviders(<ModerationAnalyticsPage />)

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledTimes(1)
      })

      // Change time range
      fireEvent.click(screen.getByText('30 Days'))

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledTimes(2)
      })

      // Change back
      fireEvent.click(screen.getByText('7 Days'))

      await waitFor(() => {
        expect(apiRequest).toHaveBeenCalledTimes(3)
      })
    })
  })
})
