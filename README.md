# Welcome to your Lovable project

## Project info

**URL**: https://lovable.dev/projects/f1718176-4080-4bf5-9910-b3d5b66f3fb7

## Backend API

This repository now includes a Python FastAPI backend scaffold located in the `backend/` directory. The backend provides AI-powered automation using AgentScope and local Ollama LLMs, and persists data to Supabase.

See `backend/README.md` for setup, configuration, and usage instructions.

## Revenue Analytics

The revenue analytics system provides comprehensive insights into subscription-based revenue, including Monthly Recurring Revenue (MRR), Annual Recurring Revenue (ARR), subscription trends, customer lifetime value (LTV), and revenue breakdowns by pricing package.

### API Endpoints

- `GET /api/analytics/revenue/summary` - Retrieves key revenue metrics like MRR, ARR, total revenue, active subscriptions, cancelled subscriptions, and churn rate for a specified time range.
- `GET /api/analytics/revenue/by-package` - Returns revenue breakdown by pricing package, including subscription counts and average revenue per subscription.
- `GET /api/analytics/revenue/subscription-trends` - Provides time-series data on new subscriptions, cancellations, net changes, and cumulative active subscriptions, with daily or weekly aggregation.
- `GET /api/analytics/revenue/customer-ltv` - Lists customer lifetime value metrics, such as total spent, subscription count, and estimated LTV, with pagination support.
- `GET /api/analytics/revenue/subscriptions/list` - Lists all subscriptions with filtering options (e.g., by status or package) and pagination.

### Generating Test Data

To create sample subscription data for testing and development:

1. Run the script: `python backend/generate_test_subscription_data.py`
2. This generates 20-30 subscriptions across Starter, Professional, and Enterprise pricing tiers, with varied statuses (70% active, 20% cancelled, 10% expired), random start dates over the past year, and calculated end dates and pricing.

### Running Tests

To verify the revenue analytics functionality:

1. Set up environment variables in `.env`: `USER_JWT_TOKEN` and `ADMIN_JWT_TOKEN` for authentication.
2. Run the test suite: `python backend/test_analytics_api.py`
3. This executes all analytics tests, including revenue-specific ones for data consistency, edge cases, and endpoint validation.

### Frontend Integration

Revenue metrics are visualized in the Dashboard component. Use the following custom hooks for data fetching:

- `useAnalytics`: Fetches summary revenue metrics.
- `useSubscriptionTrends`: Retrieves subscription trend data with time range and aggregation options.
- `useRevenueByPackage`: Gets revenue breakdown by package.
- `useCustomerLTV`: Fetches customer LTV data with pagination.

Example usage:

```typescript
import { useAnalytics, useSubscriptionTrends } from '@/hooks/useAnalyticsTrends';

const { data: summary } = useAnalytics({ timeRange: { start_date: '2024-01-01', end_date: '2024-12-31' } });
const { data: trends } = useSubscriptionTrends({ timeRange: { start_date: '2024-01-01', end_date: '2024-12-31' }, aggregation: 'daily' });
```

### Database Schema

Revenue analytics rely on the following tables and migrations:

- **Migrations**: `supabase/migrations/20250126000004_add_pricing.sql` (defines `pricing_packages` and `user_subscriptions` tables) and `20250126000006_add_revenue_analytics.sql` (adds RPC functions for analytics).
- **Relationships**:
  - `user_subscriptions` links users to subscriptions, referencing `pricing_packages` for package details and `pricing_campaigns` for discounts.
  - RPC functions query these tables to compute metrics like MRR (sum of active subscription prices) and trends (grouped by creation/cancellation dates).

For more details, refer to the migration files and backend models.

## Real-Time Analytics Updates

The dashboard supports real-time analytics updates via WebSocket connections, allowing you to see metrics update instantly as data changes.

### Architecture
- **Backend**: FastAPI WebSocket endpoint at `/api/ws/analytics` with JWT authentication
- **Event Broadcasting**: Redis pub/sub for scalable event distribution across multiple backend instances
- **Frontend**: Custom React hook (`useWebSocket`) that integrates with React Query for automatic cache invalidation

### Setup Requirements
- Redis must be running and configured via `REDIS_URL` environment variable
- If Redis is unavailable, the system gracefully degrades to polling-based updates

### Events Triggered
- Lead creation/updates → refreshes lead metrics and trends
- Conversation messages → refreshes conversation metrics and trends
- Subscription changes → refreshes revenue metrics and subscription trends
- Agent actions → refreshes agent performance metrics

### Testing
- Start Redis: `redis-server` (or use Docker: `docker run -d -p 6379:6379 redis`)
- Start backend: `cd backend && uvicorn app.main:app --reload`
- Start frontend: `npm run dev`
- Open dashboard and observe the "Live" indicator in the top-right corner
- Create a test lead via API or UI and watch metrics update in real-time

### Troubleshooting
- If WebSocket shows "Offline", check that Redis is running and `REDIS_URL` is configured
- Check browser console for WebSocket connection errors
- Verify JWT token is valid (WebSocket requires authentication)
- Check backend logs for Redis connection issues

## How can I edit this code?

There are several ways of editing your application.

**Use Lovable**

Simply visit the [Lovable Project](https://lovable.dev/projects/f1718176-4080-4bf5-9910-b3d5b66f3fb7) and start prompting.

Changes made via Lovable will be committed automatically to this repo.

**Use your preferred IDE**

If you want to work locally using your own IDE, you can clone this repo and push changes. Pushed changes will also be reflected in Lovable.

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

Follow these steps:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd <YOUR_PROJECT_NAME>

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

**Edit a file directly in GitHub**

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

**Use GitHub Codespaces**

- Navigate to the main page of your repository.
- Click on the "Code" button (green button) near the top right.
- Select the "Codespaces" tab.
- Click on "New codespace" to launch a new Codespace environment.
- Edit files directly within the Codespace and commit and push your changes once you're done.

## What technologies are used for this project?

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

Backend:

- FastAPI (Python)
- AgentScope (Agent orchestration)
- Ollama (local LLMs, e.g., llama3)
- Supabase (Postgres) for persistence


## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/f1718176-4080-4bf5-9910-b3d5b66f3fb7) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
