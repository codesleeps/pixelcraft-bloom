# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PixelCraft Bloom is a full-stack application built with:
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python) + AgentScope + Ollama (local LLMs) + Supabase
- **Authentication**: Supabase Auth with role-based access control
- **Database**: Supabase (PostgreSQL)

## Common Commands

### Frontend Development

```bash
# Install dependencies
npm i

# Start development server (runs on http://localhost:8080)
npm run dev

# Build for production
npm run build

# Build for development (with dev mode)
npm run build:dev

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Testing (Frontend)

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage

# Coverage report with UI
npm run test:coverage:ui
```

Test coverage thresholds are set to 70% for branches, functions, lines, and statements.

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env and add SUPABASE_KEY and other secrets

# Run development server with auto-reload
python run.py --reload

# Access API documentation
# http://localhost:8000/docs
```

### Backend Prerequisites

1. **Ollama**: Install from https://ollama.com
   - Pull a model: `ollama pull llama3`
   - Default host: http://localhost:11434

2. **Supabase**: Project and service role key required
   - Configure SUPABASE_URL and SUPABASE_KEY in backend/.env

## Architecture

### Frontend Architecture

**Entry Point**: `src/main.tsx` → `src/App.tsx`

**Routing**: HashRouter with these routes:
- `/` - Landing page (Index)
- `/auth` - Authentication page
- `/strategy-session` - Strategy session form
- `/partnership` - Partnership information
- `/dashboard` - Protected dashboard (requires authentication)

**Key Directories**:
- `src/components/` - React components including shadcn/ui components in `ui/` subdirectory
- `src/pages/` - Page-level components (Auth, Dashboard, Index, ModelAnalytics, ModelTest, NotFound, Partnership, StrategySession)
- `src/hooks/` - Custom React hooks (including `useAuth` for authentication)
- `src/integrations/supabase/` - Supabase client and type definitions
- `src/lib/` - Utility functions (e.g., `cn()` for className merging)
- `src/types/` - TypeScript type definitions
- `src/test/` - Test setup and test files

**State Management**:
- React Query (@tanstack/react-query) for server state
- Context API for authentication (AuthProvider in `src/hooks/useAuth.tsx`)

**Styling**: Tailwind CSS with path alias `@/` pointing to `src/`

**Authentication Flow**:
- Supabase Auth with email/password
- Role-based access control (admin/user roles)
- User profiles stored in `user_profiles` table with role field
- Protected routes wrapped with `ProtectedRoute` component

### Backend Architecture

**Entry Point**: `backend/run.py` → `backend/app/main.py`

**API Structure** (all routes under `/api` prefix):
- `/api/chat/` - Chat endpoints (message, stream, history)
- `/api/agents/` - Agent management endpoints (list, detail, invoke, health)
- `/api/leads/` - Lead management endpoints (submit, get, analyze, list)
- `/api/pricing/` - Pricing calculation endpoints
- `/api/analytics/` - Analytics and metrics endpoints

**Agent System**:

The backend uses an **orchestrator pattern** with multiple specialized agents:

1. **AgentOrchestrator** (`backend/app/agents/orchestrator.py`):
   - Central coordinator for all agents
   - Handles agent registration, routing, and workflow execution
   - Routes messages based on keywords to appropriate specialized agents
   - Logs execution metrics to Supabase `agent_logs` table
   - Supports multi-agent workflows (chat → recommendations → lead qualification)

2. **Specialized Agents** (all extend `BaseAgent`):
   - `chat_agent` - General conversation handling
   - `lead_qualification` - Analyzes and scores leads
   - `service_recommendation` - Recommends services based on needs
   - `web_development_agent` - Website/web development inquiries
   - `digital_marketing_agent` - Marketing and SEO queries
   - `brand_design_agent` - Branding and design questions
   - `ecommerce_solutions_agent` - E-commerce platform queries
   - `content_creation_agent` - Content writing and creation
   - `analytics_consulting_agent` - Analytics and data tracking

3. **Base Agent System** (`backend/app/agents/base.py`):
   - `BaseAgent` class provides:
     - Memory management per conversation
     - Tool usage framework
     - System prompt building
     - Interaction logging to Supabase
   - `AgentMemory` tracks conversation history
   - `AgentTool` defines available tools with validation
   - `AgentResponse` standardized response format

**Key Backend Directories**:
- `backend/app/agents/` - Agent implementations and orchestration
- `backend/app/routes/` - FastAPI route handlers
- `backend/app/models/` - Pydantic models for request/response schemas
- `backend/app/utils/` - Utility clients (Ollama, Supabase, auth, logging)

**Database Tables** (Supabase):
- `leads` - Lead information and qualification data
- `conversations` - Chat conversation history
- `agent_logs` - Agent execution metrics and logs
- `user_profiles` - User profile data with roles

**LLM Integration**:
- Uses Ollama for local LLM inference
- AgentScope framework for agent orchestration
- Default model: llama3 (configurable via OLLAMA_MODEL env var)

## Development Guidelines

### TypeScript Configuration

The project uses relaxed TypeScript settings:
- `noImplicitAny: false`
- `noUnusedParameters: false`
- `noUnusedLocals: false`
- `strictNullChecks: false`

When adding code, follow the existing patterns and don't enforce strict type checking unless explicitly requested.

### Import Aliases

Use the `@/` alias for imports:
```typescript
import { Button } from "@/components/ui/button"
import { supabase } from "@/integrations/supabase/client"
```

### Styling Patterns

Use Tailwind CSS with the `cn()` utility for conditional classes:
```typescript
import { cn } from "@/lib/utils"

