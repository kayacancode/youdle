-- Migration: Add last_synced_at to blog_posts
-- Run this SQL in your Supabase SQL Editor to add the last_synced_at field
-- This field tracks when a blog post was last synced with Blogger

-- ============================================================================
-- Add last_synced_at column to blog_posts table
-- ============================================================================

-- Add the column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'blog_posts'
        AND column_name = 'last_synced_at'
    ) THEN
        ALTER TABLE blog_posts ADD COLUMN last_synced_at TIMESTAMPTZ;
        RAISE NOTICE 'Column last_synced_at added to blog_posts table';
    ELSE
        RAISE NOTICE 'Column last_synced_at already exists in blog_posts table';
    END IF;
END $$;

-- Create index for efficient queries on last_synced_at
CREATE INDEX IF NOT EXISTS idx_blog_posts_last_synced_at ON blog_posts(last_synced_at DESC);

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Added: last_synced_at field to blog_posts table';
END $$;
