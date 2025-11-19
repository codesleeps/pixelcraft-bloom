# Welcome to PixelCraft Bloom

## Project info

**URL**: <https://codesleeps.github.io/pixelcraft-bloom/>

## Backend API

This repository now includes a Python FastAPI backend scaffold located in the `backend/` directory. The backend provides AI-powered automation using AgentScope and local Ollama LLMs, and persists data to Supabase.

See `backend/README.md` for setup, configuration, and usage instructions.

## AI Model Setup

PixelCraft Bloom leverages local AI models via Ollama for AI-powered features like chat, lead qualification, and content creation. This section guides you through installing, configuring, and managing these models. The system also supports HuggingFace as a cloud fallback for enhanced reliability.

### Installing Ollama

1. Visit [ollama.ai](https://ollama.ai) and download the installer for your operating system (macOS, Windows, or Linux).
2. Run the installer and follow the on-screen instructions to complete the setup.
3. Verify installation by running `ollama --version` in your terminal.

Ollama runs as a local server on port 11434 by default, providing a REST API for model interactions.

### Pulling Required Models

The backend agents require the following models. Pull them using Ollama's CLI:

```bash
ollama pull llama2
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

- **llama2**: General-purpose model for chat and text generation.
- **llama3**: Advanced model for conversational AI and reasoning tasks.
- **mistral**: Efficient model for fast, lightweight processing across various tasks.
- **codellama**: Specialized model for code generation, ideal for web development and technical content.

These models are automatically selected by the ModelManager based on task type (e.g., chat vs. code generation).

### Configuring Ollama

Ollama is configured via environment variables in `backend/.env`. Default settings are provided, but customize as needed:

```
OLLAMA_HOST=http://localhost:11434  # Ollama server URL
OLLAMA_MODEL=llama3                 # Default model
OLLAMA_KEEP_ALIVE=10m               # Model keep-alive duration
OLLAMA_TEMPERATURE=0.7              # Response creativity (0.0-1.0)
OLLAMA_STREAM=true                  # Enable streaming responses
```

Ensure Ollama is running (`ollama serve`) before starting the backend.

### HuggingFace API Key Setup (Cloud Fallback)

For cloud-based model fallback when local Ollama models are unavailable:

1. Create a HuggingFace account at [huggingface.co](https://huggingface.co).
2. Navigate to **Settings > Access Tokens** and generate a new API token with "Read" permissions.
3. Add the token to `backend/.env`:

```
HUGGINGFACE_API_KEY=your-api-key-here
```

This enables automatic failover to HuggingFace-hosted models (e.g., via their Inference API) for improved uptime.

### Model Testing Instructions

Test models after setup to ensure functionality:

1. Start the backend: `cd backend && uvicorn app.main:app --reload`.
2. Use the API endpoint `POST /api/models/test` with a JSON payload like `{"model": "llama3", "prompt": "Hello, world!"}`.
3. Alternatively, use the frontend **ModelTester** component in the dashboard to interactively test models, view latency, and compare outputs.
4. Check the response for successful generation; expect JSON with `{"response": "...", "latency": 123}`.

Run backend tests for comprehensive validation: `cd backend && pytest test_models.py`.

### Model Performance Monitoring

Track model health and metrics in real-time:

- **Health Check**: Query `GET /api/models/health` for overall status (e.g., model availability and response times).
- **Metrics**: Use `GET /api/models/metrics` for detailed stats like latency, success rate, token usage, and error counts.
- **Dashboard**: View live metrics in the frontend **ModelsDashboard** component, including performance trends and model comparisons.
- **Logs**: Monitor backend logs for model-specific events (e.g., fallbacks or failures).

Metrics are persisted to Supabase for historical analysis.

### Troubleshooting Common Model Issues

- **Ollama Not Responding**: Ensure Ollama is running (`ollama serve`). Check `OLLAMA_HOST` in `.env` and verify port 11434 is open.
- **Model Not Found Error**: Pull the model manually (`ollama pull <model_name>`). Confirm the model name matches those in `backend/app/models/config.py`.
- **Connection Refused**: Restart Ollama or update `OLLAMA_HOST` if using a custom setup.
- **Slow Responses**: Increase `OLLAMA_KEEP_ALIVE` or switch to lighter models like `mistral`. Monitor system RAM/CPU usage.
- **Out of Memory**: Use smaller models (e.g., `llama2:7b` instead of full versions) or add more RAM to your machine.
- **Cloud Fallback Failing**: Verify `HUGGINGFACE_API_KEY` is valid and has sufficient API quota. Check HuggingFace status at [status.huggingface.co](https://status.huggingface.co).
- **Streaming Not Working**: Ensure `OLLAMA_STREAM=true` and use WebSocket-compatible endpoints.

For persistent issues, check backend logs and refer to [Ollama documentation](https://github.com/jmorganca/ollama) or [HuggingFace docs](https://huggingface.co/docs).

### Model Configuration Options

Advanced configuration is handled in `backend/app/models/config.py` and `.env`:

- **Task Mapping**: Assign models to tasks (e.g., `chat: llama3`, `code: codellama`).
- **Health Checks**: Set intervals via `MODEL_HEALTH_CHECK_INTERVAL=300` (seconds).
- **Retries/Timeouts**: Configure `MODEL_MAX_RETRIES=3` and `MODEL_REQUEST_TIMEOUT=30` for robustness.
- **Caching**: Enable response caching with `MODEL_CACHE_TTL=3600` to reduce API calls.
- **Warmup**: Set `MODEL_WARMUP_ON_STARTUP=true` to preload models on backend startup.
- **Cost Tracking**: For HuggingFace, track usage via API responses (no direct config needed).

Refer to `backend/.env.example` for all variables and their descriptions.

### Examples of Using Different Models for Tasks

The ModelManager intelligently selects models based on agent tasks:

- **Chat Agent**: Uses `llama3` for natural, conversational responses (e.g., customer inquiries).
- **Lead Qualification**: Employs `mistral` for efficient analysis of lead data and scoring.
- **Web Development**: Leverages `codellama` for generating HTML/CSS/JS code snippets.
- **Content Creation**: Relies on `llama2` for creative writing and blog post drafts.
- **Analytics Consulting**: Uses `mistral` for data interpretation and report generation.

Override defaults via API parameters (e.g., `POST /api/models/generate` with `{"model": "codellama", "task": "code"}`).

For detailed backend setup, see `backend/README.md`. If issues persist, check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for comprehensive instructions.

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

## Notification System

**Overview:**

- Explain that the platform includes a comprehensive notification system for real-time alerts about leads, agent actions, workflows, and system events
- Notifications are delivered via both REST API and WebSocket for real-time updates
- Users see notifications in a dropdown menu in the dashboard header, and critical alerts appear as toast notifications

**Notification Types:**

- **Lead notifications**: Created when leads are submitted or analyzed
- **Agent notifications**: Created when agents complete tasks or encounter errors
- **Workflow notifications**: Created when workflows complete or fail
- **Conversation notifications**: Created for important conversation milestones
- **System notifications**: Created for system-wide alerts (admin only)

**Severity Levels:**

- **Info**: General informational notifications (blue)
- **Success**: Successful operations (green)
- **Warning**: Important warnings that need attention (yellow)
- **Error**: Critical errors that require immediate action (red)

**Backend API Endpoints:**

- `GET /api/notifications` - List notifications with filtering and pagination
- `GET /api/notifications/{id}` - Get a specific notification
- `POST /api/notifications/mark-read` - Mark notifications as read
- `POST /api/notifications/mark-all-read` - Mark all notifications as read
- `DELETE /api/notifications/{id}` - Delete a notification
- `GET /api/notifications/unread-count` - Get unread notification count
- `WS /api/ws/notifications` - WebSocket endpoint for real-time notifications

**Database Schema:**

- `notifications` table stores all notifications with recipient, type, severity, title, message, action URL, metadata, and read status
- RLS policies ensure users can only access their own notifications
- Automatic cleanup of expired notifications

**Frontend Integration:**

- `useNotifications` hook provides access to notifications with real-time updates
- Notification bell icon in dashboard header shows unread count
- Clicking the bell opens a dropdown with recent notifications
- Critical notifications (errors/warnings) appear as Sonner toast notifications
- Notifications can link to related resources (e.g., leads, workflows)

**Creating Notifications (for developers):**

```python
from app.utils.notification_service import create_notification

await create_notification(
    recipient_id=user_id,
    notification_type="lead",
    severity="success",
    title="New Lead Created",
    message="Lead has been successfully created",
    action_url="/dashboard/leads/123",
    metadata={"lead_id": "123"}
)
```

**Real-Time Delivery:**

- Notifications are published to Redis channel `notifications:user:{user_id}`
- WebSocket connection automatically receives new notifications
- Frontend React Query cache is invalidated, triggering UI updates
- Toast notifications appear immediately for critical events

## Test Suites

This project includes comprehensive test suites for both frontend and backend components, with a focus on automated testing to ensure reliability and maintainability.

### Frontend Tests

- **Command to run tests**: `npm test` or `npm run test:watch`
- **Command for coverage**: `npm run test:coverage`
- **Location of test files**: `src/**/__tests__/` and `src/**/*.test.tsx`
- **Note about test utilities**: Test utilities are available in `src/test/utils/` (e.g., `renderWithProviders` for component testing), and mocks are located in `src/test/mocks/` (e.g., for WebSocket and authentication).

### Backend Tests

- **Command to run tests**: `cd backend && pytest`
- **Command for coverage**: `cd backend && pytest --cov=app --cov-report=html`
- **Location of test files**: `backend/tests/`
- **Note about fixtures**: Shared fixtures and utilities are defined in `backend/tests/conftest.py` for mocking dependencies like Supabase and Redis.

### Notification System Tests

The notification system has extensive test coverage across frontend and backend layers to validate real-time delivery, API endpoints, and WebSocket functionality.

- **Frontend**: Hook tests (`useNotifications.test.tsx` for WebSocket lifecycle and mutations), Dashboard tests (`Dashboard.notifications.test.tsx` for toast display and filtering).
- **Backend**: API tests (`test_notifications_api.py` for REST endpoints), WebSocket tests (`test_notifications_websocket.py` for real-time delivery), Service tests (`test_notification_service.py` for utility functions).
- **Note about mocked dependencies**: Tests mock WebSocket connections, Supabase database queries, and Redis pub/sub to ensure isolation and reliability.

### Running Specific Tests

- **Frontend**: `npm test -- useNotifications` to run a specific test file (e.g., hook tests).
- **Backend**: `pytest tests/test_notifications_api.py` to run a specific test file, or `pytest -k "test_mark_read"` to run tests matching a pattern (e.g., mark-read functionality).

### Coverage Thresholds

- **Frontend**: 70% (branches, functions, lines, statements)
- **Backend**: 70% (to be configured)

For manual testing of notifications (e.g., during development):

- Create test notifications via API or directly in the database.
- Monitor WebSocket connections in browser DevTools.
- Check Redis pub/sub messages: `redis-cli SUBSCRIBE notifications:user:*`

## How can I edit this code?

There are several ways of editing your application.

### Use Lovable

Simply visit the [GitHub Project](https://github.com/codesleeps/pixelcraft-bloom) and start editing

### Use your preferred IDE

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

### Edit a file directly in GitHub

- Navigate to the desired file(s).
- Click the "Edit" button (pencil icon) at the top right of the file view.
- Make your changes and commit the changes.

### Use GitHub Codespaces

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

## Production Deployment

Recommended architecture for production:

- Frontend (static site and SPA) on Vercel
- Backend (Python API + WebSocket) on a Hostinger VPS (or Render)

### Frontend on Vercel

- `vercel.json` provides security headers, long-term asset caching, and safe SPA rewrites that avoid hijacking static HTML pages.
- Project settings:
  - Build command: `npm run build`
  - Output directory: `dist`
  - Install command: `npm ci`
  - Environment variables: `VITE_API_BASE_URL`, `VITE_WS_URL`, etc.

### Backend on Hostinger VPS

1. Provision an Ubuntu VPS and open ports 80/443.
2. Install Python 3.11+, Nginx, and Certbot.
3. Deploy the FastAPI app behind a process manager (`uvicorn`/`gunicorn` via `systemd`).
4. Use `ops/nginx.conf` as a template:
   - Set your domain in `server_name`.
   - Proxy to `http://127.0.0.1:8000`.
   - WebSocket upgrade headers are included.
   - Basic rate limiting and security headers are enabled.
5. Issue TLS with Let’s Encrypt: `sudo certbot --nginx -d api.yourdomain.com`.
6. Verify `/health` returns 200.

### CI/CD

- Vercel Git Integration handles frontend deployments.
- GitHub Actions already build and deploy to GitHub Pages (`dist/`). Keep or disable as needed.
- Add backend test workflow if desired (`pytest`).

### Security & Performance

- CSP, HSTS, X-Frame-Options, and Permissions-Policy are applied at Vercel’s edge.
- Nginx adds complementary headers and basic rate limiting for the API.
- Immutable assets cached for 1 year; HTML stays non-cached.

### Launch Checklist

- Update CSP sources in `vercel.json` if using external CDNs.
- Set `VITE_API_BASE_URL` to your backend domain.
- Validate dashboard pages and SPA routes.
- Confirm WebSocket features (live analytics, activity log).
- Configure monitoring (Sentry, UptimeRobot) and backups.

## How can I deploy this project?

Simply open [Lovable](https://lovable.dev/projects/f1718176-4080-4bf5-9910-b3d5b66f3fb7) and click on Share -> Publish.

## Can I connect a custom domain to my Lovable project?

Yes, you can!

To connect a domain, navigate to Project > Settings > Domains and click Connect Domain.

Read more here: [Setting up a custom domain](https://docs.lovable.dev/tips-tricks/custom-domain#step-by-step-guide)
