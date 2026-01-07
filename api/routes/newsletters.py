"""
Newsletter API Routes
Endpoints for managing Mailchimp newsletter campaigns.
"""
import sys
import os
from uuid import uuid4
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import pytz
except ImportError:
    pytz = None

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================

class NewsletterCreate(BaseModel):
    """Request to create a newsletter"""
    title: Optional[str] = None
    subject: Optional[str] = None
    post_ids: List[str]


class NewsletterUpdate(BaseModel):
    """Request to update a newsletter"""
    title: Optional[str] = None
    subject: Optional[str] = None
    post_ids: Optional[List[str]] = None


class BlogPostSummary(BaseModel):
    """Summary of a blog post for newsletter"""
    id: str
    title: str
    category: str
    blogger_url: Optional[str] = None


class Newsletter(BaseModel):
    """Newsletter model"""
    id: str
    title: str
    subject: str
    html_content: str
    status: str
    mailchimp_campaign_id: Optional[str] = None
    mailchimp_web_id: Optional[str] = None
    scheduled_for: Optional[str] = None
    sent_at: Optional[str] = None
    emails_sent: int = 0
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    posts: List[BlogPostSummary] = []


class NewsletterListResponse(BaseModel):
    """Response for listing newsletters"""
    newsletters: List[Newsletter]
    total: int


# ============================================================================
# Helper Functions
# ============================================================================

def get_next_thursday_9am_cst() -> datetime:
    """
    Calculate the next Thursday at 9 AM CST (Central Time), returned as UTC for Mailchimp.
    """
    if pytz is None:
        # Fallback: approximate CST as UTC-6
        utc_now = datetime.utcnow()
        cst_now = utc_now - timedelta(hours=6)

        days_until_thursday = (3 - cst_now.weekday()) % 7
        if days_until_thursday == 0 and cst_now.hour >= 9:
            days_until_thursday = 7

        next_thursday_cst = cst_now.replace(hour=9, minute=0, second=0, microsecond=0)
        next_thursday_cst += timedelta(days=days_until_thursday)

        # Convert back to UTC
        return next_thursday_cst + timedelta(hours=6)

    cst = pytz.timezone('America/Chicago')
    utc = pytz.UTC

    now = datetime.now(cst)
    days_until_thursday = (3 - now.weekday()) % 7

    # If today is Thursday but past 9 AM, get next week
    if days_until_thursday == 0 and now.hour >= 9:
        days_until_thursday = 7

    next_thursday = now.replace(hour=9, minute=0, second=0, microsecond=0)
    next_thursday += timedelta(days=days_until_thursday)

    # Convert to UTC for Mailchimp API
    return next_thursday.astimezone(utc).replace(tzinfo=None)


def get_newsletter_with_posts(supabase, newsletter_id: str) -> Optional[dict]:
    """
    Get a newsletter with its associated posts.
    """
    # Get newsletter
    result = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
    if not result.data:
        return None

    newsletter = result.data

    # Get associated posts
    posts_result = supabase.table("newsletter_posts").select(
        "blog_post_id, position"
    ).eq("newsletter_id", newsletter_id).order("position").execute()

    posts = []
    if posts_result.data:
        post_ids = [p["blog_post_id"] for p in posts_result.data]
        if post_ids:
            blog_posts_result = supabase.table("blog_posts").select(
                "id, title, category, blogger_url"
            ).in_("id", post_ids).execute()

            if blog_posts_result.data:
                # Maintain order from newsletter_posts
                post_map = {p["id"]: p for p in blog_posts_result.data}
                posts = [post_map[pid] for pid in post_ids if pid in post_map]

    newsletter["posts"] = posts
    return newsletter


def generate_newsletter_html(supabase, post_ids: List[str]) -> str:
    """
    Generate newsletter HTML from blog post IDs.
    """
    from mailchimp_campaign import MailchimpCampaign

    # Get posts from database
    posts_result = supabase.table("blog_posts").select(
        "id, title, category, blogger_url"
    ).in_("id", post_ids).execute()

    posts = posts_result.data if posts_result.data else []

    # Separate by category
    shoppers = []
    recalls = []

    for post in posts:
        article = {
            "title": post.get("title", "Article"),
            "url": post.get("blogger_url", "#"),
            "category": post.get("category", "SHOPPERS"),
            "summary": post.get("summary", "")
        }

        if post.get("category", "").upper() == "RECALL":
            recalls.append(article)
        else:
            shoppers.append(article)

    # Create HTML
    mailchimp = MailchimpCampaign()
    return mailchimp.create_newsletter_html(shoppers, recalls)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("", response_model=NewsletterListResponse)
