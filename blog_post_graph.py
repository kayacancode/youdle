# blog_post_graph.py
# LangGraph StateGraph for blog post generation workflow orchestration

import os
import sys
import hashlib
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import operator

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from langgraph.graph import StateGraph, START, END

# Import existing components
from zap_exa_ranker import main as search_articles_exa
from langchain_blog_agent import BlogPostGenerator
from image_generator import get_image_generator
from supabase_storage import get_supabase_client
from example_store import ExampleStore
from reflection_agent import ReflectionAgent
from prompt_refiner import PromptRefiner
from learning_memory import LearningMemory
from imgbb_upload import upload_image_to_imgbb, DEFAULT_RECALL_IMAGE_URL


# ============================================================================
# STATE DEFINITION
# ============================================================================

class BlogPostState(TypedDict):
    """
    State schema for the blog post generation workflow.
    
    Annotated fields with operator.add will accumulate values across nodes.
    """
    # Input parameters
    batch_size: int
    search_days_back: int
    model: str
    use_placeholder_images: bool
    
    # Search results
    search_results: Dict[str, Any]
    
    # Selected articles
    articles: List[Dict[str, Any]]
    shoppers_articles: List[Dict[str, Any]]
    recall_articles: List[Dict[str, Any]]
    
    # Learning context
    learning_context: Dict[str, Any]
    shoppers_context: Dict[str, Any]
    recall_context: Dict[str, Any]
    
    # Generated blog posts (accumulates across iterations)
    generated_posts: Annotated[List[Dict[str, Any]], operator.add]
    
    # Reflection results
    reflection_results: List[Dict[str, Any]]
    posts_needing_regeneration: List[Dict[str, Any]]
    regeneration_count: int
    max_regenerations: int
    
    # Image generation results
    images: List[Dict[str, Any]]
    
    # Upload results
    uploaded_urls: List[Dict[str, Any]]
    
    # Final assembled posts
    final_posts: List[Dict[str, Any]]
    
    # Saved file paths
    saved_files: List[str]
    
    # Processing cache (for deduplication)
    processed_urls: Dict[str, str]
    
    # Errors and logging
    errors: Annotated[List[str], operator.add]
    logs: Annotated[List[str], operator.add]
    
    # Workflow metadata
    start_time: str
    end_time: str


# ============================================================================
# CONFIGURATION
# ============================================================================

BLOG_POSTS_DIR = "blog_posts"
MAX_REGENERATIONS = 2
MAX_WORKERS = 4


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_url_hash(url: str) -> str:
    """Generate a hash for a URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def create_initial_state(
    batch_size: int = 30,
    search_days_back: int = 30,
    model: str = "gpt-4",
    use_placeholder_images: bool = False
) -> BlogPostState:
    """Create the initial state for the workflow."""
    return BlogPostState(
        batch_size=batch_size,
        search_days_back=search_days_back,
        model=model,
        use_placeholder_images=use_placeholder_images,
        search_results={},
        articles=[],
        shoppers_articles=[],
        recall_articles=[],
        learning_context={},
        shoppers_context={},
        recall_context={},
        generated_posts=[],
        reflection_results=[],
        posts_needing_regeneration=[],
        regeneration_count=0,
        max_regenerations=MAX_REGENERATIONS,
        images=[],
        uploaded_urls=[],
        final_posts=[],
        saved_files=[],
        processed_urls={},
        errors=[],
        logs=[],
        start_time=datetime.now().isoformat(),
        end_time=""
    )


# ============================================================================
# NODE IMPLEMENTATIONS
# ============================================================================

def search_articles_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Search for articles using Exa API.
    
    Calls the existing zap_exa_ranker.py functionality.
    """
    logs = [f"[{datetime.now().isoformat()}] Searching for articles..."]
    
    try:
        input_data = {
            "batch_size": state["batch_size"],
            "batch_index": 0,
            "search_days_back": state["search_days_back"]
        }
        
        search_results = search_articles_exa(input_data)
        
        if search_results.get("error"):
            return {
                "search_results": {},
                "errors": [f"Search error: {search_results['error']}"],
                "logs": logs + [f"Search failed: {search_results['error']}"]
            }
        
        logs.append(f"Found {len(search_results.get('items', []))} articles")
        
        return {
            "search_results": search_results,
            "logs": logs
        }
        
    except Exception as e:
        return {
            "search_results": {},
            "errors": [f"Search exception: {str(e)}"],
            "logs": logs + [f"Search exception: {str(e)}"]
        }


