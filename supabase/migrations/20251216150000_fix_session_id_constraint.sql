-- Migration: Fix session_id constraint violation
-- Date: 2025-12-16
-- Issue: ERROR 23502 - null value in column "session_id" violates not-null constraint
-- Purpose: Remove NOT NULL and UNIQUE constraints from session_id column to align with consolidated schema
-- Context:
--   - supabase/migrations/20250126000000_ai_features_schema.sql defined session_id as NOT NULL UNIQUE
--   - backend/consolidated_migration.sql and database/supabase_schema.sql define session_id as nullable (TEXT)
--   - backend/payload_fix_errors.sql inserts rows without session_id
--   - Application code queries by session_id but does not provide it during insert
-- This migration makes session_id optional and removes uniqueness so multiple conversations can share the same session.

BEGIN;

-- Remove NOT NULL constraint (safe if column exists)
ALTER TABLE public.conversations
  ALTER COLUMN session_id DROP NOT NULL;

-- Remove UNIQUE constraint if it exists (default name: conversations_session_id_key)
ALTER TABLE public.conversations
  DROP CONSTRAINT IF EXISTS conversations_session_id_key;

-- Keep existing non-unique index (if any) for performance; do not drop idx_conversations_session_id
-- Add comment documenting the intent
COMMENT ON COLUMN public.conversations.session_id IS
  'Optional session identifier for grouping related conversations. Nullable to support legacy data and flexible session management.';

COMMIT;

-- Verification: Check column definition
SELECT
  column_name,
  is_nullable,
  data_type,
  character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'conversations'
  AND column_name = 'session_id';

-- Verification: Check constraints on session_id
SELECT
  conname AS constraint_name,
  contype AS constraint_type
FROM pg_constraint
WHERE conrelid = 'public.conversations'::regclass
  AND conname LIKE '%session_id%';

-- Note: Ensure any performance index like idx_conversations_session_id remains in place (non-unique)
-- If it was previously unique, recreate it as non-unique separately if needed:
-- CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON public.conversations (session_id);
