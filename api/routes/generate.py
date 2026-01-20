"""
Generate API Routes
Endpoints for blog post generation.
"""
import sys
import os
import re
from html import unescape
from difflib import SequenceMatcher
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
    blogger_post_id: Optional[str] = None
    blogger_url: Optional[str] = None
    blogger_published_at: Optional[str] = None
    last_synced_at: Optional[str] = None


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
    title: Optional[str] = None
    html_content: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


@router.patch("/posts/{post_id}")
async def update_blog_post(post_id: str, updates: BlogPostUpdate):
    """
    Update blog post content (html_content, image_url, category).
    If the post is published to Blogger (has blogger_post_id), also updates Blogger.
    """
    if updates.category and updates.category.upper() not in ["SHOPPERS", "RECALL"]:
        raise HTTPException(status_code=400, detail="Invalid category. Must be: SHOPPERS or RECALL")

    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        # First, get the current post to check if it has blogger_post_id
        current_post = supabase.table("blog_posts").select("*").eq("id", post_id).single().execute()
        if not current_post.data:
            raise HTTPException(status_code=404, detail="Post not found")

        post_data = current_post.data
        blogger_post_id = post_data.get("blogger_post_id")

        # Build update dict from provided fields only
        update_data = {}
        if updates.title is not None:
            update_data["title"] = updates.title
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

        # Update local database
        result = supabase.table("blog_posts").update(update_data).eq("id", post_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        updated_post = result.data[0]

        # If post is published to Blogger, sync the changes
        blogger_sync_result = None
        if blogger_post_id:
            try:
                from blogger_client import get_blogger_client
                blogger = get_blogger_client()

                if blogger.is_configured():
                    # Prepare update for Blogger
                    blogger_update_kwargs = {}
                    if updates.title is not None:
                        blogger_update_kwargs["title"] = updates.title
                    if updates.html_content is not None:
                        blogger_update_kwargs["html_content"] = updates.html_content
                    if updates.category is not None:
                        blogger_update_kwargs["labels"] = [updates.category.upper()]

                    if blogger_update_kwargs:
                        blogger_sync_result = blogger.update_post(
                            blogger_post_id=blogger_post_id,
                            **blogger_update_kwargs
                        )
            except Exception as blogger_err:
                # Don't fail the whole request if Blogger sync fails
                blogger_sync_result = {"error": str(blogger_err)}

        response = {
            "message": "Post updated successfully",
            "post": updated_post
        }

        if blogger_post_id:
            response["blogger_synced"] = blogger_sync_result is not None and "error" not in (blogger_sync_result or {})
            if blogger_sync_result and "error" in blogger_sync_result:
                response["blogger_sync_error"] = blogger_sync_result["error"]

        return response

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

        # Check if already published to Blogger (has both ID and URL)
        if post.get("blogger_post_id") and post.get("blogger_url"):
            raise HTTPException(
                status_code=400,
                detail=f"Post already published to Blogger. URL: {post.get('blogger_url')}"
            )

        # Publish to Blogger
        labels = [post.get("category", "SHOPPERS")]

        # If post has blogger_post_id but no URL, it's a draft - re-publish it
        if post.get("blogger_post_id"):
            # First update the draft with current content, then publish
            blogger.update_post(
                blogger_post_id=post["blogger_post_id"],
                title=post["title"],
                html_content=post["html_content"],
                labels=labels
            )
            blogger_result = blogger.publish_draft(post["blogger_post_id"])
        else:
            # Create new post on Blogger
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
    Reverts the post to draft status on Blogger and resets local status to reviewed.
    The post remains on Blogger as a draft so it can be re-published later.
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

        # Revert to draft on Blogger if it has a blogger_post_id and Blogger is configured
        blogger_result = None
        if post.get("blogger_post_id") and blogger.is_configured():
            try:
                blogger_result = blogger.revert_to_draft(post["blogger_post_id"])
            except Exception as e:
                # Log but don't fail - post might already be a draft or deleted
                print(f"Warning: Could not revert to draft on Blogger: {e}")

        # Update the database - keep blogger_post_id so we can re-publish, clear URL and published time
        update_result = supabase.table("blog_posts").update({
            "status": "reviewed",
            "blogger_url": None,
            "blogger_published_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", post_id).execute()

        return {
            "message": "Post reverted to draft on Blogger successfully",
            "blogger_status": blogger_result.get("status") if blogger_result else None,
            "post": update_result.data[0] if update_result.data else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unpublish from Blogger: {str(e)}")


def normalize_title(title: str) -> str:
    """Normalize title for comparison: strip HTML, decode entities, lowercase, normalize whitespace."""
    if not title:
        return ""
    # Strip HTML tags
    title = re.sub(r'<[^>]+>', '', title)
    # Decode HTML entities
    title = unescape(title)
    # Lowercase and strip
    title = title.lower().strip()
    # Normalize whitespace
    title = re.sub(r'\s+', ' ', title)
    return title


def title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity ratio between two normalized titles."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return 0.0
    return SequenceMatcher(None, norm1, norm2).ratio()


@router.post("/blogger/sync")
async def sync_with_blogger():
    """
    Enhanced sync with comprehensive three-phase detection and auto-fix:
    Phase 1: Discovery - Fetch all LIVE and DRAFT posts from Blogger
    Phase 2: Verification - Detect status mismatches
    Phase 3: Auto-Fix - Fix detected issues
    """
    try:
        from supabase_storage import get_supabase_client
        from blogger_client import get_blogger_client

        supabase = get_supabase_client()
        blogger = get_blogger_client()

        if not blogger.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Blogger API not configured"
            )

        # === PHASE 1: DISCOVERY ===
        # Fetch all posts from Blogger (both LIVE and DRAFT)
        live_posts = blogger.list_posts(status='LIVE')
        draft_posts = blogger.list_posts(status='DRAFT')

        # Combine and create lookup maps
        all_blogger_posts = live_posts + draft_posts
        blogger_by_id = {bp.get('id'): bp for bp in all_blogger_posts}
        live_post_ids = {bp.get('id') for bp in live_posts}
        draft_post_ids = {bp.get('id') for bp in draft_posts}

        # Get all posts from database
        db_result = supabase.table("blog_posts").select("*").execute()
        db_posts = db_result.data or []

        synced_count = 0
        issues_found = 0
        issues_fixed = 0
        details = []

        # === PHASE 2 & 3: VERIFICATION AND AUTO-FIX ===
        for db_post in db_posts:
            db_id = db_post['id']
            db_title = db_post.get('title', '')
            db_status = db_post.get('status')
            existing_blogger_id = db_post.get('blogger_post_id')
            existing_blogger_url = db_post.get('blogger_url')

            # Find matching Blogger post using multi-tier matching
            blogger_post = None
            match_type = None

            # Tier 1: Match by blogger_post_id if we have one
            if existing_blogger_id:
                if existing_blogger_id in blogger_by_id:
                    blogger_post = blogger_by_id[existing_blogger_id]
                    match_type = "id_match"
                else:
                    # Blogger post ID exists locally but not found on Blogger (deleted)
                    issues_found += 1
                    if db_status == 'published':
                        # Revert to reviewed, clear all blogger fields
                        update_data = {
                            "status": "reviewed",
                            "blogger_post_id": None,
                            "blogger_url": None,
                            "blogger_published_at": None,
                            "updated_at": datetime.utcnow().isoformat(),
                            "last_synced_at": datetime.utcnow().isoformat()
                        }
                        supabase.table("blog_posts").update(update_data).eq("id", db_id).execute()
                        issues_fixed += 1
                        details.append({
                            "post_id": db_id,
                            "title": db_title,
                            "issue_type": "deleted_on_blogger",
                            "local_status": db_status,
                            "blogger_status": "DELETED",
                            "action_taken": "reverted_to_reviewed_cleared_fields"
                        })
                    continue

            # Tier 2: Fuzzy title match (if no ID match found)
            if not blogger_post:
                best_match = None
                best_score = 0.0

                for bp in all_blogger_posts:
                    score = title_similarity(db_title, bp.get('title', ''))
                    if score > best_score and score >= 0.85:
                        best_score = score
                        best_match = bp

                if best_match:
                    blogger_post = best_match
                    match_type = f"title_match_{best_score:.2f}"

            # Handle posts marked published but never actually published to Blogger
            if not blogger_post and db_status == 'published' and not existing_blogger_url:
                issues_found += 1
                issues_fixed += 1
                update_data = {
                    "status": "reviewed",
                    "blogger_post_id": None,
                    "blogger_url": None,
                    "blogger_published_at": None,
                    "updated_at": datetime.utcnow().isoformat(),
                    "last_synced_at": datetime.utcnow().isoformat()
                }
                supabase.table("blog_posts").update(update_data).eq("id", db_id).execute()
                synced_count += 1
                details.append({
                    "post_id": db_id,
                    "title": db_title,
                    "issue_type": "published_but_not_on_blogger",
                    "local_status": db_status,
                    "blogger_status": "NOT_FOUND",
                    "action_taken": "reverted_to_reviewed"
                })
                continue

            # Process matched posts
            if blogger_post:
                blogger_id = blogger_post.get('id')
                blogger_url = blogger_post.get('url')
                blogger_status = 'LIVE' if blogger_id in live_post_ids else 'DRAFT'
                blogger_title = blogger_post.get('title', '')
                blogger_content = blogger_post.get('content', '')

                update_data = {
                    "blogger_post_id": blogger_id,
                    "updated_at": datetime.utcnow().isoformat(),
                    "last_synced_at": datetime.utcnow().isoformat()
                }

                issue_detected = False
                issue_type = None
                action_taken = None

                # Case 1: Local published + Blogger DRAFT
                if db_status == 'published' and blogger_status == 'DRAFT':
                    issue_detected = True
                    issue_type = "status_mismatch_local_published_blogger_draft"
                    # Clear URL but keep ID (post exists but not live)
                    update_data["blogger_url"] = None
                    update_data["blogger_published_at"] = None
                    action_taken = "cleared_blogger_url"

                # Case 2: Local published + No blogger_url (incomplete publish)
                elif db_status == 'published' and not existing_blogger_url and blogger_status == 'LIVE':
                    issue_detected = True
                    issue_type = "missing_blogger_url"
                    # Update with correct URL
                    update_data["blogger_url"] = blogger_url
                    update_data["blogger_published_at"] = blogger_post.get('published')
                    update_data["status"] = "published"
                    action_taken = "added_missing_url"

                # Case 3: Local draft/reviewed + Blogger LIVE
                elif db_status in ['draft', 'reviewed'] and blogger_status == 'LIVE':
                    issue_detected = True
                    issue_type = "status_mismatch_local_draft_blogger_live"
                    # Update to published
                    update_data["status"] = "published"
                    update_data["blogger_url"] = blogger_url
                    update_data["blogger_published_at"] = blogger_post.get('published')
                    action_taken = "updated_to_published"

                # Case 4: Normal sync for published posts
                elif blogger_status == 'LIVE':
                    update_data["status"] = "published"
                    update_data["blogger_url"] = blogger_url
                    update_data["blogger_published_at"] = blogger_post.get('published')

                # Sync content and title from Blogger
                content_synced = False
                title_synced = False

                if blogger_title and blogger_title != db_post.get('title', ''):
                    update_data['title'] = blogger_title
                    title_synced = True

                if blogger_content:
                    db_content = db_post.get('html_content', '')
                    if blogger_content != db_content:
                        update_data['html_content'] = blogger_content
                        content_synced = True

                # Check if update is needed
                needs_update = (
                    db_post.get('status') != update_data.get('status', db_status) or
                    db_post.get('blogger_post_id') != blogger_id or
                    db_post.get('blogger_url') != update_data.get('blogger_url', existing_blogger_url) or
                    content_synced or
                    title_synced
                )

                if needs_update:
                    supabase.table("blog_posts").update(update_data).eq("id", db_id).execute()
                    synced_count += 1

                    if issue_detected:
                        issues_found += 1
                        issues_fixed += 1
                        details.append({
                            "post_id": db_id,
                            "title": blogger_title or db_title,
                            "issue_type": issue_type,
                            "local_status": db_status,
                            "blogger_status": blogger_status,
                            "action_taken": action_taken
                        })

        return {
            "message": f"Sync completed. {synced_count} posts synced, {issues_fixed} issues fixed.",
            "synced_count": synced_count,
            "issues_found": issues_found,
            "issues_fixed": issues_fixed,
            "blogger_live_posts": len(live_posts),
            "blogger_draft_posts": len(draft_posts),
            "database_posts_checked": len(db_posts),
            "details": details
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync with Blogger: {str(e)}")


