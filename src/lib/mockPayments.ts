// Mock payment gateway for testing purposes
export interface MockCheckoutSessionRequest {
  price_id?: string;
  mode?: 'subscription' | 'payment';
  success_url?: string;
  cancel_url?: string;
  customer_email?: string | null;
  metadata?: Record<string, any>;
}

export interface MockCheckoutSessionResponse {
  id: string;
  url: string;
}

export class MockPaymentGateway {
  private static sessionIdCounter = 1;

  static async createCheckoutSession(req: MockCheckoutSessionRequest): Promise<MockCheckoutSessionResponse> {
    // Validate required parameters
    if (!req.success_url) {
      throw new Error('success_url is required');
    }

    if (!req.cancel_url) {
      throw new Error('cancel_url is required');
    }

    // Generate a mock session ID
    const sessionId = `mock_session_${this.sessionIdCounter++}`;
    
    // Create a mock redirect URL that simulates the payment flow
    const mockUrl = new URL(req.success_url);
    mockUrl.searchParams.set('session_id', sessionId);
    mockUrl.searchParams.set('mock_payment', 'true');
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Simulate occasional failures for testing error handling
    if (Math.random() < 0.1) { // 10% failure rate
      throw new Error('Payment service temporarily unavailable. Please try again.');
    }

    return {
      id: sessionId,
      url: mockUrl.toString()
    };
  }

  static async simulatePaymentResult(sessionId: string): Promise<{ success: boolean; message: string }> {
    // Simulate payment processing
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Most payments succeed in the mock gateway
    const success = Math.random() > 0.2; // 80% success rate
    
    return {
      success,
      message: success 
        ? 'Payment processed successfully!' 
        : 'Payment failed. Please check your payment details and try again.'
    };
  }
}

// Enhanced payment functions with better error handling and UI states
export interface PaymentState {
  status: 'idle' | 'processing' | 'success' | 'failed' | 'cancelled';
  message: string;
  sessionId?: string;
}

export async function createMockCheckoutSession(req: MockCheckoutSessionRequest): Promise<MockCheckoutSessionResponse> {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  
  try {
    // Try real payment gateway first
    const res = await fetch(`${apiBase}/api/payments/create-checkout-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });

    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`Server responded with ${res.status}: ${detail || 'Unknown error'}`);
    }
    
    return res.json();
  } catch (error) {
    // Fallback to mock gateway if real one fails
    console.warn('Real payment gateway failed, falling back to mock gateway:', error);
    
    try {
      return await MockPaymentGateway.createCheckoutSession(req);
    } catch (mockError) {
      // Provide user-friendly error messages
      if (mockError instanceof TypeError && mockError.message.includes('fetch')) {
        throw new Error('Cannot connect to payment server. Please ensure the backend is running at ' + apiBase);
      }
      throw mockError;
    }
  }
}