def select_articles_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Select top articles for blog post generation.

    Filters out already-processed articles and selects articles based on batch_size.
    Allocates 1 recall article and remaining slots for shoppers articles.
    """
    logs = [f"[{datetime.now().isoformat()}] Selecting top articles..."]

    search_results = state.get("search_results", {})
    processed_urls = state.get("processed_urls", {})
    batch_size = state.get("batch_size", 6)

    # Calculate article allocation: 1 recall + rest shoppers
    # Ensure at least 1 recall if batch_size > 0
    max_recall = 1 if batch_size > 0 else 0
    max_shoppers = max(0, batch_size - max_recall)

    items = search_results.get("items", [])
    recall_items = search_results.get("recall_items", [])

    # Filter out already cached articles
    today = datetime.now().strftime("%Y-%m-%d")

    def is_not_cached(item):
        url = item.get("link", "")
        url_hash = get_url_hash(url)
        cached = processed_urls.get(url_hash, {})
        return cached.get("date") != today if isinstance(cached, dict) else True

    # Select shoppers articles
    shoppers_articles = [
        item for item in items
        if item.get("category", "").upper() != "RECALL"
        and is_not_cached(item)
    ][:max_shoppers]

    # Select recall articles
    recall_articles = [
        item for item in recall_items
        if is_not_cached(item)
    ][:max_recall]

    all_articles = (shoppers_articles + recall_articles)[:batch_size]

    logs.append(f"Selected {len(shoppers_articles)} shoppers + {len(recall_articles)} recall articles (batch_size={batch_size}, total={len(all_articles)})")

    return {
        "shoppers_articles": shoppers_articles,
        "recall_articles": recall_articles,
        "articles": all_articles,
        "logs": logs
    }


def load_learning_context_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Load learning context (examples, memory, patterns) for generation.
    """
    logs = [f"[{datetime.now().isoformat()}] Loading learning context..."]
    
    try:
        supabase = get_supabase_client()
        example_store = ExampleStore(supabase)
        prompt_refiner = PromptRefiner(supabase)
        learning_memory = LearningMemory(supabase)
        
        def load_context_for_category(category: str) -> Dict[str, Any]:
            memory = learning_memory.load_session_memory(category)
            examples = example_store.get_examples_for_generation(category)
            prompt_additions = prompt_refiner.get_refined_prompt_section(category)
            
            return {
                "memory": memory,
                "good_examples": examples.get("good", []),
                "bad_examples": examples.get("bad", []),
                "prompt_additions": prompt_additions,
                "common_mistakes": memory.get("common_mistakes", [])
            }
        
        shoppers_context = load_context_for_category("shoppers")
        recall_context = load_context_for_category("recall")
        
        logs.append(f"Loaded {len(shoppers_context['good_examples'])} good examples")
        logs.append(f"Found {len(shoppers_context['common_mistakes'])} common mistakes to avoid")
        
        return {
            "shoppers_context": shoppers_context,
            "recall_context": recall_context,
            "learning_context": {
                "shoppers": shoppers_context,
                "recall": recall_context
            },
            "logs": logs
        }
        
    except Exception as e:
        logs.append(f"Learning context load error (continuing with empty): {str(e)}")
        empty_context = {
            "memory": {},
            "good_examples": [],
            "bad_examples": [],
            "prompt_additions": "",
            "common_mistakes": []
        }
        return {
            "shoppers_context": empty_context,
            "recall_context": empty_context,
            "learning_context": {"shoppers": empty_context, "recall": empty_context},
            "logs": logs
        }


