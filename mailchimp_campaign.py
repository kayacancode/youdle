# mailchimp_campaign.py
# Mailchimp integration for creating newsletter campaigns

import os
import json
from datetime import datetime
from html import escape, unescape
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

EMAIL_SUBJECT = "Youdle grocery news to save you time and money"
NEWSLETTER_DESCRIPTION = "Your weekly guide to grocery savings, food safety alerts, and what's trending in stores."

NEWSLETTER_TEMPLATE = """<!doctype html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <!--[if gte mso 15]>
  <xml>
    <o:OfficeDocumentSettings>
      <o:AllowPNG/>
      <o:PixelsPerInch>96</o:PixelsPerInch>
    </o:OfficeDocumentSettings>
  </xml>
  <![endif]-->
  <meta charset="UTF-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Grocery Retail Newsletter</title>
  <style type="text/css">
    body, #bodyTable, #bodyCell {{ margin:0; padding:0; width:100%; height:100%; }}
    table {{ border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; }}
    img, a img {{ border:0; outline:none; text-decoration:none; -ms-interpolation-mode:bicubic; }}
    p {{ margin:10px 0; padding:0; }}
    h1,h2,h3,h4,h5,h6 {{ margin:0; padding:0; display:block; }}

    .ExternalClass, .ExternalClass p, .ExternalClass td, .ExternalClass div, .ExternalClass span, .ExternalClass font {{ line-height:100%; width:100%; }}
    .ReadMsgBody {{ width:100%; }}
    a[x-apple-data-detectors] {{ color:inherit !important; text-decoration:none !important; font-size:inherit !important; font-family:inherit !important; font-weight:inherit !important; line-height:inherit !important; }}
    a[href^="tel"], a[href^="sms"] {{ text-decoration:none; color:inherit; cursor:default; }}

    #templateHeader, #templateBody, #templateFooter {{ background-size:cover; background-repeat:no-repeat; background-position:center; border-top:0; border-bottom:0; }}
    #templateHeader {{ background-color:#ffffff; padding:54px 0; }}
    #templateBody   {{ background-color:#ffffff; padding:27px 0 63px; }}
    #templateFooter {{ background-color:#333333; padding:45px 0 63px; }}

    .templateContainer {{ max-width:600px !important; }}
    .headerContainer .mcnTextContent,
    .bodyContainer .mcnTextContent,
    .footerContainer .mcnTextContent {{ font-family:Helvetica, Arial, sans-serif; line-height:150%; }}

    .headerContainer .mcnTextContent {{ color:#757575; font-size:16px; text-align:left; }}
    .headerContainer .mcnTextContent a {{ color:#007C89; text-decoration:underline; }}
    .bodyContainer .mcnTextContent {{ color:#757575; font-size:16px; text-align:left; }}
    .bodyContainer .mcnTextContent a {{ color:#007C89; text-decoration:underline; }}
    .footerContainer .mcnTextContent {{ color:#FFFFFF; font-size:12px; text-align:center; }}
    .footerContainer .mcnTextContent a {{ color:#FFFFFF; text-decoration:underline; }}

    h1 {{ color:#222222; font-family:Helvetica; font-size:40px; font-weight:bold; line-height:150%; text-align:left; }}
    h2 {{ color:#222222; font-family:Helvetica; font-size:28px; font-weight:bold; line-height:150%; text-align:left; }}
    h3 {{ color:#444444; font-family:Helvetica; font-size:22px; font-weight:bold; line-height:150%; text-align:left; }}
    h4 {{ color:#949494; font-family:Georgia; font-size:20px; font-style:italic; line-height:125%; text-align:left; }}

    @media only screen and (max-width:480px){{
      body, table, td, p, a, li, blockquote {{ -webkit-text-size-adjust:none !important; }}
      body {{ width:100% !important; min-width:100% !important; }}
      .mcnImage {{ width:100% !important; }}
      .mcnRetinaImage {{ max-width:100% !important; }}
      .templateContainer {{ width:100% !important; }}
      h1 {{ font-size:30px !important; line-height:125% !important; }}
      h2 {{ font-size:26px !important; line-height:125% !important; }}
      h3 {{ font-size:20px !important; line-height:150% !important; }}
      h4 {{ font-size:18px !important; line-height:150% !important; }}
      .mcnTextContent {{ padding:0 18px !important; font-size:16px !important; line-height:150% !important; }}
    }}
  </style>
</head>
<body>
  <center>
    <table id="bodyTable" width="100%" height="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td id="bodyCell" align="center" valign="top">

          <!-- HEADER -->
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td id="templateHeader" align="center" valign="top">
                <table class="templateContainer" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td class="headerContainer" align="center">
                      <img src="https://mcusercontent.com/a8e33153b11c8b750221ce4aa/images/5f2d9977-bf45-cdb6-23dd-0c18573407e4.png" width="113" style="display:block; max-width:100%;" alt="Youdle Logo">
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

          <!-- BODY -->
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td id="templateBody" align="center" valign="top">
                <table class="templateContainer" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td class="bodyContainer">

                      <!-- Intro -->
                      <table width="100%" cellpadding="0" cellspacing="0" class="mcnCaptionBlock">
                        <tr>
                          <td class="mcnCaptionBlockInner" style="padding:9px;">
                            <table align="left" width="100%" class="mcnCaptionBottomContent" cellpadding="0" cellspacing="0">
                              <tr>
                                <td class="mcnTextContent" style="padding:0 18px;">
                                  <h2>Welcome to Our Grocery Newsletter</h2>
                                  <p>Grocery retail trends, shopper insights, and inventory tips—built for shoppers, independent store owners and emergency managers.</p>

                                  <!-- Article List -->
                                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                                    <tr><td style="padding:18px;">
                                      <ul style="padding-left:18px; margin:0;">
                                        {article_links}
                                      </ul>
                                    </td></tr>
                                  </table>

                                  {recall_section}
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                      </table>

                      <!-- Sponsors -->
                      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse; margin:0; padding:0;">
                        <tr>
                          <td align="center" valign="top" style="margin:0; padding:0;">
                            <p style="margin:18px 0 12px; font-weight:bold; font-size:16px;">SPONSORS</p>
                            <a href="http://youdle.io/" target="_blank" style="display:block; margin:0; padding:0;">
                              <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjR5B9lMXv8puWdDrQFWmN2mqQyBefSvy2CAsZV4OIigpfXxKNjCK_Nplbbfg4FWx4pUYv7S2gXFarP8lWaSigTg2nRozbZ6u_eMhyphenhyphengPW32tCB0ApUwyWu1L_Xc18KppPVbY4_OKd-99HCFz-Zc82NwFQnJxA7BbAFsHdF6GeHsZYqixyUllrWVpcpkLT58/s700/(700%20x%20150%20px)%20Green%20Groceries%20Home%20Delivery%20App%20Instagram%20Post%20(1).png" alt="Youdle Sponsor" border="0" style="max-width:100%;">
                            </a>
                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">
                              <tr>
                                <td align="center">
                                  <a href="http://youdle.io/" target="_blank" style="background-color:#f93822; color:#ffffff; text-decoration:none; font-weight:bold; font-family:Helvetica, Arial, sans-serif; padding:12px 24px; border-radius:4px; display:inline-block;">
                                    Let's Get Started
                                  </a>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                      </table>

                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

          <!-- FOOTER -->
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td id="templateFooter" align="center" valign="top">
                <table class="templateContainer" width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td class="footerContainer" align="center" style="padding:18px;">
                      <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                          <td class="mcnTextContent" style="color:#FFFFFF; text-align:center;">
                            <p style="color:#FFFFFF;"><em>Copyright © {year} Youdle, All rights reserved.</em></p>
                            <p style="color:#FFFFFF;"><strong>Contact us:</strong></p>
                            <p><a href="mailto:info@getyoudle.com" style="color:#FFFFFF;">info@getyoudle.com</a></p>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

        </td>
      </tr>
    </table>
  </center>
</body>
</html>"""

