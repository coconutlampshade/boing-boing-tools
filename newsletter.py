#!/usr/bin/env python3
"""
Daily Newsletter Generator

Fetches published posts from WordPress REST API and generates an HTML newsletter
with AI-generated subhead and introduction.

Usage:
    python3 newsletter.py                    # Generate today's newsletter
    python3 newsletter.py --date 2026-01-14  # Generate for a specific date
    python3 newsletter.py --open             # Generate and open in browser

Environment variables:
    WP_USER          Your WordPress username
    WP_APP_PASSWORD  WordPress application password
    ANTHROPIC_API_KEY  Anthropic API key for AI intro generation
"""

import os
import sys
import re
import json
import argparse
import base64
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from html import unescape

import requests
import pytz
from bs4 import BeautifulSoup
from anthropic import Anthropic
from dotenv import load_dotenv

# Configuration
SCRIPT_DIR = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(SCRIPT_DIR / ".env")
WP_SITE = "https://boingboing.net"
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
PACIFIC = pytz.timezone('US/Pacific')

# Cache for author names
AUTHOR_CACHE = {}


def get_time_window(target_date=None):
    """Get noon-to-noon time window for the target date.

    Returns (start_dt, end_dt) in UTC for API queries.
    """
    if target_date:
        # Parse target date and use it as the "end" date
        end_date = datetime.strptime(target_date, "%Y-%m-%d")
        end_date = PACIFIC.localize(end_date.replace(hour=12, minute=0, second=0, microsecond=0))
    else:
        # Default: noon today Pacific
        now = datetime.now(PACIFIC)
        end_date = now.replace(hour=12, minute=0, second=0, microsecond=0)

    # Start: noon yesterday Pacific
    start_date = end_date - timedelta(days=1)

    # Convert to UTC for API
    start_utc = start_date.astimezone(pytz.UTC)
    end_utc = end_date.astimezone(pytz.UTC)

    return start_utc, end_utc


def get_auth_headers():
    """Create authentication headers for WordPress API."""
    if not WP_USER or not WP_APP_PASSWORD:
        print("Error: WP_USER and WP_APP_PASSWORD environment variables required.")
        print("\nSet them with:")
        print('  export WP_USER="your-username"')
        print('  export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"')
        sys.exit(1)

    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    auth_header = base64.b64encode(credentials.encode()).decode()

    return {
        "Authorization": f"Basic {auth_header}",
        "User-Agent": "BoingBoingTools/1.0"
    }