<div className={cn("base-classes", condition && "conditional-classes")} />
```

### Authentication Patterns

Access authentication state via the `useAuth` hook:
```typescript
import { useAuth } from "@/hooks/useAuth"

const { user, session, role, loading, signIn, signOut } = useAuth()
```

### Backend Agent Development

When creating or modifying agents:

1. Extend `BaseAgent` class
2. Define agent configuration with `BaseAgentConfig`
3. Implement `process_message()` method
4. Register agent in orchestrator
5. Add routing keywords to `orchestrator.route_message()` if needed
6. Use agent memory for conversation context
7. Log interactions via `_log_interaction()`

Example agent structure:
```python
from .base import BaseAgent, BaseAgentConfig, AgentResponse

def create_my_agent(model: str = "llama3") -> BaseAgent:
    config = BaseAgentConfig(
        agent_id="my_agent",
        name="My Agent",
        description="Agent description",
        default_model=model,
        system_prompt="System instructions here",
        capabilities=["capability1", "capability2"]
    )
    return BaseAgent(config)
```

### Environment Variables

**Frontend** (`.env` in root):
- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY` - Supabase anon/publishable key (client-safe)

**Backend** (`backend/.env`):
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key (NEVER expose to frontend)
- `SUPABASE_JWT_SECRET` - JWT secret for authentication
- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Default LLM model (default: llama3)
- `CORS_ORIGINS` - Comma-separated allowed CORS origins

## Testing Strategy

- Frontend tests use Vitest + Testing Library
- Test setup in `src/test/setup.ts`
- Use `@testing-library/react` for component tests
- Use `@testing-library/jest-dom` matchers for assertions
- Backend test files: `backend/test_*.py`

## Deployment Notes

**Frontend**:
- Production build uses base path `/pixelcraft-bloom/`
- Development uses base path `./`
- Can deploy via Lovable platform

**Backend**:
- FastAPI server runs on port 8000 by default
- Requires Ollama running locally or remotely
- Requires Supabase project with proper table setup
- Update CORS_ORIGINS for production domain

## Agent Workflow Patterns

**Single Agent Invocation**:
```python
orchestrator = AgentOrchestrator()
response = await orchestrator.invoke(
    agent_id="chat",
    input_data={"message": "Hello"},
    conversation_id="conv_123"
)
```

**Smart Routing**:
```python
# Automatically routes to appropriate agent based on message content
response = await orchestrator.route_message(
    message="I need help with SEO",
    conversation_id="conv_123"
)
```

**Multi-Agent Workflow**:
```python
# Executes multiple agents in sequence
results = await orchestrator.multi_agent_workflow(
    input_data={"message": "I need a website"},
    conversation_id="conv_123",
    run_chat=True,
    run_recommendations=True,
    run_lead_analysis=True
)
```
