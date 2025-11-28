# Backend API and WebSocket Documentation

This document describes the REST API endpoints, WebSocket channels and authentication, environment configuration, and database schema mapping used by the PixelCraft Bloom backend.

---

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-repo/pixelcraft-bloom.git
   cd pixelcraft-bloom/backend
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying `.env.example` to `.env` and filling in the required values (see Environment Variables section below).

4. Run the application:
   ```
   python main.py
   ```

## AI Model Setup

The backend uses Ollama for local AI model inference, with HuggingFace as an optional fallback when Ollama is unavailable. Follow these steps to set up AI functionality.

### Installing Ollama

1. Download and install Ollama from the official website: [https://ollama.ai](https://ollama.ai).
2. Follow the platform-specific installation instructions for your operating system (Windows, macOS, or Linux).

### Pulling Required Models

Pull the necessary models for the agents to function properly:

```
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull codellama:latest
```

These models are used by various agents (e.g., ChatAgent, LeadQualificationAgent) for generating responses and analyses.

### Verifying Ollama Setup

1. Start Ollama (if not already running):
   ```
   ollama serve
   ```

2. Verify Ollama is running and models are available:
   ```
   curl http://localhost:11434/api/tags
   ```
   This should return a JSON response listing the pulled models.

### Configuring Environment Variables

Update your `.env` file with Ollama settings (refer to `.env.example` for details):

- `OLLAMA_HOST`: URL where Ollama is running (default: `http://localhost:11434`).
- `OLLAMA_MODEL`: Default model to use (default: `llama3`).
- `OLLAMA_TEMPERATURE`: Generation temperature (default: `0.7`).
- `OLLAMA_KEEP_ALIVE`: Keep-alive duration (default: `10m`).

Example:
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TEMPERATURE=0.7
OLLAMA_KEEP_ALIVE=10m
```

### Model Fallback Behavior

If Ollama is unavailable (e.g., not running or models not pulled), the system automatically falls back to HuggingFace models for inference. To enable this:

1. Obtain a HuggingFace API key from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2. Set the `HUGGINGFACE_API_KEY` in your `.env` file:
   ```
   HUGGINGFACE_API_KEY=your-huggingface-api-key-here
   ```

Fallback occurs seamlessly in the ModelManager, logging warnings when switching. Agents will use fallback responses if both Ollama and HuggingFace fail.

### Troubleshooting Common Ollama Issues

- **Ollama not running**: Ensure Ollama is started with `ollama serve`. Check if port 11434 is in use or blocked by firewall.
- **Models not found**: Confirm models are pulled using `ollama list`. If missing, re-run the pull commands above.
- **Connection timeout errors**: Verify `OLLAMA_HOST` is correct and Ollama is accessible. Increase timeout settings in config if needed.
- **Performance issues**: Ensure sufficient RAM/CPU for model inference. Use smaller models (e.g., `llama3:8b` instead of `llama3.1:8b`) if resources are limited.
- **General debugging**: Check Ollama logs or run `ollama --help` for more options. Restart Ollama after configuration changes.

---

## Table of Contents
- Installation
- AI Model Setup
- REST API
  - Agents
    - POST /api/agents/invoke
    - POST /api/agents/workflows/execute
  - Analytics (overview)
    - Notifications (overview)
- WebSockets

### Channels

#### /api/ws/analytics
Real-time analytics events for leads, conversations, and subscriptions.

- URL: `/api/ws/analytics`
- Authentication: Query parameter `token` with valid Supabase JWT
- Connection: `wss://your-domain.com/api/ws/analytics?token=<supabase_jwt_token>`

#### /api/ws/notifications
Real-time notifications for the authenticated user.

- URL: `/api/ws/notifications`
- Authentication: Query parameter `token` with valid Supabase JWT
- Connection: `wss://your-domain.com/api/ws/notifications?token=<supabase_jwt_token>`

#### /api/ws/workflows
Real-time workflow status updates.

- URL: `/api/ws/workflows`
- Authentication: Query parameter `token` with valid Supabase JWT
- Connection: `wss://your-domain.com/api/ws/workflows?token=<supabase_jwt_token>`

### Authentication Flow

1. Client obtains a valid Supabase JWT token through authentication
2. Client connects to WebSocket endpoint with token as query parameter
3. Server validates token using `verify_supabase_token` function
4. If valid, connection is established and user-specific channels are subscribed
5. If invalid, connection is closed with code 1008 (Policy Violation)

### Client Message Schemas

#### Heartbeat (All Channels)
```json
{
  "type": "heartbeat",
  "timestamp": "2023-06-15T12:34:56Z"
}
```

### Server Event Schemas

#### Analytics Events
```json
{
  "type": "lead_created",
  "data": {
    "lead_id": "string",
    "user_id": "string",
    "created_at": "ISO timestamp"
  }
}
```

```json
{
  "type": "lead_analyzed",
  "data": {
    "lead_id": "string",
    "user_id": "string",
    "analysis_id": "string",
    "completed_at": "ISO timestamp"
  }
}
```

```json
{
  "type": "message_created",
  "data": {
    "conversation_id": "string",
    "message_id": "string",
    "user_id": "string",
    "created_at": "ISO timestamp"
  }
}
```

```json
{
  "type": "conversation_deleted",
  "data": {
    "conversation_id": "string",
    "user_id": "string",
    "deleted_at": "ISO timestamp"
  }
}
```

```json
{
  "type": "subscription_created",
  "data": {
    "subscription_id": "string",
    "user_id": "string",
    "plan": "string",
    "created_at": "ISO timestamp"
  }
}
```

```json
{
  "type": "subscription_updated",
  "data": {
    "subscription_id": "string",
    "user_id": "string",
    "plan": "string",
    "updated_at": "ISO timestamp"
  }
}
```

#### Notification Events
```json
{
  "type": "notification_created",
  "data": {
    "notification_id": "string",
    "user_id": "string",
    "notification_type": "string",
    "severity": "info|warning|error",
    "title": "string",
    "message": "string",
    "created_at": "ISO timestamp",
    "read": false,
    "metadata": {}
  }
}
```

#### Workflow Events
```json
{
  "type": "workflow_status_update",
  "data": {
    "workflow_run_id": "string",
    "workflow_id": "string",
    "user_id": "string",
    "status": "queued|running|completed|failed",
    "step": "string",
    "progress": 0.75,
    "updated_at": "ISO timestamp"
  }
}
```
- Environment Variables
- Database Schema Mapping to Migrations

---

## REST API

All API endpoints are prefixed with `/api`. Authentication is typically performed via a Bearer JWT or a Supabase-authenticated user token where applicable.

### Agents

#### POST /api/agents/invoke
Invoke a single agent for a request.

- URL: `/api/agents/invoke`
- Method: POST
- Auth: Bearer JWT (service, server-to-server) OR user session depending on deployment
- Content-Type: application/json

Request body:
```
{
  "agent_type": "string",               // e.g., "lead_agent", "chat_agent"
  "input": { "...": "..." },          // Arbitrary JSON input for the agent
  "user_id": "string",                 // Optional: end-user identifier
  "metadata": { "...": "..." }        // Optional: correlation or tracking metadata
}
```

Response body (success):
```
{
  "request_id": "string",
  "status": "queued" | "running" | "completed" | "failed",
  "result": { "...": "..." },      // Present when status is completed
  "error": "string|null"            // Present when status is failed
}
```

### Payments (Stripe)

Enable server-side Stripe payments for subscriptions or one-off charges.

- Endpoints
  - `POST /api/payments/create-checkout-session`
    - Creates a Stripe Checkout Session. Request body:
      ```json
      {
        "price_id": "price_123",          // optional if STRIPE_PRICE_ID is set
        "mode": "subscription",           // or "payment"
        "success_url": "https://app.example.com/payments/success",
        "cancel_url": "https://app.example.com/payments/cancel",
        "customer_email": "user@example.com",
        "metadata": {"package_id": "uuid"}
      }
      ```
    - Response:
      ```json
      { "id": "cs_XXX", "url": "https://checkout.stripe.com/..." }
      ```

  - `POST /api/payments/webhook`
    - Receives Stripe events. Verifies signature using `STRIPE_WEBHOOK_SECRET`.
    - On `checkout.session.completed` (subscription mode), inserts a record into `user_subscriptions` with `status='active'`, `start_date`, and `final_price`.
    - Note: For full lifecycle (cancellations, upgrades), extend mapping to include Stripe IDs in your schema.

- Environment variables (set in `.env`):
  - `STRIPE_API_KEY` – secret key (test or live)
  - `STRIPE_WEBHOOK_SECRET` – signing secret for your webhook endpoint
  - `STRIPE_PRICE_ID` – default price ID to use when the client does not pass one
  - `STRIPE_MODE` – `subscription` or `payment`
  - `STRIPE_SUCCESS_URL` – frontend success page
  - `STRIPE_CANCEL_URL` – frontend cancel page

- Webhook setup
  - In Stripe Dashboard → Developers → Webhooks, add an endpoint:
    - URL: `https://api.yourdomain.com/api/payments/webhook`
    - Select events: `checkout.session.completed`, `customer.subscription.*` (as needed)
    - Copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

- Testing locally
  - Use `stripe listen --forward-to localhost:8000/api/payments/webhook`
  - Create a session via `POST /api/payments/create-checkout-session` using test price IDs.
  - Complete checkout in Stripe’s hosted page; verify entry in `user_subscriptions`.

- Supabase data model
  - `user_subscriptions` stores subscription records and prices.
  - Extend the table later with `stripe_customer_id`, `stripe_subscription_id` for precise lifecycle tracking.


Response body (error):
```
{
  "error": "Invalid agent_type or input",
  "code": "BAD_REQUEST"
}
```

Common status codes: 200, 400, 401, 403, 500

---

#### POST /api/agents/workflows/execute
Execute an agent workflow (multi-step orchestration).

- URL: `/api/agents/workflows/execute`
- Method: POST
- Auth: Bearer JWT (service) OR user session
- Content-Type: application/json

Request body:
```
{
  "workflow_id": "string",            // Workflow identifier
  "inputs": { "...": "..." },        // Workflow inputs
  "user_id": "string",               // Optional
  "async": true | false                // Optional, default false
}
```

Response body (success):
```
{
  "workflow_run_id": "string",
  "status": "queued" | "running" | "completed" | "failed",
  "outputs": { "...": "..." },     // Present when completed
  "error": "string|null"
}
```

If `async: true`, you typically receive a queued/running status, and final results are delivered over WebSocket events or polling endpoints.

---

### Analytics (overview)
The backend exposes analytics endpoints (see `backend/app/routes/analytics.py`) for aggregated metrics (leads, conversations, revenue). Authentication depends on role.

- Typical responses include summary values and deltas:
```
{
  "total_leads": { "value": 123, "change": 5.4 },
  "active_conversations": { "value": 12, "change": -2.1 },
  "conversion_rate": { "value": 14.2, "change": 0.7 },
  "total_revenue": { "value": 10234, "change": 3.3 }
}
```

### Notifications (overview)
REST endpoints under `backend/app/routes/notifications.py` provide list/fetch operations. Real-time notifications are delivered via the WebSocket `/api/ws/notifications` channel.

---

## WebSockets

### Channels
- `/api/ws/analytics`: Real-time updates for analytics time-series and KPIs.
- `/api/ws/workflows`: Real-time workflow run status updates.
- `/api/ws/notifications`: Real-time user notifications (success, warning, error).

### Authentication Flow
1. Client obtains a JWT (or session token) from the authentication provider (e.g., Supabase or your auth server).
2. Client connects to the WebSocket endpoint using a Bearer token (header) or token query parameter.
   - Example URL: `wss://your-api-host/api/ws/analytics?token=JWT_HERE`
3. Server validates the token, extracts claims (sub/user id, role/scope), and either accepts or closes the connection.
4. On reconnect, client should back off (exponential or jitter) and retry.

Token generation (example claims):
```
{
  "sub": "user-uuid",
  "role": "user" | "admin",
  "exp": 1735689600,
  "iat": 1735603200,
  "scope": ["analytics:read", "notifications:read"]
}
```

### Client Message Schemas
- Subscribe to a topic or stream:
```
{
  "type": "subscribe",
  "topic": "lead_trends",           // Example topics: lead_trends, conversation_trends, workflow_run:<id>
  "params": { "start_date": "ISO", "end_date": "ISO", "aggregation": "daily" }
}
```

- Unsubscribe:
```
{ "type": "unsubscribe", "topic": "lead_trends" }
```

- Ping (optional):
```
{ "type": "ping" }
```

### Server Event Schemas
- Analytics update:
```
{
  "type": "event",
  "channel": "analytics",
  "topic": "lead_trends",
  "data": [ { "date": "ISO", "value": 12 }, ... ],
  "ts": "ISO"
}
```

- Workflow status:
```
{
  "type": "event",
  "channel": "workflows",
  "topic": "workflow_run:abc123",
  "data": { "status": "running" | "completed" | "failed", "progress": 0.6 },
  "ts": "ISO"
}
```

- Notification:
```
{
  "type": "event",
  "channel": "notifications",
  "topic": "user:USER_ID",
  "data": { "id": "uuid", "severity": "success" | "warning" | "error", "title": "...", "message": "...", "action_url": "/path" },
  "ts": "ISO"
}
```

- Error:
```
{
  "type": "error",
  "code": "UNAUTHORIZED" | "INVALID_TOPIC" | "BAD_REQUEST",
  "message": "..."
}
```

---

## Environment Variables

Frontend (Vite):
- `VITE_API_URL`: Base URL for API (http/https). Example: `http://localhost:8000`
- `VITE_SUPABASE_URL`: Supabase URL (for client features)
- `VITE_SUPABASE_PUBLISHABLE_KEY`: Supabase anon/publishable key (never use service key in client)

Backend:
- `API_JWT_SECRET` or keys for signing/validating JWTs
- Service credentials for databases and external services should be kept server-side only.

Supabase Keys:
- Use publishable (anon) key in the browser, with Row Level Security (RLS) protecting data.
- Use service role key only on the server (never in frontend). Ensure the backend loads it from secure env and never exposes it.

---

## Database Schema Mapping to Migrations

The Supabase migrations under `supabase/migrations` define the database schema, functions, and policies. Key areas:

- Notifications tables and triggers:
  - `20250126000009_add_notifications.sql`
- Analytics and metrics:
  - `20250126000002_add_analytics_functions.sql`
  - `20250126000006_add_revenue_analytics.sql`
  - `20250126000007_add_trends_functions.sql`
  - `20250126000003_add_model_metrics.sql`
- Pricing:
  - `20250126000004_add_pricing.sql`
- AI / agents / workflows:
  - `20250126000008_add_workflow_tables.sql`
- Roles and user permissions:
  - `20250126000005_add_user_roles.sql`
- Foundational features:
  - `20250126000000_ai_features_schema.sql`
  - `20250126000001_add_helper_functions.sql`

Consult each file for table definitions (e.g., `notifications`, `pricing_packages`, `pricing_campaigns`), views, functions, and RLS policies.

---

## Examples

### Example: Invoking an agent
```
curl -X POST "$API_URL/api/agents/invoke" \
  -H "Authorization: Bearer $API_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "lead_agent",
    "input": {"query": "Find top prospects in SaaS"},
    "metadata": {"source": "dashboard"}
  }'
```

### Example: Connecting to notifications WebSocket
```
const ws = new WebSocket(`${API_WS}/api/ws/notifications?token=${jwt}`);
ws.onopen = () => ws.send(JSON.stringify({ type: 'subscribe', topic: `user:${userId}` }));
ws.onmessage = (ev) => console.log('event', JSON.parse(ev.data));
```

---

If you change schemas or add endpoints, update this document accordingly.
