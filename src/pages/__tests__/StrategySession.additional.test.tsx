import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StrategySession from '@/pages/StrategySession'

const apiBase = 'http://localhost:8000'

describe('StrategySession booking flow - additional tests', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockImplementation((input: any, init?: any) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/appointments/availability')) {
        return Promise.resolve(new Response(JSON.stringify({ success: true, slots: [
          { start_time: new Date().toISOString(), end_time: new Date(Date.now()+60*60*1000).toISOString(), duration_minutes: 60, available: true }
        ] }), { status: 200 })) as any
      }
      if (url.includes('/api/appointments/book')) {
        return Promise.resolve(new Response(JSON.stringify({ success: true, appointment_id: 'apt_1' }), { status: 200 })) as any
      }
      return Promise.resolve(new Response('{}', { status: 200 })) as any
    })
  })

  it('shows validation errors for required fields', async () => {
    render(
      <MemoryRouter>
        <StrategySession />
      </MemoryRouter>
    )

    // Try to submit without filling form
    const continueButton = screen.getByRole('button', { name: /Continue to Select Time/i })
    fireEvent.click(continueButton)

    // Should stay on form and show validation errors
    await waitFor(() => expect(screen.getByText(/Please fill in this field/i)).toBeInTheDocument())
  })

  it('handles booking API errors gracefully', async () => {
    // Mock API to return error
    vi.spyOn(global, 'fetch').mockImplementationOnce((input: any) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/appointments/book')) {
        return Promise.resolve(new Response('Internal Server Error', { status: 500 })) as any
      }
      if (url.includes('/api/appointments/availability')) {
        return Promise.resolve(new Response(JSON.stringify({ success: true, slots: [
          { start_time: new Date().toISOString(), end_time: new Date(Date.now()+60*60*1000).toISOString(), duration_minutes: 60, available: true }
        ] }), { status: 200 })) as any
      }
      return Promise.resolve(new Response('{}', { status: 200 })) as any
    })

    render(
      <MemoryRouter>
        <StrategySession />
      </MemoryRouter>
    )

    // Fill form
    fireEvent.change(screen.getByPlaceholderText('First Name'), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByPlaceholderText('Last Name'), { target: { value: 'Lovelace' } })
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'ada@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('Company Name'), { target: { value: 'Analytical' } })
    fireEvent.change(screen.getByPlaceholderText('Phone Number'), { target: { value: '+44' } })
    fireEvent.change(screen.getByPlaceholderText('What are your main business goals for the next 12 months?'), { target: { value: 'Grow revenue' } })
    fireEvent.change(screen.getByRole('combobox', { name: /Monthly Budget Range/i }), { target: { value: '1k-5k' } })
    fireEvent.change(screen.getByRole('combobox', { name: /Timeline/i }), { target: { value: '3-months' } })

    fireEvent.click(screen.getByRole('button', { name: /Continue to Select Time/i }))

    await waitFor(() => expect(screen.getByText(/Select Your Time/i)).toBeInTheDocument())

    // Choose time slot
    const timeButtons = await screen.findAllByRole('button')
    const timeSlotButton = timeButtons.find(b => /AM|PM|\d{1,2}:\d{2}/.test(b.textContent || ''))
    if (timeSlotButton) {
      fireEvent.click(timeSlotButton)
    }

    // Try to book
    const confirmBtn = screen.getByRole('button', { name: /Confirm Appointment/i })
    fireEvent.click(confirmBtn)

    // Should show error toast
    await waitFor(() => expect(screen.getByText(/Booking Failed/i)).toBeInTheDocument())
  })

  it('resets form after successful booking', async () => {
    render(
      <MemoryRouter>
        <StrategySession />
      </MemoryRouter>
    )

    // Fill form
    fireEvent.change(screen.getByPlaceholderText('First Name'), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByPlaceholderText('Last Name'), { target: { value: 'Lovelace' } })
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'ada@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('Company Name'), { target: { value: 'Analytical' } })
    fireEvent.change(screen.getByPlaceholderText('Phone Number'), { target: { value: '+44' } })
    fireEvent.change(screen.getByPlaceholderText('What are your main business goals for the next 12 months?'), { target: { value: 'Grow revenue' } })
    fireEvent.change(screen.getByRole('combobox', { name: /Monthly Budget Range/i }), { target: { value: '1k-5k' } })
    fireEvent.change(screen.getByRole('combobox', { name: /Timeline/i }), { target: { value: '3-months' } })

    fireEvent.click(screen.getByRole('button', { name: /Continue to Select Time/i }))

    await waitFor(() => expect(screen.getByText(/Select Your Time/i)).toBeInTheDocument())

    // Choose time slot
    const timeButtons = await screen.findAllByRole('button')
    const timeSlotButton = timeButtons.find(b => /AM|PM|\d{1,2}:\d{2}/.test(b.textContent || ''))
    if (timeSlotButton) {
      fireEvent.click(timeSlotButton)
    }

    // Book appointment
    const confirmBtn = screen.getByRole('button', { name: /Confirm Appointment/i })
    fireEvent.click(confirmBtn)

    // Should show success toast and reset form
    await waitFor(() => expect(screen.getByText(/Appointment Booked Successfully!/i)).toBeInTheDocument())
    await waitFor(() => expect(screen.getByText(/Book Your Free Session/i)).toBeInTheDocument())
  })
})