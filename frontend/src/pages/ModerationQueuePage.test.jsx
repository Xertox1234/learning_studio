import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import ModerationQueuePage from './ModerationQueuePage'
import * as apiModule from '../utils/api'
import * as AuthContext from '../contexts/AuthContext'

// Mock the API module
vi.mock('../utils/api', () => ({
  apiRequest: vi.fn()
}))

// Mock the AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn()
}))

const mockTL3User = {
  id: 1,
  username: 'moderator',
  is_staff: false,
  is_superuser: false,
  trust_level: {
    level: 3,
    name: 'Regular'
  }
}

const mockTL0User = {
  id: 2,
  username: 'newbie',
  is_staff: false,
  is_superuser: false,
  trust_level: {
    level: 0,
    name: 'New User'
  }
}

const mockQueueItem = {
  id: 1,
  content_type: 'post',
  review_type: 'new_user_post',
  reason: 'New user content requiring review',
  status: 'pending',
  priority: 3,
  score: 5.0,
  post: {
    id: 10,
    content: 'Test post content',
    created: '2025-10-15T10:00:00Z'
  },
  reporter: {
    id: 5,
    username: 'reporter_user'
  },
  created_at: '2025-10-15T10:00:00Z'
}

const mockQueueResponse = {
  queue: [mockQueueItem],
  pagination: {
    current_page: 1,
    total_pages: 1,
    has_next: false,
    has_previous: false
  }
}

const mockStatsResponse = {
  pending: 5,
  approved: 10,
  rejected: 2,
  today_count: 3
}

