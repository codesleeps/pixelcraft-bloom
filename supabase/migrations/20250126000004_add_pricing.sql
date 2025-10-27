-- Create pricing packages table
create table pricing_packages (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  price_monthly numeric,
  price_yearly numeric,
  features jsonb,
  max_projects integer,
  max_team_members integer,
  priority integer default 0,
  is_active boolean default true,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Create pricing campaigns table
create table pricing_campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  code text unique,
  discount_type text check (discount_type in ('percentage', 'fixed')),
  discount_value numeric not null check (discount_value > 0),
  max_uses integer,
  used_count integer default 0,
  start_date timestamptz,
  end_date timestamptz,
  applicable_packages uuid[],
  is_active boolean default true,
  created_at timestamptz default now()
);

-- Create user subscriptions table
create table user_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  package_id uuid references pricing_packages(id) on delete set null,
  campaign_id uuid references pricing_campaigns(id) on delete set null,
  status text check (status in ('active', 'cancelled', 'expired', 'pending')),
  start_date timestamptz,
  end_date timestamptz,
  original_price numeric,
  discount_amount numeric default 0,
  final_price numeric,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Create indexes for better performance
create index idx_pricing_packages_active on pricing_packages (is_active, priority);
create index idx_pricing_campaigns_active on pricing_campaigns (is_active, code);
create index idx_pricing_campaigns_dates on pricing_campaigns (start_date, end_date);
create index idx_user_subscriptions_user on user_subscriptions (user_id);
create index idx_user_subscriptions_status on user_subscriptions (status);
create index idx_user_subscriptions_dates on user_subscriptions (start_date, end_date);

-- Insert sample pricing packages
insert into pricing_packages (name, description, price_monthly, price_yearly, features, max_projects, max_team_members, priority) values
('Starter', 'Perfect for small businesses and startups', 99, 990, '[
  {"name": "1 Project", "included": true},
  {"name": "5 Team Members", "included": true},
  {"name": "Basic AI Agents", "included": true},
  {"name": "Email Support", "included": true},
  {"name": "Analytics Dashboard", "included": true},
  {"name": "API Access", "included": false},
  {"name": "Custom Integrations", "included": false}
]', 1, 5, 1),

('Professional', 'Ideal for growing businesses', 299, 2990, '[
  {"name": "5 Projects", "included": true},
  {"name": "20 Team Members", "included": true},
  {"name": "Advanced AI Agents", "included": true},
  {"name": "Priority Support", "included": true},
  {"name": "Advanced Analytics", "included": true},
  {"name": "API Access", "included": true},
  {"name": "Custom Integrations", "included": false}
]', 5, 20, 2),

('Enterprise', 'For large organizations and enterprises', 599, 5990, '[
  {"name": "Unlimited Projects", "included": true},
  {"name": "Unlimited Team Members", "included": true},
  {"name": "Custom AI Models", "included": true},
  {"name": "Dedicated Support", "included": true},
  {"name": "Enterprise Analytics", "included": true},
  {"name": "API Access", "included": true},
  {"name": "Custom Integrations", "included": true}
]', null, null, 3);

-- Insert sample campaigns
insert into pricing_campaigns (name, code, discount_type, discount_value, max_uses, start_date, end_date, applicable_packages, is_active) values
('Launch Special', 'LAUNCH50', 'percentage', 50, 100, now(), now() + interval '3 months', (select array_agg(id) from pricing_packages where is_active = true), true),
('Annual Discount', 'ANNUAL20', 'percentage', 20, null, now(), now() + interval '1 year', (select array_agg(id) from pricing_packages where is_active = true), true),
('Holiday Sale', 'HOLIDAY30', 'percentage', 30, 50, now(), now() + interval '1 month', (select array_agg(id) from pricing_packages where is_active = true), true);