def fetch_author(author_id, headers):
    """Fetch author name by ID, with caching."""
    if author_id in AUTHOR_CACHE:
        return AUTHOR_CACHE[author_id]

    try:
        response = requests.get(
            f"{WP_SITE}/wp-json/wp/v2/users/{author_id}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            name = data.get("name", "Unknown")
            AUTHOR_CACHE[author_id] = name
            return name
    except Exception:
        pass

    return "Unknown"


def fetch_published_posts(start_utc, end_utc):
    """Fetch published posts within the time window."""
    headers = get_auth_headers()

    # Format dates for API (ISO 8601)
    after = start_utc.strftime("%Y-%m-%dT%H:%M:%S")
    before = end_utc.strftime("%Y-%m-%dT%H:%M:%S")

    print(f"Fetching posts from {start_utc.astimezone(PACIFIC).strftime('%Y-%m-%d %I:%M %p PT')}")
    print(f"                  to {end_utc.astimezone(PACIFIC).strftime('%Y-%m-%d %I:%M %p PT')}")

    all_posts = []
    page = 1

    while True:
        try:
            response = requests.get(
                f"{WP_SITE}/wp-json/wp/v2/posts",
                params={
                    "status": "publish",
                    "after": after,
                    "before": before,
                    "per_page": 100,
                    "page": page,
                    "orderby": "date",
                    "order": "desc",
                    "_embed": "author,wp:featuredmedia"  # Include author and featured image
                },
                headers=headers,
                timeout=30
            )

            if response.status_code == 400:
                # No more pages
                break

            if response.status_code == 401:
                print("Error: Authentication failed.")
                sys.exit(1)

            if response.status_code == 403:
                print("Error: Access forbidden. IP may need Cloudflare whitelist.")
                sys.exit(1)

            response.raise_for_status()
            posts = response.json()

            if not posts:
                break

            all_posts.extend(posts)

            # Check if there are more pages
            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching posts: {e}")
            sys.exit(1)

    # Filter out shop posts
    headers_for_author = headers
    filtered_posts = []
    for post in all_posts:
        # Get author name
        author_id = post.get("author")

        # Check embedded author first
        embedded = post.get("_embedded", {})
        author_data = embedded.get("author", [{}])[0] if embedded.get("author") else {}
        author_name = author_data.get("name") if author_data else None

        if not author_name and author_id:
            author_name = fetch_author(author_id, headers_for_author)

        if author_name == "Boing Boing's Shop":
            continue

        post["_author_name"] = author_name or "Unknown"
        filtered_posts.append(post)

    print(f"Found {len(filtered_posts)} posts (excluded shop posts)")
    return filtered_posts


def format_post_date(date_str):
    """Format ISO date to 'h:mm am PT Day Mon DD, YYYY'."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    dt_pacific = dt.astimezone(PACIFIC)
    formatted = dt_pacific.strftime("%-I:%M %p PT %a %b %-d, %Y")
    return formatted.replace("AM", "am").replace("PM", "pm")


def clean_content(html_content):
    """Clean up post content for newsletter."""
    if not html_content:
        return ""

    # Remove "The post X appeared first on Y" text
    content = re.sub(
        r'<p[^>]*>The post .+? appeared first on .+?\.?</p>',
        '', html_content, flags=re.DOTALL | re.IGNORECASE
    )
    content = re.sub(
        r'The post .+? appeared first on .+?\.?',
        '', content, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove "This entry was posted in..." text
    content = re.sub(
        r'<p[^>]*>This entry was posted in .+?\.?</p>',
        '', content, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove Creative Commons notice
    content = re.sub(
        r'Boing Boing is published under a Creative Commons license.*?\.?',
        '', content, flags=re.IGNORECASE
    )

    # Remove ad placeholders and video containers
    content = re.sub(
        r'<div class="boing-primis-video.*?</div>\s*</div>\s*</div>',
        '', content, flags=re.DOTALL
    )
    content = re.sub(
        r'<div class="advads-edit-bar.*?</div>',
        '', content, flags=re.DOTALL
    )

    return content.strip()


def extract_featured_image(post):
    """Extract featured image URL and caption from embedded data."""
    embedded = post.get("_embedded", {})

    # Get featured media from embedded data
    media = embedded.get("wp:featuredmedia", [])
    if media and len(media) > 0:
        media_item = media[0]

        # Get image URL
        source_url = media_item.get("source_url", "")

        # Get caption
        caption = ""
        caption_data = media_item.get("caption", {})
        if isinstance(caption_data, dict):
            caption = caption_data.get("rendered", "")
        elif isinstance(caption_data, str):
            caption = caption_data

        # Clean caption HTML
        if caption:
            soup = BeautifulSoup(caption, "html.parser")
            caption = soup.get_text().strip()

        # Try alt text if no caption
        if not caption:
            caption = media_item.get("alt_text", "")

        return source_url, caption

    return None, None


def generate_ai_intro(posts):
    """Generate subhead and introduction using Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set. Using default intro.")
        return "All our posts from the past 24 hours", "Here are today's Boing Boing stories. Thanks for supporting independent journalism!"

    # Build list of headlines for Claude
    headlines = [post.get("title", {}).get("rendered", "") for post in posts]
    headlines_text = "\n".join([f"- {h}" for h in headlines[:30]])  # Limit to 30

    client = Anthropic(api_key=api_key)

    prompt = f"""You're writing the newsletter intro for Boing Boing, a blog about tech, culture, science, and politics.

Here are today's post headlines:
{headlines_text}

Generate:
1. SUBHEAD: A witty 5-10 word subhead that captures the day's theme or highlights an interesting story. Don't use generic phrases like "All our posts from the past 24 hours". Be specific and clever.

2. INTRO: A 1-2 sentence introduction (under 50 words) that gives readers a taste of what's inside. Mention 1-2 specific stories. End with a brief thanks for reading.

Return ONLY valid JSON:
{{"subhead": "your subhead here", "intro": "your intro here"}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text

        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("subhead", ""), data.get("intro", "")

    except Exception as e:
        print(f"Warning: AI intro generation failed: {e}")

    return "All our posts from the past 24 hours", "Here are today's Boing Boing stories. Thanks for supporting independent journalism!"


def render_html(target_date, subhead, intro, posts):
    """Render newsletter HTML."""
    # Format the date for the header
    if target_date:
        dt = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        dt = datetime.now(PACIFIC)

    date_header = dt.strftime("%B %-d, %Y")

    html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boing Boing Feed</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
            background-color: #f5f5f5;
            color: #333;
        }}
        article {{
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #1a1a1a;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 24px;
            line-height: 1.3;
        }}
        h6 {{
            color: #666;
            font-weight: normal;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 14px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 4px;
        }}
        figcaption.image-caption {{
            color: #666;
            text-align: center;
            margin: 10px 0 20px;
            font-size: 14px;
            font-style: italic;
        }}
        p {{
            margin: 15px 0;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .meta {{
            font-size: 14px;
            color: #666;
            margin-bottom: 30px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        h3 {{
            text-align: center;
            color: #666;
            margin-top: 0;
            margin-bottom: 30px;
            font-weight: normal;
        }}
        blockquote {{
            border-left: 3px solid #ccc;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
        }}
    </style>
</head>
<body>
    <h1>Boing Boing, {date_header}</h1>
    <h3>{subhead}</h3>
<p>Generated on: {datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S %Z')}</p><p>{intro}</p>'''

    for i, post in enumerate(posts):
        title = post.get("title", {}).get("rendered", "Untitled")
        title = unescape(title)

        author = post.get("_author_name", "Unknown")
        date_str = post.get("date", "")
        formatted_date = format_post_date(date_str) if date_str else ""

        content = post.get("content", {}).get("rendered", "")
        content = clean_content(content)

        link = post.get("link", "")

        # Get featured image
        img_url, caption = extract_featured_image(post)

        html += '<article>'
        html += f'<h2>{title}</h2>'

        if author and formatted_date:
            html += f'<h6>{author} / {formatted_date}</h6>'

        # Add featured image if present
        if img_url:
            if caption:
                html += f'<figure><img src="{img_url}"/><figcaption class="image-caption">{caption}</figcaption></figure>'
            else:
                html += f'<img src="{img_url}"/>'

        # Add content
        html += content

        html += '</article>'

        # Add spacer between articles (except after last one)
        if i < len(posts) - 1:
            html += '<p> </p>'

    html += '''
</body>
</html>
'''
    return html


def main():
    parser = argparse.ArgumentParser(description="Generate daily newsletter from Boing Boing posts")
    parser.add_argument("--date", "-d", help="Target date (YYYY-MM-DD). Default: today")
    parser.add_argument("--open", "-o", action="store_true", help="Open in browser after generating")
    parser.add_argument("--output", help="Output filename. Default: newsletter_DATE.html")
    args = parser.parse_args()

    # Get time window
    start_utc, end_utc = get_time_window(args.date)

    # Fetch posts
    posts = fetch_published_posts(start_utc, end_utc)

    if not posts:
        print("No posts found in the time window.")
        return

    # Generate AI intro
    print("Generating AI subhead and introduction...")
    subhead, intro = generate_ai_intro(posts)
    print(f"  Subhead: {subhead}")

    # Render HTML
    print("Rendering HTML...")
    html = render_html(args.date, subhead, intro, posts)

    # Determine output filename
    if args.output:
        output_file = Path(args.output)
    else:
        target_date = args.date or datetime.now(PACIFIC).strftime("%Y-%m-%d")
        output_file = SCRIPT_DIR / f"newsletter_{target_date}.html"

    # Write file
    output_file.write_text(html)
    print(f"\nNewsletter saved to: {output_file}")
    print(f"  Posts included: {len(posts)}")

    # Open in browser if requested
    if args.open:
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
