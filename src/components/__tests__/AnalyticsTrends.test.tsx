import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { AnalyticsTrends } from '@/components/AnalyticsTrends'

// Mock Supabase
vi.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: 'test-token' } },
        error: null
      })
    }
  }
}))

describe('AnalyticsTrends', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock fetch API
    vi.spyOn(global, 'fetch').mockImplementation((input: any) => {
      const url = typeof input === 'string' ? input : input.toString()
      
      if (url.includes('/api/analytics/leads/trends')) {
        return Promise.resolve(new Response(JSON.stringify({
          data: [
            { date: '2025-01-01', value: 10 },
            { date: '2025-01-02', value: 15 },
            { date: '2025-01-03', value: 12 }
          ]
        }), { status: 200 })) as any
      }
      
      if (url.includes('/api/analytics/conversations/trends')) {
        return Promise.resolve(new Response(JSON.stringify({
          data: [
            { date: '2025-01-01', value: 5 },
            { date: '2025-01-02', value: 8 },
            { date: '2025-01-03', value: 6 }
          ]
        }), { status: 200 })) as any
      }
      
      if (url.includes('/api/analytics/revenue/subscription-trends')) {
        return Promise.resolve(new Response(JSON.stringify({
          data: [
            { 
              period: '2025-01-01', 
              new_subscriptions: 3, 
              cancelled_subscriptions: 1, 
              net_change: 2, 
              cumulative_active: 10 
            },
            { 
              period: '2025-01-02', 
              new_subscriptions: 2, 
              cancelled_subscriptions: 0, 
              net_change: 2, 
              cumulative_active: 12 
            }
          ]
        }), { status: 200 })) as any
      }
      
      if (url.includes('/api/analytics/revenue/by-package')) {
        return Promise.resolve(new Response(JSON.stringify([
          { 
            package_id: 'pkg_1', 
            package_name: 'Basic', 
            subscription_count: 15, 
            total_revenue: 1500, 
            avg_revenue_per_subscription: 100 
          },
          { 
            package_id: 'pkg_2', 
            package_name: 'Premium', 
            subscription_count: 8, 
            total_revenue: 2400, 
            avg_revenue_per_subscription: 300 
          }
        ]), { status: 200 })) as any
      }
      
      return Promise.resolve(new Response('{}', { status: 200 })) as any
    })
  })

  it('renders loading state initially', () => {
    render(<AnalyticsTrends />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders analytics charts after data loads', async () => {
    render(<AnalyticsTrends />)
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
    
    // Check that chart titles are rendered
    expect(screen.getByText(/Lead Creation Trends/i)).toBeInTheDocument()
    expect(screen.getByText(/Conversation Trends/i)).toBeInTheDocument()
    expect(screen.getByText(/Subscription Trends/i)).toBeInTheDocument()
    expect(screen.getByText(/Revenue by Package/i)).toBeInTheDocument()
    
    // Check that data points are rendered in charts
    expect(screen.getByText(/Leads Created/i)).toBeInTheDocument()
    expect(screen.getByText(/Conversations/i)).toBeInTheDocument()
    expect(screen.getByText(/New Subscriptions/i)).toBeInTheDocument()
    expect(screen.getByText(/Total Revenue/i)).toBeInTheDocument()
  })

  it('handles API errors gracefully', async () => {
    // Mock API to return error
    vi.spyOn(global, 'fetch').mockImplementationOnce(() => {
      return Promise.resolve(new Response('Internal Server Error', { status: 500 })) as any
    })

    render(<AnalyticsTrends />)
    
    // Wait for error to be displayed
    await waitFor(() => {
      expect(screen.getByText(/Error Loading Analytics/i)).toBeInTheDocument()
    })
    
    // Check that error message is displayed
    expect(screen.getByText(/Failed to load analytics data/i)).toBeInTheDocument()
  })

  it('allows time range selection', async () => {
    render(<AnalyticsTrends />)
    
    // Wait for component to load
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument()
    })
    
    // Check that time range selector is present
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })
})