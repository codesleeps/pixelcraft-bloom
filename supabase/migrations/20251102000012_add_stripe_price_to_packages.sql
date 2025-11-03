-- Add stripe_price_id to pricing_packages for mapping from Stripe to internal packages
alter table pricing_packages
  add column if not exists stripe_price_id text;

create unique index if not exists idx_pricing_packages_stripe_price on pricing_packages (stripe_price_id);

