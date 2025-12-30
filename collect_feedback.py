#!/usr/bin/env python3
# collect_feedback.py
# CLI interface for collecting human feedback on generated blog posts

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from feedback_collector import FeedbackCollector
from example_store import ExampleStore


def load_blog_posts(directory: str = "blog_posts") -> List[Dict[str, Any]]:
    """
    Load generated blog posts from a directory.
    
    Args:
        directory: Path to blog posts directory
        
    Returns:
        List of blog post data
    """
    posts = []
    
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return posts
    
    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            filepath = os.path.join(directory, filename)
            
            with open(filepath, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # Try to load metadata
            metadata_path = filepath.replace(".html", ".json")
            metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            
            posts.append({
                "id": filename.replace(".html", ""),
                "filename": filename,
                "filepath": filepath,
                "html_content": html_content,
                "metadata": metadata,
                "article_data": metadata.get("article", {})
            })
    
    return posts


def display_post(post: Dict[str, Any]) -> None:
    """Display a blog post for review."""
    print("\n" + "=" * 60)
    print(f"POST: {post['filename']}")
    print("=" * 60)
    
    metadata = post.get("metadata", {})
    if metadata:
        print(f"Title: {metadata.get('title', 'N/A')}")
        print(f"Category: {metadata.get('category', 'N/A')}")
        print(f"Original Link: {metadata.get('original_link', 'N/A')}")
    
    print("\n--- HTML Content ---")
    # Show first 1000 chars
    content = post.get("html_content", "")
    if len(content) > 1000:
        print(content[:1000] + "\n... (truncated)")
    else:
        print(content)
    print("--- End Content ---\n")


def get_feedback_input() -> Dict[str, Any]:
    """Get feedback input from user."""
    print("\nProvide feedback for this post:")
    print("-" * 40)
    
    # Score
    while True:
        try:
            score = int(input("Quality score (1-5): "))
            if 1 <= score <= 5:
                break
            print("Please enter a number between 1 and 5")
        except ValueError:
            print("Please enter a valid number")
    
    # Approved
    approved_input = input("Approved for publication? (y/n): ").strip().lower()
    approved = approved_input in ["y", "yes", "1", "true"]
    
    # Feedback type
    print("\nFeedback type:")
    print("  1. Structure")
    print("  2. Content")
    print("  3. Tone")
    print("  4. Completeness")
    print("  5. Overall")
    
    type_map = {
        "1": "structure",
        "2": "content",
        "3": "tone",
        "4": "completeness",
        "5": "overall"
    }
    
    type_input = input("Select type (1-5) [5]: ").strip() or "5"
    feedback_type = type_map.get(type_input, "overall")
    
    # Comments
    comments = input("Comments (optional): ").strip()
    
    # Reviewer notes
    reviewer_notes = input("Reviewer notes (optional): ").strip()
    
    return {
        "score": score,
        "approved": approved,
        "feedback_type": feedback_type,
        "comments": comments,
        "reviewer_notes": reviewer_notes
    }


def process_posts_interactive(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process posts interactively for feedback.
    
    Args:
        posts: List of blog posts
        
    Returns:
        List of feedback results
    """
    collector = FeedbackCollector()
    results = []
    
    print(f"\nFound {len(posts)} posts to review.")
    
    for i, post in enumerate(posts):
        print(f"\n[{i + 1}/{len(posts)}]")
        display_post(post)
        
        # Ask if user wants to provide feedback
        action = input("\nAction: (r)eview, (s)kip, (q)uit: ").strip().lower()
        
        if action == "q":
            print("Exiting...")
            break
        elif action == "s":
            print("Skipping...")
            continue
        else:
            # Get feedback
            feedback = get_feedback_input()
            
            # Collect feedback
            result = collector.collect_feedback(
                blog_post_id=post["id"],
                blog_post_html=post["html_content"],
                article_data=post.get("article_data", {}),
                score=feedback["score"],
                approved=feedback["approved"],
                feedback_type=feedback["feedback_type"],
                comments=feedback["comments"],
                reviewer_notes=feedback["reviewer_notes"]
            )
            
            result["post_id"] = post["id"]
            results.append(result)
            
            print(f"\nFeedback saved: {'Approved' if feedback['approved'] else 'Not approved'}")
    
    return results


def process_posts_batch(
    posts: List[Dict[str, Any]],
    approve_all: bool = False,
    default_score: int = 4
) -> List[Dict[str, Any]]:
    """
    Process posts in batch mode.
    
    Args:
        posts: List of blog posts
        approve_all: Approve all posts
        default_score: Default score to assign
        
    Returns:
        List of feedback results
    """
    collector = FeedbackCollector()
    results = []
    
    for post in posts:
        result = collector.collect_feedback(
            blog_post_id=post["id"],
            blog_post_html=post["html_content"],
            article_data=post.get("article_data", {}),
            score=default_score,
            approved=approve_all,
            feedback_type="overall",
            comments="Batch processed"
        )
        
        result["post_id"] = post["id"]
        results.append(result)
    
    return results


def main():
    """Main entry point for the feedback collector CLI."""
    parser = argparse.ArgumentParser(
        description="Collect feedback on generated blog posts"
    )
    
    parser.add_argument(
        "--directory", "-d",
        default="blog_posts",
        help="Directory containing blog posts (default: blog_posts)"
    )
    
    parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="Run in batch mode (non-interactive)"
    )
    
    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Approve all posts (batch mode only)"
    )
    
    parser.add_argument(
        "--score",
        type=int,
        default=4,
        choices=[1, 2, 3, 4, 5],
        help="Default score for batch mode (default: 4)"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show feedback summary only"
    )
    
    args = parser.parse_args()
    
    if args.summary:
        collector = FeedbackCollector()
        summary = collector.get_feedback_summary()
        
        print("\n=== Feedback Summary ===")
        print(f"Total feedback: {summary['total_feedback']}")
        print(f"Average score: {summary['average_score']}")
        print(f"Approval rate: {collector.get_approval_rate():.1f}%")
        
        if summary.get("common_issues"):
            print("\nCommon issues:")
            for issue in summary["common_issues"][:5]:
                print(f"  - {issue}")
        
        return
    
    # Load posts
    posts = load_blog_posts(args.directory)
    
    if not posts:
        print(f"No blog posts found in {args.directory}")
        return
    
    # Process posts
    if args.batch:
        results = process_posts_batch(
            posts,
            approve_all=args.approve_all,
            default_score=args.score
        )
        print(f"\nProcessed {len(results)} posts in batch mode")
    else:
        results = process_posts_interactive(posts)
        print(f"\nProcessed {len(results)} posts")
    
    # Show summary
    if results:
        approved_count = sum(1 for r in results if r.get("approved", False))
        print(f"\nApproved: {approved_count}/{len(results)}")


if __name__ == "__main__":
    main()



