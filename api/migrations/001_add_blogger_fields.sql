-- Migration: Add Blogger integration fields to blog_posts table
-- Run this in Supabase SQL Editor to add Blogger fields to existing table

-- Add Blogger fields (safe to run multiple times - will skip if exists)
ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS blogger_post_id TEXT;

ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS blogger_url TEXT;

ALTER TABLE blog_posts
ADD COLUMN IF NOT EXISTS blogger_published_at TIMESTAMPTZ;

-- Create index for faster Blogger URL lookups
CREATE INDEX IF NOT EXISTS idx_blog_posts_blogger_post_id ON blog_posts(blogger_post_id);

-- Verify migration
DO $$
BEGIN
    RAISE NOTICE 'Migration complete: Blogger fields added to blog_posts table';
END $$;
