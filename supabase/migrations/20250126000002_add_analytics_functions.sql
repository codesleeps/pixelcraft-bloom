-- Complex queries for analytics and reporting

-- Function to get lead conversion metrics
create or replace function get_lead_conversion_metrics(
    start_date timestamptz default '-infinity',
    end_date timestamptz default 'infinity'
)
returns table (
    total_leads bigint,
    qualified_leads bigint,
    conversion_rate numeric,
    avg_lead_score numeric
) as $$
begin
    return query
    select 
        count(*) as total_leads,
        count(*) filter (where lead_status = 'qualified') as qualified_leads,
        (count(*) filter (where lead_status = 'qualified')::numeric / 
         nullif(count(*), 0)::numeric * 100) as conversion_rate,
        avg(lead_score)::numeric as avg_lead_score
    from leads
    where created_at between start_date and end_date
    and deleted_at is null;
end;
$$ language plpgsql security definer;

-- Function to get conversation analytics
create or replace function get_conversation_analytics(
    start_date timestamptz default '-infinity',
    end_date timestamptz default 'infinity'
)
returns table (
    total_conversations bigint,
    avg_messages_per_conversation numeric,
    active_conversations bigint,
    completed_conversations bigint
) as $$
begin
    return query
    with conversation_stats as (
        select 
            c.id,
            count(m.id) as message_count
        from conversations c
        left join messages m on c.id = m.conversation_id
        where c.created_at between start_date and end_date
        group by c.id
    )
    select
        count(*)::bigint as total_conversations,
        (avg(cs.message_count))::numeric as avg_messages_per_conversation,
        count(*) filter (where c.status = 'active')::bigint as active_conversations,
        count(*) filter (where c.status = 'completed')::bigint as completed_conversations
    from conversations c
    left join conversation_stats cs on c.id = cs.id
    where c.created_at between start_date and end_date
    and c.deleted_at is null;
end;
$$ language plpgsql security definer;

-- Function to get service recommendation insights
create or replace function get_service_recommendations_insights()
returns table (
    service_name text,
    total_recommendations bigint,
    accepted_count bigint,
    acceptance_rate numeric,
    avg_confidence numeric
) as $$
begin
    return query
    select 
        sr.service_name,
        count(*)::bigint as total_recommendations,
        count(*) filter (where status = 'accepted')::bigint as accepted_count,
        (count(*) filter (where status = 'accepted')::numeric / 
         nullif(count(*), 0)::numeric * 100) as acceptance_rate,
        avg(confidence_score)::numeric as avg_confidence
    from service_recommendations sr
    group by sr.service_name
    order by total_recommendations desc;
end;
$$ language plpgsql security definer;

-- Function to get agent performance metrics
create or replace function get_agent_performance_metrics(
    start_date timestamptz default '-infinity',
    end_date timestamptz default 'infinity'
)
returns table (
    agent_type text,
    total_actions bigint,
    success_rate numeric,
    avg_execution_time numeric,
    error_rate numeric
) as $$
begin
    return query
    select 
        al.agent_type,
        count(*)::bigint as total_actions,
        (count(*) filter (where status = 'success')::numeric / 
         nullif(count(*), 0)::numeric * 100) as success_rate,
        avg(execution_time_ms)::numeric as avg_execution_time,
        (count(*) filter (where status = 'error')::numeric / 
         nullif(count(*), 0)::numeric * 100) as error_rate
    from agent_logs al
    where created_at between start_date and end_date
    group by al.agent_type
    order by total_actions desc;
end;
$$ language plpgsql security definer;