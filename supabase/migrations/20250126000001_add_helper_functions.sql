-- Function to get user ID by email
create or replace function get_user_id_by_email(email text)
returns uuid as $$
  select id from auth.users where email = $1 limit 1;
$$ language sql security definer;