# image_generator.py
# Google Gemini-powered image generation for Youdle blog posts

import os
import base64
import asyncio
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_IMAGE_SIZE = 600  # pixels
IMAGE_PROMPT_TEMPLATE = """Create a retail-safe image for a grocery-focused newsletter titled "{title}".

Theme/Context: {theme}

Strictly follow these guidelines:
- Professional grocery context
- No humans; if present, only abstract silhouettes without facial features
- No brand names or logos; show generic private-label packaging
- English-only shelf labels; simple words and US dollar prices; all text sharp
- No UI overlays; no out-of-focus text
- Clean, modern, inviting grocery store aesthetic
- Focus on the products/items mentioned in the article
- Size: {size}px width

The image should be suitable for a professional newsletter about grocery shopping and consumer products."""


class ImageGenerator:
    """Google Gemini-powered image generator for blog posts using new google.genai client."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generator.

        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Use new google.genai client
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-image-preview"

    def _create_image_prompt(
        self,
        title: str,
        theme: str = "",
        size: int = DEFAULT_IMAGE_SIZE
    ) -> str:
        """Create a detailed prompt for image generation."""
        return IMAGE_PROMPT_TEMPLATE.format(
            title=title,
            theme=theme or "grocery shopping and consumer products",
            size=size
        )

    def generate_image(
        self,
        title: str,
        theme: str = "",
        size: int = DEFAULT_IMAGE_SIZE
    ) -> Dict[str, Any]:
        """
        Generate an image for a blog post.

        Args:
            title: Blog post title
            theme: Additional theme/context for the image
            size: Image width in pixels

        Returns:
            Dictionary with image_data (base64), format, and metadata
        """
        prompt = self._create_image_prompt(title, theme, size)

        try:
            print(f"[ImageGenerator] Generating image with model: {self.model_name}")
            print(f"[ImageGenerator] Prompt: {prompt[:100]}...")

            # Use generate_content for image generation (not generate_images)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            print(f"[ImageGenerator] Response received: {type(response)}")

            # Extract image from response parts
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Get the image bytes from inline_data
                        image_bytes = part.inline_data.data
                        image_data = base64.b64encode(image_bytes).decode('utf-8')

                        print(f"[ImageGenerator] Success! Image data length: {len(image_data)}")

                        return {
                            "success": True,
                            "image_data": image_data,
                            "format": part.inline_data.mime_type.split('/')[-1] if part.inline_data.mime_type else "png",
                            "prompt": prompt,
                            "title": title
                        }

            print(f"[ImageGenerator] No image in response parts")
            return {
                "success": False,
                "error": "No image generated in response",
                "prompt": prompt,
                "title": title
            }

        except Exception as e:
            import traceback
            error_detail = f"{type(e).__name__}: {str(e)}"
            print(f"[ImageGenerator] ERROR: {error_detail}")
            print(f"[ImageGenerator] Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": error_detail,
                "prompt": prompt,
                "title": title
            }

    def generate_image_for_article(
        self,
        article: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an image for an article.

        Args:
            article: Article dictionary with title, content, category

        Returns:
            Dictionary with image data and metadata
        """
        title = article.get("title", "Grocery News")
        content = article.get("content", article.get("description", ""))
        category = article.get("category", "SHOPPERS")

        # Create theme based on category and content
        if category.upper() == "RECALL":
            theme = "Food safety alert, recall notice, consumer warning"
        else:
            # Extract key themes from content
            theme = f"Based on: {content[:200]}..." if content else ""

        return self.generate_image(title=title, theme=theme)

    async def generate_images_concurrent(
        self,
        articles: List[Dict[str, Any]],
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generate images for multiple articles concurrently.

        Args:
            articles: List of article dictionaries
            max_workers: Maximum number of concurrent workers

        Returns:
            List of image generation results
        """
        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self.generate_image_for_article,
                    article
                )
                for article in articles
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "article": articles[i]
                })
            else:
                result["article"] = articles[i]
                processed_results.append(result)

        return processed_results


class PlaceholderImageGenerator:
    """
    Fallback image generator that creates placeholder images.
    Use this for testing or when Gemini API is unavailable.
    """

    def __init__(self):
        """Initialize the placeholder generator."""
        pass

    def generate_image(
        self,
        title: str,
        theme: str = "",
        size: int = DEFAULT_IMAGE_SIZE
    ) -> Dict[str, Any]:
        """Generate a placeholder image."""
        # Create a simple SVG placeholder
        svg = f'''<svg width="{size}" height="{int(size * 9/16)}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" text-anchor="middle" fill="#888" font-size="20">
                {title[:30]}...
            </text>
        </svg>'''

        image_data = base64.b64encode(svg.encode('utf-8')).decode('utf-8')

        return {
            "success": True,
            "image_data": image_data,
            "format": "svg",
            "placeholder": True,
            "title": title
        }

    def generate_image_for_article(
        self,
        article: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a placeholder image for an article."""
        return self.generate_image(
            title=article.get("title", "Article Image"),
            theme=article.get("category", "")
        )

    async def generate_images_concurrent(
        self,
        articles: List[Dict[str, Any]],
        max_workers: int = 4
    ) -> List[Dict[str, Any]]:
        """Generate placeholder images for multiple articles."""
        results = []
        for article in articles:
            result = self.generate_image_for_article(article)
            result["article"] = article
            results.append(result)
        return results


def get_image_generator(use_placeholder: bool = False) -> ImageGenerator:
    """
    Get an image generator instance.

    Args:
        use_placeholder: Use placeholder generator instead of Gemini

    Returns:
        ImageGenerator or PlaceholderImageGenerator instance
    """
    if use_placeholder:
        return PlaceholderImageGenerator()

    try:
        return ImageGenerator()
    except ValueError:
        print("Warning: GEMINI_API_KEY not set, using placeholder images")
        return PlaceholderImageGenerator()


# For testing
if __name__ == "__main__":
    import json

    # Test with real generator
    generator = get_image_generator(use_placeholder=False)

    test_article = {
        "title": "New Organic Snacks Hit Store Shelves",
        "content": "A new line of organic snack foods is now available at major grocery chains.",
        "category": "SHOPPERS"
    }

    print("Testing image generation...")
    result = generator.generate_image_for_article(test_article)

    print(f"Success: {result['success']}")
    print(f"Format: {result.get('format', 'unknown')}")
    print(f"Data length: {len(result.get('image_data', ''))}")
    if not result['success']:
        print(f"Error: {result.get('error', 'unknown')}")