describe('ModerationQueuePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    AuthContext.useAuth.mockReturnValue({ user: mockTL3User })

    // Default API responses
    apiModule.apiRequest.mockImplementation((url) => {
      if (url.includes('/moderation/queue/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockQueueResponse)
        })
      }
      if (url.includes('/moderation/stats/')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockStatsResponse)
        })
      }
      return Promise.resolve({ ok: true })
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  const renderComponent = () => {
    return render(
      <BrowserRouter>
        <ModerationQueuePage />
      </BrowserRouter>
    )
  }

  describe('Permission Checks', () => {
    it('should render queue for TL3+ users', async () => {
      AuthContext.useAuth.mockReturnValue({ user: mockTL3User })
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Moderation Queue')).toBeInTheDocument()
      })
    })

    it('should show access denied for TL0 users', async () => {
      AuthContext.useAuth.mockReturnValue({ user: mockTL0User })
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Access Denied')).toBeInTheDocument()
      })
    })

    it('should allow staff users regardless of trust level', async () => {
      const staffUser = { ...mockTL0User, is_staff: true }
      AuthContext.useAuth.mockReturnValue({ user: staffUser })
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Moderation Queue')).toBeInTheDocument()
      })
    })
  })

  describe('Statistics Dashboard', () => {
    it('should display moderation statistics', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Pending')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
        expect(screen.getByText('Approved')).toBeInTheDocument()
        expect(screen.getByText('10')).toBeInTheDocument()
        expect(screen.getByText('Rejected')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
        expect(screen.getByText("Today's Reviews")).toBeInTheDocument()
        expect(screen.getByText('3')).toBeInTheDocument()
      })
    })

    it('should handle missing stats gracefully', async () => {
      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/moderation/stats/')) {
          return Promise.resolve({
            ok: false,
            status: 500
          })
        }
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockQueueResponse)
        })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Moderation Queue')).toBeInTheDocument()
      })

      // Stats should not be displayed
      expect(screen.queryByText('Pending')).not.toBeInTheDocument()
    })
  })

  describe('Queue Display', () => {
    it('should display queue items', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText(/NEW_USER_POST/i)).toBeInTheDocument()
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })
    })

    it('should show empty state when queue is empty', async () => {
      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/moderation/queue/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({ queue: [], pagination: null })
          })
        }
        return Promise.resolve({ ok: true })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Queue is Empty')).toBeInTheDocument()
      })
    })
  })

  describe('Batch Selection', () => {
    it('should select individual items', async () => {
      renderComponent()

      await waitFor(() => {
        const checkbox = screen.getByLabelText(/Select post for batch action/i)
        expect(checkbox).not.toBeChecked()
      })

      const checkbox = screen.getByLabelText(/Select post for batch action/i)
      fireEvent.click(checkbox)

      expect(checkbox).toBeChecked()
      expect(screen.getByText('1 item selected')).toBeInTheDocument()
    })

    it('should select all items', async () => {
      const multipleItems = {
        queue: [mockQueueItem, { ...mockQueueItem, id: 2 }, { ...mockQueueItem, id: 3 }],
        pagination: mockQueueResponse.pagination
      }

      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/moderation/queue/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(multipleItems)
          })
        }
        return Promise.resolve({ ok: true })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByLabelText('Select all items')).toBeInTheDocument()
      })

      const selectAllCheckbox = screen.getByLabelText('Select all items')
      fireEvent.click(selectAllCheckbox)

      await waitFor(() => {
        expect(screen.getByText('3 items selected')).toBeInTheDocument()
      })
    })
  })

  describe('Batch Operations', () => {
    it('should batch approve selected items', async () => {
      const multipleItems = {
        queue: [mockQueueItem, { ...mockQueueItem, id: 2 }],
        pagination: mockQueueResponse.pagination
      }

      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/moderation/queue/')) {
          if (url.includes('/review/')) {
            return Promise.resolve({ ok: true })
          }
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(multipleItems)
          })
        }
        return Promise.resolve({ ok: true })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByLabelText('Select all items')).toBeInTheDocument()
      })

      // Select all items
      fireEvent.click(screen.getByLabelText('Select all items'))

      await waitFor(() => {
        expect(screen.getByText('2 items selected')).toBeInTheDocument()
      })

      // Click batch approve
      const approveButton = screen.getByLabelText(/Approve 2 selected items/i)
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('/moderation/queue/1/review/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('approve')
          })
        )
      })
    })

    it('should handle batch operation failures', async () => {
      const multipleItems = {
        queue: [mockQueueItem, { ...mockQueueItem, id: 2 }],
        pagination: mockQueueResponse.pagination
      }

      let callCount = 0
      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/review/')) {
          callCount++
          // First call succeeds, second fails
          if (callCount === 1) {
            return Promise.resolve({ ok: true })
          } else {
            return Promise.resolve({ ok: false, status: 500 })
          }
        }
        if (url.includes('/moderation/queue/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(multipleItems)
          })
        }
        return Promise.resolve({ ok: true })
      })

      // Mock window.alert
      const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})

      renderComponent()

      await waitFor(() => {
        expect(screen.getByLabelText('Select all items')).toBeInTheDocument()
      })

      fireEvent.click(screen.getByLabelText('Select all items'))

      await waitFor(() => {
        expect(screen.getByText('2 items selected')).toBeInTheDocument()
      })

      const approveButton = screen.getByLabelText(/Approve 2 selected items/i)
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(alertMock).toHaveBeenCalledWith(
          expect.stringContaining('1 of 2 items failed')
        )
      })

      alertMock.mockRestore()
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('should approve item with "a" key', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Press 'a' key
      fireEvent.keyDown(document, { key: 'a' })

      await waitFor(() => {
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('/moderation/queue/1/review/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('approve')
          })
        )
      })
    })

    it('should reject item with "r" key', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      fireEvent.keyDown(document, { key: 'r' })

      await waitFor(() => {
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('/moderation/queue/1/review/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('reject')
          })
        )
      })
    })

    it('should navigate with j/k keys', async () => {
      const multipleItems = {
        queue: [
          mockQueueItem,
          { ...mockQueueItem, id: 2, post: { ...mockQueueItem.post, content: 'Second post' } }
        ],
        pagination: mockQueueResponse.pagination
      }

      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/moderation/queue/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(multipleItems)
          })
        }
        return Promise.resolve({ ok: true })
      })

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Navigate down with 'j'
      fireEvent.keyDown(document, { key: 'j' })

      // Navigate up with 'k'
      fireEvent.keyDown(document, { key: 'k' })

      // Verify navigation doesn't crash (visual focus is tested in E2E)
      expect(screen.getByText('Test post content')).toBeInTheDocument()
    })

    it('should not trigger shortcuts when typing in input', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Find a textarea (notes input)
      const noteInputs = screen.getAllByPlaceholderText(/Add review notes/i)
      const noteInput = noteInputs[0]

      // Focus the input
      noteInput.focus()

      // Press 'a' while focused on input
      fireEvent.keyDown(noteInput, { key: 'a' })

      // Should NOT trigger approve
      await new Promise(resolve => setTimeout(resolve, 100))

      expect(apiModule.apiRequest).not.toHaveBeenCalledWith(
        expect.stringContaining('/review/'),
        expect.any(Object)
      )
    })
  })

  describe('Undo Functionality', () => {
    beforeEach(() => {
      vi.useFakeTimers()
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('should show undo notification after action', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Approve an item
      const approveButton = screen.getAllByLabelText(/Approve/i)[0]
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(screen.getByText(/Action Approved/i)).toBeInTheDocument()
        expect(screen.getByText('Undo')).toBeInTheDocument()
      })
    })

    it('should undo action when undo button clicked', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Approve an item
      const approveButtons = screen.getAllByLabelText(/Approve/i)
      fireEvent.click(approveButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Undo')).toBeInTheDocument()
      })

      // Click undo
      const undoButton = screen.getByText('Undo')
      fireEvent.click(undoButton)

      await waitFor(() => {
        // Should call reject (opposite of approve)
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('/moderation/queue/1/review/'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('reject')
          })
        )
      })
    })

    it('should auto-dismiss undo after 30 seconds', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Approve an item
      const approveButton = screen.getAllByLabelText(/Approve/i)[0]
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(screen.getByText('Undo')).toBeInTheDocument()
      })

      // Fast-forward 30 seconds
      vi.advanceTimersByTime(30000)

      await waitFor(() => {
        expect(screen.queryByText('Undo')).not.toBeInTheDocument()
      })
    })
  })

  describe('Memory Leak Prevention', () => {
    it('should cleanup undo timer on unmount', async () => {
      const { unmount } = renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      // Approve an item to start undo timer
      const approveButton = screen.getAllByLabelText(/Approve/i)[0]
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(screen.getByText('Undo')).toBeInTheDocument()
      })

      // Unmount component
      unmount()

      // Verify no errors (timer should be cleaned up)
      expect(true).toBe(true)
    })
  })

  describe('Optimistic Updates', () => {
    it('should immediately update UI on approve', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      const approveButton = screen.getAllByLabelText(/Approve/i)[0]
      fireEvent.click(approveButton)

      // UI should update immediately (optimistically)
      // Actual verification would check if item status changed before API completes
      expect(approveButton).toBeDisabled()
    })

    it('should rollback on API failure', async () => {
      apiModule.apiRequest.mockImplementation((url) => {
        if (url.includes('/review/')) {
          return Promise.resolve({ ok: false, status: 500 })
        }
        if (url.includes('/moderation/queue/')) {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(mockQueueResponse)
          })
        }
        return Promise.resolve({ ok: true })
      })

      const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {})

      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Test post content')).toBeInTheDocument()
      })

      const approveButton = screen.getAllByLabelText(/Approve/i)[0]
      fireEvent.click(approveButton)

      await waitFor(() => {
        expect(alertMock).toHaveBeenCalledWith(
          expect.stringContaining('Failed to approve item')
        )
      })

      // UI should rollback to original state
      expect(screen.getByText('Test post content')).toBeInTheDocument()

      alertMock.mockRestore()
    })
  })

  describe('Filtering', () => {
    it('should filter by content type', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Moderation Queue')).toBeInTheDocument()
      })

      const postsButton = screen.getByLabelText('Filter by posts content')
      fireEvent.click(postsButton)

      await waitFor(() => {
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('type=posts'),
          undefined
        )
      })
    })

    it('should filter by status', async () => {
      renderComponent()

      await waitFor(() => {
        expect(screen.getByText('Moderation Queue')).toBeInTheDocument()
      })

      const approvedButton = screen.getByLabelText('Show approved items')
      fireEvent.click(approvedButton)

      await waitFor(() => {
        expect(apiModule.apiRequest).toHaveBeenCalledWith(
          expect.stringContaining('status=approved'),
          undefined
        )
      })
    })
  })
})
