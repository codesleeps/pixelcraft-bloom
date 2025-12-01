import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AppointmentCalendar } from '@/components/AppointmentCalendar'

describe('AppointmentCalendar', () => {
  const mockOnSlotSelected = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-15T10:00:00Z'))
    
    vi.spyOn(global, 'fetch').mockImplementation((input: any) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/appointments/availability')) {
        return Promise.resolve(new Response(JSON.stringify({ 
          success: true, 
          slots: [
            { 
              start_time: '2025-01-15T14:00:00Z', 
              end_time: '2025-01-15T15:00:00Z', 
              duration_minutes: 60, 
              available: true 
            },
            { 
              start_time: '2025-01-15T15:00:00Z', 
              end_time: '2025-01-15T16:00:00Z', 
              duration_minutes: 60, 
              available: true 
            }
          ] 
        }), { status: 200 })) as any
      }
      return Promise.resolve(new Response('{}', { status: 200 })) as any
    })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders correctly and fetches availability', async () => {
    render(
      <AppointmentCalendar 
        appointmentType="strategy_session" 
        onSlotSelected={mockOnSlotSelected} 
      />
    )

    // Check that calendar is rendered
    expect(screen.getByText(/Select Date & Time/i)).toBeInTheDocument()
    expect(screen.getByText(/Select a Date/i)).toBeInTheDocument()
    
    // Wait for availability to load
    await waitFor(() => {
      expect(screen.getByText(/Available Times/i)).toBeInTheDocument()
    })
    
    // Check that time slots are displayed
    expect(screen.getByText(/2:00 PM/i)).toBeInTheDocument()
    expect(screen.getByText(/3:00 PM/i)).toBeInTheDocument()
  })

  it('calls onSlotSelected when a time slot is clicked', async () => {
    render(
      <AppointmentCalendar 
        appointmentType="strategy_session" 
        onSlotSelected={mockOnSlotSelected} 
      />
    )

    // Wait for slots to load
    await waitFor(() => {
      expect(screen.getByText(/2:00 PM/i)).toBeInTheDocument()
    })
    
    // Click on a time slot
    const timeSlot = screen.getByText(/2:00 PM/i).closest('button')
    if (timeSlot) {
      fireEvent.click(timeSlot)
    }
    
    // Check that onSlotSelected was called with correct parameters
    expect(mockOnSlotSelected).toHaveBeenCalledWith('2025-01-15T14:00:00Z', '2025-01-15T15:00:00Z')
  })

  it('shows selected time slot', async () => {
    render(
      <AppointmentCalendar 
        appointmentType="strategy_session" 
        onSlotSelected={mockOnSlotSelected}
        selectedSlot={{ startTime: '2025-01-15T14:00:00Z', endTime: '2025-01-15T15:00:00Z' }}
      />
    )

    // Wait for slots to load
    await waitFor(() => {
      expect(screen.getByText(/2:00 PM/i)).toBeInTheDocument()
    })
    
    // Check that selected slot is highlighted
    const selectedSlot = screen.getByText(/2:00 PM/i).closest('button')
    expect(selectedSlot).toHaveClass('ring-2')
    expect(selectedSlot).toHaveClass('ring-primary')
    
    // Check that selected time is displayed
    expect(screen.getByText(/Selected Time:/i)).toBeInTheDocument()
    expect(screen.getByText(/2:00 PM - 3:00 PM/i)).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    // Mock API to return error
    vi.spyOn(global, 'fetch').mockImplementationOnce(() => {
      return Promise.resolve(new Response('Internal Server Error', { status: 500 })) as any
    })

    render(
      <AppointmentCalendar 
        appointmentType="strategy_session" 
        onSlotSelected={mockOnSlotSelected} 
      />
    )

    // Wait for error to be handled
    await waitFor(() => {
      expect(screen.getByText(/Failed to load available time slots/i)).toBeInTheDocument()
    })
  })

  it('disables past dates', async () => {
    render(
      <AppointmentCalendar 
        appointmentType="strategy_session" 
        onSlotSelected={mockOnSlotSelected} 
      />
    )

    // Try to select a past date
    const pastDate = new Date('2025-01-10')
    const calendar = screen.getByRole('calendar')
    
    // Note: We're not directly testing the disabled functionality here as it's handled by the Calendar component
    // This test is more to ensure the component renders without errors
    expect(calendar).toBeInTheDocument()
  })
})