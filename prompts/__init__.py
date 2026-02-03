# prompts/__init__.py
"""
Youdle Blog Prompt Module

Provides comprehensive prompts for blog post generation with:
- Shared voice/tone guidelines
- Category-specific structures (SHOPPERS vs RECALL)
- Four-part close format
- Zeigarnik gap headline formulas
"""

from .shoppers_prompt import SHOPPERS_BLOG_PROMPT
from .recall_prompt import RECALL_BLOG_PROMPT
from .reflection_prompt import REFLECTION_PROMPT
from .base_guidelines import (
    VOICE_TONE_GUIDELINES,
    TWO_AUDIENCE_APPROACH,
    ATTRIBUTION_RULES,
    HEADLINE_FORMULAS,
    FOUR_PART_CLOSE,
    WHAT_TO_EXCLUDE,
    STRUCTURE_RULES,
)

__all__ = [
    'SHOPPERS_BLOG_PROMPT',
    'RECALL_BLOG_PROMPT',
    'REFLECTION_PROMPT',
    'VOICE_TONE_GUIDELINES',
    'TWO_AUDIENCE_APPROACH',
    'ATTRIBUTION_RULES',
    'HEADLINE_FORMULAS',
    'FOUR_PART_CLOSE',
    'WHAT_TO_EXCLUDE',
    'STRUCTURE_RULES',
    'get_prompt',
]


def get_prompt(category: str) -> str:
    """
    Get the appropriate prompt for a category.

    Args:
        category: Either "shoppers" or "recall" (case-insensitive)

    Returns:
        The full prompt string for that category
    """
    if category.upper() == "RECALL":
        return RECALL_BLOG_PROMPT
    return SHOPPERS_BLOG_PROMPT
