-- Migration to add notifications table - January 2025
-- Table: notifications - comprehensive notification system with real-time delivery

-----------------------------------------------
-- Create notifications table
-----------------------------------------------

create table notifications (
  id uuid primary key default gen_random_uuid(),
  recipient_id uuid references auth.users(id) on delete cascade not null,
  notification_type text not null check (notification_type in ('lead', 'agent', 'workflow', 'system', 'conversation')),
  severity text not null check (severity in ('info', 'success', 'warning', 'error')) default 'info',
  title text not null,
  message text not null,
  action_url text,
  metadata jsonb default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz default now(),
  expires_at timestamptz
);

-----------------------------------------------
-- Create indexes for performance
-----------------------------------------------

create index notifications_recipient_id_idx on notifications(recipient_id);
create index notifications_read_at_idx on notifications(read_at);
create index notifications_created_at_idx on notifications(created_at desc);
create index notifications_notification_type_idx on notifications(notification_type);
create index notifications_severity_idx on notifications(severity);

-----------------------------------------------
-- Enable Row Level Security
-----------------------------------------------

alter table notifications enable row level security;

-----------------------------------------------
-- Create RLS Policies
-----------------------------------------------

create policy "Users can view own notifications"
  on notifications for select
  using (auth.uid() = recipient_id);

create policy "Users can update own notifications"
  on notifications for update
  using (auth.uid() = recipient_id);

create policy "Backend service can manage all notifications"
  on notifications for all
  using (auth.role() = 'service_role');

-----------------------------------------------
-- Function for automatic cleanup of expired notifications
-----------------------------------------------

create or replace function delete_expired_notifications()
returns void as $$
begin
  delete from notifications where expires_at is not null and expires_at < now();
end;
$$ language plpgsql;

-- To enable periodic cleanup, install the pg_cron extension and schedule the function:
-- CREATE EXTENSION IF NOT EXISTS pg_cron;
-- SELECT cron.schedule('delete-expired-notifications', '0 * * * *', 'SELECT delete_expired_notifications();'); -- Runs every hour