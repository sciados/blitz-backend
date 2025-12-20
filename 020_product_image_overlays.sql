-- Migration: Add product_image_overlays table
-- Run this in pgAdmin SQL editor

CREATE TABLE product_image_overlays (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    image_source VARCHAR(50) NOT NULL CHECK (image_source IN ('intelligence', 'uploaded')),
    product_intelligence_id INTEGER REFERENCES product_intelligence(id) ON DELETE SET NULL,
    position_x FLOAT NOT NULL DEFAULT 0.5,  -- 0.0 to 1.0 (left to right)
    position_y FLOAT NOT NULL DEFAULT 0.5,  -- 0.0 to 1.0 (top to bottom)
    scale FLOAT NOT NULL DEFAULT 1.0,       -- 0.1 to 3.0 (size multiplier)
    rotation FLOAT NOT NULL DEFAULT 0.0,    -- degrees
    opacity FLOAT NOT NULL DEFAULT 1.0,     -- 0.0 to 1.0 (transparency)
    z_index INTEGER NOT NULL DEFAULT 1,     -- layer stacking order
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_product_image_overlays_campaign_id ON product_image_overlays(campaign_id);
CREATE INDEX idx_product_image_overlays_product_intelligence_id ON product_image_overlays(product_intelligence_id);
CREATE INDEX idx_product_image_overlays_z_index ON product_image_overlays(z_index);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_product_image_overlays_updated_at
    BEFORE UPDATE ON product_image_overlays
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add foreign key constraint for created_by (if users table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        ALTER TABLE product_image_overlays
        ADD CONSTRAINT fk_product_image_overlays_created_by
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;
