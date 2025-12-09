-- Migration 034: Add error_code column to video_generations
-- This SQL can be run directly on the database

-- Add error_code column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'video_generations'
        AND column_name = 'error_code'
    ) THEN
        ALTER TABLE video_generations ADD COLUMN error_code VARCHAR(50);
        RAISE NOTICE 'Added error_code column to video_generations table';
    ELSE
        RAISE NOTICE 'error_code column already exists, skipping';
    END IF;
END
$$;
