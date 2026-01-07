"""
Blogger API Client
Handles publishing posts to Google Blogger.
"""
import os
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class BloggerClient:
    """Client for interacting with the Google Blogger API v3."""

    SCOPES = ['https://www.googleapis.com/auth/blogger']

    def __init__(self):
        self.blog_id = os.getenv('BLOGGER_BLOG_ID')
        self.client_id = os.getenv('BLOGGER_CLIENT_ID')
        self.client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
        self.refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
        self._service = None

    def is_configured(self) -> bool:
        """Check if all required Blogger credentials are configured."""
        return all([
            self.blog_id,
            self.client_id,
            self.client_secret,
            self.refresh_token
        ])

    def _get_credentials(self) -> Credentials:
        """Create OAuth2 credentials from refresh token."""
        return Credentials(
            token=None,
            refresh_token=self.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.SCOPES
        )

    def _get_service(self):
        """Get or create the Blogger API service."""
        if self._service is None:
            credentials = self._get_credentials()
            self._service = build('blogger', 'v3', credentials=credentials)
        return self._service

    def publish_post(
        self,
        title: str,
        html_content: str,
        labels: Optional[list] = None,
        is_draft: bool = False
    ) -> Dict[str, Any]:
        """
        Publish a post to Blogger.

        Args:
            title: Post title
            html_content: HTML content of the post
            labels: Optional list of labels/tags
            is_draft: If True, creates as draft instead of publishing

        Returns:
            Dict containing blogger_post_id, blogger_url, and published_at
        """
        if not self.is_configured():
            raise ValueError(
                "Blogger API not configured. Please set BLOGGER_BLOG_ID, "
                "BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, and BLOGGER_REFRESH_TOKEN "
                "environment variables."
            )

        service = self._get_service()

        # Build the post body
        post_body = {
            'kind': 'blogger#post',
            'title': title,
            'content': html_content,
        }

        if labels:
            post_body['labels'] = labels

        try:
            # Insert the post
            request = service.posts().insert(
                blogId=self.blog_id,
                body=post_body,
                isDraft=is_draft
            )
            response = request.execute()

            return {
                'blogger_post_id': response.get('id'),
                'blogger_url': response.get('url'),
                'published_at': response.get('published'),
                'status': 'draft' if is_draft else 'live'
            }

        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else str(e)
            raise Exception(f"Blogger API error: {error_details}")

    def update_post(
        self,
        blogger_post_id: str,
        title: Optional[str] = None,
        html_content: Optional[str] = None,
        labels: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Update an existing post on Blogger.

        Args:
            blogger_post_id: The Blogger post ID
            title: New title (optional)
            html_content: New HTML content (optional)
            labels: New labels (optional)

        Returns:
            Updated post info
        """
        if not self.is_configured():
            raise ValueError("Blogger API not configured.")

        service = self._get_service()

        # First get the existing post
        existing = service.posts().get(
            blogId=self.blog_id,
            postId=blogger_post_id
        ).execute()

        # Update only provided fields
        if title:
            existing['title'] = title
        if html_content:
            existing['content'] = html_content
        if labels is not None:
            existing['labels'] = labels

        try:
            response = service.posts().update(
                blogId=self.blog_id,
                postId=blogger_post_id,
                body=existing
            ).execute()

            return {
                'blogger_post_id': response.get('id'),
                'blogger_url': response.get('url'),
                'updated_at': response.get('updated')
            }

        except HttpError as e:
            raise Exception(f"Blogger API error: {str(e)}")

    def delete_post(self, blogger_post_id: str) -> bool:
        """
        Delete a post from Blogger.

        Args:
            blogger_post_id: The Blogger post ID

        Returns:
            True if successful
        """
        if not self.is_configured():
            raise ValueError("Blogger API not configured.")

        service = self._get_service()

        try:
            service.posts().delete(
                blogId=self.blog_id,
                postId=blogger_post_id
            ).execute()
            return True

        except HttpError as e:
            raise Exception(f"Blogger API error: {str(e)}")

    def get_post(self, blogger_post_id: str) -> Dict[str, Any]:
        """
        Get a post from Blogger.

        Args:
            blogger_post_id: The Blogger post ID

        Returns:
            Post data from Blogger
        """
        if not self.is_configured():
            raise ValueError("Blogger API not configured.")

        service = self._get_service()

        try:
            response = service.posts().get(
                blogId=self.blog_id,
                postId=blogger_post_id
            ).execute()
            return response

        except HttpError as e:
            raise Exception(f"Blogger API error: {str(e)}")

    def list_posts(self, max_results: int = 500) -> list:
        """
        List all posts from Blogger.

        Args:
            max_results: Maximum number of posts to fetch

        Returns:
            List of posts from Blogger
        """
        if not self.is_configured():
            raise ValueError("Blogger API not configured.")

        service = self._get_service()
        all_posts = []
        page_token = None

        try:
            while True:
                request = service.posts().list(
                    blogId=self.blog_id,
                    maxResults=min(max_results - len(all_posts), 100),
                    pageToken=page_token,
                    status='live'
                )
                response = request.execute()

                posts = response.get('items', [])
                all_posts.extend(posts)

                page_token = response.get('nextPageToken')
                if not page_token or len(all_posts) >= max_results:
                    break

            return all_posts

        except HttpError as e:
            raise Exception(f"Blogger API error: {str(e)}")


# Singleton instance
_blogger_client = None

def get_blogger_client() -> BloggerClient:
    """Get the singleton Blogger client instance."""
    global _blogger_client
    if _blogger_client is None:
        _blogger_client = BloggerClient()
    return _blogger_client
