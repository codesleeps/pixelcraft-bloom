-- Migration for Advanced Workflow Orchestration - January 2025
-- Tables: workflow_executions, agent_messages, shared_memory

-----------------------------------------------
-- Drop tables if they exist (for clean migrations)
-----------------------------------------------

drop table if exists shared_memory;
drop table if exists agent_messages;
drop table if exists workflow_executions;

-----------------------------------------------
-- Create tables with proper constraints
-----------------------------------------------

-- Workflow executions table - tracks multi-agent workflow state and progress
create table workflow_executions (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade not null,
  workflow_type text not null,
  current_state text not null,
  current_step text,
  participating_agents text[],
  workflow_config jsonb default '{}'::jsonb,
  execution_plan jsonb default '{}'::jsonb,
  results jsonb default '{}'::jsonb,
  metadata jsonb default '{}'::jsonb,
  started_at timestamptz default now(),
  completed_at timestamptz,
  error_message text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Agent messages table - stores agent-to-agent communication within workflows
create table agent_messages (
  id uuid primary key default gen_random_uuid(),
  workflow_execution_id uuid references workflow_executions(id) on delete cascade not null,
  from_agent text not null,
  to_agent text not null,
  message_type text not null,
  content jsonb not null,
  status text check (status in ('pending', 'delivered', 'processed', 'failed')) default 'pending',
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  processed_at timestamptz
);

-- Shared memory table - stores context accessible to all agents in a workflow
create table shared_memory (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade not null,
  workflow_execution_id uuid references workflow_executions(id) on delete cascade,
  memory_key text not null,
  memory_value jsonb not null,
  scope text not null check (scope in ('conversation', 'workflow', 'global')),
  created_by_agent text not null,
  access_count integer default 0,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  expires_at timestamptz,
  constraint shared_memory_unique_key unique (conversation_id, memory_key, scope)
);

-----------------------------------------------
-- Create indexes for performance
-----------------------------------------------

-- Workflow executions indexes
create index workflow_executions_conversation_id_idx on workflow_executions(conversation_id);
create index workflow_executions_current_state_idx on workflow_executions(current_state);
create index workflow_executions_started_at_idx on workflow_executions(started_at);

-- Agent messages indexes
create index agent_messages_workflow_execution_id_idx on agent_messages(workflow_execution_id);
create index agent_messages_to_agent_status_idx on agent_messages(to_agent, status);

-- Shared memory indexes
create index shared_memory_conversation_id_idx on shared_memory(conversation_id);
create index shared_memory_workflow_execution_id_idx on shared_memory(workflow_execution_id);
create index shared_memory_memory_key_idx on shared_memory(memory_key);

-----------------------------------------------
-- Create update triggers for updated_at
-----------------------------------------------

-- Workflow executions updated_at trigger
create trigger workflow_executions_updated_at_trigger
  before update on workflow_executions
  for each row
  execute function update_updated_at_column();

-- Shared memory updated_at trigger
create trigger shared_memory_updated_at_trigger
  before update on shared_memory
  for each row
  execute function update_updated_at_column();

-----------------------------------------------
-- Enable Row Level Security
-----------------------------------------------

-- Enable RLS on all tables
alter table workflow_executions enable row level security;
alter table agent_messages enable row level security;
alter table shared_memory enable row level security;

-----------------------------------------------
-- Create RLS Policies
-----------------------------------------------

-- Workflow executions policies
create policy "Users can view own workflow executions"
  on workflow_executions for select
  using (
    exists (
      select 1 from conversations c
      where c.id = workflow_executions.conversation_id
      and c.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all workflow executions"
  on workflow_executions for all
  using (auth.role() = 'service_role');

-- Agent messages policies
create policy "Users can view own agent messages"
  on agent_messages for select
  using (
    exists (
      select 1 from workflow_executions we
      join conversations c on c.id = we.conversation_id
      where we.id = agent_messages.workflow_execution_id
      and c.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all agent messages"
  on agent_messages for all
  using (auth.role() = 'service_role');

-- Shared memory policies
create policy "Users can view own shared memory"
  on shared_memory for select
  using (
    exists (
      select 1 from conversations c
      where c.id = shared_memory.conversation_id
      and c.user_id = auth.uid()
    )
  );

create policy "Backend service can manage all shared memory"
  on shared_memory for all
  using (auth.role() = 'service_role');