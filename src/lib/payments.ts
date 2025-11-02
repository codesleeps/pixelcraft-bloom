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
  const res = await fetch(`${apiBase}/api/payments/create-checkout-session`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`Failed to create checkout session: ${detail}`);
  }
  return res.json();
}

