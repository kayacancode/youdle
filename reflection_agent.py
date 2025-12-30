# reflection_agent.py
# Self-reflection agent for evaluating generated blog posts

import os
import re
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ReflectionAgent:
    """
    Self-reflection agent that evaluates generated blog posts
    for compliance with structure and content requirements.
    """
    
    # Required elements for validation
    REQUIRED_ELEMENTS = {
        "div_wrapper": {
            "pattern": r"^\s*<div[^>]*>.*</div>\s*$",
            "description": "Must be wrapped in <div>...</div>",
            "flags": re.DOTALL
        },
        "image_tag": {
            "pattern": r'<img[^>]+src=["\'][^"\']*IMAGE_HERE[^"\']*["\'][^>]*>',
            "description": "Must have image tag with {IMAGE_HERE} placeholder"
        },
        "h2_headline": {
            "pattern": r"<h2[^>]*>.+</h2>",
            "description": "Must have exactly one <h2> headline"
        },
        "memphis_opener": {
            "pattern": r"MEMPHIS,\s*Tenn\.\s*\(Youdle\)\s*[–-]",
            "description": "First paragraph must start with 'MEMPHIS, Tenn. (Youdle) –'"
        },
        "list_elements": {
            "pattern": r"<ul[^>]*>.*<li[^>]*>.*</li>.*</ul>",
            "description": "Must have <ul> with <li> elements",
            "flags": re.DOTALL
        },
        "youdle_link": {
            "pattern": r'<a[^>]+href=["\']https?://(?:www\.)?youdle\.io/?["\'][^>]*>',
            "description": "Must include link to Youdle.io"
        },
        "more_info_link": {
            "pattern": r'<a[^>]+href=["\'][^"\']+["\'][^>]*>More information</a>',
            "description": "Must include 'More information' link",
            "flags": re.IGNORECASE
        },
        "community_link": {
            "pattern": r'<a[^>]+href=["\']https?://(?:www\.)?youdle\.io/community["\'][^>]*>.*Community.*</a>',
            "description": "Must end with Youdle Community link",
            "flags": re.IGNORECASE | re.DOTALL
        }
    }
    
    # Word count target
    TARGET_WORD_COUNT = 250
    WORD_COUNT_TOLERANCE = 50  # ±50 words
    
    def __init__(self):
        """Initialize the reflection agent."""
        pass
    
    def validate_structure(self, html_content: str) -> Dict[str, Any]:
        """
        Validate the HTML structure of a blog post.
        
        Args:
            html_content: Generated HTML blog post
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "is_valid": True,
            "passed": [],
            "failed": [],
            "warnings": []
        }
        
        for element_name, config in self.REQUIRED_ELEMENTS.items():
            pattern = config["pattern"]
            flags = config.get("flags", 0)
            description = config["description"]
            
            if re.search(pattern, html_content, flags):
                results["passed"].append({
                    "element": element_name,
                    "description": description
                })
            else:
                results["failed"].append({
                    "element": element_name,
                    "description": description,
                    "suggestion": f"Add: {description}"
                })
                results["is_valid"] = False
        
        return results
    
    def validate_word_count(self, html_content: str) -> Dict[str, Any]:
        """
        Validate the word count of the blog post.
        
        Args:
            html_content: Generated HTML blog post
            
        Returns:
            Dictionary with word count validation
        """
        # Strip HTML tags to get text content
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = re.sub(r'\s+', ' ', text).strip()
        word_count = len(text.split())
        
        min_words = self.TARGET_WORD_COUNT - self.WORD_COUNT_TOLERANCE
        max_words = self.TARGET_WORD_COUNT + self.WORD_COUNT_TOLERANCE
        
        is_valid = min_words <= word_count <= max_words
        
        result = {
            "word_count": word_count,
            "target": self.TARGET_WORD_COUNT,
            "min_acceptable": min_words,
            "max_acceptable": max_words,
            "is_valid": is_valid
        }
        
        if not is_valid:
            if word_count < min_words:
                result["suggestion"] = f"Add more content (current: {word_count}, target: ~{self.TARGET_WORD_COUNT})"
            else:
                result["suggestion"] = f"Reduce content (current: {word_count}, target: ~{self.TARGET_WORD_COUNT})"
        
        return result
    
    def check_common_mistakes(
        self,
        html_content: str,
        bad_examples: List[str] = None
    ) -> List[str]:
        """
        Check for common mistakes based on bad examples.
        
        Args:
            html_content: Generated HTML blog post
            bad_examples: List of bad example HTML posts
            
        Returns:
            List of detected issues
        """
        issues = []
        
        # Check for markdown artifacts
        if "```" in html_content:
            issues.append("Contains markdown code block markers")
        if "**" in html_content:
            issues.append("Contains markdown bold markers")
        
        # Check for unwanted HTML elements
        if "<html" in html_content.lower():
            issues.append("Contains <html> tag (should only have <div>)")
        if "<body" in html_content.lower():
            issues.append("Contains <body> tag (should only have <div>)")
        if "<head" in html_content.lower():
            issues.append("Contains <head> tag (should only have <div>)")
        
        # Check for placeholder issues
        if "{original_link}" in html_content:
            issues.append("Contains unreplaced {original_link} placeholder")
        if "{{" in html_content and "}}" in html_content:
            # Check for unintended template variables (except IMAGE_HERE)
            if re.search(r'\{\{(?!IMAGE_HERE)[^}]+\}\}', html_content):
                issues.append("Contains unreplaced template variables")
        
        # Check for empty required elements
        if re.search(r'<h2[^>]*>\s*</h2>', html_content):
            issues.append("Empty <h2> headline")
        if re.search(r'<li[^>]*>\s*</li>', html_content):
            issues.append("Empty <li> elements")
        
        # Check image tag format
        img_match = re.search(r'<img[^>]+>', html_content)
        if img_match:
            img_tag = img_match.group()
            if 'alt=' not in img_tag:
                issues.append("Image tag missing alt attribute")
        
        return issues
    
    def reflect(
        self,
        html_content: str,
        bad_examples: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform full reflection on a generated blog post.
        
        Args:
            html_content: Generated HTML blog post
            bad_examples: List of bad example HTML posts to avoid
            
        Returns:
            Complete reflection result
        """
        # Validate structure
        structure_result = self.validate_structure(html_content)
        
        # Validate word count
        word_count_result = self.validate_word_count(html_content)
        
        # Check common mistakes
        common_mistakes = self.check_common_mistakes(html_content, bad_examples)
        
        # Compile issues and suggestions
        issues = []
        suggestions = []
        
        for failed in structure_result["failed"]:
            issues.append(failed["description"])
            suggestions.append(failed["suggestion"])
        
        if not word_count_result["is_valid"]:
            issues.append(f"Word count issue: {word_count_result['word_count']} words")
            suggestions.append(word_count_result.get("suggestion", ""))
        
        issues.extend(common_mistakes)
        
        # Determine overall validity
        is_valid = (
            structure_result["is_valid"] and 
            word_count_result["is_valid"] and 
            len(common_mistakes) == 0
        )
        
        return {
            "is_valid": is_valid,
            "structure": structure_result,
            "word_count": word_count_result,
            "common_mistakes": common_mistakes,
            "issues": issues,
            "suggestions": suggestions,
            "summary": self._create_summary(is_valid, issues)
        }
    
    def _create_summary(self, is_valid: bool, issues: List[str]) -> str:
        """Create a human-readable summary of the reflection."""
        if is_valid:
            return "Blog post meets all requirements."
        else:
            issue_count = len(issues)
            return f"Blog post has {issue_count} issue(s): {'; '.join(issues[:3])}"
    
    def should_regenerate(self, reflection_result: Dict[str, Any]) -> bool:
        """
        Determine if the blog post should be regenerated.
        
        Args:
            reflection_result: Result from reflect()
            
        Returns:
            True if regeneration is recommended
        """
        # Regenerate if structure is invalid
        if not reflection_result["structure"]["is_valid"]:
            return True
        
        # Regenerate if there are serious common mistakes
        serious_mistakes = [
            m for m in reflection_result["common_mistakes"]
            if "placeholder" in m.lower() or "empty" in m.lower()
        ]
        if serious_mistakes:
            return True
        
        return False
    
    def get_regeneration_hints(
        self,
        reflection_result: Dict[str, Any]
    ) -> str:
        """
        Get hints for regeneration based on reflection.
        
        Args:
            reflection_result: Result from reflect()
            
        Returns:
            String of hints to include in regeneration prompt
        """
        hints = []
        
        for issue in reflection_result["issues"]:
            hints.append(f"- Fix: {issue}")
        
        for suggestion in reflection_result["suggestions"]:
            if suggestion:
                hints.append(f"- {suggestion}")
        
        return "\n".join(hints) if hints else "No specific hints."


# For testing
if __name__ == "__main__":
    agent = ReflectionAgent()
    
    # Test with a sample blog post
    test_html = """
    <div>
        <img src="{IMAGE_HERE}" alt="article image"/>
        <h2>Test Headline</h2>
        <p>MEMPHIS, Tenn. (Youdle) – This is a test paragraph with some content about grocery shopping and products.</p>
        <p>More content here to pad out the word count for testing purposes.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        <p>Check out <a href="https://www.youdle.io/">Youdle</a> for more.</p>
        <p><a href="https://example.com/article">More information</a></p>
        <p>Share your thoughts in the <a href="https://www.youdle.io/community">Youdle Community!</a></p>
    </div>
    """
    
    print("Testing reflection agent...")
    result = agent.reflect(test_html)
    
    print(f"\nIs Valid: {result['is_valid']}")
    print(f"Summary: {result['summary']}")
    print(f"\nWord Count: {result['word_count']['word_count']}")
    print(f"Issues: {result['issues']}")
    print(f"Should Regenerate: {agent.should_regenerate(result)}")



