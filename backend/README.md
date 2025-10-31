# Backend API and WebSocket Documentation

This document describes the REST API endpoints, WebSocket channels and authentication, environment configuration, and database schema mapping used by the PixelCraft Bloom backend.

---

## Table of Contents
- REST API
  - Agents
    - POST /api/agents/invoke
    - POST /api/agents/workflows/execute
  - Analytics (overview)
  - Notifications (overview)
- WebSockets
  - Channels
    - /api/ws/analytics
    - /api/ws/workflows
    - /api/ws/notifications
  - Authentication Flow
  - Client Message Schemas
  - Server Event Schemas
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