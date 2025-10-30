-- Revenue analytics functions for subscription and pricing data

-- Function to get revenue summary metrics
create or replace function get_revenue_summary(
    start_date timestamptz default '-infinity',
    end_date timestamptz default 'infinity',
    user_uuid uuid default null
)
returns table (
    mrr numeric,
    arr numeric,
    total_revenue numeric,
    active_subscriptions bigint,
    cancelled_subscriptions bigint,
    churn_rate numeric
) as $$
begin
    return query
    select
        coalesce(sum(us.final_price) filter (where us.status = 'active'), 0)::numeric as mrr,
        coalesce(sum(us.final_price) filter (where us.status = 'active'), 0)::numeric * 12 as arr,
        coalesce(sum(us.final_price), 0)::numeric as total_revenue,
        count(*) filter (where us.status = 'active')::bigint as active_subscriptions,
        count(*) filter (where us.status = 'cancelled')::bigint as cancelled_subscriptions,
        (count(*) filter (where us.status = 'cancelled')::numeric /
         nullif(count(*) filter (where us.status in ('active', 'cancelled')), 0)::numeric * 100)::numeric as churn_rate
    from user_subscriptions us
    where us.created_at between start_date and end_date
    and (user_uuid is null or us.user_id = user_uuid);
end;
$$ language plpgsql security definer;

-- Function to get revenue breakdown by pricing package
create or replace function get_revenue_by_package(
    start_date timestamptz,
    end_date timestamptz,
    user_uuid uuid default null
)
returns table (
    package_id uuid,
    package_name text,
    subscription_count bigint,
    total_revenue numeric,
    avg_revenue_per_subscription numeric
) as $$
begin
    return query
    select
        pp.id as package_id,
        pp.name as package_name,
        count(us.id)::bigint as subscription_count,
        coalesce(sum(us.final_price), 0)::numeric as total_revenue,
        coalesce(avg(us.final_price), 0)::numeric as avg_revenue_per_subscription
    from pricing_packages pp
    left join user_subscriptions us on pp.id = us.package_id
    where us.created_at between start_date and end_date
    and (user_uuid is null or us.user_id = user_uuid)
    group by pp.id, pp.name
    order by total_revenue desc;
end;
$$ language plpgsql security definer;

-- Function to get subscription trends over time
-- Note: Cancellations are tracked using updated_at as a proxy for cancellation time.
-- For more accurate tracking, consider adding a cancelled_at timestamp column in a future migration.
create or replace function get_subscription_trends(
    start_date timestamptz,
    end_date timestamptz,
    aggregation text default 'daily',
    user_uuid uuid default null
)
returns table (
    period timestamptz,
    new_subscriptions bigint,
    cancelled_subscriptions bigint,
    net_change bigint,
    cumulative_active bigint
) as $$
begin
    return query
    with new_subs as (
        -- Count new subscriptions grouped by creation period
        select
            date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.created_at) as period,
            count(*)::bigint as new_subscriptions
        from user_subscriptions us
        where us.created_at between start_date and end_date
        and (user_uuid is null or us.user_id = user_uuid)
        group by date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.created_at)
    ),
    cancelled_subs as (
        -- Count cancelled subscriptions grouped by cancellation period (using updated_at as proxy)
        select
            date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.updated_at) as period,
            count(*)::bigint as cancelled_subscriptions
        from user_subscriptions us
        where us.status = 'cancelled'
        and us.updated_at between start_date and end_date
        and (user_uuid is null or us.user_id = user_uuid)
        group by date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.updated_at)
    ),
    combined_trends as (
        -- Combine new and cancelled counts per period, handling missing periods with full outer join
        select
            coalesce(ns.period, cs.period) as period,
            coalesce(ns.new_subscriptions, 0)::bigint as new_subscriptions,
            coalesce(cs.cancelled_subscriptions, 0)::bigint as cancelled_subscriptions,
            coalesce(ns.new_subscriptions, 0)::bigint - coalesce(cs.cancelled_subscriptions, 0)::bigint as net_change
        from new_subs ns
        full outer join cancelled_subs cs on ns.period = cs.period
    )
    select
        ct.period,
        ct.new_subscriptions,
        ct.cancelled_subscriptions,
        ct.net_change,
        sum(ct.net_change) over (order by ct.period)::bigint as cumulative_active
    from combined_trends ct
    order by ct.period;
end;
$$ language plpgsql security definer;

-- Function to get customer lifetime value metrics
create or replace function get_customer_ltv(
    user_uuid uuid default null
)
returns table (
    user_id uuid,
    total_spent numeric,
    subscription_count bigint,
    avg_subscription_value numeric,
    lifetime_months numeric,
    estimated_ltv numeric
) as $$
begin
    return query
    select
        us.user_id,
        coalesce(sum(us.final_price), 0)::numeric as total_spent,
        count(us.id)::bigint as subscription_count,
        coalesce(avg(us.final_price), 0)::numeric as avg_subscription_value,
        extract(epoch from (max(us.end_date) - min(us.start_date))) / (30 * 24 * 3600)::numeric as lifetime_months,
        coalesce(sum(us.final_price), 0)::numeric as estimated_ltv
    from user_subscriptions us
    where (user_uuid is null or us.user_id = user_uuid)
    group by us.user_id
    order by total_spent desc;
end;
$$ language plpgsql security definer;
