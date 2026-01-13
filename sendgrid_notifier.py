# sendgrid_notifier.py
# SendGrid integration for transactional notification emails

import os
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
except ImportError:
    SendGridAPIClient = None
    print("Warning: sendgrid not installed. Run: pip install sendgrid")


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SENDER_EMAIL = "info@getyoudle.com"
DEFAULT_SENDER_NAME = "Youdle"
DASHBOARD_URL = "https://youdle.vercel.app"  # Update with actual dashboard URL


# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

BASE_EMAIL_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
    .header {{ background-color: #1a1a2e; padding: 30px; text-align: center; }}
    .header img {{ max-width: 120px; }}
    .header h1 {{ color: #ffffff; margin: 15px 0 0 0; font-size: 24px; }}
    .content {{ padding: 30px; }}
    .status-box {{ background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }}
    .status-item {{ display: flex; justify-content: space-between; margin: 10px 0; }}
    .status-label {{ color: #666; }}
    .status-value {{ font-weight: bold; color: #333; }}
    .status-good {{ color: #28a745; }}
    .status-warning {{ color: #ffc107; }}
    .status-danger {{ color: #dc3545; }}
    .cta-button {{ display: inline-block; background-color: #f93822; color: #ffffff; text-decoration: none; padding: 12px 30px; border-radius: 5px; font-weight: bold; margin: 20px 0; }}
    .cta-button:hover {{ background-color: #e02d1a; }}
    .footer {{ background-color: #333; color: #fff; padding: 20px; text-align: center; font-size: 12px; }}
    .footer a {{ color: #fff; }}
    .urgency-high {{ border-left: 4px solid #dc3545; padding-left: 15px; }}
    .urgency-medium {{ border-left: 4px solid #ffc107; padding-left: 15px; }}
    .urgency-low {{ border-left: 4px solid #28a745; padding-left: 15px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Youdle</h1>
    </div>
    <div class="content">
      {content}
    </div>
    <div class="footer">
      <p>&copy; {year} Youdle. All rights reserved.</p>
      <p><a href="mailto:info@getyoudle.com">info@getyoudle.com</a></p>
    </div>
  </div>
</body>
</html>"""


class SendGridNotifier:
    """
    SendGrid integration for sending transactional notification emails.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        admin_email: Optional[str] = None,
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None
    ):
        """
        Initialize SendGrid client.

        Args:
            api_key: SendGrid API key (defaults to SENDGRID_API_KEY env var)
            admin_email: Admin email to receive notifications (defaults to ADMIN_NOTIFICATION_EMAIL env var)
            sender_email: Sender email address (defaults to DEFAULT_SENDER_EMAIL)
            sender_name: Sender display name (defaults to DEFAULT_SENDER_NAME)
        """
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.admin_email = admin_email or os.getenv("ADMIN_NOTIFICATION_EMAIL")
        self.sender_email = sender_email or os.getenv("SENDER_EMAIL", DEFAULT_SENDER_EMAIL)
        self.sender_name = sender_name or DEFAULT_SENDER_NAME

        self.client = None
        if self.api_key and SendGridAPIClient:
            try:
                self.client = SendGridAPIClient(self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize SendGrid client: {e}")

    def _build_html(self, subject: str, content: str) -> str:
        """Build full HTML email from content."""
        return BASE_EMAIL_TEMPLATE.format(
            subject=subject,
            content=content,
            year=datetime.now().year
        )

    def send_notification(
        self,
        subject: str,
        html_content: str,
        to_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification email.

        Args:
            subject: Email subject line
            html_content: HTML content for the email body
            to_email: Recipient email (uses admin_email if not provided)

        Returns:
            Result dictionary with success status
        """
        to_email = to_email or self.admin_email

        if not self.client:
            return {
                "success": False,
                "error": "SendGrid client not initialized. Check SENDGRID_API_KEY."
            }

        if not to_email:
            return {
                "success": False,
                "error": "No recipient email provided. Set ADMIN_NOTIFICATION_EMAIL."
            }

        try:
            message = Mail(
                from_email=Email(self.sender_email, self.sender_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.client.send(message)

            return {
                "success": True,
                "status_code": response.status_code,
                "to_email": to_email,
                "subject": subject
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def send_blogs_generated_notification(
        self,
        posts_generated: int,
        shoppers_count: int = 0,
        recall_count: int = 0
    ) -> Dict[str, Any]:
        """
        Send notification that blogs have been generated.

        Args:
            posts_generated: Total number of posts generated
            shoppers_count: Number of SHOPPERS posts
            recall_count: Number of RECALL posts
        """
        subject = "Youdle: This Week's Blogs Have Been Generated"

        content = f"""
        <h2>Blog Posts Generated Successfully</h2>
        <p>This week's blog posts have been generated and are ready for your review.</p>

        <div class="status-box">
            <div class="status-item">
                <span class="status-label">Total Posts Generated:</span>
                <span class="status-value">{posts_generated}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Shoppers Articles:</span>
                <span class="status-value">{shoppers_count}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Recall Articles:</span>
                <span class="status-value">{recall_count}</span>
            </div>
        </div>

        <p><strong>Action Required:</strong> Please review and publish these blog posts before Thursday 9 AM CST when the newsletter will be sent.</p>

        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}/posts" class="cta-button">Review Blog Posts</a>
        </p>

        <p><strong>Publishing Requirements:</strong></p>
        <ul>
            <li>At least 6 Shoppers articles must be published</li>
            <li>At least 1 Recall article must be published</li>
            <li>Total: 7 posts minimum</li>
        </ul>
        """

        html = self._build_html(subject, content)
        return self.send_notification(subject, html)

    def send_reminder_notification(
        self,
        reminder_type: str,
        published_count: int,
        required_count: int,
        shoppers_published: int = 0,
        recall_published: int = 0
    ) -> Dict[str, Any]:
        """
        Send a reminder notification with current publish status.

        Args:
            reminder_type: Type of reminder (tuesday_evening, wednesday_morning, wednesday_evening)
            published_count: Number of posts currently published
            required_count: Number of posts required (7)
            shoppers_published: Number of SHOPPERS posts published
            recall_published: Number of RECALL posts published
        """
        remaining = max(0, required_count - published_count)
        shoppers_needed = max(0, 6 - shoppers_published)
        recall_needed = max(0, 1 - recall_published)

        # Determine urgency based on reminder type
        urgency_map = {
            "tuesday_evening": ("medium", "Wednesday"),
            "wednesday_morning": ("medium", "tomorrow morning"),
            "wednesday_evening": ("high", "tomorrow at 9 AM CST")
        }
        urgency, deadline = urgency_map.get(reminder_type, ("medium", "soon"))

        # Subject line based on urgency
        if urgency == "high":
            subject = "URGENT: Blog Posts Need Publishing Before Newsletter"
        else:
            subject = "Reminder: Please Review and Publish This Week's Blogs"

        # Status color
        if published_count >= required_count:
            status_class = "status-good"
            status_text = "On Track"
        elif published_count >= required_count - 2:
            status_class = "status-warning"
            status_text = "Almost There"
        else:
            status_class = "status-danger"
            status_text = "Action Needed"

        content = f"""
        <div class="urgency-{urgency}">
            <h2>Blog Publishing Reminder</h2>
            <p>The weekly newsletter will be sent <strong>{deadline}</strong>. Please ensure all required blog posts are published.</p>
        </div>

        <div class="status-box">
            <h3>Current Status: <span class="{status_class}">{status_text}</span></h3>
            <div class="status-item">
                <span class="status-label">Posts Published:</span>
                <span class="status-value {status_class}">{published_count} / {required_count}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Shoppers Published:</span>
                <span class="status-value">{shoppers_published} / 6 required</span>
            </div>
            <div class="status-item">
                <span class="status-label">Recall Published:</span>
                <span class="status-value">{recall_published} / 1 required</span>
            </div>
        </div>

        {"<p><strong>Still needed:</strong></p><ul>" +
         (f"<li>{shoppers_needed} more Shoppers article(s)</li>" if shoppers_needed > 0 else "") +
         (f"<li>{recall_needed} more Recall article(s)</li>" if recall_needed > 0 else "") +
         "</ul>" if remaining > 0 else "<p style='color: #28a745;'><strong>All requirements met! You're all set for the newsletter.</strong></p>"}

        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}/posts" class="cta-button">Review & Publish Posts</a>
        </p>
        """

        html = self._build_html(subject, content)
        return self.send_notification(subject, html)

    def send_final_warning_notification(
        self,
        published_count: int,
        required_count: int,
        shoppers_published: int = 0,
        recall_published: int = 0
    ) -> Dict[str, Any]:
        """
        Send final warning before newsletter is sent.

        Args:
            published_count: Number of posts currently published
            required_count: Number of posts required
            shoppers_published: Number of SHOPPERS posts published
            recall_published: Number of RECALL posts published
        """
        subject = "FINAL NOTICE: Newsletter Will Be Sent Tomorrow Morning"

        meets_requirement = (shoppers_published >= 6 and recall_published >= 1)

        if meets_requirement:
            status_message = """
            <p style="color: #28a745; font-weight: bold;">
                All publishing requirements are met! The newsletter will be created and sent automatically tomorrow at 9 AM CST.
            </p>
            """
        else:
            shoppers_needed = max(0, 6 - shoppers_published)
            recall_needed = max(0, 1 - recall_published)
            status_message = f"""
            <p style="color: #dc3545; font-weight: bold;">
                WARNING: Publishing requirements are NOT met. The newsletter will be CANCELLED if not resolved.
            </p>
            <p><strong>Still needed:</strong></p>
            <ul>
                {"<li>" + str(shoppers_needed) + " more Shoppers article(s)</li>" if shoppers_needed > 0 else ""}
                {"<li>" + str(recall_needed) + " more Recall article(s)</li>" if recall_needed > 0 else ""}
            </ul>
            """

        content = f"""
        <div class="urgency-high">
            <h2>Final Newsletter Notice</h2>
            <p>The weekly newsletter will be created and sent <strong>tomorrow at 9 AM CST</strong>.</p>
        </div>

        <div class="status-box">
            <div class="status-item">
                <span class="status-label">Posts Published:</span>
                <span class="status-value">{published_count} / {required_count}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Shoppers Published:</span>
                <span class="status-value">{shoppers_published} / 6 required</span>
            </div>
            <div class="status-item">
                <span class="status-label">Recall Published:</span>
                <span class="status-value">{recall_published} / 1 required</span>
            </div>
        </div>

        {status_message}

        <p>Please review and make sure all your blog posts are published before the deadline.</p>

        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}/posts" class="cta-button">Review Posts Now</a>
        </p>
        """

        html = self._build_html(subject, content)
        return self.send_notification(subject, html)

    def send_newsletter_cancelled_notification(
        self,
        published_count: int,
        required_count: int,
        shoppers_published: int = 0,
        recall_published: int = 0
    ) -> Dict[str, Any]:
        """
        Send notification that newsletter was cancelled due to insufficient published posts.

        Args:
            published_count: Number of posts that were published
            required_count: Number of posts that were required
            shoppers_published: Number of SHOPPERS posts published
            recall_published: Number of RECALL posts published
        """
        subject = "Newsletter Cancelled: Blogs Were Not Published"

        shoppers_needed = max(0, 6 - shoppers_published)
        recall_needed = max(0, 1 - recall_published)

        content = f"""
        <div class="urgency-high">
            <h2>Newsletter Automation Failed</h2>
            <p>The automatic newsletter was <strong>cancelled</strong> because the required blog posts were not published in time.</p>
        </div>

        <div class="status-box">
            <h3 style="color: #dc3545;">Publishing Status at Deadline</h3>
            <div class="status-item">
                <span class="status-label">Posts Published:</span>
                <span class="status-value status-danger">{published_count} / {required_count} required</span>
            </div>
            <div class="status-item">
                <span class="status-label">Shoppers Published:</span>
                <span class="status-value">{shoppers_published} / 6 required</span>
            </div>
            <div class="status-item">
                <span class="status-label">Recall Published:</span>
                <span class="status-value">{recall_published} / 1 required</span>
            </div>
        </div>

        <p><strong>What was missing:</strong></p>
        <ul>
            {"<li>" + str(shoppers_needed) + " Shoppers article(s)</li>" if shoppers_needed > 0 else ""}
            {"<li>" + str(recall_needed) + " Recall article(s)</li>" if recall_needed > 0 else ""}
        </ul>

        <h3>Next Steps</h3>
        <ol>
            <li>Go to the dashboard and publish the remaining blog posts</li>
            <li>Create a new newsletter manually from the published posts</li>
            <li>Review and send the newsletter from the dashboard</li>
        </ol>

        <p style="text-align: center;">
            <a href="{DASHBOARD_URL}/posts" class="cta-button">Publish Blog Posts</a>
        </p>

        <p style="text-align: center; margin-top: 10px;">
            <a href="{DASHBOARD_URL}/newsletters" class="cta-button" style="background-color: #333;">Create Newsletter Manually</a>
        </p>
        """

        html = self._build_html(subject, content)
        return self.send_notification(subject, html)


# For testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send notification emails via SendGrid")
    parser.add_argument("--type", "-t", required=True,
                        choices=["generated", "reminder", "warning", "cancelled"],
                        help="Type of notification to send")
    parser.add_argument("--reminder-type", "-r",
                        choices=["tuesday_evening", "wednesday_morning", "wednesday_evening"],
                        help="Type of reminder (for reminder notifications)")
    parser.add_argument("--published", "-p", type=int, default=0,
                        help="Number of published posts")
    parser.add_argument("--shoppers", "-s", type=int, default=0,
                        help="Number of published shoppers posts")
    parser.add_argument("--recall", type=int, default=0,
                        help="Number of published recall posts")
    parser.add_argument("--test", action="store_true",
                        help="Test mode - print email instead of sending")

    args = parser.parse_args()

    notifier = SendGridNotifier()

    if args.type == "generated":
        result = notifier.send_blogs_generated_notification(
            posts_generated=args.published or 7,
            shoppers_count=args.shoppers or 6,
            recall_count=args.recall or 1
        )
    elif args.type == "reminder":
        result = notifier.send_reminder_notification(
            reminder_type=args.reminder_type or "tuesday_evening",
            published_count=args.published,
            required_count=7,
            shoppers_published=args.shoppers,
            recall_published=args.recall
        )
    elif args.type == "warning":
        result = notifier.send_final_warning_notification(
            published_count=args.published,
            required_count=7,
            shoppers_published=args.shoppers,
            recall_published=args.recall
        )
    elif args.type == "cancelled":
        result = notifier.send_newsletter_cancelled_notification(
            published_count=args.published,
            required_count=7,
            shoppers_published=args.shoppers,
            recall_published=args.recall
        )

    print(f"Result: {result}")
