-- Add Stripe-related fields to user_subscriptions for lifecycle tracking
alter table user_subscriptions
  add column if not exists stripe_customer_id text,
  add column if not exists stripe_subscription_id text,
  add column if not exists stripe_price_id text,
  add column if not exists stripe_status text,
  add column if not exists cancel_at_period_end boolean,
  add column if not exists canceled_at timestamptz,
  add column if not exists current_period_start timestamptz,
  add column if not exists current_period_end timestamptz,
  add column if not exists currency text,
  add column if not exists mode text;

-- Index for quick lookup by Stripe subscription id
create index if not exists idx_user_subscriptions_stripe_sub_id on user_subscriptions (stripe_subscription_id);

