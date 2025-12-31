-- Delete orphaned image records from GeneratedImage table
-- These are records where the image_url points to a file that doesn't exist

-- First, let's see what orphaned records exist:
-- SELECT id, image_url, campaign_id, created_at
-- FROM generated_images
-- WHERE image_url NOT LIKE '%placeholder%'
-- ORDER BY created_at DESC;

-- Delete orphaned records from GeneratedImage table
-- (Uncomment the DELETE line when you're ready to run it)

-- DELETE FROM generated_images
-- WHERE id IN (
--     SELECT id FROM generated_images
--     WHERE image_url NOT LIKE '%placeholder%'
--     -- Add more conditions to identify orphaned records
-- );

-- Delete orphaned records from ImageEdit table
-- (Uncomment the DELETE line when you're ready to run it)

-- DELETE FROM image_edits
-- WHERE id IN (
--     SELECT id FROM image_edits
--     WHERE edited_image_path IS NOT NULL
--     -- Add more conditions to identify orphaned records
-- );

-- Example: Delete records with IDs that you know are orphaned
-- Replace 1, 2, 3 with the actual IDs of orphaned records

-- DELETE FROM generated_images WHERE id IN (1, 2, 3);
-- DELETE FROM image_edits WHERE id IN (4, 5, 6);
