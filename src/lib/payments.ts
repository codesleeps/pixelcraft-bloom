export interface CheckoutSessionRequest {
  price_id?: string;
  mode?: 'subscription' | 'payment';
  success_url?: string;
  cancel_url?: string;
  customer_email?: string | null;
  metadata?: Record<string, any>;
}

export interface CheckoutSessionResponse {
  id: string;
  url: string;
}

export interface PaymentState {
  status: 'idle' | 'processing' | 'success' | 'failed' | 'cancelled';
  message: string;
  sessionId?: string;
}

export async function createCheckoutSession(req: CheckoutSessionRequest): Promise<CheckoutSessionResponse> {
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  
  try {
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
    // Provide user-friendly error messages
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to payment server. Please ensure the backend is running at ' + apiBase);
    }
    throw error;
  }
}

// Enhanced function with better error handling and UI state management
export async function createCheckoutSessionWithState(req: CheckoutSessionRequest): Promise<PaymentState> {
  try {
    // Validate required parameters
    if (!req.success_url) {
      return {
        status: 'failed',
        message: 'Success URL is required'
      };
    }

    if (!req.cancel_url) {
      return {
        status: 'failed',
        message: 'Cancel URL is required'
      };
    }

    const response = await createCheckoutSession(req);
    
    return {
      status: 'success',
      message: 'Redirecting to payment gateway...',
      sessionId: response.id
    };
  } catch (error) {
    console.error('Payment error:', error);
    
    return {
      status: 'failed',
      message: error instanceof Error ? error.message : 'An unexpected error occurred during payment processing'
    };
  }
}