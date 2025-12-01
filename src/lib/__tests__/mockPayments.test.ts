import { describe, it, expect, vi } from 'vitest'
import { MockPaymentGateway, createMockCheckoutSession } from '@/lib/mockPayments'

describe('MockPaymentGateway', () => {
  it('creates a checkout session with valid parameters', async () => {
    const req = {
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
      mode: 'subscription' as const,
      metadata: { package_id: 'pkg_123' }
    }

    const result = await MockPaymentGateway.createCheckoutSession(req)
    
    expect(result.id).toMatch(/^mock_session_\d+$/)
    expect(result.url).toContain('https://example.com/success')
    expect(result.url).toContain('session_id=')
    expect(result.url).toContain('mock_payment=true')
  })

  it('throws error when success_url is missing', async () => {
    const req = {
      cancel_url: 'https://example.com/cancel'
    }

    await expect(MockPaymentGateway.createCheckoutSession(req))
      .rejects
      .toThrow('success_url is required')
  })

  it('throws error when cancel_url is missing', async () => {
    const req = {
      success_url: 'https://example.com/success'
    }

    await expect(MockPaymentGateway.createCheckoutSession(req))
      .rejects
      .toThrow('cancel_url is required')
  })

  it('simulates payment result', async () => {
    const result = await MockPaymentGateway.simulatePaymentResult('test_session_id')
    
    expect(result).toHaveProperty('success')
    expect(result).toHaveProperty('message')
    expect(typeof result.success).toBe('boolean')
    expect(typeof result.message).toBe('string')
  })
})

describe('createMockCheckoutSession', () => {
  it('falls back to mock gateway when real gateway fails', async () => {
    // Mock fetch to simulate real gateway failure
    vi.spyOn(global, 'fetch').mockImplementationOnce(() => {
      return Promise.resolve(new Response('Service Unavailable', { status: 503 })) as any
    })

    const req = {
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel'
    }

    const result = await createMockCheckoutSession(req)
    
    expect(result.id).toMatch(/^mock_session_\d+$/)
    expect(result.url).toContain('https://example.com/success')
  })

  it('throws error when both real and mock gateways fail', async () => {
    // Mock fetch to simulate real gateway failure
    vi.spyOn(global, 'fetch').mockImplementationOnce(() => {
      return Promise.resolve(new Response('Service Unavailable', { status: 503 })) as any
    })

    // Mock MockPaymentGateway to also fail
    vi.spyOn(MockPaymentGateway, 'createCheckoutSession').mockImplementationOnce(() => {
      throw new Error('Mock gateway also failed')
    })

    const req = {
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel'
    }

    await expect(createMockCheckoutSession(req))
      .rejects
      .toThrow('Mock gateway also failed')
  })
})