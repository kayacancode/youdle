# langchain_blog_agent.py
# LangChain-powered blog post generation chains for Youdle

import os
from typing import List, Dict, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Initialize LLM cache to prevent regenerating identical content
set_llm_cache(InMemoryCache())

# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SHOPPERS_BLOG_PROMPT = """Task: You are a Lead Content Strategist for Youdle, a grocery insights platform. Your goal is to transform the provided article into a 250-word HTML newsletter section for U.S. shoppers.

Content Guidelines

Tone: Conversational, approachable, and neighborly. Balance professionalism with a "friendly heads-up" vibe.

Audience: U.S. everyday shoppers only. Avoid B2B language or advice for retailers.

Geographic Scope: Focus strictly on U.S. topics and products.

Substance: Summarize the core news, explain why it matters to the reader's wallet or health, and provide actionable next steps.

Structure Requirements (Strict Order)

Image: Start with EXACTLY this tag: <img src="{{IMAGE_HERE}}" alt="article image"/>
IMPORTANT: Use the LITERAL text "{{IMAGE_HERE}}" as the src value. Do NOT replace it with any URL from the article. This placeholder will be replaced later with a generated image.

Headline: One <h2> headline. Rephrase the source title to be punchy and shopper-centric.

Body Content: * Begin the first paragraph with: MEMPHIS, Tenn. (Youdle) –

Provide 2–4 <p> paragraphs.

Use a <ul> list with <li> tags for key details, product names, or tips to improve readability.

Links & Closing:

Include one inline mention of <a href="https://www.youdle.io/">Youdle</a>.

Include a "More information" link: <a href="{{original_link}}">More information</a>.

End exactly with: Share your thoughts in the <a href="https://www.youdle.io/community">Youdle Community!</a>

Output Rules

Format: Output a single raw HTML block enclosed in <div>...</div>.

No "Fluff": Do not include <html>, <body>, markdown backticks, or category labels.

Integrity: Do not cut off the article; ensure a complete narrative within the 250-word limit.

{examples_section}

Now generate a blog post for this article:
Title: {title}
Content: {content}
Original Link: {original_link}
"""

RECALL_BLOG_PROMPT = """Task:
You are a Recall Lead Content Strategist for Youdle, a grocery insights platform. Your goal is to transform the provided article into a 250-word HTML newsletter section for U.S. shoppers.

Content Guidelines

Tone: Conversational, approachable, and neighborly. Balance professionalism with a "friendly heads-up" vibe.

Audience: U.S. everyday shoppers only. Avoid B2B language or advice for retailers.

Geographic Scope: Focus strictly on U.S. topics and products.

Substance: Summarize the core news, explain why it matters to the reader's wallet or health, and provide actionable next steps.

Strict Formatting Requirements (Strict Order)
Image: Start with EXACTLY this tag: <img src="{{IMAGE_HERE}}" alt="article image"/>
IMPORTANT: Use the LITERAL text "{{IMAGE_HERE}}" as the src value. Do NOT replace it with any URL from the article. This placeholder will be replaced later with an image.
Headline: One <h2> headline. Rephrase the source title to be punchy and shopper-centric.
Body Content: * Begin the first paragraph with: MEMPHIS, Tenn. (Youdle) –
Provide 2–4 <p> paragraphs. Summarizing the risk and the why
Use a <ul> list with <li> to list exact product names and identifiers (UPCs/Dates).

Links & Closing:

Include one inline mention of <a href="https://www.youdle.io/">Youdle</a>.

Include a "More information" link: <a href="{{original_link}}">More information</a>.

End exactly with: Share your thoughts in the <a href="https://www.youdle.io/community">Youdle Community!</a>

Output Rules

Format: Output a single raw HTML block enclosed in <div>...</div>.

No "Fluff": Do not include <html>, <body>, markdown backticks, or category labels.

Integrity: Do not cut off the article; ensure a complete narrative within the 250-word limit.

{examples_section}

Now generate a recall blog post for this article:
Title: {title}
Content: {content}
Original Link: {original_link}
"""

REFLECTION_PROMPT = """Review this generated blog post and check for compliance:

1. HTML structure: Must start with <div> and end with </div>
2. Image tag: Must have <img src="{{IMAGE_HERE}}" alt="article image"/> at the start
3. Headline: Must have exactly one <h2> tag
4. First paragraph: Must begin with "MEMPHIS, Tenn. (Youdle) –"
5. List: Must have a <ul> with <li> items
6. Links: Must include Youdle link and "More information" link
7. Closing: Must end with the Youdle Community link
8. Word count: Should be approximately 250 words

