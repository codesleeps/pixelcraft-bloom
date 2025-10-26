-- Migration for PixelCraft AI features - October 2025
-- Tables: leads, conversations, messages, agent_logs, appointments, service_recommendations, generated_content

-- Helper function to automatically update updated_at timestamps
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-----------------------------------------------
-- Drop tables if they exist (for clean migrations)
-----------------------------------------------

drop table if exists generated_content;
drop table if exists service_recommendations;
drop table if exists appointments;
drop table if exists agent_logs;
drop table if exists messages;
drop table if exists conversations;
drop table if exists leads;

-----------------------------------------------
-- Create tables with proper constraints
-----------------------------------------------

-- Leads table - core prospect information
create table leads (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  first_name text,
  last_name text,
  company text,
  phone text,
  website text,
  user_id uuid references auth.users(id),
  lead_score integer check (lead_score >= 0 and lead_score <= 100),
  lead_status text check (lead_status in ('new', 'contacted', 'qualified', 'opportunity', 'customer', 'lost')) default 'new',
  source text not null,
  services_interested text[],
  budget_range text,
  timeline text,
  notes text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  deleted_at timestamptz,
  constraint leads_email_unique unique (email)
);

-- Conversations table - tracks interaction sessions
create table conversations (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade,
  session_id text not null unique,
  user_id uuid references auth.users(id),
  status text check (status in ('active', 'paused', 'completed', 'archived')) default 'active',
  channel text not null check (channel in ('chat', 'email', 'phone', 'web', 'other')),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  deleted_at timestamptz
);

-- Messages table - individual interactions within conversations
create table messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade not null,
  role text check (role in ('user', 'assistant', 'system')) not null,
  content text not null,
  agent_type text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Agent logs table - detailed tracking of AI agent actions
create table agent_logs (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade,
  agent_type text not null,
  action text not null,
  input_data jsonb default '{}'::jsonb,
  output_data jsonb default '{}'::jsonb,
  execution_time_ms integer,
  status text check (status in ('success', 'error', 'timeout')) not null,
  error_message text,
  created_at timestamptz default now()
);

