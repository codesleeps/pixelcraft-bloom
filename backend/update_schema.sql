-- Add missing channel column to conversations table
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS channel TEXT DEFAULT 'chat';

-- Also create the model_metrics table if you haven't yet
CREATE TABLE IF NOT EXISTS model_metrics (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    tokens_in INTEGER,
    tokens_out INTEGER,
    latency_ms INTEGER,
    status TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_model_metrics_model ON model_metrics(model_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_created_at ON model_metrics(created_at);

ALTER TABLE model_metrics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Enable all for service role" ON model_metrics FOR ALL USING (true);
