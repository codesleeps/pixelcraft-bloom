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

Next steps
- Implement AgentScope agents under `app/agents/`.
- Add tests and CI for backend code.
- Harden security (vault secrets, rotated keys, RLS policies in Supabase).