-- Appointments table - scheduled meetings/callbacks
create table appointments (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade not null,
  conversation_id uuid references conversations(id) on delete set null,
  appointment_type text not null,
  scheduled_at timestamptz not null,
  duration_minutes integer not null,
  status text check (status in ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')) default 'scheduled',
  meeting_link text,
  notes text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  deleted_at timestamptz
);

-- Service recommendations table - AI-generated service suggestions
create table service_recommendations (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade not null,
  conversation_id uuid references conversations(id) on delete set null,
  service_name text not null,
  confidence_score decimal(5,2) check (confidence_score >= 0 and confidence_score <= 1),
  reasoning text,
  priority text check (priority in ('high', 'medium', 'low')),
  status text check (status in ('suggested', 'accepted', 'rejected')) default 'suggested',
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

-- Generated content table - AI-produced content/assets
create table generated_content (
  id uuid primary key default gen_random_uuid(),
  lead_id uuid references leads(id) on delete cascade,
  content_type text not null,
  title text not null,
  content text not null,
  agent_type text not null,
  status text check (status in ('draft', 'review', 'approved', 'published', 'archived')) default 'draft',
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  deleted_at timestamptz
);

-----------------------------------------------
-- Create indexes for performance
-----------------------------------------------

-- Leads indexes
create index leads_lead_status_idx on leads(lead_status) where deleted_at is null;
create index leads_created_at_idx on leads(created_at);
create index leads_lead_score_idx on leads(lead_score) where deleted_at is null;

-- Conversations indexes
create index conversations_lead_id_idx on conversations(lead_id);
create index conversations_status_idx on conversations(status) where deleted_at is null;
create index conversations_created_at_idx on conversations(created_at);

-- Messages indexes
create index messages_conversation_id_idx on messages(conversation_id);
create index messages_created_at_idx on messages(created_at);
create index messages_role_idx on messages(role);

-- Agent logs indexes
create index agent_logs_conversation_id_idx on agent_logs(conversation_id);
create index agent_logs_agent_type_idx on agent_logs(agent_type);
create index agent_logs_created_at_idx on agent_logs(created_at);

-- Appointments indexes
create index appointments_lead_id_idx on appointments(lead_id);
create index appointments_status_idx on appointments(status) where deleted_at is null;
create index appointments_scheduled_at_idx on appointments(scheduled_at) where status = 'scheduled';

-- Service recommendations indexes
create index service_recommendations_lead_id_idx on service_recommendations(lead_id);
create index service_recommendations_status_idx on service_recommendations(status);

-- Generated content indexes
create index generated_content_lead_id_idx on generated_content(lead_id);
create index generated_content_status_idx on generated_content(status) where deleted_at is null;

-----------------------------------------------
-- Create update triggers for updated_at
-----------------------------------------------

-- Leads updated_at trigger
create trigger leads_updated_at_trigger
  before update on leads
  for each row
  execute function update_updated_at_column();

-- Conversations updated_at trigger
create trigger conversations_updated_at_trigger
  before update on conversations
  for each row
  execute function update_updated_at_column();

-- Appointments updated_at trigger
create trigger appointments_updated_at_trigger
  before update on appointments
  for each row
  execute function update_updated_at_column();

-- Generated content updated_at trigger
create trigger generated_content_updated_at_trigger
  before update on generated_content
  for each row
  execute function update_updated_at_column();

-----------------------------------------------
-- Enable Row Level Security
-----------------------------------------------

-- Enable RLS on all tables
alter table leads enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table agent_logs enable row level security;
alter table appointments enable row level security;
alter table service_recommendations enable row level security;
alter table generated_content enable row level security;

-----------------------------------------------
-- Create RLS Policies
-----------------------------------------------

-- Leads policies (allow authenticated users to see their own leads)
create policy "Users can view own leads"
  on leads for select
  using (auth.uid() = user_id);

create policy "Backend service can manage all leads"
  on leads for all
  using (auth.role() = 'service_role');

-- Conversations policies
create policy "Users can view own conversations"
  on conversations for select
  using (auth.uid() = user_id);

create policy "Backend service can manage all conversations"
  on conversations for all
  using (auth.role() = 'service_role');

-- Messages policies
create policy "Users can view conversation messages"
  on messages for select
  using (
    exists (
      select 1 from conversations c
      where c.id = messages.conversation_id
      and c.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all messages"
  on messages for all
  using (auth.role() = 'service_role');

-- Agent logs policies (service role only)
create policy "Backend service can manage agent logs"
  on agent_logs for all
  using (auth.role() = 'service_role');

-- Appointments policies
create policy "Users can view own appointments"
  on appointments for select
  using (
    exists (
      select 1 from leads l
      where l.id = appointments.lead_id
      and l.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all appointments"
  on appointments for all
  using (auth.role() = 'service_role');

-- Service recommendations policies
create policy "Users can view own recommendations"
  on service_recommendations for select
  using (
    exists (
      select 1 from leads l
      where l.id = service_recommendations.lead_id
      and l.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all recommendations"
  on service_recommendations for all
  using (auth.role() = 'service_role');

-- Generated content policies
create policy "Users can view own content"
  on generated_content for select
  using (
    exists (
      select 1 from leads l
      where l.id = generated_content.lead_id
      and l.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all content"
  on generated_content for all
  using (auth.role() = 'service_role');

-----------------------------------------------
-- Insert test data (if needed)
-----------------------------------------------

-- Create a function to insert test data
create or replace function insert_test_data(test_user_id uuid)
returns void as $$
declare
    test_lead_id uuid;
    test_conversation_id uuid;
begin
    -- Only proceed if a valid user ID is provided
    if test_user_id is not null then
        -- Insert test lead
        insert into leads (
            email,
            first_name,
            last_name,
            company,
            user_id,
            lead_score,
            lead_status,
            source,
            services_interested,
            budget_range,
            timeline
        ) values (
            'test@example.com',
            'John',
            'Doe',
            'Acme Corp',
            test_user_id,
            75,
            'new',
            'web',
            array['SEO', 'Content Marketing'],
            '$5k-10k',
            'Q1 2026'
        ) returning id into test_lead_id;

        -- Insert test conversation
        insert into conversations (
            lead_id,
            session_id,
            channel,
            status,
            user_id
        ) values (
            test_lead_id,
            'test-session-001',
            'chat',
            'active',
            test_user_id
        ) returning id into test_conversation_id;

        -- Insert test message
        insert into messages (
            conversation_id,
            role,
            content,
            agent_type
        ) values (
            test_conversation_id,
            'user',
            'Hi, I need help with SEO services',
            'chat'
        );
    end if;
end;
$$ language plpgsql;

-- To insert test data, uncomment and run the following line:
-- select insert_test_data((select id from auth.users where email = 'your-test-user@example.com' limit 1));