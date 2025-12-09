-- Migration 033: Add missing columns to video_generations
-- This SQL can be run directly on the database

-- Add generation_mode_used column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'video_generations'
        AND column_name = 'generation_mode_used'
    ) THEN
        ALTER TABLE video_generations ADD COLUMN generation_mode_used VARCHAR(50);
    END IF;
END
$$;

-- Add slides column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'video_generations'
        AND column_name = 'slides'
    ) THEN
        ALTER TABLE video_generations ADD COLUMN slides JSONB;
    END IF;
END
$$;
