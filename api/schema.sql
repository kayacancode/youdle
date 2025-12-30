-- Supabase Schema for Youdle Dashboard
-- Run this SQL in your Supabase SQL Editor
-- NOTE: This will create tables if they don't exist

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Job Queue Table (REQUIRED for dashboard)
-- Tracks generation jobs and their status
-- ============================================================================
DROP TABLE IF EXISTS job_queue CASCADE;
CREATE TABLE job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    config JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster status queries
CREATE INDEX idx_job_queue_status ON job_queue(status);
CREATE INDEX idx_job_queue_started_at ON job_queue(started_at DESC);

-- ============================================================================
-- Blog Posts Table (REQUIRED for dashboard)
-- Stores generated blog posts
-- ============================================================================
DROP TABLE IF EXISTS blog_posts CASCADE;
CREATE TABLE blog_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    html_content TEXT NOT NULL,
    image_url TEXT,
    category TEXT NOT NULL DEFAULT 'SHOPPERS' CHECK (category IN ('SHOPPERS', 'RECALL')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'reviewed', 'published')),
    article_url TEXT,
    job_id UUID REFERENCES job_queue(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_category ON blog_posts(category);
CREATE INDEX idx_blog_posts_job_id ON blog_posts(job_id);
CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at DESC);

-- ============================================================================
-- Feedback Table (REQUIRED for review workflow)
-- Stores human feedback on generated posts
-- ============================================================================
DROP TABLE IF EXISTS feedback CASCADE;
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    feedback_type TEXT DEFAULT 'general' CHECK (feedback_type IN ('general', 'content', 'formatting', 'accuracy', 'tone')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for post feedback queries
CREATE INDEX idx_feedback_post_id ON feedback(post_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);

-- ============================================================================
-- Row Level Security (RLS)
-- Enable RLS but allow all operations for now (no auth)
-- ============================================================================
ALTER TABLE job_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- Allow all operations (adjust for production with proper auth)
DROP POLICY IF EXISTS "Allow all for job_queue" ON job_queue;
DROP POLICY IF EXISTS "Allow all for blog_posts" ON blog_posts;
DROP POLICY IF EXISTS "Allow all for feedback" ON feedback;

CREATE POLICY "Allow all for job_queue" ON job_queue FOR ALL USING (true);
CREATE POLICY "Allow all for blog_posts" ON blog_posts FOR ALL USING (true);
CREATE POLICY "Allow all for feedback" ON feedback FOR ALL USING (true);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for blog_posts updated_at
DROP TRIGGER IF EXISTS update_blog_posts_updated_at ON blog_posts;
CREATE TRIGGER update_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Enable Realtime (optional - comment out if you get errors)
-- ============================================================================
-- Note: If these fail, your Supabase project may not have realtime enabled
-- You can safely skip these lines

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE job_queue;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add job_queue to realtime: %', SQLERRM;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE blog_posts;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add blog_posts to realtime: %', SQLERRM;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE feedback;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add feedback to realtime: %', SQLERRM;
END $$;

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Schema created successfully! Tables: job_queue, blog_posts, feedback';
END $$;