def generate_posts_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Generate blog posts using LangChain batch processing.
    
    Uses the BlogPostGenerator.batch_generate() for parallel generation.
    """
    logs = [f"[{datetime.now().isoformat()}] Generating blog posts..."]
    
    articles = state.get("articles", [])
    
    if not articles:
        return {
            "generated_posts": [],
            "logs": logs + ["No articles to process"]
        }
    
    # Check if we're regenerating specific posts
    posts_needing_regeneration = state.get("posts_needing_regeneration", [])
    if posts_needing_regeneration:
        articles_to_process = posts_needing_regeneration
        logs.append(f"Regenerating {len(articles_to_process)} posts...")
    else:
        articles_to_process = articles
    
    try:
        generator = BlogPostGenerator(model=state.get("model", "gpt-4"))
        
        # Prepare articles with learning context
        shoppers_context = state.get("shoppers_context", {})
        recall_context = state.get("recall_context", {})
        
        generated_posts = []
        
        for article in articles_to_process:
            category = article.get("category", "SHOPPERS").lower()
            context = recall_context if category == "recall" else shoppers_context
            
            result = generator.generate_with_reflection(
                title=article.get("title", ""),
                content=article.get("content", article.get("description", "")),
                original_link=article.get("link", ""),
                category=category,
                good_examples=context.get("good_examples"),
                bad_examples=context.get("bad_examples")
            )
            
            result["article"] = article
            result["category"] = category
            result["post_id"] = get_url_hash(article.get("link", ""))
            
            generated_posts.append(result)
            
            status = "✓" if result.get("success") else "✗"
            logs.append(f"  {status} {article.get('title', 'Unknown')[:50]}...")
        
        logs.append(f"Generated {len(generated_posts)} blog posts")
        
        return {
            "generated_posts": generated_posts,
            "logs": logs
        }
        
    except Exception as e:
        return {
            "generated_posts": [],
            "errors": [f"Generation error: {str(e)}"],
            "logs": logs + [f"Generation exception: {str(e)}"]
        }


def reflect_posts_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Run reflection agent on generated posts to validate quality.
    """
    logs = [f"[{datetime.now().isoformat()}] Reflecting on generated posts..."]
    
    generated_posts = state.get("generated_posts", [])
    
    if not generated_posts:
        return {
            "reflection_results": [],
            "posts_needing_regeneration": [],
            "logs": logs + ["No posts to reflect on"]
        }
    
    try:
        reflection_agent = ReflectionAgent()
        learning_context = state.get("learning_context", {})
        
        reflection_results = []
        posts_needing_regeneration = []
        
        for post in generated_posts:
            blog_post = post.get("blog_post", "")
            category = post.get("category", "shoppers")
            bad_examples = learning_context.get(category, {}).get("bad_examples", [])
            
            reflection = reflection_agent.reflect(blog_post, bad_examples)
            
            result = {
                "post_id": post.get("post_id"),
                "reflection": reflection,
                "is_valid": reflection.get("is_valid", False),
                "should_regenerate": reflection_agent.should_regenerate(reflection)
            }
            
            reflection_results.append(result)
            
            if result["should_regenerate"]:
                # Include reflection hints for regeneration
                post_with_hints = post.get("article", {}).copy()
                post_with_hints["regeneration_hints"] = reflection_agent.get_regeneration_hints(reflection)
                posts_needing_regeneration.append(post_with_hints)
                logs.append(f"  ⚠ Post {post.get('post_id')} needs regeneration")
        
        valid_count = sum(1 for r in reflection_results if r["is_valid"])
        logs.append(f"Reflection complete: {valid_count}/{len(reflection_results)} valid")
        
        return {
            "reflection_results": reflection_results,
            "posts_needing_regeneration": posts_needing_regeneration,
            "logs": logs
        }
        
    except Exception as e:
        logs.append(f"Reflection error (continuing): {str(e)}")
        return {
            "reflection_results": [],
            "posts_needing_regeneration": [],
            "logs": logs
        }


def should_regenerate(state: BlogPostState) -> str:
    """
    Conditional edge function: Determine if regeneration is needed.
    
    Returns:
        "regenerate" - if posts need regeneration and we haven't exceeded max
        "continue" - if all posts are valid or we've hit max regenerations
    """
    posts_needing_regeneration = state.get("posts_needing_regeneration", [])
    regeneration_count = state.get("regeneration_count", 0)
    max_regenerations = state.get("max_regenerations", MAX_REGENERATIONS)
    
    if posts_needing_regeneration and regeneration_count < max_regenerations:
        return "regenerate"
    
    return "continue"


