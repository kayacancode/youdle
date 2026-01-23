# fetch_published_posts.py
# Fetch published blog posts from Supabase and write to JSON files
# This ensures the newsletter workflow uses fresh data from the database,
# not stale artifact files from the blog generation step.

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
# DATE UTILITIES (copied from check_blog_status.py for consistency)
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
# FETCH PUBLISHED POSTS
# ============================================================================

def fetch_published_posts(supabase: Client, week_start: datetime) -> List[Dict[str, Any]]:
    """
    Query Supabase for this week's published blog posts.

    A post is considered "published" if:
    1. created_at >= week_start
    2. status == 'published'
    3. blogger_url is set (actually published to Blogger)

    Args:
        supabase: Supabase client
        week_start: Start of the week (datetime)

    Returns:
        List of published blog post records
    """
    week_start_iso = week_start.isoformat()

    try:
        # Query for published posts with blogger_url
        result = supabase.table("blog_posts").select(
            "id, title, category, status, blogger_url, blogger_post_id, "
            "summary, original_link, created_at, generated_at"
        ).gte(
            "created_at", week_start_iso
        ).eq(
            "status", "published"
        ).not_.is_(
            "blogger_url", "null"
        ).execute()

        return result.data or []
    except Exception as e:
        print(f"Error querying blog posts: {e}")
        return []


def write_post_json(post: Dict[str, Any], output_dir: str) -> str:
    """
    Write a blog post to a JSON file.

    Args:
        post: Blog post record from Supabase
        output_dir: Output directory path

    Returns:
        Path to the written file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Build the JSON structure expected by mailchimp_campaign.py
    post_data = {
        "title": post.get("title", "Article"),
        "blogger_url": post.get("blogger_url"),
        "published_url": post.get("blogger_url"),  # Alias for compatibility
        "category": post.get("category", "SHOPPERS"),
        "summary": post.get("summary", ""),
        "description": post.get("summary", ""),  # Alias for compatibility
        "original_link": post.get("original_link", ""),
        "generated_at": post.get("generated_at", post.get("created_at", "")),
        "blogger_post_id": post.get("blogger_post_id"),
        "status": post.get("status"),
        "id": post.get("id")
    }

    # Use the database ID for the filename
    post_id = post.get("id", "unknown")
    filename = f"{post_id}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(post_data, f, indent=2, ensure_ascii=False)

    return filepath


def fetch_and_write_posts(output_dir: str = "blog_posts") -> Dict[str, Any]:
    """
    Main function to fetch published posts and write them to JSON files.

    Args:
        output_dir: Directory to write JSON files

    Returns:
        Result dictionary with counts and status
    """
    supabase = get_supabase_client()
    if supabase is None:
        return {
            "success": False,
            "error": "Could not connect to Supabase"
        }

    week_start = get_week_start_date()
    print(f"Fetching posts created since: {week_start.isoformat()}")

    posts = fetch_published_posts(supabase, week_start)

    if not posts:
        return {
            "success": True,
            "week_start": week_start.isoformat(),
            "posts_fetched": 0,
            "shoppers_count": 0,
            "recall_count": 0,
            "files_written": [],
            "warning": "No published posts found for this week"
        }

    # Count by category
    shoppers_count = sum(1 for p in posts if (p.get("category") or "").upper() == "SHOPPERS")
    recall_count = sum(1 for p in posts if (p.get("category") or "").upper() == "RECALL")

    # Write each post to a JSON file
    files_written = []
    for post in posts:
        filepath = write_post_json(post, output_dir)
        files_written.append(filepath)
        print(f"  Wrote: {filepath} - {post.get('title', 'Untitled')[:50]}")

    return {
        "success": True,
        "week_start": week_start.isoformat(),
        "posts_fetched": len(posts),
        "shoppers_count": shoppers_count,
        "recall_count": recall_count,
        "files_written": files_written
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fetch published blog posts from Supabase and write to JSON files"
    )
    parser.add_argument(
        "--output", "-o",
        default="blog_posts",
        help="Output directory for JSON files (default: blog_posts)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output result as JSON"
    )

    args = parser.parse_args()

    result = fetch_and_write_posts(args.output)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print()
        print("=" * 50)
        print("FETCH PUBLISHED POSTS RESULT")
        print("=" * 50)
        print(f"Week Start: {result.get('week_start', 'N/A')}")
        print(f"Posts Fetched: {result.get('posts_fetched', 0)}")
        print(f"  SHOPPERS: {result.get('shoppers_count', 0)}")
        print(f"  RECALL: {result.get('recall_count', 0)}")
        print()

        if result.get("warning"):
            print(f"Warning: {result['warning']}")
        elif result.get("error"):
            print(f"Error: {result['error']}")
        else:
            print(f"Files written to: {args.output}/")

        print("=" * 50)

    # Exit with error if failed
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
