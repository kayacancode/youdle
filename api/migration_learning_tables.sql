-- Migration: Add Learning System Tables
-- Run this SQL in your Supabase SQL Editor to add the missing tables
-- This adds the learning_insights, blog_examples, and blog_feedback tables

-- ============================================================================
-- Blog Examples Table
-- Stores example blog posts for learning and improvement
-- ============================================================================
CREATE TABLE IF NOT EXISTS blog_examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_article_url TEXT NOT NULL,
    original_article_title TEXT NOT NULL,
    generated_html TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('shoppers', 'recall')),
    feedback_score INT DEFAULT 0 CHECK (feedback_score >= 0 AND feedback_score <= 5),
    feedback_comments TEXT DEFAULT '',
    is_good_example BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for blog_examples
CREATE INDEX IF NOT EXISTS idx_blog_examples_category ON blog_examples(category);
CREATE INDEX IF NOT EXISTS idx_blog_examples_is_good ON blog_examples(is_good_example);
CREATE INDEX IF NOT EXISTS idx_blog_examples_score ON blog_examples(feedback_score DESC);
CREATE INDEX IF NOT EXISTS idx_blog_examples_created_at ON blog_examples(created_at DESC);

-- ============================================================================
-- Blog Feedback Table
-- Stores detailed feedback for blog posts (different from the general feedback table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS blog_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blog_post_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('structure', 'content', 'tone', 'completeness', 'general')),
    score INT NOT NULL CHECK (score >= 1 AND score <= 5),
    comments TEXT DEFAULT '',
    approved BOOLEAN DEFAULT false,
    reviewer_notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for blog_feedback
CREATE INDEX IF NOT EXISTS idx_blog_feedback_post_id ON blog_feedback(blog_post_id);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_type ON blog_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_score ON blog_feedback(score);
CREATE INDEX IF NOT EXISTS idx_blog_feedback_created_at ON blog_feedback(created_at DESC);

-- ============================================================================
-- Learning Insights Table
-- Stores learning insights and patterns discovered from feedback
-- ============================================================================
CREATE TABLE IF NOT EXISTS learning_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_type TEXT NOT NULL CHECK (insight_type IN ('common_mistake', 'improvement_pattern', 'best_practice', 'user_preference', 'general')),
    description TEXT NOT NULL,
    category TEXT DEFAULT '',
    frequency INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for learning_insights
CREATE INDEX IF NOT EXISTS idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_learning_insights_category ON learning_insights(category);
CREATE INDEX IF NOT EXISTS idx_learning_insights_frequency ON learning_insights(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_learning_insights_created_at ON learning_insights(created_at DESC);

-- ============================================================================
-- Row Level Security (RLS)
-- Enable RLS with open policies (adjust for production with proper auth)
-- ============================================================================
ALTER TABLE blog_examples ENABLE ROW LEVEL SECURITY;
ALTER TABLE blog_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_insights ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Enable all for blog_examples" ON blog_examples;
DROP POLICY IF EXISTS "Enable all for blog_feedback" ON blog_feedback;
DROP POLICY IF EXISTS "Enable all for learning_insights" ON learning_insights;

-- Create open policies (allow all operations)
CREATE POLICY "Enable all for blog_examples" ON blog_examples FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable all for blog_feedback" ON blog_feedback FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable all for learning_insights" ON learning_insights FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- Enable Realtime (optional)
-- ============================================================================
DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE blog_examples;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add blog_examples to realtime: %', SQLERRM;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE blog_feedback;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add blog_feedback to realtime: %', SQLERRM;
END $$;

DO $$
BEGIN
    ALTER PUBLICATION supabase_realtime ADD TABLE learning_insights;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not add learning_insights to realtime: %', SQLERRM;
END $$;

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Learning system tables created successfully!';
    RAISE NOTICE 'Tables added: blog_examples, blog_feedback, learning_insights';
END $$;
