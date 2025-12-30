# mailchimp_campaign.py
# Mailchimp integration for creating newsletter campaigns

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from mailchimp3 import MailChimp
except ImportError:
    MailChimp = None
    print("Warning: mailchimp3 not installed. Run: pip install mailchimp3")


# ============================================================================
# CONFIGURATION
# ============================================================================

NEWSLETTER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Youdle Weekly Newsletter</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid #4CAF50;
        }}
        .header h1 {{
            color: #4CAF50;
            margin: 0;
        }}
        .section {{
            padding: 20px 0;
            border-bottom: 1px solid #eee;
        }}
        .section h2 {{
            color: #333;
            margin-bottom: 15px;
        }}
        .article-list {{
            list-style: none;
            padding: 0;
        }}
        .article-list li {{
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .article-list li:last-child {{
            border-bottom: none;
        }}
        .article-link {{
            color: #2196F3;
            text-decoration: none;
            font-weight: 500;
        }}
        .article-link:hover {{
            text-decoration: underline;
        }}
        .recall-section {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .recall-section h2 {{
            color: #856404;
        }}
        .footer {{
            text-align: center;
            padding: 20px 0;
            color: #666;
            font-size: 14px;
        }}
        .footer a {{
            color: #4CAF50;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛒 Youdle Weekly</h1>
        <p>Your grocery insights, delivered fresh</p>
    </div>
    
    <div class="section">
        <h2>📰 This Week's Top Stories</h2>
        <ul class="article-list">
            {article_links}
        </ul>
    </div>
    
    {recall_section}
    
    <div class="footer">
        <p>
            <a href="https://www.youdle.io/">Visit Youdle</a> | 
            <a href="https://www.youdle.io/community">Join the Community</a>
        </p>
        <p>© {year} Youdle. All rights reserved.</p>
        <p><small>You're receiving this email because you subscribed to Youdle updates.</small></p>
    </div>
</body>
</html>
"""

RECALL_SECTION_TEMPLATE = """
    <div class="recall-section">
        <h2>⚠️ Recall Alert</h2>
        <p>Stay informed about the latest food safety recalls:</p>
        <ul class="article-list">
            {recall_links}
        </ul>
    </div>
"""


class MailchimpCampaign:
    """
    Mailchimp integration for creating newsletter campaigns.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        server_prefix: Optional[str] = None,
        list_id: Optional[str] = None
    ):
        """
        Initialize Mailchimp client.
        
        Args:
            api_key: Mailchimp API key (defaults to MAILCHIMP_API_KEY env var)
            server_prefix: Server prefix (defaults to MAILCHIMP_SERVER_PREFIX env var)
            list_id: Default list ID (defaults to MAILCHIMP_LIST_ID env var)
        """
        self.api_key = api_key or os.getenv("MAILCHIMP_API_KEY")
        self.server_prefix = server_prefix or os.getenv("MAILCHIMP_SERVER_PREFIX", "us1")
        self.list_id = list_id or os.getenv("MAILCHIMP_LIST_ID")
        
        self.client = None
        if self.api_key and MailChimp:
            try:
                self.client = MailChimp(
                    mc_api=self.api_key,
                    mc_user='apikey'
                )
            except Exception as e:
                print(f"Warning: Could not initialize Mailchimp client: {e}")
    
    def _format_article_link(
        self,
        title: str,
        url: str,
        category: str = ""
    ) -> str:
        """Format an article as an HTML list item."""
        return f'<li><a href="{url}" class="article-link">{title}</a></li>'
    
    def _format_recall_link(
        self,
        title: str,
        url: str
    ) -> str:
        """Format a recall article as an HTML list item."""
        return f'<li><a href="{url}" class="article-link">⚠️ {title}</a></li>'
    
    def create_newsletter_html(
        self,
        articles: List[Dict[str, Any]],
        recall_articles: List[Dict[str, Any]] = None
    ) -> str:
        """
        Create newsletter HTML from articles.
        
        Args:
            articles: List of article data (title, url)
            recall_articles: List of recall article data
            
        Returns:
            HTML newsletter content
        """
        # Format article links
        article_links = "\n            ".join([
            self._format_article_link(
                title=a.get("title", "Article"),
                url=a.get("url", a.get("link", "#")),
                category=a.get("category", "")
            )
            for a in articles[:6]
        ])
        
        # Format recall section
        if recall_articles:
            recall_links = "\n            ".join([
                self._format_recall_link(
                    title=a.get("title", "Recall Alert"),
                    url=a.get("url", a.get("link", "#"))
                )
                for a in recall_articles[:3]
            ])
            recall_section = RECALL_SECTION_TEMPLATE.format(recall_links=recall_links)
        else:
            recall_section = ""
        
        # Create newsletter
        return NEWSLETTER_TEMPLATE.format(
            article_links=article_links,
            recall_section=recall_section,
            year=datetime.now().year
        )
    
    def create_campaign(
        self,
        subject: str,
        html_content: str,
        list_id: Optional[str] = None,
        from_name: str = "Youdle",
        reply_to: str = "newsletter@youdle.io"
    ) -> Dict[str, Any]:
        """
        Create a Mailchimp campaign.
        
        Args:
            subject: Email subject line
            html_content: HTML content for the email
            list_id: Mailchimp list ID (uses default if not provided)
            from_name: Sender name
            reply_to: Reply-to email address
            
        Returns:
            Campaign data or error
        """
        list_id = list_id or self.list_id
        
        if not self.client:
            return {
                "success": False,
                "error": "Mailchimp client not initialized"
            }
        
        if not list_id:
            return {
                "success": False,
                "error": "No list ID provided"
            }
        
        try:
            # Create campaign
            campaign = self.client.campaigns.create({
                "type": "regular",
                "recipients": {
                    "list_id": list_id
                },
                "settings": {
                    "subject_line": subject,
                    "from_name": from_name,
                    "reply_to": reply_to,
                    "title": f"Youdle Newsletter - {datetime.now().strftime('%Y-%m-%d')}"
                }
            })
            
            campaign_id = campaign["id"]
            
            # Set campaign content
            self.client.campaigns.content.update(
                campaign_id,
                {"html": html_content}
            )
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "web_id": campaign.get("web_id"),
                "status": "draft"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_campaign(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Send a campaign immediately.
        
        Args:
            campaign_id: Mailchimp campaign ID
            
        Returns:
            Result dictionary
        """
        if not self.client:
            return {
                "success": False,
                "error": "Mailchimp client not initialized"
            }
        
        try:
            self.client.campaigns.actions.send(campaign_id)
            return {
                "success": True,
                "campaign_id": campaign_id,
                "status": "sent"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def schedule_campaign(
        self,
        campaign_id: str,
        schedule_time: datetime
    ) -> Dict[str, Any]:
        """
        Schedule a campaign for later.
        
        Args:
            campaign_id: Mailchimp campaign ID
            schedule_time: When to send the campaign (UTC)
            
        Returns:
            Result dictionary
        """
        if not self.client:
            return {
                "success": False,
                "error": "Mailchimp client not initialized"
            }
        
        try:
            self.client.campaigns.actions.schedule(
                campaign_id,
                {"schedule_time": schedule_time.isoformat()}
            )
            return {
                "success": True,
                "campaign_id": campaign_id,
                "scheduled_time": schedule_time.isoformat(),
                "status": "scheduled"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_campaign_status(
        self,
        campaign_id: str
    ) -> Dict[str, Any]:
        """
        Get the status of a campaign.
        
        Args:
            campaign_id: Mailchimp campaign ID
            
        Returns:
            Campaign status
        """
        if not self.client:
            return {
                "success": False,
                "error": "Mailchimp client not initialized"
            }
        
        try:
            campaign = self.client.campaigns.get(campaign_id)
            return {
                "success": True,
                "campaign_id": campaign_id,
                "status": campaign.get("status"),
                "emails_sent": campaign.get("emails_sent", 0),
                "send_time": campaign.get("send_time")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def load_published_posts(
    directory: str = "blog_posts",
    approved_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Load published blog posts from directory.
    
    Args:
        directory: Path to blog posts directory
        approved_only: Only load approved posts
        
    Returns:
        List of post data
    """
    posts = []
    
    if not os.path.exists(directory):
        return posts
    
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # Check if post has a blogger URL (published)
                blogger_url = metadata.get("blogger_url", metadata.get("published_url"))
                
                if blogger_url:
                    posts.append({
                        "title": metadata.get("title", "Article"),
                        "url": blogger_url,
                        "category": metadata.get("category", "SHOPPERS"),
                        "original_link": metadata.get("original_link", ""),
                        "generated_at": metadata.get("generated_at", "")
                    })
                elif not approved_only:
                    # Include unpublished posts
                    posts.append({
                        "title": metadata.get("title", "Article"),
                        "url": metadata.get("original_link", "#"),
                        "category": metadata.get("category", "SHOPPERS"),
                        "original_link": metadata.get("original_link", ""),
                        "generated_at": metadata.get("generated_at", "")
                    })
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
    
    return posts


def create_newsletter_campaign(
    directory: str = "blog_posts",
    subject: Optional[str] = None,
    send_immediately: bool = False
) -> Dict[str, Any]:
    """
    Create a newsletter campaign from published blog posts.
    
    Args:
        directory: Path to blog posts directory
        subject: Email subject (auto-generated if not provided)
        send_immediately: Send the campaign immediately after creation
        
    Returns:
        Campaign result
    """
    # Load published posts
    posts = load_published_posts(directory)
    
    if not posts:
        return {
            "success": False,
            "error": "No published posts found"
        }
    
    # Separate shoppers and recall posts
    shoppers_posts = [p for p in posts if p.get("category", "").upper() != "RECALL"]
    recall_posts = [p for p in posts if p.get("category", "").upper() == "RECALL"]
    
    if not shoppers_posts and not recall_posts:
        return {
            "success": False,
            "error": "No posts to include in newsletter"
        }
    
    # Create campaign
    mailchimp = MailchimpCampaign()
    
    # Generate HTML
    html_content = mailchimp.create_newsletter_html(
        articles=shoppers_posts,
        recall_articles=recall_posts
    )
    
    # Create subject if not provided
    if not subject:
        date_str = datetime.now().strftime("%B %d, %Y")
        subject = f"🛒 Youdle Weekly: Your Grocery Insights for {date_str}"
    
    # Create campaign
    result = mailchimp.create_campaign(
        subject=subject,
        html_content=html_content
    )
    
    if result.get("success") and send_immediately:
        send_result = mailchimp.send_campaign(result["campaign_id"])
        result["send_result"] = send_result
    
    return result


# For testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create Mailchimp newsletter campaign")
    parser.add_argument("--directory", "-d", default="blog_posts", help="Blog posts directory")
    parser.add_argument("--subject", "-s", help="Email subject")
    parser.add_argument("--send", action="store_true", help="Send immediately")
    parser.add_argument("--preview", action="store_true", help="Preview HTML only")
    
    args = parser.parse_args()
    
    if args.preview:
        # Just show HTML preview
        posts = load_published_posts(args.directory, approved_only=False)
        
        if posts:
            shoppers = [p for p in posts if p.get("category", "").upper() != "RECALL"]
            recalls = [p for p in posts if p.get("category", "").upper() == "RECALL"]
            
            mailchimp = MailchimpCampaign()
            html = mailchimp.create_newsletter_html(shoppers, recalls)
            
            print("=" * 60)
            print("NEWSLETTER PREVIEW")
            print("=" * 60)
            print(html[:2000])
            print("...")
        else:
            print("No posts found for preview")
    else:
        result = create_newsletter_campaign(
            directory=args.directory,
            subject=args.subject,
            send_immediately=args.send
        )
        
        print(json.dumps(result, indent=2))



