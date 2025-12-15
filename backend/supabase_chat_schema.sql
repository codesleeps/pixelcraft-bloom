-- Chat History Tables for Supabase
-- Run this in Supabase SQL Editor to create the necessary tables

-- Conversations table to store all chat messages
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    session_id TEXT,
    user_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_deleted_at ON conversations(deleted_at) WHERE deleted_at IS NULL;

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations for service role (backend)
CREATE POLICY "Enable all for service role" ON conversations
    FOR ALL
    USING (true);

-- Optional: Add policy for authenticated users to only see their own conversations
CREATE POLICY "Users can view their own conversations" ON conversations
    FOR SELECT
    USING (auth.uid()::text = user_id);
