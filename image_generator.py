# image_generator.py
# Google Gemini-powered image generation for Youdle blog posts
#
# Changes:
# - Use a robust import for the Google Generative AI client (google.generativeai)
# - Provide a helpful ImportError message when the client is not available
# - Keep behavior identical otherwise

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

# Robust import for the Google Generative AI client.
# The package exposes its module as `google.generativeai`. Some installs
# or namespace collisions (a legacy `google` package) can cause
# `from google import genai` to fail. Prefer the explicit import and
# provide a clear error message if it's not available.
genai = None
try:
    import google.generativeai as genai  # preferred
except Exception:
    try:
        # fallback: older or different packaging may expose `genai` on google
        from google import genai  # type: ignore
    except Exception:
        genai = None


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
    """Google Gemini-powered image generator for blog posts using google.generativeai client."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generator.

        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        if genai is None:
            raise ImportError(
                "google.generativeai (google-generativeai) client not available. "
                "Install it with `pip install google-generativeai` and ensure there is "
                "no conflicting `google` package installed (run `pip uninstall google` if necessary)."
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Initialize with google-generativeai
        genai.configure(api_key=self.api_key)
        # Use gemini-3-flash-preview for image generation
        self.model_name = "gemini-3-flash-preview"
        # Configure model with response_modalities to enable image output
        self.generation_config = genai.types.GenerationConfig(
            response_modalities=["TEXT", "IMAGE"]
        )
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config=self.generation_config
        )

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
            print(f"[ImageGenerator] Generating image with model: {self.model_name} (response_modalities: TEXT, IMAGE)", flush=True)
            print(f"[ImageGenerator] Prompt: {prompt[:80]}...", flush=True)

            response = self.model.generate_content(prompt)

            # Debug: Print response structure
            if getattr(response, "candidates", None):
                candidate = response.candidates[0]
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None) if content else None
                part_types = []
                if parts:
                    for part in parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            part_types.append("IMAGE")
                        elif hasattr(part, 'text') and part.text:
                            part_types.append("TEXT")
                print(f"[ImageGenerator] Response parts: {part_types if part_types else 'none'}", flush=True)

            # Extract image from response parts
            if getattr(response, "candidates", None):
                candidate = response.candidates[0]
                content = getattr(candidate, "content", None)
                parts = getattr(content, "parts", None)
                if parts:
                    for part in parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Get the image bytes from inline_data
                            image_bytes = part.inline_data.data
                            image_data = base64.b64encode(image_bytes).decode('utf-8')
                            return {
                                "success": True,
                                "image_data": image_data,
                                "format": getattr(part.inline_data, "mime_type", "image/png"),
                                "metadata": {"model": self.model_name}
                            }

            # If no inline image found, return failure
            return {
                "success": False,
                "error": "No image data in response",
                "image_data": None,
                "format": None,
                "metadata": {"model": self.model_name}
            }

        except Exception as e:
            print("[ImageGenerator] Image generation failed:", str(e))
            return {
                "success": False,
                "error": str(e),
                "image_data": None
            }

    def generate_image_for_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image for an article."""
        return self.generate_image(
            title=article.get("title", "Article Image"),
            theme=article.get("category", "")
        )


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
