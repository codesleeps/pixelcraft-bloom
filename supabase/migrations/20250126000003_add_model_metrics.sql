-- Create model performance and caching tables

-- Model response cache table
create table model_response_cache (
    id uuid primary key default gen_random_uuid(),
    model_name text not null,
    task_type text not null,
    prompt_hash text not null,  -- Hash of the prompt for quick lookup
    prompt text not null,
    response text not null,
    tokens_used integer,
    execution_time_ms integer,
    created_at timestamptz default now(),
    expires_at timestamptz,
    constraint unique_prompt_model unique (prompt_hash, model_name)
);

-- Model performance tracking
create table model_performance_metrics (
    id uuid primary key default gen_random_uuid(),
    model_name text not null,
    task_type text not null,
    total_requests bigint default 0,
    successful_requests bigint default 0,
    failed_requests bigint default 0,
    total_tokens bigint default 0,
    avg_response_time numeric default 0,
    cache_hits bigint default 0,
    cache_misses bigint default 0,
    last_error text,
    last_error_at timestamptz,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Create indexes for better performance
create index idx_cache_lookup on model_response_cache (prompt_hash, model_name);
create index idx_cache_expiry on model_response_cache (expires_at);
create index idx_model_metrics on model_performance_metrics (model_name, task_type);

-- Function to cleanup expired cache entries
create or replace function cleanup_expired_cache()
returns void as $$
begin
    delete from model_response_cache
    where expires_at < now();
end;
$$ language plpgsql security definer;

-- Function to get model performance metrics
create or replace function get_model_performance_metrics(
    start_date timestamptz default '-infinity',
    end_date timestamptz default 'infinity'
)
returns table (
    model_name text,
    task_type text,
    success_rate numeric,
    avg_response_time numeric,
    cache_hit_rate numeric,
    total_requests bigint,
    total_tokens bigint
) as $$
begin
    return query
    select 
        mp.model_name,
        mp.task_type,
        (mp.successful_requests::numeric / nullif(mp.total_requests, 0)::numeric * 100) as success_rate,
        mp.avg_response_time,
        (mp.cache_hits::numeric / nullif(mp.total_requests, 0)::numeric * 100) as cache_hit_rate,
        mp.total_requests,
        mp.total_tokens
    from model_performance_metrics mp
    where mp.created_at between start_date and end_date
    order by mp.total_requests desc;
end;
$$ language plpgsql security definer;

-- Function to update model metrics
create or replace function update_model_metrics(
    p_model_name text,
    p_task_type text,
    p_success boolean,
    p_response_time numeric,
    p_tokens_used integer,
    p_cache_hit boolean,
    p_error_message text default null
)
returns void as $$
declare
    v_metric_id uuid;
begin
    -- Get or create metrics record
    select id into v_metric_id
    from model_performance_metrics
    where model_name = p_model_name and task_type = p_task_type;
    
    if not found then
        insert into model_performance_metrics (model_name, task_type)
        values (p_model_name, p_task_type)
        returning id into v_metric_id;
    end if;
    
    -- Update metrics
    update model_performance_metrics
    set
        total_requests = total_requests + 1,
        successful_requests = successful_requests + case when p_success then 1 else 0 end,
        failed_requests = failed_requests + case when p_success then 0 else 1 end,
        total_tokens = total_tokens + coalesce(p_tokens_used, 0),
        avg_response_time = (avg_response_time * total_requests + p_response_time) / (total_requests + 1),
        cache_hits = cache_hits + case when p_cache_hit then 1 else 0 end,
        cache_misses = cache_misses + case when p_cache_hit then 0 else 1 end,
        last_error = case when not p_success then p_error_message else last_error end,
        last_error_at = case when not p_success then now() else last_error_at end,
        updated_at = now()
    where id = v_metric_id;
end;
$$ language plpgsql security definer;