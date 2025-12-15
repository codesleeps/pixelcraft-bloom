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
DROP POLICY IF EXISTS "Enable all for service role" ON model_metrics;
DROP POLICY IF EXISTS "Service role full access" ON model_metrics;

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
