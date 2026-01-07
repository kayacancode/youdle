# image_generator.py
# Google Gemini-powered image generation for Youdle blog posts
# Uses the new google-genai SDK for image generation

import os
import base64
from typing import Optional, Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import the new google-genai SDK
genai_client = None
genai_types = None
try:
    from google import genai
    from google.genai import types as genai_types
    genai_client = genai
except ImportError:
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_IMAGE_SIZE = "1K"  # Options: "1K", "2K", "4K"
DEFAULT_ASPECT_RATIO = "16:9"

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

The image should be suitable for a professional newsletter about grocery shopping and consumer products."""


class ImageGenerator:
    """Google Gemini-powered image generator using the new google-genai SDK."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the image generator.

        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        if genai_client is None:
            raise ImportError(
                "google-genai SDK not available. "
                "Install it with `pip install google-genai`"
            )

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # Initialize the new client
        self.client = genai_client.Client(api_key=self.api_key)
        self.model_name = "gemini-3-pro-image-preview"

    def _create_image_prompt(
        self,
        title: str,
        theme: str = ""
    ) -> str:
        """Create a detailed prompt for image generation."""
        return IMAGE_PROMPT_TEMPLATE.format(
            title=title,
            theme=theme or "grocery shopping and consumer products"
        )

    def generate_image(
        self,
        title: str,
        theme: str = "",
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        image_size: str = DEFAULT_IMAGE_SIZE
    ) -> Dict[str, Any]:
        """
        Generate an image for a blog post.

        Args:
            title: Blog post title
            theme: Additional theme/context for the image
            aspect_ratio: Image aspect ratio (e.g., "16:9", "1:1")
            image_size: Resolution ("1K", "2K", "4K")

        Returns:
            Dictionary with image_data (base64), format, and metadata
        """
        prompt = self._create_image_prompt(title, theme)

        try:
            print(f"[ImageGenerator] Generating image with model: {self.model_name}", flush=True)
            print(f"[ImageGenerator] Prompt: {prompt[:80]}...", flush=True)

            # Use the new google-genai API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                    image_config=genai_types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                        image_size=image_size
                    )
                )
            )

            # Debug: Print response structure
            part_types = []
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        part_types.append("IMAGE")
                    elif hasattr(part, 'text') and part.text:
                        part_types.append("TEXT")
            print(f"[ImageGenerator] Response parts: {part_types if part_types else 'none'}", flush=True)

            # Extract image from response parts
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Get the image bytes from inline_data
                        image_bytes = part.inline_data.data
                        # Handle if already bytes or needs encoding
                        if isinstance(image_bytes, bytes):
                            image_data = base64.b64encode(image_bytes).decode('utf-8')
                        else:
                            image_data = image_bytes  # Already base64 string

                        mime_type = getattr(part.inline_data, "mime_type", "image/png")
                        print(f"[ImageGenerator] ✓ Image generated successfully ({mime_type})", flush=True)

                        return {
                            "success": True,
                            "image_data": image_data,
                            "format": mime_type,
                            "metadata": {"model": self.model_name}
                        }

            # If no inline image found, return failure
            print("[ImageGenerator] ✗ No image data in response", flush=True)
            return {
                "success": False,
                "error": "No image data in response",
                "image_data": None,
                "format": None,
                "metadata": {"model": self.model_name}
            }

        except Exception as e:
            print(f"[ImageGenerator] ✗ Image generation failed: {str(e)}", flush=True)
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
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        image_size: str = DEFAULT_IMAGE_SIZE
    ) -> Dict[str, Any]:
        """Generate a placeholder image."""
        # Create a simple SVG placeholder
        svg = f'''<svg width="600" height="338" xmlns="http://www.w3.org/2000/svg">
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
    except (ImportError, ValueError) as e:
        print(f"Warning: Cannot initialize ImageGenerator ({e}), using placeholder images")
        return PlaceholderImageGenerator()
