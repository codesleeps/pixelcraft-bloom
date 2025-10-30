-- Migration to add trend analytics functions

-- Function to get lead trends over time
create or replace function get_lead_trends(
    start_date timestamptz,
    end_date timestamptz,
    aggregation text,
    user_uuid uuid default null
)
returns table (
    date timestamptz,
    value bigint
) as $$
begin
    return query
    select
        date_trunc(aggregation, l.created_at) as date,
        count(*)::bigint as value
    from leads l
    where l.created_at between start_date and end_date
    and l.deleted_at is null
    and (user_uuid is null or l.user_id = user_uuid)
    group by date_trunc(aggregation, l.created_at)
    order by date asc;
end;
$$ language plpgsql security definer;

-- Function to get conversation trends over time
create or replace function get_conversation_trends(
    start_date timestamptz,
    end_date timestamptz,
    aggregation text,
    user_uuid uuid default null,
    status_filter text default null,
    channel_filter text default null
)
returns table (
    date timestamptz,
    value bigint
) as $$
begin
    return query
    select
        date_trunc(aggregation, c.created_at) as date,
        count(*)::bigint as value
    from conversations c
    where c.created_at between start_date and end_date
    and c.deleted_at is null
    and (user_uuid is null or c.user_id = user_uuid)
    and (status_filter is null or c.status = status_filter)
    and (channel_filter is null or c.channel = channel_filter)
    group by date_trunc(aggregation, c.created_at)
    order by date asc;
end;
$$ language plpgsql security definer;

-- Function to get agent trends (success rate over time)
create or replace function get_agent_trends(
    start_date timestamptz,
    end_date timestamptz,
    agent_type_filter text default null
)
returns table (
    date timestamptz,
    value numeric
) as $$
begin
    return query
    select
        date_trunc('day', al.created_at) as date,
        (count(*) filter (where al.status = 'success')::numeric /
         nullif(count(*), 0)::numeric * 100) as value
    from agent_logs al
    where al.created_at between start_date and end_date
    and (agent_type_filter is null or al.agent_type = agent_type_filter)
    group by date_trunc('day', al.created_at)
    order by date asc;
end;
$$ language plpgsql security definer;