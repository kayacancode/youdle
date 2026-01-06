"""
Blogger OAuth Token Generator
Run this script to get the refresh token needed for the Blogger API.

Prerequisites:
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Enable the Blogger API v3
4. Create OAuth 2.0 credentials (Desktop App type)
5. Download the credentials JSON and save as 'client_secret.json' in this folder

Usage:
    python get_blogger_token.py

After running, copy the refresh_token to your .env file.
"""
import os
import json

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Missing dependencies. Install them with:")
        print("  pip install google-auth-oauthlib")
        return

    SCOPES = ['https://www.googleapis.com/auth/blogger']

    # Check for client secret file
    client_secret_path = os.path.join(os.path.dirname(__file__), 'client_secret.json')

    if not os.path.exists(client_secret_path):
        print("=" * 60)
        print("SETUP INSTRUCTIONS")
        print("=" * 60)
        print()
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable the 'Blogger API v3' in APIs & Services > Library")
        print("4. Go to APIs & Services > Credentials")
        print("5. Click 'Create Credentials' > 'OAuth client ID'")
        print("6. Select 'Desktop App' as application type")
        print("7. Download the JSON file")
        print("8. Save it as 'client_secret.json' in the api/ folder")
        print("9. Run this script again")
        print()
        print(f"Expected path: {client_secret_path}")
        return

    # Load client secrets
    with open(client_secret_path, 'r') as f:
        client_config = json.load(f)

    # Extract client ID and secret
    if 'installed' in client_config:
        client_id = client_config['installed']['client_id']
        client_secret = client_config['installed']['client_secret']
    elif 'web' in client_config:
        client_id = client_config['web']['client_id']
        client_secret = client_config['web']['client_secret']
    else:
        print("Invalid client_secret.json format")
        return

    print("Starting OAuth flow...")
    print("A browser window will open. Sign in and authorize the app.")
    print()

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
    credentials = flow.run_local_server(port=8080)

    print()
    print("=" * 60)
    print("SUCCESS! Add these to your .env file:")
    print("=" * 60)
    print()
    print(f"BLOGGER_CLIENT_ID={client_id}")
    print(f"BLOGGER_CLIENT_SECRET={client_secret}")
    print(f"BLOGGER_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("=" * 60)
    print("Don't forget to also set BLOGGER_BLOG_ID!")
    print()
    print("To find your Blog ID:")
    print("1. Go to your Blogger dashboard")
    print("2. Select your blog")
    print("3. Look at the URL - it contains your blog ID")
    print("   Example: https://www.blogger.com/blog/posts/1234567890")
    print("   Blog ID is: 1234567890")
    print("=" * 60)


if __name__ == '__main__':
    main()