def increment_regeneration_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Increment regeneration counter before looping back.
    """
    return {
        "regeneration_count": state.get("regeneration_count", 0) + 1,
        "logs": [f"[{datetime.now().isoformat()}] Regeneration attempt {state.get('regeneration_count', 0) + 1}"]
    }


def generate_images_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Generate images for all blog posts in parallel.
    """
    logs = [f"[{datetime.now().isoformat()}] Generating images..."]
    
    generated_posts = state.get("generated_posts", [])
    
    if not generated_posts:
        return {"images": [], "logs": logs + ["No posts for image generation"]}
    
    try:
        image_generator = get_image_generator(
            use_placeholder=state.get("use_placeholder_images", False)
        )
        
        images = []
        
        for post in generated_posts:
            if not post.get("success") and not post.get("blog_post"):
                continue

            article = post.get("article", {})
            category = post.get("category", "").upper()

            # Skip RECALL articles - they use a default image instead of generated
            if category == "RECALL":
                logs.append(f"  ⊘ Skipping image for RECALL: {article.get('title', 'Unknown')[:40]}...")
                # Add placeholder entry so upload_images_node knows about this post
                images.append({
                    "post_id": post.get("post_id"),
                    "success": False,
                    "is_recall": True
                })
                continue

            image_result = image_generator.generate_image_for_article(article)
            image_result["post_id"] = post.get("post_id")
            image_result["is_recall"] = False

            images.append(image_result)

            status = "✓" if image_result.get("success") else "✗"
            error_msg = f" ({image_result.get('error', 'unknown error')})" if not image_result.get("success") else ""
            logs.append(f"  {status} Image for {article.get('title', 'Unknown')[:40]}...{error_msg}")
        
        logs.append(f"Generated {len([i for i in images if i.get('success')])} images")
        
        return {
            "images": images,
            "logs": logs
        }
        
    except Exception as e:
        return {
            "images": [],
            "errors": [f"Image generation error: {str(e)}"],
            "logs": logs + [f"Image generation exception: {str(e)}"]
        }


def upload_images_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Upload generated images to imgBB.
    RECALL articles get a default image URL instead.
    """
    logs = [f"[{datetime.now().isoformat()}] Uploading images to imgBB..."]

    images = state.get("images", [])

    if not images:
        return {"uploaded_urls": [], "logs": logs + ["No images to upload"]}

    try:
        uploaded_urls = []

        for image in images:
            post_id = image.get("post_id", "unknown")

            # RECALL articles use default image
            if image.get("is_recall"):
                uploaded_urls.append({
                    "post_id": post_id,
                    "url": DEFAULT_RECALL_IMAGE_URL,
                    "success": True
                })
                logs.append(f"  ✓ Using default image for RECALL post {post_id}")
                continue

            # Failed image generation - use placeholder
            if not image.get("success"):
                uploaded_urls.append({
                    "post_id": post_id,
                    "url": "{IMAGE_HERE}",
                    "success": False
                })
                logs.append(f"  ✗ No image data for {post_id}")
                continue

            # Upload to imgBB
            upload_result = upload_image_to_imgbb(
                image_data=image.get("image_data", ""),
                name=post_id
            )

            uploaded_urls.append({
                "post_id": post_id,
                "url": upload_result.get("url", "{IMAGE_HERE}"),
                "success": upload_result.get("success", False)
            })

            status = "✓" if upload_result.get("success") else "✗"
            logs.append(f"  {status} Uploaded {post_id} to imgBB")

        success_count = sum(1 for u in uploaded_urls if u.get("success"))
        logs.append(f"Uploaded {success_count}/{len(uploaded_urls)} images")

        return {
            "uploaded_urls": uploaded_urls,
            "logs": logs
        }

    except Exception as e:
        return {
            "uploaded_urls": [],
            "errors": [f"Upload error: {str(e)}"],
            "logs": logs + [f"Upload exception: {str(e)}"]
        }


def assemble_html_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Assemble final HTML by replacing placeholders with image URLs.
    """
    logs = [f"[{datetime.now().isoformat()}] Assembling final HTML..."]

    generated_posts = state.get("generated_posts", [])
    uploaded_urls = state.get("uploaded_urls", [])

    # Create URL lookup
    url_lookup = {u["post_id"]: u["url"] for u in uploaded_urls}

    # Deduplicate posts by post_id, keeping only the latest version
    # (since regeneration cycles can create duplicates with operator.add)
    posts_by_id = {}
    for post in generated_posts:
        if not post.get("blog_post"):
            continue
        post_id = post.get("post_id", "")
        # Keep the latest version (last one in list)
        posts_by_id[post_id] = post

    logs.append(f"Deduplicated {len(generated_posts)} posts down to {len(posts_by_id)} unique posts")

    final_posts = []

    for post_id, post in posts_by_id.items():
        blog_post = post.get("blog_post", "")
        article = post.get("article", {})
        original_link = article.get("link", "")

        # Get image URL
        image_url = url_lookup.get(post_id, "{IMAGE_HERE}")

        # Replace placeholders
        final_html = blog_post
        final_html = final_html.replace("{IMAGE_HERE}", image_url)
        final_html = final_html.replace("{{IMAGE_HERE}}", image_url)
        final_html = final_html.replace("{original_link}", original_link)

        final_post = {
            "post_id": post_id,
            "html": final_html,
            "title": article.get("title", ""),
            "category": post.get("category", "shoppers"),
            "original_link": original_link,
            "image_url": image_url,
            "article": article,
            "reflection": post.get("reflection", {}),
            "attempts": post.get("attempts", 1)
        }

        final_posts.append(final_post)

    logs.append(f"Assembled {len(final_posts)} final blog posts")

    return {
        "final_posts": final_posts,
        "logs": logs
    }


