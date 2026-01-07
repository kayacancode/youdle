"""
Generate API Routes
Endpoints for blog post generation.
"""
import sys
import os
from uuid import uuid4
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

router = APIRouter()


class GenerationConfig(BaseModel):
    """Configuration for blog post generation"""
    batch_size: int = 10
    search_days_back: int = 30
    model: str = "gpt-4"
    use_placeholder_images: bool = False
    use_legacy_orchestrator: bool = False


class GenerationResponse(BaseModel):
    """Response after starting generation"""
    job_id: str
    status: str
    message: str
    config: GenerationConfig


class BlogPost(BaseModel):
    """Blog post model"""
    id: str
    title: str
    html_content: str
    image_url: Optional[str]
    category: str
    status: str
    article_url: str
    created_at: str


def run_generation_task(job_id: str, config: dict):
    """
    Background task to run blog generation.
    Updates job status in Supabase as it progresses.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        # Update job status to running
        supabase.table("job_queue").update({
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        
        # Run the blog generation workflow
        from blog_post_generator import run_generation
        
        result = run_generation(
            model=config.get("model", "gpt-4"),
            use_placeholder_images=config.get("use_placeholder_images", False),
            batch_size=config.get("batch_size", 10),
            search_days_back=config.get("search_days_back", 30),
            use_langgraph=not config.get("use_legacy_orchestrator", False)
        )

        # Get posts from result - handle both LangGraph and legacy return structures
        final_posts = []

        # Try LangGraph structure first (final_state.final_posts)
        if result.get("final_state"):
            final_posts = result["final_state"].get("final_posts", [])
        # Fallback to legacy structure (results array)
        elif result.get("results"):
            final_posts = result["results"]

        # Limit final_posts to configured batch_size to prevent over-generation
        configured_batch_size = config.get("batch_size", 10)
        if len(final_posts) > configured_batch_size:
            final_posts = final_posts[:configured_batch_size]

        # Store generated posts in database
        inserted_count = 0
        for post in final_posts:
            try:
                # Handle key differences between LangGraph and legacy
                # LangGraph uses: html, original_link
                # Legacy uses: file_path (need to read HTML from file)
                html_content = post.get("html", "")
                
                # If no html, try to read from file_path (legacy)
                if not html_content and post.get("file_path"):
                    try:
                        with open(post["file_path"], "r") as f:
                            html_content = f.read()
                    except Exception:
                        pass
                
                # Get article URL (different key names)
                article_url = post.get("original_link", "") or post.get("source_url", "")
                
                supabase.table("blog_posts").insert({
                    "id": str(uuid4()),
                    "title": post.get("title", ""),
                    "html_content": html_content,
                    "image_url": post.get("image_url", ""),
                    "category": post.get("category", "SHOPPERS").upper(),
                    "status": "draft",
                    "article_url": article_url,
                    "job_id": job_id,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                inserted_count += 1
            except Exception as insert_err:
                pass

        # Update job status to completed
        supabase.table("job_queue").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "result": {
                "posts_generated": inserted_count,
                "errors": result.get("errors", [])
            }
        }).eq("id", job_id).execute()
        
    except Exception as e:
        # Update job status to failed
        try:
            from supabase_storage import get_supabase_client
            supabase = get_supabase_client()
            if supabase:
                supabase.table("job_queue").update({
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "error": str(e)
                }).eq("id", job_id).execute()
        except:
            pass
        raise


@router.post("/run", response_model=GenerationResponse)
async def run_generation_endpoint(
    background_tasks: BackgroundTasks,
    config: GenerationConfig = GenerationConfig()
):
    """
    Start a new blog post generation run.
    Returns immediately with a job ID that can be used to track progress.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Supabase not configured")
        
        job_id = str(uuid4())
        
        # Create job record
        supabase.table("job_queue").insert({
            "id": job_id,
            "status": "pending",
            "config": config.model_dump(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }).execute()
        
        # Start background task
        background_tasks.add_task(run_generation_task, job_id, config.model_dump())
        
        return GenerationResponse(
            job_id=job_id,
            status="pending",
            message="Generation started. Use /api/jobs/{job_id} to track progress.",
            config=config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")


@router.get("/posts", response_model=List[BlogPost])
async def get_blog_posts(
    status: Optional[str] = Query(default=None, description="Filter by status: draft, reviewed, published"),
    category: Optional[str] = Query(default=None, description="Filter by category: SHOPPERS or RECALL"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    Get generated blog posts from the database.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        query = supabase.table("blog_posts").select("*").order("created_at", desc=True)
        
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category.upper())
        
        query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get posts: {str(e)}")


@router.get("/posts/{post_id}")
async def get_blog_post(post_id: str):
    """
    Get a specific blog post by ID.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")


@router.patch("/posts/{post_id}/status")
async def update_post_status(
    post_id: str,
    status: str = Query(..., description="New status: draft, reviewed, published")
):
    """
    Update the status of a blog post.
    """
    if status not in ["draft", "reviewed", "published"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be: draft, reviewed, or published")
    
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()
        
        result = supabase.table("blog_posts").update({
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", post_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return {"message": f"Post status updated to {status}", "post": result.data[0]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update post: {str(e)}")


@router.delete("/posts/{post_id}")
async def delete_blog_post(post_id: str):
    """
    Delete a blog post.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        result = supabase.table("blog_posts").delete().eq("id", post_id).execute()

        return {"message": "Post deleted", "id": post_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


class BlogPostUpdate(BaseModel):
    """Blog post update model"""
    html_content: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


@router.patch("/posts/{post_id}")
async def update_blog_post(post_id: str, updates: BlogPostUpdate):
    """
    Update blog post content (html_content, image_url, category).
    """
    if updates.category and updates.category.upper() not in ["SHOPPERS", "RECALL"]:
        raise HTTPException(status_code=400, detail="Invalid category. Must be: SHOPPERS or RECALL")

    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        # Build update dict from provided fields only
        update_data = {}
        if updates.html_content is not None:
            update_data["html_content"] = updates.html_content
        if updates.image_url is not None:
            update_data["image_url"] = updates.image_url
        if updates.category is not None:
            update_data["category"] = updates.category.upper()

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided to update")

        # Always update the updated_at timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = supabase.table("blog_posts").update(update_data).eq("id", post_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        return {"message": "Post updated successfully", "post": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update post: {str(e)}")


@router.get("/blogger/status")
async def get_blogger_status():
    """
    Check if Blogger API is configured and ready.
    """
    try:
        from blogger_client import get_blogger_client
        client = get_blogger_client()

        return {
            "configured": client.is_configured(),
            "blog_id": client.blog_id if client.is_configured() else None,
            "message": "Blogger API is configured" if client.is_configured() else "Blogger API not configured. Set BLOGGER_BLOG_ID, BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, and BLOGGER_REFRESH_TOKEN environment variables."
        }
    except Exception as e:
        return {
            "configured": False,
            "blog_id": None,
            "message": f"Error checking Blogger status: {str(e)}"
        }


@router.post("/posts/{post_id}/publish")
async def publish_post_to_blogger(post_id: str):
    """
    Publish a blog post to Blogger.
    This actually publishes the post to the connected Blogger blog.
    """
    try:
        from supabase_storage import get_supabase_client
        from blogger_client import get_blogger_client

        supabase = get_supabase_client()
        blogger = get_blogger_client()

        # Check if Blogger is configured
        if not blogger.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Blogger API not configured. Please set BLOGGER_BLOG_ID, BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, and BLOGGER_REFRESH_TOKEN environment variables."
            )

        # Get the post from database
        result = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        post = result.data

        # Check if already published to Blogger
        if post.get("blogger_post_id"):
            raise HTTPException(
                status_code=400,
                detail=f"Post already published to Blogger. URL: {post.get('blogger_url')}"
            )

        # Publish to Blogger
        labels = [post.get("category", "SHOPPERS")]

        blogger_result = blogger.publish_post(
            title=post["title"],
            html_content=post["html_content"],
            labels=labels,
            is_draft=False
        )

        # Update the database with Blogger info
        update_result = supabase.table("blog_posts").update({
            "status": "published",
            "blogger_post_id": blogger_result["blogger_post_id"],
            "blogger_url": blogger_result["blogger_url"],
            "blogger_published_at": blogger_result.get("published_at") or datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", post_id).execute()

        # Trigger newsletter auto-create check
        try:
            from routes.newsletters import check_auto_create_newsletter
            import asyncio
            asyncio.create_task(check_auto_create_newsletter())
        except Exception as e:
            # Don't fail the publish if newsletter creation fails
            print(f"Warning: Newsletter auto-create check failed: {e}")

        return {
            "message": "Post published to Blogger successfully",
            "blogger_post_id": blogger_result["blogger_post_id"],
            "blogger_url": blogger_result["blogger_url"],
            "post": update_result.data[0] if update_result.data else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish to Blogger: {str(e)}")


@router.post("/posts/{post_id}/unpublish")
async def unpublish_post_from_blogger(post_id: str):
    """
    Unpublish a blog post from Blogger.
    Deletes the post from Blogger and resets status to reviewed.
    """
    try:
        from supabase_storage import get_supabase_client
        from blogger_client import get_blogger_client

        supabase = get_supabase_client()
        blogger = get_blogger_client()

        # Get the post from database
        result = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        post = result.data

        # Check if published to Blogger
        if not post.get("blogger_post_id"):
            raise HTTPException(
                status_code=400,
                detail="Post is not published to Blogger"
            )

        # Delete from Blogger if configured
        if blogger.is_configured():
            try:
                blogger.delete_post(post["blogger_post_id"])
            except Exception as e:
                # Log but don't fail - post might already be deleted from Blogger
                print(f"Warning: Could not delete from Blogger: {e}")

        # Update the database - clear blogger fields and reset status
        update_result = supabase.table("blog_posts").update({
            "status": "reviewed",
            "blogger_post_id": None,
            "blogger_url": None,
            "blogger_published_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", post_id).execute()

        return {
            "message": "Post unpublished from Blogger successfully",
            "post": update_result.data[0] if update_result.data else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unpublish from Blogger: {str(e)}")


