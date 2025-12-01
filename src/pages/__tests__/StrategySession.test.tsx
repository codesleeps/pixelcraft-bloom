import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import StrategySession from '@/pages/StrategySession'

const apiBase = 'http://localhost:8000'

describe('StrategySession booking flow', () => {
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

  it('navigates from form to calendar and books an appointment', async () => {
    render(
      <MemoryRouter>
        <StrategySession />
      </MemoryRouter>
    )

    fireEvent.change(screen.getByPlaceholderText('First Name'), { target: { value: 'Ada' } })
    fireEvent.change(screen.getByPlaceholderText('Last Name'), { target: { value: 'Lovelace' } })
    fireEvent.change(screen.getByPlaceholderText('Email Address'), { target: { value: 'ada@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('Company Name'), { target: { value: 'Analytical' } })
    fireEvent.change(screen.getByPlaceholderText('Phone Number'), { target: { value: '+44' } })

    fireEvent.click(screen.getByRole('button', { name: /Continue to Select Time/i }))

    await waitFor(() => expect(screen.getByText(/Select Your Time/i)).toBeInTheDocument())

    // choose first slot button if present
    const timeButtons = await screen.findAllByRole('button')
    fireEvent.click(timeButtons.find(b => /AM|PM|\d{1,2}:\d{2}/.test(b.textContent || ''))!)

    const confirmBtn = screen.getByRole('button', { name: /Confirm Appointment/i })
    fireEvent.click(confirmBtn)

    await waitFor(() => expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/appointments/book'), expect.any(Object)
    ))
  })
})
