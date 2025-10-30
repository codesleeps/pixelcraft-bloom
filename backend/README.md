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

Next steps
- Implement AgentScope agents under `app/agents/`.
- Add tests and CI for backend code.
- Harden security (vault secrets, rotated keys, RLS policies in Supabase).
