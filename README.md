# Youdle Blog Post Generation Agent

A **LangGraph**-orchestrated agent that automatically generates blog posts from news articles, creates images, and sends newsletters via Mailchimp.

## Features

- **LangGraph StateGraph**: Explicit state management with conditional routing and graph visualization
- **Automated Article Search**: Uses Exa AI to find relevant grocery and recall articles
- **AI Blog Post Generation**: LangChain chains + OpenAI for generating HTML blog posts
- **Self-Reflection Loop**: Validates posts and regenerates if quality checks fail
- **Image Generation**: Google Gemini for retail-safe newsletter images
- **Cloud Storage**: Supabase for image hosting
- **Learning System**: Agent learns from feedback to improve over time
- **Newsletter Automation**: Mailchimp integration for email campaigns
- **GitHub Actions**: Scheduled workflows for automation

## Architecture

The workflow is orchestrated using **LangGraph StateGraph** with conditional routing:

```
                              LangGraph StateGraph
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│  [START] ──▶ search_articles ──▶ select_articles ──▶ load_learning       │
│                                                              │           │
│                                                              ▼           │
│              ┌──────────────────────────────────── generate_posts        │
│              │                                           │               │
│              ▼                                           ▼               │
│     increment_regeneration ◀───[regenerate]──── reflect_posts            │
│                                                      │                   │
│                                              [continue]                  │
│                                                      ▼                   │
│                                            generate_images               │
│                                                      │                   │
│                                                      ▼                   │
│                                             upload_images                │
│                                                      │                   │
│                                                      ▼                   │
│                                              assemble_html               │
│                                                      │                   │
│                                                      ▼                   │
│                                               save_posts ──▶ [END]       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                           Human Review Phase
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Review Posts ──▶ Provide Feedback ──▶ Update Learning ──▶ Publish      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

                           Campaign Phase (GitHub Actions)
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Load Published Posts ──▶ Create Mailchimp Campaign ──▶ Send Newsletter │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Key LangGraph Benefits

- **Explicit State**: All data flows through `BlogPostState` TypedDict
- **Conditional Routing**: Automatic regeneration when reflection fails
- **Graph Visualization**: Debug and monitor workflow execution
- **Checkpointing**: Resume from any state (future enhancement)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file with your API keys:

```env
# Required
EXA_API_KEY=your_exa_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional (for full functionality)
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key
MAILCHIMP_API_KEY=your_mailchimp_api_key
MAILCHIMP_LIST_ID=your_list_id
MAILCHIMP_SERVER_PREFIX=us1
```

### 3. Generate Blog Posts

```bash
python generate_blog_posts.py
```

Options:
- `--model gpt-3.5-turbo` - Use a faster/cheaper model
- `--placeholder-images` - Skip Gemini image generation
- `--batch-size 50` - Search more articles
- `--days-back 14` - Limit search to recent articles
- `--dry-run` - Preview without generating
- `--legacy` - Use legacy async orchestration (skip LangGraph)

### 4. Review and Provide Feedback

```bash
python collect_feedback.py
```

This starts an interactive CLI for reviewing posts and providing feedback.

### 5. Create Newsletter Campaign

```bash
python mailchimp_campaign.py --preview  # Preview first
python mailchimp_campaign.py            # Create draft
python mailchimp_campaign.py --send     # Create and send
```

## File Structure

```
youdle/
├── generate_blog_posts.py      # Main entry point
├── blog_post_graph.py          # LangGraph StateGraph (NEW)
├── blog_post_generator.py      # Orchestrator (uses LangGraph)
├── langchain_blog_agent.py     # LangChain chains
├── image_generator.py          # Gemini integration
├── supabase_storage.py         # Storage client
├── mailchimp_campaign.py       # Newsletter creation
├── collect_feedback.py         # Feedback CLI
├── zap_exa_ranker.py           # Article search
│
├── # Learning System
├── example_store.py            # Good/bad examples
├── feedback_collector.py       # Feedback storage
├── reflection_agent.py         # Self-evaluation
├── prompt_refiner.py           # Prompt optimization
├── learning_memory.py          # Cross-session memory
│
├── # FastAPI Backend
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   ├── search.py           # Article search endpoints
│   │   ├── generate.py         # Generation endpoints
│   │   └── jobs.py             # Job management
│   ├── schema.sql              # Supabase schema
│   └── requirements.txt
│
├── # Next.js Dashboard
├── frontend/
│   ├── src/
│   │   ├── app/                # Pages (dashboard, articles, posts, review)
│   │   ├── components/         # React components
│   │   └── lib/                # API client, Supabase, hooks
│   └── package.json
│
├── # Output
├── blog_posts/                 # Generated HTML files
│
├── # Automation
├── .github/workflows/
│   ├── generate-blog-posts.yml # Daily generation
│   ├── create-newsletter.yml   # Weekly newsletter
│   └── feedback-analysis.yml   # Weekly learning
│
├── requirements.txt
└── README.md
```

## Dashboard (NEW)

A full-stack React dashboard for managing the blog generation pipeline.

### Features

- **Dashboard Home**: System stats, quick actions, recent jobs
- **Article Search**: Preview Exa search results with scores
- **Blog Posts**: View generated HTML, update status, copy for publishing
- **Review Panel**: Human review workflow with ratings and feedback
- **Jobs Monitor**: Real-time job tracking with Supabase subscriptions
- **Settings**: Configure generation parameters

### Running the Dashboard

#### 1. Setup Database

Run the SQL schema in your Supabase SQL Editor:

```bash
# Copy the contents of api/schema.sql and run in Supabase
```

#### 2. Start FastAPI Backend

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

#### 3. Start Next.js Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: http://localhost:3000

#### 4. Environment Variables

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

**Backend** (`.env` in root):
```env
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
# ... other keys
```

### Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Overview stats, quick actions, recent jobs |
| Articles | `/articles` | Search preview, filter by category |
| Blog Posts | `/posts` | View/edit posts, update status |
| Review | `/review` | Human review queue with feedback |
| Jobs | `/jobs` | Real-time job monitoring |
| Settings | `/settings` | Configuration and API status |

## Learning System

The agent improves over time through:

1. **Few-Shot Learning**: Good/bad examples in prompts
2. **Self-Reflection**: Validates structure before saving
3. **Human Feedback**: Ratings and comments stored
4. **Prompt Refinement**: Auto-updates based on patterns
5. **Cross-Session Memory**: Remembers mistakes to avoid

### Database Schema (Supabase)

```sql
-- Blog examples for few-shot learning
CREATE TABLE blog_examples (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_article_url TEXT,
    original_article_title TEXT,
    generated_html TEXT,
    category TEXT,
    feedback_score INTEGER,
    feedback_comments TEXT,
    is_good_example BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Human feedback on generated posts
CREATE TABLE blog_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blog_post_id TEXT,
    feedback_type TEXT,
    score INTEGER,
    comments TEXT,
    approved BOOLEAN,
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Learning insights
CREATE TABLE learning_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    insight_type TEXT,
    description TEXT,
    category TEXT,
    frequency INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## GitHub Actions Workflows

### 1. Generate Blog Posts (Daily)

Runs at 6 AM UTC. Generates new blog posts and uploads as artifacts.

### 2. Create Newsletter (Weekly)

Runs Fridays at 2 PM UTC. Creates Mailchimp campaign from published posts.

### 3. Feedback Analysis (Weekly)

Runs Mondays at 9 AM UTC. Analyzes feedback patterns and refines prompts.

### Required Secrets

Add these to your GitHub repository secrets:

- `EXA_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `MAILCHIMP_API_KEY`
- `MAILCHIMP_LIST_ID`
- `MAILCHIMP_SERVER_PREFIX`

## Workflow

1. **Generation Phase** (Automated/Manual)
   - Search for articles
   - Generate blog posts with AI
   - Create images
   - Save HTML files

2. **Review Phase** (Human)
   - Review generated posts
   - Provide feedback
   - Edit if needed
   - Publish to Blogger

3. **Learning Phase** (Automated)
   - Store feedback
   - Update example store
   - Refine prompts

4. **Campaign Phase** (Automated)
   - Load published posts
   - Create Mailchimp campaign
   - Send newsletter

## Customization

### Blog Post Templates

Edit the prompts in `langchain_blog_agent.py`:
- `SHOPPERS_BLOG_PROMPT` - For regular articles
- `RECALL_BLOG_PROMPT` - For recall alerts

### Newsletter Template

Edit `NEWSLETTER_TEMPLATE` in `mailchimp_campaign.py`.

### Image Generation

Edit `IMAGE_PROMPT_TEMPLATE` in `image_generator.py`.

## Troubleshooting

### Common Issues

1. **"EXA_API_KEY not set"**
   - Ensure your `.env` file exists and has the key
   - Run `source .env` or restart your terminal

2. **"No articles found"**
   - Try increasing `--batch-size`
   - Check Exa API quota

3. **"Mailchimp client not initialized"**
   - Verify MAILCHIMP_API_KEY format (key-serverprefix)
   - Check list ID is correct

4. **Image generation fails**
   - Use `--placeholder-images` to skip Gemini
   - Verify GEMINI_API_KEY

## License

MIT License - See LICENSE file for details.


