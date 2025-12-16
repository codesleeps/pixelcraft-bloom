-- ============================================================================
-- PAYLOAD: MASTER FIX FOR LEGACY MAPPING AND SCHEMA
-- ============================================================================
-- Targeted fix for Legacy ID: baeec2ec-5ce3-479e-9333-f5d7903c8b34
-- New UUID Mapping: 38c0612e-1405-44b4-bf22-13dd59f41b21
-- ============================================================================

BEGIN;

-- 1. Ensure Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Fix Legacy Conversation Mapping
DO $$
DECLARE
    target_legacy_id TEXT := 'baeec2ec-5ce3-479e-9333-f5d7903c8b34';
    new_uuid UUID := '38c0612e-1405-44b4-bf22-13dd59f41b21';
BEGIN
    RAISE NOTICE 'Attempting to map Legacy ID % to UUID %', target_legacy_id, new_uuid;

    IF EXISTS (SELECT 1 FROM public.conversations WHERE conversation_id = target_legacy_id) THEN
        -- Update existing record
        UPDATE public.conversations 
        SET id = new_uuid
        WHERE conversation_id = target_legacy_id;
        RAISE NOTICE 'Updated existing conversation record.';
    ELSE
        -- Insert new record if missing
        INSERT INTO public.conversations (
            id, 
            conversation_id, 
            role, 
            content, 
            status,
            created_at,
            updated_at
        )
        VALUES (
            new_uuid, 
            target_legacy_id,
            'system',
            'Legacy conversation restored via payload fix.',
            'active',
            NOW(),
            NOW()
        );
        RAISE NOTICE 'Inserted new conversation record for legacy ID.';
    END IF;
END $$;

-- 3. Verify Model Metrics Schema (Self-Healing)
DO $$
BEGIN
    -- Ensure status enum exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model_status') THEN
        CREATE TYPE model_status AS ENUM ('success', 'error', 'processing');
    END IF;

    -- Ensure columns exist
    ALTER TABLE public.model_metrics ADD COLUMN IF NOT EXISTS latency_ms INTEGER;
    ALTER TABLE public.model_metrics ADD COLUMN IF NOT EXISTS status model_status DEFAULT 'processing';
    
    RAISE NOTICE 'Model metrics schema verified.';
END $$;

COMMIT;

-- 4. Final Status Report
SELECT 
    id, 
    conversation_id, 
    created_at 
FROM public.conversations 
WHERE conversation_id = 'baeec2ec-5ce3-479e-9333-f5d7903c8b34';