RECALL_SECTION_TEMPLATE = """
                                  <!-- Weekly Recall Roundup -->
                                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                                    <tr><td style="padding:18px;">
                                      <h2 style="margin:0 0 12px 0; font-size:20px; color:#1B1B1B; font-weight:700;">Weekly Recall Roundup</h2>
                                      <ul style="padding-left:18px; margin:0;">
                                        {recall_links}
                                      </ul>
                                    </td></tr>
                                  </table>"""


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
        category: str = "",
        summary: str = ""
    ) -> str:
        """Format an article as an HTML list item with optional summary."""
        title_escaped = escape(title)
        url_escaped = escape(url)

        # Truncate and escape summary (max 240 chars)
        summary_raw = (summary or "")[:240]
        summary_escaped = escape(unescape(summary_raw))
        summary_html = f'<div style="color:#555; font-weight:400; margin-top:4px;">{summary_escaped}</div>' if summary_escaped else ""

        return (
            '<li style="margin:0 0 12px 0; line-height:1.5;">'
            f'<a href="{url_escaped}" target="_blank" style="color:#007C89; text-decoration:none; font-weight:600;">{title_escaped}</a>'
            f'{summary_html}'
            '</li>'
        )
    
    def _format_recall_link(
        self,
        title: str,
        url: str,
        summary: str = ""
    ) -> str:
        """Format a recall article as an HTML list item with optional summary."""
        title_escaped = escape(title)
        url_escaped = escape(url)

        # Truncate and escape summary (max 240 chars)
        summary_raw = (summary or "")[:240]
        summary_escaped = escape(unescape(summary_raw))
        summary_html = f'<div style="color:#555; font-weight:400; margin-top:4px;">{summary_escaped}</div>' if summary_escaped else ""

        return (
            '<li style="margin:0 0 12px 0; line-height:1.5;">'
            f'<a href="{url_escaped}" target="_blank" style="color:#B8860B; text-decoration:none; font-weight:600;">⚠️ {title_escaped}</a>'
            f'{summary_html}'
            '</li>'
        )
    
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
        # Format article links with summaries
        article_links = "\n            ".join([
            self._format_article_link(
                title=a.get("title", "Article"),
                url=a.get("url", a.get("link", "#")),
                category=a.get("category", ""),
                summary=a.get("summary", a.get("description", ""))
            )
            for a in articles[:6]
        ])

        # Format recall section with summaries
        if recall_articles:
            recall_links = "\n            ".join([
                self._format_recall_link(
                    title=a.get("title", "Recall Alert"),
                    url=a.get("url", a.get("link", "#")),
                    summary=a.get("summary", a.get("description", ""))
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
        reply_to: str = "info@getyoudle.com"
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
                        "generated_at": metadata.get("generated_at", ""),
                        "summary": metadata.get("summary", metadata.get("description", ""))
                    })
                elif not approved_only:
                    # Include unpublished posts
                    posts.append({
                        "title": metadata.get("title", "Article"),
                        "url": metadata.get("original_link", "#"),
                        "category": metadata.get("category", "SHOPPERS"),
                        "original_link": metadata.get("original_link", ""),
                        "generated_at": metadata.get("generated_at", ""),
                        "summary": metadata.get("summary", metadata.get("description", ""))
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