async def list_newsletters(
    status: Optional[str] = Query(default=None, description="Filter by status: draft, scheduled, sent, failed"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0)
):
    """
    List all newsletters with optional status filter.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get count
        count_query = supabase.table("newsletters").select("id", count="exact")
        if status:
            count_query = count_query.eq("status", status)
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else len(count_result.data or [])

        # Get newsletters
        query = supabase.table("newsletters").select("*").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        query = query.range(offset, offset + limit - 1)
        result = query.execute()

        newsletters = []
        for nl in (result.data or []):
            # Get posts for each newsletter
            posts_result = supabase.table("newsletter_posts").select(
                "blog_post_id"
            ).eq("newsletter_id", nl["id"]).execute()

            posts = []
            if posts_result.data:
                post_ids = [p["blog_post_id"] for p in posts_result.data]
                if post_ids:
                    blog_posts_result = supabase.table("blog_posts").select(
                        "id, title, category, blogger_url"
                    ).in_("id", post_ids).execute()
                    posts = blog_posts_result.data or []

            nl["posts"] = posts
            newsletters.append(nl)

        return NewsletterListResponse(newsletters=newsletters, total=total)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list newsletters: {str(e)}")


@router.get("/published-posts", response_model=List[BlogPostSummary])
async def get_published_posts_for_newsletter():
    """
    Get published blog posts that can be added to a newsletter.
    Returns posts with blogger_url (published to Blogger) from the last 3 days.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Calculate 3-day cutoff
        cutoff = (datetime.utcnow() - timedelta(days=3)).isoformat()

        # Get published posts with blogger_url from last 3 days
        result = supabase.table("blog_posts").select(
            "id, title, category, blogger_url"
        ).eq("status", "published").not_.is_("blogger_url", "null").gte(
            "created_at", cutoff
        ).order(
            "created_at", desc=True
        ).limit(50).execute()

        return result.data if result.data else []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get published posts: {str(e)}")


@router.get("/status")
async def get_mailchimp_status():
    """
    Check if Mailchimp is configured and ready.
    """
    try:
        from mailchimp_campaign import MailchimpCampaign

        mailchimp = MailchimpCampaign()

        configured = bool(mailchimp.api_key and mailchimp.list_id)

        return {
            "configured": configured,
            "has_api_key": bool(mailchimp.api_key),
            "has_list_id": bool(mailchimp.list_id),
            "server_prefix": mailchimp.server_prefix,
            "message": "Mailchimp is configured" if configured else "Mailchimp not fully configured. Check MAILCHIMP_API_KEY and MAILCHIMP_LIST_ID environment variables."
        }
    except Exception as e:
        return {
            "configured": False,
            "has_api_key": False,
            "has_list_id": False,
            "server_prefix": None,
            "message": f"Error checking Mailchimp status: {str(e)}"
        }


@router.get("/{newsletter_id}", response_model=Newsletter)
async def get_newsletter(newsletter_id: str):
    """
    Get a specific newsletter by ID.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        newsletter = get_newsletter_with_posts(supabase, newsletter_id)

        if not newsletter:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        return newsletter

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get newsletter: {str(e)}")


@router.post("", response_model=Newsletter)
async def create_newsletter(data: NewsletterCreate):
    """
    Create a new newsletter from selected blog posts.
    """
    if not data.post_ids:
        raise HTTPException(status_code=400, detail="At least one post ID is required")

    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Generate default title and subject if not provided
        date_str = datetime.now().strftime("%B %d, %Y")
        title = data.title or f"Weekly Newsletter - {date_str}"
        subject = data.subject or f"Youdle Weekly: Your Grocery Insights for {date_str}"

        # Generate HTML content
        html_content = generate_newsletter_html(supabase, data.post_ids)

        # Create newsletter
        newsletter_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        supabase.table("newsletters").insert({
            "id": newsletter_id,
            "title": title,
            "subject": subject,
            "html_content": html_content,
            "status": "draft",
            "created_at": now,
            "updated_at": now
        }).execute()

        # Link posts to newsletter
        for i, post_id in enumerate(data.post_ids):
            supabase.table("newsletter_posts").insert({
                "id": str(uuid4()),
                "newsletter_id": newsletter_id,
                "blog_post_id": post_id,
                "position": i
            }).execute()

        # Return the created newsletter
        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create newsletter: {str(e)}")


@router.patch("/{newsletter_id}", response_model=Newsletter)
async def update_newsletter(newsletter_id: str, data: NewsletterUpdate):
    """
    Update a newsletter (only draft newsletters can be updated).
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get existing newsletter
        existing = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        if existing.data["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft newsletters can be updated")

        # Build update data
        update_data = {"updated_at": datetime.utcnow().isoformat()}

        if data.title is not None:
            update_data["title"] = data.title
        if data.subject is not None:
            update_data["subject"] = data.subject

        # Update posts if provided
        if data.post_ids is not None:
            # Delete existing links
            supabase.table("newsletter_posts").delete().eq("newsletter_id", newsletter_id).execute()

            # Add new links
            for i, post_id in enumerate(data.post_ids):
                supabase.table("newsletter_posts").insert({
                    "id": str(uuid4()),
                    "newsletter_id": newsletter_id,
                    "blog_post_id": post_id,
                    "position": i
                }).execute()

            # Regenerate HTML
            update_data["html_content"] = generate_newsletter_html(supabase, data.post_ids)

        # Update newsletter
        supabase.table("newsletters").update(update_data).eq("id", newsletter_id).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update newsletter: {str(e)}")


