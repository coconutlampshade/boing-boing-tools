#!/usr/bin/env python3
"""
Daily Digest Newsletter Generator

Fetches published posts from WordPress REST API and generates an HTML digest
with excerpts (first 1-2 paragraphs) and "Read more" links, plus AI-generated
subhead and introduction.

Usage:
    python3 digest.py                    # Generate today's digest
    python3 digest.py --date 2026-01-14  # Generate for a specific date
    python3 digest.py --open             # Generate and open in browser

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
from html import unescape, escape

import requests
import pytz
from bs4 import BeautifulSoup
from anthropic import Anthropic

# Configuration
SCRIPT_DIR = Path(__file__).parent
WP_SITE = "https://boingboing.net"
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")
PACIFIC = pytz.timezone('US/Pacific')

# Cache for author names
AUTHOR_CACHE = {}


def get_time_window(target_date=None):
    """Get noon-to-noon time window for the target date."""
    if target_date:
        end_date = datetime.strptime(target_date, "%Y-%m-%d")
        end_date = PACIFIC.localize(end_date.replace(hour=12, minute=0, second=0, microsecond=0))
    else:
        now = datetime.now(PACIFIC)
        end_date = now.replace(hour=12, minute=0, second=0, microsecond=0)

    start_date = end_date - timedelta(days=1)
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
                    "_embed": "author,wp:featuredmedia"
                },
                headers=headers,
                timeout=30
            )

            if response.status_code == 400:
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

            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
            if page >= total_pages:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            print(f"Error fetching posts: {e}")
            sys.exit(1)

    # Get author names for all posts (including shop posts)
    headers_for_author = headers
    for post in all_posts:
        author_id = post.get("author")
        embedded = post.get("_embedded", {})
        author_data = embedded.get("author", [{}])[0] if embedded.get("author") else {}
        author_name = author_data.get("name") if author_data else None

        if not author_name and author_id:
            author_name = fetch_author(author_id, headers_for_author)

        post["_author_name"] = author_name or "Unknown"

    print(f"Found {len(all_posts)} posts")
    return all_posts


def format_post_date(date_str):
    """Format ISO date to 'Day, DD Mon YYYY'."""
    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    dt_pacific = dt.astimezone(PACIFIC)
    return dt_pacific.strftime("%a, %d %b %Y")


def extract_excerpt(html_content, max_paragraphs=2):
    """Extract first 1-2 paragraphs from content."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(['script', 'style', 'iframe']):
        tag.decompose()

    # Remove ad placeholders
    for div in soup.find_all('div', class_=lambda x: x and 'boing-primis' in x):
        div.decompose()
    for div in soup.find_all('div', class_=lambda x: x and 'advads' in x):
        div.decompose()

    # Get paragraphs
    paragraphs = []
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text and len(text) > 20:  # Skip very short paragraphs
            paragraphs.append(str(p))
            if len(paragraphs) >= max_paragraphs:
                break

    # Also check for blockquotes (often used in posts)
    if len(paragraphs) < max_paragraphs:
        for bq in soup.find_all('blockquote'):
            paragraphs.append(str(bq))
            if len(paragraphs) >= max_paragraphs:
                break

    return '\n'.join(paragraphs)


def clean_full_content(html_content):
    """Clean full content for shop posts (remove ads, keep everything else)."""
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted elements
    for tag in soup.find_all(['script', 'style']):
        tag.decompose()

    # Remove ad placeholders
    for div in soup.find_all('div', class_=lambda x: x and 'boing-primis' in x):
        div.decompose()
    for div in soup.find_all('div', class_=lambda x: x and 'advads' in x):
        div.decompose()

    # Remove "The post X appeared first on Y" text
    for p in soup.find_all('p'):
        text = p.get_text(strip=True).lower()
        if 'appeared first on' in text or 'this entry was posted' in text:
            p.decompose()

    return str(soup)


def extract_featured_image(post):
    """Extract featured image URL and alt text from embedded data."""
    embedded = post.get("_embedded", {})
    media = embedded.get("wp:featuredmedia", [])

    if media and len(media) > 0:
        media_item = media[0]
        source_url = media_item.get("source_url", "")
        alt_text = media_item.get("alt_text", "")

        # Get caption for alt text fallback
        if not alt_text:
            caption_data = media_item.get("caption", {})
            if isinstance(caption_data, dict):
                caption_html = caption_data.get("rendered", "")
                if caption_html:
                    soup = BeautifulSoup(caption_html, "html.parser")
                    alt_text = soup.get_text().strip()

        return source_url, alt_text

    return None, None


def generate_ai_intro(posts):
    """Generate subhead and introduction using Claude."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set. Using default intro.")
        return "Today's posts", "Here are today's Boing Boing stories. Thanks for reading!"

    headlines = [post.get("title", {}).get("rendered", "") for post in posts]
    headlines_text = "\n".join([f"- {unescape(h)}" for h in headlines[:30]])

    client = Anthropic(api_key=api_key)

    prompt = f"""You're writing the newsletter intro for Boing Boing, a blog about tech, culture, science, and politics.

