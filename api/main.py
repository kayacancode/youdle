"""
Youdle Blog Agent API
FastAPI server that wraps the Python blog generation pipeline.
"""
import sys
import os
from uuid import uuid4
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path so we can import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Youdle Blog Agent API",
    description="API for managing blog post generation, article search, and content review",
    version="1.0.0"
)

# CORS for Next.js frontend
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://youdle.vercel.app",
    "https://youdle.io",
    "https://www.youdle.io",
]

# Add additional origins from environment variable if set
extra_origins = os.getenv("CORS_ORIGINS", "")
if extra_origins:
    cors_origins.extend([o.strip() for o in extra_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from routes import search, generate, jobs

# Include routers
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(generate.router, prefix="/api/generate", tags=["Generate"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])


@app.get("/")
async def root():
    """API root - health check"""
    return {
        "status": "healthy",
        "service": "Youdle Blog Agent API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Get overall system statistics"""
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        # Get counts from database
        jobs_result = supabase.table("job_queue").select("id, status").execute()
        posts_result = supabase.table("blog_posts").select("id, status, category").execute()
        
        jobs_data = jobs_result.data if jobs_result.data else []
        posts_data = posts_result.data if posts_result.data else []
        
        # Calculate stats
        total_jobs = len(jobs_data)
        running_jobs = len([j for j in jobs_data if j.get("status") == "running"])
        completed_jobs = len([j for j in jobs_data if j.get("status") == "completed"])
        failed_jobs = len([j for j in jobs_data if j.get("status") == "failed"])
        
        total_posts = len(posts_data)
        draft_posts = len([p for p in posts_data if p.get("status") == "draft"])
        reviewed_posts = len([p for p in posts_data if p.get("status") == "reviewed"])
        published_posts = len([p for p in posts_data if p.get("status") == "published"])
        shoppers_posts = len([p for p in posts_data if p.get("category") == "SHOPPERS"])
        recall_posts = len([p for p in posts_data if p.get("category") == "RECALL"])
        
        return {
            "jobs": {
                "total": total_jobs,
                "running": running_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs
            },
            "posts": {
                "total": total_posts,
                "draft": draft_posts,
                "reviewed": reviewed_posts,
                "published": published_posts,
                "by_category": {
                    "shoppers": shoppers_posts,
                    "recall": recall_posts
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Return empty stats if database not configured
        return {
            "jobs": {"total": 0, "running": 0, "completed": 0, "failed": 0},
            "posts": {
                "total": 0, "draft": 0, "reviewed": 0, "published": 0,
                "by_category": {"shoppers": 0, "recall": 0}
            },
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)