@router.delete("/{newsletter_id}")
async def delete_newsletter(newsletter_id: str):
    """
    Delete a newsletter (only draft newsletters can be deleted).
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get existing newsletter
        existing = supabase.table("newsletters").select("status").eq("id", newsletter_id).single().execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        if existing.data["status"] not in ["draft", "failed"]:
            raise HTTPException(status_code=400, detail="Only draft or failed newsletters can be deleted")

        # Delete newsletter (cascade will delete newsletter_posts)
        supabase.table("newsletters").delete().eq("id", newsletter_id).execute()

        return {"message": "Newsletter deleted", "id": newsletter_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete newsletter: {str(e)}")


@router.get("/{newsletter_id}/preview")
async def preview_newsletter(newsletter_id: str):
    """
    Get the rendered HTML preview of a newsletter.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        result = supabase.table("newsletters").select("html_content").eq("id", newsletter_id).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        return {"html": result.data["html_content"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get preview: {str(e)}")


@router.post("/{newsletter_id}/schedule", response_model=Newsletter)
async def schedule_newsletter(newsletter_id: str):
    """
    Schedule a newsletter for the next Thursday at 9 AM EST.
    Creates a Mailchimp campaign and schedules it.
    """
    try:
        from supabase_storage import get_supabase_client
        from mailchimp_campaign import MailchimpCampaign

        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get newsletter
        newsletter = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
        if not newsletter.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        nl = newsletter.data

        if nl["status"] != "draft":
            raise HTTPException(status_code=400, detail="Only draft newsletters can be scheduled")

        # Create Mailchimp campaign
        mailchimp = MailchimpCampaign()

        campaign_result = mailchimp.create_campaign(
            subject=nl["subject"],
            html_content=nl["html_content"]
        )

        if not campaign_result.get("success"):
            supabase.table("newsletters").update({
                "status": "failed",
                "error": campaign_result.get("error", "Failed to create campaign"),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", newsletter_id).execute()
            raise HTTPException(status_code=500, detail=campaign_result.get("error", "Failed to create Mailchimp campaign"))

        campaign_id = campaign_result["campaign_id"]

        # Schedule for Thursday 9 AM CST
        schedule_time = get_next_thursday_9am_cst()

        schedule_result = mailchimp.schedule_campaign(campaign_id, schedule_time)

        if not schedule_result.get("success"):
            supabase.table("newsletters").update({
                "status": "failed",
                "mailchimp_campaign_id": campaign_id,
                "error": schedule_result.get("error", "Failed to schedule campaign"),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", newsletter_id).execute()
            raise HTTPException(status_code=500, detail=schedule_result.get("error", "Failed to schedule campaign"))

        # Update newsletter status
        supabase.table("newsletters").update({
            "status": "scheduled",
            "mailchimp_campaign_id": campaign_id,
            "mailchimp_web_id": campaign_result.get("web_id"),
            "scheduled_for": schedule_time.isoformat(),
            "error": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", newsletter_id).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule newsletter: {str(e)}")


@router.post("/{newsletter_id}/send", response_model=Newsletter)
async def send_newsletter(newsletter_id: str):
    """
    Send a newsletter immediately.
    Creates a Mailchimp campaign and sends it right away.
    """
    try:
        from supabase_storage import get_supabase_client
        from mailchimp_campaign import MailchimpCampaign

        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get newsletter
        newsletter = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
        if not newsletter.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        nl = newsletter.data

        if nl["status"] not in ["draft", "scheduled"]:
            raise HTTPException(status_code=400, detail="Newsletter cannot be sent (already sent or failed)")

        mailchimp = MailchimpCampaign()

        # Use existing campaign or create new one
        campaign_id = nl.get("mailchimp_campaign_id")

        if not campaign_id:
            # Create new campaign
            campaign_result = mailchimp.create_campaign(
                subject=nl["subject"],
                html_content=nl["html_content"]
            )

            if not campaign_result.get("success"):
                supabase.table("newsletters").update({
                    "status": "failed",
                    "error": campaign_result.get("error", "Failed to create campaign"),
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", newsletter_id).execute()
                raise HTTPException(status_code=500, detail=campaign_result.get("error", "Failed to create Mailchimp campaign"))

            campaign_id = campaign_result["campaign_id"]

        # Send campaign
        send_result = mailchimp.send_campaign(campaign_id)

        if not send_result.get("success"):
            supabase.table("newsletters").update({
                "status": "failed",
                "mailchimp_campaign_id": campaign_id,
                "error": send_result.get("error", "Failed to send campaign"),
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", newsletter_id).execute()
            raise HTTPException(status_code=500, detail=send_result.get("error", "Failed to send campaign"))

        # Update newsletter status
        supabase.table("newsletters").update({
            "status": "sent",
            "mailchimp_campaign_id": campaign_id,
            "sent_at": datetime.utcnow().isoformat(),
            "scheduled_for": None,
            "error": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", newsletter_id).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send newsletter: {str(e)}")


@router.post("/{newsletter_id}/unschedule", response_model=Newsletter)
async def unschedule_newsletter(newsletter_id: str):
    """
    Cancel a scheduled newsletter.
    """
    try:
        from supabase_storage import get_supabase_client
        from mailchimp_campaign import MailchimpCampaign

        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get newsletter
        newsletter = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
        if not newsletter.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        nl = newsletter.data

        if nl["status"] != "scheduled":
            raise HTTPException(status_code=400, detail="Newsletter is not scheduled")

        campaign_id = nl.get("mailchimp_campaign_id")

        if campaign_id:
            # Try to unschedule in Mailchimp
            mailchimp = MailchimpCampaign()
            try:
                if mailchimp.client:
                    mailchimp.client.campaigns.actions.unschedule(campaign_id)
            except Exception:
                pass  # Best effort - campaign might not be unschedulable

        # Update newsletter status back to draft
        supabase.table("newsletters").update({
            "status": "draft",
            "scheduled_for": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", newsletter_id).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unschedule newsletter: {str(e)}")


@router.post("/auto-create", response_model=Newsletter)
async def auto_create_newsletter():
    """
    Auto-create a newsletter from recent published posts (last 3 days) that aren't in any newsletter yet.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Calculate 3-day cutoff
        cutoff = (datetime.utcnow() - timedelta(days=3)).isoformat()

        # Get published posts with blogger_url from last 3 days
        all_posts = supabase.table("blog_posts").select(
            "id"
        ).eq("status", "published").not_.is_("blogger_url", "null").gte(
            "created_at", cutoff
        ).order(
            "created_at", desc=True
        ).limit(20).execute()

        if not all_posts.data:
            raise HTTPException(status_code=400, detail="No published posts available")

        all_post_ids = [p["id"] for p in all_posts.data]

        # Get posts already in newsletters
        used_posts = supabase.table("newsletter_posts").select("blog_post_id").execute()
        used_post_ids = set(p["blog_post_id"] for p in (used_posts.data or []))

        # Filter to unused posts
        available_post_ids = [pid for pid in all_post_ids if pid not in used_post_ids]

        if not available_post_ids:
            raise HTTPException(status_code=400, detail="All published posts are already in newsletters")

        # Create newsletter with available posts
        date_str = datetime.now().strftime("%B %d, %Y")
        title = f"Weekly Newsletter - {date_str}"
        subject = f"Youdle Weekly: Your Grocery Insights for {date_str}"

        html_content = generate_newsletter_html(supabase, available_post_ids)

        newsletter_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        supabase.table("newsletters").insert({
            "id": newsletter_id,
            "title": title,
            "subject": subject,
            "html_content": html_content,
            "status": "draft",
            "created_at": now,
            "updated_at": now
        }).execute()

        # Link posts
        for i, post_id in enumerate(available_post_ids):
            supabase.table("newsletter_posts").insert({
                "id": str(uuid4()),
                "newsletter_id": newsletter_id,
                "blog_post_id": post_id,
                "position": i
            }).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-create newsletter: {str(e)}")


@router.post("/{newsletter_id}/sync-stats", response_model=Newsletter)
async def sync_newsletter_stats(newsletter_id: str):
    """
    Sync campaign statistics from Mailchimp for a sent newsletter.
    """
    try:
        from supabase_storage import get_supabase_client
        from mailchimp_campaign import MailchimpCampaign

        supabase = get_supabase_client()

        if supabase is None:
            raise HTTPException(status_code=503, detail="Database not configured")

        # Get newsletter
        newsletter = supabase.table("newsletters").select("*").eq("id", newsletter_id).single().execute()
        if not newsletter.data:
            raise HTTPException(status_code=404, detail="Newsletter not found")

        nl = newsletter.data
        campaign_id = nl.get("mailchimp_campaign_id")

        if not campaign_id:
            raise HTTPException(status_code=400, detail="Newsletter has no Mailchimp campaign")

        mailchimp = MailchimpCampaign()
        status_result = mailchimp.get_campaign_status(campaign_id)

        if not status_result.get("success"):
            raise HTTPException(status_code=500, detail=status_result.get("error", "Failed to get campaign status"))

        # Update stats
        update_data = {
            "emails_sent": status_result.get("emails_sent", 0),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Try to get report for open/click rates
        if mailchimp.client:
            try:
                report = mailchimp.client.reports.get(campaign_id)
                update_data["open_rate"] = report.get("opens", {}).get("open_rate", 0)
                update_data["click_rate"] = report.get("clicks", {}).get("click_rate", 0)
            except Exception:
                pass

        supabase.table("newsletters").update(update_data).eq("id", newsletter_id).execute()

        return get_newsletter_with_posts(supabase, newsletter_id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync stats: {str(e)}")


# ============================================================================
# Helper for auto-create trigger
# ============================================================================

async def check_auto_create_newsletter():
    """
    Check if we should auto-create a newsletter.
    Called after publishing a post to Blogger.
    Creates a draft newsletter if 3+ published posts from the last 3 days are available.
    """
    try:
        from supabase_storage import get_supabase_client
        supabase = get_supabase_client()

        if supabase is None:
            return

        # Calculate 3-day cutoff
        cutoff = (datetime.utcnow() - timedelta(days=3)).isoformat()

        # Get published posts with blogger_url from last 3 days
        all_posts = supabase.table("blog_posts").select(
            "id"
        ).eq("status", "published").not_.is_("blogger_url", "null").gte(
            "created_at", cutoff
        ).execute()

        if not all_posts.data:
            return

        all_post_ids = [p["id"] for p in all_posts.data]

        # Get posts already in newsletters
        used_posts = supabase.table("newsletter_posts").select("blog_post_id").execute()
        used_post_ids = set(p["blog_post_id"] for p in (used_posts.data or []))

        # Filter to unused posts
        available_post_ids = [pid for pid in all_post_ids if pid not in used_post_ids]

        # Auto-create if 3+ posts available
        if len(available_post_ids) >= 3:
            date_str = datetime.now().strftime("%B %d, %Y")
            title = f"Weekly Newsletter - {date_str}"
            subject = f"Youdle Weekly: Your Grocery Insights for {date_str}"

            html_content = generate_newsletter_html(supabase, available_post_ids)

            newsletter_id = str(uuid4())
            now = datetime.utcnow().isoformat()

            supabase.table("newsletters").insert({
                "id": newsletter_id,
                "title": title,
                "subject": subject,
                "html_content": html_content,
                "status": "draft",
                "created_at": now,
                "updated_at": now
            }).execute()

            for i, post_id in enumerate(available_post_ids):
                supabase.table("newsletter_posts").insert({
                    "id": str(uuid4()),
                    "newsletter_id": newsletter_id,
                    "blog_post_id": post_id,
                    "position": i
                }).execute()

            print(f"Auto-created newsletter draft with {len(available_post_ids)} posts")

    except Exception as e:
        print(f"Warning: Auto-create newsletter check failed: {e}")
