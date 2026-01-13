# check_blog_status.py
# Check if this week's blog posts meet the publishing requirements

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import pytz
except ImportError:
    pytz = None
    print("Warning: pytz not installed. Using UTC times.")

from supabase import create_client, Client


# ============================================================================
# CONFIGURATION
# ============================================================================

# Publishing requirements
REQUIRED_SHOPPERS = 6
REQUIRED_RECALL = 1
REQUIRED_TOTAL = REQUIRED_SHOPPERS + REQUIRED_RECALL  # 7


# ============================================================================
# DATE UTILITIES
# ============================================================================

def get_chicago_timezone():
    """Get Chicago timezone object."""
    if pytz:
        return pytz.timezone('America/Chicago')
    return None


def get_week_start_date() -> datetime:
    """
    Get the most recent Tuesday at 9 AM CST (when blog generation runs).

    This defines the start of "this week's" blog posts.

    Returns:
        datetime: Start of current week in UTC
    """
    tz = get_chicago_timezone()

    if tz:
        now = datetime.now(tz)
    else:
        # Fallback: assume UTC and subtract 6 hours for CST approximation
        now = datetime.utcnow()

    # Find the most recent Tuesday
    # weekday(): Monday=0, Tuesday=1, Wednesday=2, Thursday=3, etc.
    days_since_tuesday = (now.weekday() - 1) % 7

    # If it's Tuesday but before 9 AM, use last Tuesday
    if days_since_tuesday == 0:
        if tz:
            local_hour = now.hour
        else:
            local_hour = now.hour - 6  # Rough CST approximation
        if local_hour < 9:
            days_since_tuesday = 7

    # Calculate the Tuesday date
    tuesday = now - timedelta(days=days_since_tuesday)

    # Set to 9 AM
    if tz:
        tuesday = tuesday.replace(hour=9, minute=0, second=0, microsecond=0)
        # Convert to UTC for database query
        tuesday_utc = tuesday.astimezone(pytz.UTC)
    else:
        # Approximate: 9 AM CST = 15:00 UTC
        tuesday = tuesday.replace(hour=15, minute=0, second=0, microsecond=0)
        tuesday_utc = tuesday

    return tuesday_utc


# ============================================================================
# SUPABASE CLIENT
# ============================================================================

def get_supabase_client() -> Optional[Client]:
    """
    Get a Supabase client instance.

    Returns:
        Supabase Client instance or None if credentials not set
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        return None

    return create_client(url, key)


# ============================================================================
# BLOG STATUS CHECK
# ============================================================================

def get_this_weeks_posts(supabase: Client, week_start: datetime) -> List[Dict[str, Any]]:
    """
    Query blog posts created since week_start.

    Args:
        supabase: Supabase client
        week_start: Start of the week (datetime)

    Returns:
        List of blog post records
    """
    week_start_iso = week_start.isoformat()

    try:
        result = supabase.table("blog_posts").select(
            "id, title, category, status, blogger_url, blogger_post_id, created_at"
        ).gte("created_at", week_start_iso).execute()

        return result.data or []
    except Exception as e:
        print(f"Error querying blog posts: {e}")
        return []


def check_publish_status(supabase: Optional[Client] = None) -> Dict[str, Any]:
    """
    Check the publish status of this week's blog posts.

    Args:
        supabase: Supabase client (creates one if not provided)

    Returns:
        Dictionary with status information:
        - week_start: ISO timestamp of week start
        - total_posts: Total posts created this week
        - published_posts: Number of published posts
        - shoppers_published: SHOPPERS posts published
        - recall_published: RECALL posts published
        - shoppers_total: Total SHOPPERS posts
        - recall_total: Total RECALL posts
        - required_count: Required number of posts (7)
        - meets_requirement: Boolean - does it meet 1 RECALL + 6 SHOPPERS requirement
    """
    if supabase is None:
        supabase = get_supabase_client()
        if supabase is None:
            return {
                "success": False,
                "error": "Could not connect to Supabase"
            }

    week_start = get_week_start_date()
    posts = get_this_weeks_posts(supabase, week_start)

    # Count totals
    total_posts = len(posts)

    # A post is considered "published" if:
    # 1. status == 'published' AND
    # 2. blogger_url is set (actually published to Blogger)
    published_posts = [
        p for p in posts
        if p.get('status') == 'published' and p.get('blogger_url')
    ]

    # Count by category
    shoppers_posts = [p for p in posts if (p.get('category') or '').upper() == 'SHOPPERS']
    recall_posts = [p for p in posts if (p.get('category') or '').upper() == 'RECALL']

    shoppers_published = [
        p for p in published_posts
        if (p.get('category') or '').upper() == 'SHOPPERS'
    ]
    recall_published = [
        p for p in published_posts
        if (p.get('category') or '').upper() == 'RECALL'
    ]

    # Check requirements: 1 RECALL + 6 SHOPPERS = 7 total
    meets_requirement = (
        len(recall_published) >= REQUIRED_RECALL and
        len(shoppers_published) >= REQUIRED_SHOPPERS
    )

    return {
        "success": True,
        "week_start": week_start.isoformat(),
        "total_posts": total_posts,
        "published_posts": len(published_posts),
        "shoppers_total": len(shoppers_posts),
        "shoppers_published": len(shoppers_published),
        "recall_total": len(recall_posts),
        "recall_published": len(recall_published),
        "required_count": REQUIRED_TOTAL,
        "required_shoppers": REQUIRED_SHOPPERS,
        "required_recall": REQUIRED_RECALL,
        "meets_requirement": meets_requirement
    }


def print_status_report(status: Dict[str, Any]) -> None:
    """Print a human-readable status report."""
    if not status.get("success"):
        print(f"Error: {status.get('error', 'Unknown error')}")
        return

    print("=" * 50)
    print("BLOG PUBLISH STATUS REPORT")
    print("=" * 50)
    print(f"Week Start: {status['week_start']}")
    print()
    print(f"Total Posts This Week: {status['total_posts']}")
    print(f"Published Posts: {status['published_posts']} / {status['required_count']} required")
    print()
    print("By Category:")
    print(f"  SHOPPERS: {status['shoppers_published']} / {status['required_shoppers']} required (total: {status['shoppers_total']})")
    print(f"  RECALL:   {status['recall_published']} / {status['required_recall']} required (total: {status['recall_total']})")
    print()

    if status['meets_requirement']:
        print("STATUS: READY FOR NEWSLETTER")
        print("All publishing requirements are met.")
    else:
        print("STATUS: NOT READY")
        print("Publishing requirements NOT met.")

        shoppers_needed = max(0, REQUIRED_SHOPPERS - status['shoppers_published'])
        recall_needed = max(0, REQUIRED_RECALL - status['recall_published'])

        if shoppers_needed > 0:
            print(f"  - Need {shoppers_needed} more SHOPPERS article(s)")
        if recall_needed > 0:
            print(f"  - Need {recall_needed} more RECALL article(s)")

    print("=" * 50)


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Check this week's blog post publishing status"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON (for GitHub Actions)"
    )
    parser.add_argument(
        "--exit-code", "-e",
        action="store_true",
        help="Exit with code 1 if requirements not met"
    )

    args = parser.parse_args()

    status = check_publish_status()

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print_status_report(status)

    # Exit with error code if requirements not met and --exit-code flag is set
    if args.exit_code and not status.get('meets_requirement', False):
        sys.exit(1)


if __name__ == "__main__":
    main()
