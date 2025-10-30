# PixelCraft AI Backend

This directory contains a FastAPI-based backend scaffold for PixelCraft. It provides AI automation via AgentScope and local Ollama models, and persists data to Supabase.

## Overview

- Framework: FastAPI
- LLMs: Ollama (local) via AgentScope
- Database: Supabase (Postgres)

## Prerequisites

- Python 3.10+
- Ollama installed locally (https://ollama.com)
- Supabase project and service role key

## Setup

1. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy and configure environment variables:

```bash
cp .env.example .env
# Edit .env and add SUPABASE_KEY and other secrets
```

4. (Optional) Pull an Ollama model:

```bash
# ollama pull llama3
```

## Running the server

Development mode (auto-reload):

```bash
cd backend
python run.py --reload
```

Open the API docs at: http://localhost:8000/docs

## API Endpoints (summary)

- `POST /api/chat/message` — send a chat message
- `POST /api/chat/stream` — streaming chat responses
- `GET /api/chat/history/{conversation_id}` — conversation history
- `DELETE /api/chat/history/{conversation_id}` — clear history
- `GET /api/agents` — list agents
- `GET /api/agents/{agent_type}` — agent detail
- `POST /api/agents/invoke` — invoke an agent
- `GET /api/agents/health` — agents health
- `POST /api/leads/submit` — submit a lead
- `GET /api/leads/{lead_id}` — get lead
- `POST /api/leads/{lead_id}/analyze` — analyze an existing lead
- `GET /api/leads` — list leads

## Next steps

- Implement AgentScope agent implementations (chat, lead_qualification)
- Add database migrations for `leads`, `conversations`, and `agent_logs` tables
- Add proper streaming SSE responses and authentication
# PixelCraft AI Backend

This directory contains the Python FastAPI backend for PixelCraft, designed to integrate with AgentScope and Ollama for open-source LLM usage and Supabase for persistence.

Overview
- Framework: FastAPI
- LLM Orchestration: AgentScope + Ollama (local)
- Database: Supabase (Postgres)
- Language: Python 3.10+

Prerequisites
- Python 3.10+
- Ollama installed (~ https://ollama.ai)
- Supabase project and service role key

Quick start

1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in credentials (SUPABASE_KEY, etc.)

4. Run the development server

```bash
python run.py --reload
```

API
- Swagger UI: http://localhost:8000/docs
- Health: GET /health
- Chat endpoints: /api/chat
- Agents endpoints: /api/agents
- Leads endpoints: /api/leads

Project structure
- `app/` - main application package
  - `models/` - Pydantic request/response schemas
  - `routes/` - FastAPI routers (chat, agents, leads)
  - `agents/` - AgentScope agent scaffolding
  - `utils/` - helper clients for Supabase and Ollama

## External API Integrations

### Overview
Agents can integrate with external services (CRM, email, calendar) to automate lead management and client communication. Supported integrations include HubSpot (CRM), SendGrid (Email), and Google Calendar. All integrations are optional, and agents gracefully degrade when not configured.

### Configuration
Reference the `.env.example` file for required environment variables. Follow these step-by-step setup instructions for each service:

1. **HubSpot CRM**: Create a Private App in HubSpot (Settings > Integrations > Private Apps), copy the access token, and set `CRM_API_KEY`.
2. **SendGrid Email**: Create an API key in SendGrid (Settings > API Keys) with Mail Send permissions and set `EMAIL_API_KEY`.
3. **Google Calendar**: Create a Google Cloud project, enable the Calendar API, generate credentials, and set `CALENDAR_API_KEY`.

### Available Tools
The following external tools are available to each agent:

- **Web Development Agent**: `create_project_lead`, `schedule_technical_consultation`
- **Digital Marketing Agent**: `create_marketing_lead`, `send_marketing_proposal`, `schedule_strategy_session`
- **Lead Qualification Agent**: `sync_lead_to_crm`, `send_qualification_notification`, `schedule_qualification_call`

### Tool Execution Logging
All tool executions are logged to the `agent_logs` table with timing, parameters, results, and errors. This enables analytics on tool usage and debugging of external API issues.

### Error Handling
If external services are unavailable, agents continue to function but skip external tool calls (graceful degradation). Errors are logged but do not fail the agent's primary function.

### Testing
To test external integrations:
- Check the health endpoint: `GET /health` returns external service status.
- Review agent logs: Query the `agent_logs` table for `action LIKE 'tool_execution:%'`.
- Monitor tool execution times and error rates.

### Security Notes
API keys should never be committed to version control. Use environment-specific credentials (dev, staging, production) and rotate API keys regularly.

## Advanced Agent Workflows

### Overview
The advanced agent workflow system enables sophisticated multi-agent orchestration with state management, agent-to-agent messaging, and shared memory. This allows for complex use cases such as multi-step lead qualification, collaborative service recommendations, and dynamic problem-solving where agents can communicate and share context in real-time.

### Workflow Types
1. **Multi-Agent Workflow**: Sequential execution of multiple agents (chat → recommendations → lead qualification)
2. **Conditional Workflow**: Dynamic routing based on agent responses and conditions
3. **Collaborative Workflow**: Agents communicate via messages and share context through shared memory

### Key Features
- **State Management**: Track workflow execution state (pending, running, completed, failed, paused)
- **Agent-to-Agent Messaging**: Agents can send requests, responses, notifications, and handoffs to each other
- **Shared Memory**: Conversation-scoped and workflow-scoped memory accessible to all participating agents
- **Real-time Visualization**: WebSocket endpoint for monitoring workflow execution in real-time
- **Conditional Routing**: Route to different agents based on response metadata (e.g., lead score, user intent)

### API Endpoints
- `POST /api/agents/workflows/execute` - Start a new workflow
- `GET /api/agents/workflows/{workflow_id}` - Get workflow status
- `GET /api/agents/workflows/{workflow_id}/visualization` - Get visualization data
- `POST /api/agents/workflows/{workflow_id}/messages` - Send agent message
- `PATCH /api/agents/workflows/{workflow_id}/state` - Update workflow state
- `WS /api/ws/workflows/{workflow_id}` - Real-time workflow updates

### Database Tables
- `workflow_executions`: Tracks workflow state and results
- `agent_messages`: Stores agent-to-agent messages
- `shared_memory`: Stores shared context accessible to all agents

### Example Usage
```python
# Start a conditional workflow
workflow_request = {
    "workflow_type": "conditional",
    "conversation_id": "conv_123",
    "participating_agents": ["chat", "lead_qualification", "web_development"],
    "workflow_config": {
        "routing_rules": {
            "conditions": [
                {"field": "metadata.lead_score", "operator": ">", "value": 70, "next_agent": "web_development"},
                {"default": "chat"}
            ]
        }
    },
    "input_data": {"message": "I need a website"}
}

response = await client.post("/api/agents/workflows/execute", json=workflow_request)
workflow_id = response.json()["workflow_id"]

# Monitor workflow in real-time via WebSocket
ws = await websocket_connect(f"/api/ws/workflows/{workflow_id}?token={jwt_token}")
```

### Shared Memory Usage
```python
# In an agent's process_message method
await self.set_shared_memory(conversation_id, "user_intent", intent_data, scope="workflow")
user_needs = await self.get_shared_memory(conversation_id, "user_needs", scope="workflow")
```

### Agent Messaging
```python
# Send message from one agent to another
await orchestrator.send_agent_message(
    workflow_execution_id=workflow_id,
    from_agent="chat",
    to_agent="web_development",
    message_type="handoff",
    content={"reason": "technical_consultation_needed", "context": conversation_summary}
)
```

### Testing
- Run workflow tests: `python backend/test_agents.py`
- Tests cover conditional routing, agent messaging, shared memory, and visualization

### Monitoring
- View workflow execution in real-time via WebSocket
- Query workflow_executions table for historical data
- Check agent_logs table for detailed agent actions
- Monitor agent_messages table for communication patterns

Next steps
- Implement AgentScope agents under `app/agents/`.
- Add tests and CI for backend code.
- Harden security (vault secrets, rotated keys, RLS policies in Supabase).