Here are today's post headlines:
{headlines_text}

Generate:
1. SUBHEAD: A witty 5-10 word subhead that captures the day's theme or highlights an interesting story. Don't use generic phrases like "Today's posts". Be specific and clever.

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
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("subhead", ""), data.get("intro", "")

    except Exception as e:
        print(f"Warning: AI intro generation failed: {e}")

    return "Today's posts", "Here are today's Boing Boing stories. Thanks for reading!"


def render_html(target_date, subhead, intro, posts):
    """Render digest HTML."""
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
            <title>Boing Boing Digest</title>
            <style>
                body {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                }}
                .digest-header {{
                    margin-bottom: 40px;
                }}
                .digest-header h1 {{
                    margin-bottom: 5px;
                }}
                .digest-header h3 {{
                    margin-top: 0;
                    color: #666;
                    font-weight: normal;
                }}
                .digest-header p {{
                    margin-top: 10px;
                    color: #333;
                }}
                .article {{
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #eee;
                }}
                .article h2 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                h6 {{
                    color: #666;
                    font-size: 0.9em;
                    font-weight: normal;
                    margin: 10px 0;
                }}
                .article-image {{
                    width: 100%;
                    max-width: 800px;
                    height: auto;
                    margin: 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
                .read-more {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                .read-more:hover {{
                    text-decoration: underline;
                }}
                .article-figure {{
                    margin: 20px 0;
                }}
                .article-figure figcaption {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 8px;
                    text-align: center;
                    font-style: italic;
                }}
                a {{
                    color: #0066cc;
                }}
                blockquote {{
                    border-left: 3px solid #ccc;
                    margin: 15px 0;
                    padding-left: 15px;
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <div class="digest-header">
                <h1>Boing Boing Digest, {date_header}</h1>
                <h3>{subhead}</h3>
                <p>{intro}</p>
            </div>
        '''

    for post in posts:
        title = post.get("title", {}).get("rendered", "Untitled")
        title_escaped = escape(unescape(title))
        title_display = unescape(title)

        author = post.get("_author_name", "Unknown")
        date_str = post.get("date", "")
        formatted_date = format_post_date(date_str) if date_str else ""

        link = post.get("link", "")

        content = post.get("content", {}).get("rendered", "")

        # Shop posts get full content, others get excerpt
        is_shop_post = author == "Boing Boing's Shop"
        if is_shop_post:
            article_content = clean_full_content(content)
        else:
            article_content = extract_excerpt(content, max_paragraphs=2)

        img_url, alt_text = extract_featured_image(post)
        alt_escaped = escape(alt_text) if alt_text else ""

        html += f'''
                <article class="article">
                    <h2>{title_display}</h2>
                    <h6>By {author} / {formatted_date}</h6>

                    <div class="article-content">
                        '''

        if img_url:
            html += f'<a href="{link}" title="{title_escaped}" rel="nofollow"><img src="{img_url}" class="article-image" alt="{alt_escaped}" style="display: block; margin: auto; margin-bottom: 5px; max-width: 100%;" /></a>'

        html += article_content

        # Only show "Read more" for non-shop posts
        if is_shop_post:
            html += '''
                    </div>
                </article>
                '''
        else:
            html += f'''
                    </div>
                    <p><a href="{link}" class="read-more">Read more →</a></p>
                </article>
                '''

    html += '''
        </body>
        </html>
        '''

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate daily digest from Boing Boing posts")
    parser.add_argument("--date", "-d", help="Target date (YYYY-MM-DD). Default: today")
    parser.add_argument("--open", "-o", action="store_true", help="Open in browser after generating")
    parser.add_argument("--output", help="Output filename. Default: digest_DATE.html")
    args = parser.parse_args()

    start_utc, end_utc = get_time_window(args.date)
    posts = fetch_published_posts(start_utc, end_utc)

    if not posts:
        print("No posts found in the time window.")
        return

    print("Generating AI subhead and introduction...")
    subhead, intro = generate_ai_intro(posts)
    print(f"  Subhead: {subhead}")

    print("Rendering HTML...")
    html = render_html(args.date, subhead, intro, posts)

    if args.output:
        output_file = Path(args.output)
    else:
        target_date = args.date or datetime.now(PACIFIC).strftime("%Y-%m-%d")
        output_file = SCRIPT_DIR / f"digest_{target_date}.html"

    output_file.write_text(html)
    print(f"\nDigest saved to: {output_file}")
    print(f"  Posts included: {len(posts)}")

    if args.open:
        webbrowser.open(f"file://{output_file.absolute()}")


if __name__ == "__main__":
    main()