Blog post to review:
{blog_post}

Respond with a JSON object:
{{
    "is_valid": true/false,
    "issues": ["list of issues found"],
    "suggestions": ["how to fix each issue"]
}}
"""


class BlogPostGenerator:
    """LangChain-powered blog post generator with learning capabilities."""
    
    def __init__(self, model: str = "gpt-4", temperature: float = 0.7):
        """
        Initialize the blog post generator.
        
        Args:
            model: OpenAI model to use (default: gpt-4)
            temperature: Creativity level (0-1, default: 0.7)
        """
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_retries=3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Create chains
        self.shoppers_chain = self._create_chain(SHOPPERS_BLOG_PROMPT)
        self.recall_chain = self._create_chain(RECALL_BLOG_PROMPT)
        self.reflection_chain = self._create_chain(REFLECTION_PROMPT)
    
    def _create_chain(self, prompt_template: str):
        """Create a LangChain chain from a prompt template."""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        return prompt | self.llm | StrOutputParser()
    
    def _format_examples_section(
        self, 
        good_examples: List[str] = None, 
        bad_examples: List[str] = None
    ) -> str:
        """Format examples section for few-shot learning."""
        if not good_examples and not bad_examples:
            return ""
        
        sections = []
        
        if good_examples:
            sections.append("Here are examples of GOOD blog posts (follow this structure):")
            for i, example in enumerate(good_examples[:3], 1):
                sections.append(f"\n--- Good Example {i} ---\n{example}")
        
        if bad_examples:
            sections.append("\nHere are examples of BAD blog posts (avoid these mistakes):")
            for i, example in enumerate(bad_examples[:2], 1):
                sections.append(f"\n--- Bad Example {i} ---\n{example}")
        
        sections.append("\n" + "-" * 50 + "\n")
        return "\n".join(sections)
    
    def generate_shoppers_post(
        self,
        title: str,
        content: str,
        original_link: str,
        good_examples: List[str] = None,
        bad_examples: List[str] = None
    ) -> str:
        """
        Generate a shoppers blog post.
        
        Args:
            title: Article title
            content: Article content
            original_link: Link to original article
            good_examples: List of good example HTML posts
            bad_examples: List of bad example HTML posts
            
        Returns:
            Generated HTML blog post
        """
        examples_section = self._format_examples_section(good_examples, bad_examples)
        
        return self.shoppers_chain.invoke({
            "title": title,
            "content": content,
            "original_link": original_link,
            "examples_section": examples_section
        })
    
    def generate_recall_post(
        self,
        title: str,
        content: str,
        original_link: str,
        good_examples: List[str] = None,
        bad_examples: List[str] = None
    ) -> str:
        """
        Generate a recall blog post.
        
        Args:
            title: Article title
            content: Article content
            original_link: Link to original article
            good_examples: List of good example HTML posts
            bad_examples: List of bad example HTML posts
            
        Returns:
            Generated HTML blog post
        """
        examples_section = self._format_examples_section(good_examples, bad_examples)
        
        return self.recall_chain.invoke({
            "title": title,
            "content": content,
            "original_link": original_link,
            "examples_section": examples_section
        })
    
    def reflect_on_post(self, blog_post: str) -> Dict[str, Any]:
        """
        Use reflection chain to self-evaluate a generated blog post.
        
        Args:
            blog_post: Generated HTML blog post
            
        Returns:
            Dictionary with is_valid, issues, and suggestions
        """
        import json
        
        result = self.reflection_chain.invoke({"blog_post": blog_post})
        
        try:
            # Parse JSON response
            return json.loads(result)
        except json.JSONDecodeError:
            # If parsing fails, do basic validation
            return self._basic_validation(blog_post)
    
    def _basic_validation(self, blog_post: str) -> Dict[str, Any]:
        """Perform basic HTML validation."""
        issues = []
        
        if not blog_post.strip().startswith("<div"):
            issues.append("Missing opening <div> tag")
        if not blog_post.strip().endswith("</div>"):
            issues.append("Missing closing </div> tag")
        if "{IMAGE_HERE}" not in blog_post and "<img" not in blog_post:
            issues.append("Missing image tag")
        if "<h2>" not in blog_post:
            issues.append("Missing <h2> headline")
        if "MEMPHIS, Tenn. (Youdle)" not in blog_post:
            issues.append("Missing 'MEMPHIS, Tenn. (Youdle) –' opener")
        if "<ul>" not in blog_post or "<li>" not in blog_post:
            issues.append("Missing <ul>/<li> list elements")
        if "youdle.io/community" not in blog_post.lower():
            issues.append("Missing Youdle Community link")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": [f"Fix: {issue}" for issue in issues]
        }
    
    def generate_with_reflection(
        self,
        title: str,
        content: str,
        original_link: str,
        category: str = "shoppers",
        good_examples: List[str] = None,
        bad_examples: List[str] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Generate a blog post with self-reflection and retry on issues.
        
        Args:
            title: Article title
            content: Article content
            original_link: Link to original article
            category: "shoppers" or "recall"
            good_examples: List of good example HTML posts
            bad_examples: List of bad example HTML posts
            max_retries: Maximum number of regeneration attempts
            
        Returns:
            Dictionary with blog_post, reflection, and metadata
        """
        generator = (
            self.generate_recall_post if category == "recall" 
            else self.generate_shoppers_post
        )
        
        for attempt in range(max_retries + 1):
            # Generate blog post
            blog_post = generator(
                title=title,
                content=content,
                original_link=original_link,
                good_examples=good_examples,
                bad_examples=bad_examples
            )
            
            # Reflect on the generated post
            reflection = self.reflect_on_post(blog_post)
            
            if reflection.get("is_valid", False):
                return {
                    "blog_post": blog_post,
                    "reflection": reflection,
                    "attempts": attempt + 1,
                    "success": True
                }
            
            # If not valid and we have retries left, include issues in next attempt
            if attempt < max_retries:
                # Add issues to bad examples to avoid
                issues_str = "\n".join(reflection.get("issues", []))
                if bad_examples is None:
                    bad_examples = []
                bad_examples = bad_examples + [
                    f"<!-- Previous attempt had these issues: {issues_str} -->\n{blog_post}"
                ]
        
        # Return last attempt even if not perfect
        return {
            "blog_post": blog_post,
            "reflection": reflection,
            "attempts": max_retries + 1,
            "success": False
        }
    
    def batch_generate(
        self,
        articles: List[Dict[str, Any]],
        good_examples: List[str] = None,
        bad_examples: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple blog posts in parallel using batch processing.
        
        Args:
            articles: List of article dictionaries with title, content, link, category
            good_examples: List of good example HTML posts
            bad_examples: List of bad example HTML posts
            
        Returns:
            List of generated blog post results
        """
        results = []
        
        # Prepare batch inputs
        for article in articles:
            result = self.generate_with_reflection(
                title=article["title"],
                content=article.get("content", article.get("description", "")),
                original_link=article.get("link", article.get("original_link", "")),
                category=article.get("category", "shoppers").lower(),
                good_examples=good_examples,
                bad_examples=bad_examples
            )
            result["article"] = article
            results.append(result)
        
        return results


def create_shoppers_blog_chain(model: str = "gpt-4") -> BlogPostGenerator:
    """
    Create a LangChain chain for shoppers blog post generation.
    
    Args:
        model: OpenAI model to use
        
    Returns:
        BlogPostGenerator instance configured for shoppers posts
    """
    return BlogPostGenerator(model=model)


def create_recall_blog_chain(model: str = "gpt-4") -> BlogPostGenerator:
    """
    Create a LangChain chain for recall blog post generation.
    
    Args:
        model: OpenAI model to use
        
    Returns:
        BlogPostGenerator instance configured for recall posts
    """
    return BlogPostGenerator(model=model)


# For testing
if __name__ == "__main__":
    # Test the generator
    generator = BlogPostGenerator(model="gpt-4")
    
    test_article = {
        "title": "FDA Recalls Popular Frozen Pizza Brand Due to Contamination",
        "content": "The FDA has announced a voluntary recall of XYZ Frozen Pizzas due to potential listeria contamination. The affected products were distributed nationwide between October and November 2024.",
        "link": "https://fda.gov/example-recall",
        "category": "RECALL"
    }
    
    print("Testing blog post generation...")
    result = generator.generate_with_reflection(
        title=test_article["title"],
        content=test_article["content"],
        original_link=test_article["link"],
        category="recall"
    )
    
    print(f"\nGenerated in {result['attempts']} attempt(s)")
    print(f"Valid: {result['success']}")
    print(f"\nBlog Post:\n{result['blog_post'][:500]}...")



