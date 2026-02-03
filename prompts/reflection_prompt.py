# prompts/reflection_prompt.py
# Updated REFLECTION_PROMPT for validating blog posts

REFLECTION_PROMPT = """Review this generated blog post and check for compliance with ALL requirements:

## Structure Validation
1. HTML structure: Must start with <div> and end with </div>
2. Image tag: Must have <img src="{{IMAGE_HERE}}" alt="article image"/> at the start
3. Headline: Must have exactly one <h2> tag (sentence case, not Title Case)
4. First paragraph: Must begin with "MEMPHIS, Tenn. (Youdle) -"
5. List: Must have a <ul> with <li> items

## Word Count Validation
6. Word count: Must be 400-600 words (NOT 250 - this is the new requirement)

## Four-Part Close Validation (ALL FOUR required)
7. Youdle Search CTA: Must include link to youdle.io with product/search mention
8. Youdle Community CTA: Must include link to youdle.io/community
9. Blog subscription CTA: Must include link to getyoudle.com/blog
10. Original source link: Must include "Read the full story" link to source

## Quality Validation
11. Attribution: Factual claims should be attributed to credible sources
12. No corporate language: No "innovative," "game-changing," "leverage," etc.
13. Second-person voice: Uses "you" not "consumers" or "shoppers"

Blog post to review:
{blog_post}

Respond with a JSON object:
{{
    "is_valid": true/false,
    "word_count": <actual word count>,
    "has_four_part_close": {{
        "youdle_search": true/false,
        "youdle_community": true/false,
        "youdle_blog": true/false,
        "source_link": true/false
    }},
    "issues": ["list of specific issues found"],
    "suggestions": ["how to fix each issue"]
}}
"""
