-- Create Enum for status if it doesn't exist
DO $$ BEGIN
    CREATE TYPE model_status AS ENUM ('success', 'error');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Table definition with improvements
CREATE TABLE IF NOT EXISTS model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    tokens_in INTEGER DEFAULT 0 NOT NULL,
    tokens_out INTEGER DEFAULT 0 NOT NULL,
    latency_ms INTEGER,
    status model_status, -- Uses the ENUM
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB
);

-- Compound index for common queries (finding recent metrics for specific models)
CREATE INDEX IF NOT EXISTS idx_model_metrics_lookup 
ON model_metrics(model_name, created_at DESC);

-- GIN index for metadata querying
CREATE INDEX IF NOT EXISTS idx_model_metrics_metadata 
ON model_metrics USING GIN (metadata);

-- Enable RLS
ALTER TABLE model_metrics ENABLE ROW LEVEL SECURITY;

-- Drop generic policies if they exist to avoid confusion
-- Drop any existing policies to avoid conflicts (safely)
DROP POLICY IF EXISTS "Enable all for service role" ON model_metrics;
DROP POLICY IF EXISTS "Service role full access" ON model_metrics;
DROP POLICY IF EXISTS "Authenticated read access" ON model_metrics;

-- Secure Policy: Service Role Full Access (Backend use)
CREATE POLICY "Service role full access" 
ON model_metrics 
TO service_role 
USING (true) 
WITH CHECK (true);

-- Read-only policy for authenticated users (Dashboard use)
CREATE POLICY "Authenticated read access" 
ON model_metrics 
FOR SELECT 
TO authenticated 
USING (true);

-- Ensure channel column exists on conversations (from previous fix)
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS channel TEXT DEFAULT 'chat';

-- Create workflow_executions table if it doesn't exist
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(50) NOT NULL,
    current_state VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_step VARCHAR(50),
    participating_agents TEXT[],
    workflow_config JSONB DEFAULT '{}',
    execution_plan JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying
CREATE INDEX IF NOT EXISTS idx_workflow_conversation ON workflow_executions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_workflow_type ON workflow_executions(workflow_type);

-- RLS Policies
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" 
ON workflow_executions 
TO service_role 
USING (true) 
WITH CHECK (true);

CREATE POLICY "Authenticated read access" 
ON workflow_executions 
FOR SELECT 
TO authenticated 
USING (true);

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload config';
