export interface CheckoutSessionRequest {
  price_id?: string;
  mode?: 'subscription' | 'payment';
  success_url?: string;
  cancel_url?: string;
  customer_email?: string | null;
  metadata?: Record<string, any>;
}

export async function createCheckoutSession(req: CheckoutSessionRequest) {
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