def save_posts_node(state: BlogPostState) -> Dict[str, Any]:
    """
    Node: Save final blog posts to filesystem.
    """
    logs = [f"[{datetime.now().isoformat()}] Saving blog posts..."]
    
    final_posts = state.get("final_posts", [])
    
    if not final_posts:
        return {"saved_files": [], "logs": logs + ["No posts to save"]}
    
    # Ensure output directory exists
    os.makedirs(BLOG_POSTS_DIR, exist_ok=True)
    
    saved_files = []
    processed_urls = state.get("processed_urls", {}).copy()
    
    for post in final_posts:
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(
                c for c in post.get("title", "post")[:30] 
                if c.isalnum() or c in " -_"
            ).strip().replace(" ", "_")
            
            post_id = post.get("post_id", "unknown")
            filename = f"{timestamp}_{safe_title}_{post_id}"
            
            # Save HTML
            html_path = os.path.join(BLOG_POSTS_DIR, f"{filename}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(post["html"])
            
            # Save metadata
            import json
            metadata = {
                "title": post.get("title", ""),
                "category": post.get("category", ""),
                "original_link": post.get("original_link", ""),
                "image_url": post.get("image_url", ""),
                "generated_at": datetime.now().isoformat(),
                "article": post.get("article", {}),
                "reflection": post.get("reflection", {}),
                "attempts": post.get("attempts", 1)
            }
            
            metadata_path = os.path.join(BLOG_POSTS_DIR, f"{filename}.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
            
            saved_files.append(html_path)
            
            # Update processed URLs cache
            processed_urls[post_id] = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "blog_post_id": post_id
            }
            
            logs.append(f"  ✓ Saved {filename}.html")
            
        except Exception as e:
            logs.append(f"  ✗ Error saving post: {str(e)}")
    
    logs.append(f"Saved {len(saved_files)} blog posts to {BLOG_POSTS_DIR}/")
    
    return {
        "saved_files": saved_files,
        "processed_urls": processed_urls,
        "end_time": datetime.now().isoformat(),
        "logs": logs
    }


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def create_blog_post_graph() -> StateGraph:
    """
    Create the LangGraph StateGraph for blog post generation.
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph
    workflow = StateGraph(BlogPostState)
    
    # Add nodes
    workflow.add_node("search_articles", search_articles_node)
    workflow.add_node("select_articles", select_articles_node)
    workflow.add_node("load_learning_context", load_learning_context_node)
    workflow.add_node("generate_posts", generate_posts_node)
    workflow.add_node("reflect_posts", reflect_posts_node)
    workflow.add_node("increment_regeneration", increment_regeneration_node)
    workflow.add_node("generate_images", generate_images_node)
    workflow.add_node("upload_images", upload_images_node)
    workflow.add_node("assemble_html", assemble_html_node)
    workflow.add_node("save_posts", save_posts_node)
    
    # Add edges
    workflow.add_edge(START, "search_articles")
    workflow.add_edge("search_articles", "select_articles")
    workflow.add_edge("select_articles", "load_learning_context")
    workflow.add_edge("load_learning_context", "generate_posts")
    workflow.add_edge("generate_posts", "reflect_posts")
    
    # Conditional edge: regenerate or continue
    workflow.add_conditional_edges(
        "reflect_posts",
        should_regenerate,
        {
            "regenerate": "increment_regeneration",
            "continue": "generate_images"
        }
    )
    
    # Regeneration loop
    workflow.add_edge("increment_regeneration", "generate_posts")
    
    # Continue to image generation
    workflow.add_edge("generate_images", "upload_images")
    workflow.add_edge("upload_images", "assemble_html")
    workflow.add_edge("assemble_html", "save_posts")
    workflow.add_edge("save_posts", END)
    
    return workflow.compile()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def run_blog_post_workflow(
    batch_size: int = 30,
    search_days_back: int = 30,
    model: str = "gpt-4",
    use_placeholder_images: bool = False
) -> Dict[str, Any]:
    """
    Run the complete blog post generation workflow using LangGraph.
    
    Args:
        batch_size: Number of articles to search
        search_days_back: How far back to search
        model: OpenAI model for generation
        use_placeholder_images: Use placeholder images instead of Gemini
        
    Returns:
        Final workflow state with results
    """
    print("=" * 60)
    print("LANGGRAPH BLOG POST GENERATION WORKFLOW")
    print("=" * 60)
    
    # Create the graph
    app = create_blog_post_graph()
    
    # Create initial state
    initial_state = create_initial_state(
        batch_size=batch_size,
        search_days_back=search_days_back,
        model=model,
        use_placeholder_images=use_placeholder_images
    )
    
    # Run the workflow
    final_state = app.invoke(initial_state)
    
    # Print logs to stderr to avoid contaminating JSON output
    for log in final_state.get("logs", []):
        print(log, file=sys.stderr)

    # Print errors to stderr
    if final_state.get("errors"):
        print("\n⚠️ Errors:", file=sys.stderr)
        for error in final_state["errors"]:
            print(f"  - {error}", file=sys.stderr)

    # Calculate duration
    start_time_str = final_state.get("start_time") or datetime.now().isoformat()
    end_time_str = final_state.get("end_time") or datetime.now().isoformat()
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)
    duration = (end_time - start_time).total_seconds()

    # Print summary to stderr
    print("\n" + "=" * 60, file=sys.stderr)
    print("SUMMARY", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Posts generated: {len(final_state.get('final_posts', []))}", file=sys.stderr)
    print(f"Files saved: {len(final_state.get('saved_files', []))}", file=sys.stderr)
    print(f"Errors: {len(final_state.get('errors', []))}", file=sys.stderr)
    print(f"Duration: {duration:.2f} seconds", file=sys.stderr)
    print(f"Output: {BLOG_POSTS_DIR}/", file=sys.stderr)
    
    # Return summary
    return {
        "success": len(final_state.get("errors", [])) == 0,
        "posts_generated": len(final_state.get("final_posts", [])),
        "files_saved": final_state.get("saved_files", []),
        "errors": final_state.get("errors", []),
        "duration_seconds": round(duration, 2),
        "output_directory": BLOG_POSTS_DIR,
        "final_state": final_state
    }


# For testing and CLI usage
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Run LangGraph blog post workflow")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--placeholder-images", action="store_true", help="Use placeholder images")
    parser.add_argument("--batch-size", type=int, default=30, help="Number of articles to search")
    parser.add_argument("--days-back", type=int, default=30, help="Search window in days")
    
    args = parser.parse_args()
    
    result = run_blog_post_workflow(
        batch_size=args.batch_size,
        search_days_back=args.days_back,
        model=args.model,
        use_placeholder_images=args.placeholder_images
    )
    
    # Print result (excluding full state for readability)
    result_summary = {k: v for k, v in result.items() if k != "final_state"}
    print("\nResult:")
    print(json.dumps(result_summary, indent=2, default=str))


