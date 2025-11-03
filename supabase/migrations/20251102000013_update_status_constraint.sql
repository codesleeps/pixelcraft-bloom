-- Update status check constraint on user_subscriptions to include 'paused'
do $$
begin
  -- Drop existing constraint if it exists
  if exists (
    select 1 from information_schema.table_constraints 
    where constraint_name = 'user_subscriptions_status_check' 
      and table_name = 'user_subscriptions'
  ) then
    alter table user_subscriptions drop constraint user_subscriptions_status_check;
  end if;

  -- Add new constraint including paused
  alter table user_subscriptions
    add constraint user_subscriptions_status_check
    check (status in ('active', 'cancelled', 'expired', 'pending', 'paused'));
end $$;

