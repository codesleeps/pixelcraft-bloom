-- Add invoice and payment tracking fields to user_subscriptions
alter table user_subscriptions
  add column if not exists stripe_invoice_id text,
  add column if not exists latest_payment_intent_id text,
  add column if not exists last_payment_status text,
  add column if not exists last_payment_at timestamptz,
  add column if not exists last_payment_amount numeric,
  add column if not exists next_payment_attempt timestamptz,
  add column if not exists attempt_count integer default 0,
  add column if not exists billing_cycle_anchor timestamptz,
  add column if not exists pause_collection boolean,
  add column if not exists discount_code text;

