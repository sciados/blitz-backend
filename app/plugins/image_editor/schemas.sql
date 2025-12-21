-- Image Editor Plugin Database Schema
-- Ran in pgAdmin and already created the image_edits table

-- Table to track all image editing operations
CREATE TABLE IF NOT EXISTS image_edits (
    id SERIAL PRIMARY KEY,
    
    -- User & Campaign Context
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    
    -- Image Paths
    original_image_path TEXT NOT NULL,  -- Original image path in R2
    edited_image_path TEXT NOT NULL,    -- Path to edited version in /edited/ folder
    
    -- Edit Operation Details
    operation_type VARCHAR(50) NOT NULL, -- 'inpainting', 'outpainting', 'background_removal', etc.
    operation_params JSONB,              -- Store the parameters used (prompt, mask, etc.)
    
    -- Stability AI Usage Tracking
    stability_model VARCHAR(100),        -- Model used (e.g., 'sd3-large-turbo')
    api_cost_credits DECIMAL(10, 4),     -- Cost in Stability AI credits
    processing_time_ms INTEGER,          -- Time taken to process
    
    -- Metadata
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_image_edits_user_id ON image_edits(user_id);
CREATE INDEX idx_image_edits_campaign_id ON image_edits(campaign_id);
CREATE INDEX idx_image_edits_created_at ON image_edits(created_at DESC);
CREATE INDEX idx_image_edits_operation_type ON image_edits(operation_type);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_image_edits_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the update function
CREATE TRIGGER trigger_update_image_edits_updated_at
    BEFORE UPDATE ON image_edits
    FOR EACH ROW
    EXECUTE FUNCTION update_image_edits_updated_at();

-- Optional: View for edit statistics per user
CREATE OR REPLACE VIEW user_edit_statistics AS
SELECT 
    user_id,
    COUNT(*) as total_edits,
    COUNT(CASE WHEN success = true THEN 1 END) as successful_edits,
    COUNT(CASE WHEN success = false THEN 1 END) as failed_edits,
    SUM(api_cost_credits) as total_credits_used,
    AVG(processing_time_ms) as avg_processing_time_ms,
    operation_type,
    DATE(created_at) as edit_date
FROM image_edits
GROUP BY user_id, operation_type, DATE(created_at);

-- Optional: View for campaign edit history
CREATE OR REPLACE VIEW campaign_edit_history AS
SELECT 
    ie.id,
    ie.campaign_id,
    c.name as campaign_name,
    ie.user_id,
    u.email as user_email,
    ie.original_image_path,
    ie.edited_image_path,
    ie.operation_type,
    ie.success,
    ie.created_at
FROM image_edits ie
LEFT JOIN campaigns c ON ie.campaign_id = c.id
LEFT JOIN users u ON ie.user_id = u.id
ORDER BY ie.created_at DESC;
