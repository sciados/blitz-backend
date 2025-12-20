-- Migration 034: Add error_code column to video_generations
-- This SQL can be run directly on the database

-- Add error_code column if it doesn't exist (PostgreSQL 10+)
ALTER TABLE video_generations ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);

-- Note: This is safe to run multiple times
