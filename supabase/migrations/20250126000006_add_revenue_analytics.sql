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
    with trends as (
        select
            date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.created_at) as period,
            count(*) filter (where us.created_at is not null) as new_subs,
            count(*) filter (where us.status = 'cancelled' and us.updated_at is not null) as cancelled_subs
        from user_subscriptions us
        where us.created_at between start_date and end_date
        and (user_uuid is null or us.user_id = user_uuid)
        group by date_trunc(case when aggregation = 'weekly' then 'week' else 'day' end, us.created_at)
        order by period
    ),
    net_changes as (
        select
            period,
            coalesce(new_subs, 0)::bigint as new_subscriptions,
            coalesce(cancelled_subs, 0)::bigint as cancelled_subscriptions,
            coalesce(new_subs, 0)::bigint - coalesce(cancelled_subs, 0)::bigint as net_change
        from trends
    )
    select
        nc.period,
        nc.new_subscriptions,
        nc.cancelled_subscriptions,
        nc.net_change,
        sum(nc.net_change) over (order by nc.period)::bigint as cumulative_active
    from net_changes nc
    order by nc.period;
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