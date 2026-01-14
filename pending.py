#!/usr/bin/env python3
"""
Automated Pending Posts Processor

Fetches pending posts from WordPress, copy edits with Claude API,
generates HTML files with SEO metadata, and updates index.html.

Usage:
    python3 pending.py              # List all pending posts
    python3 pending.py --process 1,3,5   # Process specific posts
    python3 pending.py --process all     # Process all pending posts
    python3 pending.py --dry-run         # Preview without creating files
"""

import os
import sys
import re
import json
import argparse
import base64
from html import unescape
from pathlib import Path

import requests
from anthropic import Anthropic

# Configuration
WP_BASE_URL = "https://boingboing.net"
WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
SCRIPT_DIR = Path(__file__).parent
INDEX_FILE = SCRIPT_DIR / "index.html"


def get_credentials():
    """Get WordPress credentials from environment."""
    username = os.environ.get("WP_USERNAME")
    password = os.environ.get("WP_APP_PASSWORD")

    if not username or not password:
        print("Error: Missing WordPress credentials.")
        print("Set WP_USERNAME and WP_APP_PASSWORD environment variables.")
        print("See .env.example for details.")
        sys.exit(1)

    return username, password


def fetch_pending_posts():
    """Fetch all pending posts from WordPress API."""
    username, password = get_credentials()

    # Basic auth with application password
    auth_string = f"{username}:{password}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{WP_API_URL}/posts",
            params={
                "status": "pending",
                "per_page": 50,
                "context": "edit"
            },
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Error: Authentication failed.")
            print("Check your WP_USERNAME and WP_APP_PASSWORD.")
        else:
            print(f"Error fetching posts: {e}")
        sys.exit(1)


def fetch_author_name(author_id, headers):
    """Fetch author display name by ID."""
    try:
        response = requests.get(
            f"{WP_API_URL}/users/{author_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json().get("name", "Unknown")
    except:
        return "Unknown"


def strip_html(html):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', '', html)
    return unescape(text).strip()


def word_count(html):
    """Count words in HTML content."""
    text = strip_html(html)
    return len(text.split())


def display_posts(posts):
    """Display numbered list of pending posts."""
    print("\nPENDING POSTS")
    print("─" * 60)

    for i, post in enumerate(posts, 1):
        title = strip_html(post.get("title", {}).get("raw", "Untitled"))
        author = post.get("_author_name", "Unknown")
        words = word_count(post.get("content", {}).get("raw", ""))

        print(f"{i:2}. {title[:55]}")
        print(f"    Author: {author} | Words: {words}")
        print()

    print(f"Total: {len(posts)} pending posts")
    print("─" * 60)


def copy_edit_with_claude(post, dry_run=False):
    """Send post to Claude for copy editing and metadata generation."""
    if dry_run:
        return {
            "edited_content": post.get("content", {}).get("raw", ""),
            "headlines": ["Headline 1", "Headline 2", "Headline 3", "Headline 4", "Headline 5"],
            "meta_headlines": ["Meta 1", "Meta 2", "Meta 3", "Meta 4", "Meta 5"],
            "meta_descriptions": ["Description 1", "Description 2", "Description 3", "Description 4", "Description 5"],
            "tags": "tag1, tag2, tag3",
            "focus_keyphrase": "focus keyphrase",
            "copy_edits_made": "Dry run - no edits made"
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    title = post.get("title", {}).get("raw", "Untitled")
    content = post.get("content", {}).get("raw", "")
    author = post.get("_author_name", "Unknown")

    prompt = f"""Copy edit this Boing Boing contributor post. Preserve the author's voice while fixing errors and tightening prose.

TITLE: {title}
AUTHOR: {author}

CONTENT:
{content}

---

Please provide:

1. EDITED_CONTENT: The copy-edited post (preserve all WordPress block comments, hyperlinks, images, embeds)

2. COPY_EDITS_MADE: Brief list of changes (e.g., "- Fixed typo: 'teh' → 'the'")

3. HEADLINES: 5 headline options (70 chars max each, sentence case)

4. TAGS: 3-5 category tags, comma-separated, broadest to most specific

5. FOCUS_KEYPHRASE: Yoast SEO focus keyphrase (3-5 words)

6. META_HEADLINES: 5 meta headline options (60 chars max each)

7. META_DESCRIPTIONS: 5 meta description options (120 chars max each)

Output as JSON with these exact keys: edited_content, copy_edits_made, headlines (array), tags, focus_keyphrase, meta_headlines (array), meta_descriptions (array)"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract JSON from response
        text = response.content[0].text

        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"Warning: Could not parse Claude response for '{title}'")
            return None

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        return None


def search_previously(title, content):
    """Search boingboing.net for related 'Previously' articles."""
    # Extract key terms from title
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}
    words = [w.lower() for w in re.findall(r'\w+', title) if w.lower() not in stop_words]

    query = ' '.join(words[:4])
    search_url = f"https://www.google.com/search?q=site:boingboing.net+{query}"

    # Return placeholder - actual search would need to be done manually or via API
    return []


def generate_html(post, edit_result, source_url=""):
    """Generate HTML file content for the post."""
    title = strip_html(post.get("title", {}).get("raw", "Untitled"))
    author = post.get("_author_name", "Unknown")
    content = edit_result.get("edited_content", "")

    headlines_html = "\n".join([
        f'<div class="item-row"><span>{h}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>'
        for h in edit_result.get("headlines", [])
    ])

    meta_headlines_html = "\n".join([
        f'<div class="item-row"><span>{h}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>'
        for h in edit_result.get("meta_headlines", [])
    ])

    meta_desc_html = "\n".join([
        f'<div class="item-row"><span>{d}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>'
        for d in edit_result.get("meta_descriptions", [])
    ])

    copy_edits = edit_result.get("copy_edits_made", "").replace("\n", "<br>\n")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post Preview</title>
    <link rel="stylesheet" href="post-style.css">
</head>
<body>

<div class="headline-row">
    <h1 id="headline">{title}</h1>
    <button class="copy-btn" onclick="copyText('headline')">copy</button>
</div>

<article id="postBody">
{content}

<div class="previously" id="previously">
<strong>Previously:</strong>
<ul>
<li><a href="#">[Search site:boingboing.net for related articles]</a></li>
</ul>
</div>
</article>

<div class="post-actions">
    <button class="copy-btn" onclick="copyPostOnly()">Copy post</button>
    <button class="copy-btn" onclick="copyPreviouslyOnly()">Copy previously</button>
</div>

<hr>

<div class="metadata">

<div class="section-header">
    <h3>Source</h3>
    <button class="copy-btn" onclick="copyText('sourceUrl')">copy</button>
</div>
<p class="source-url" id="sourceUrl">{source_url}</p>

<h3>Headlines (70 characters max)</h3>
{headlines_html}

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Category Tags</h3>
    <button class="copy-btn" onclick="copyText('tags')">copy</button>
</div>
<p id="tags">{edit_result.get("tags", "")}</p>

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Yoast Focus Keyphrase</h3>
    <button class="copy-btn" onclick="copyText('focusKeyphrase')">copy</button>
</div>
<p id="focusKeyphrase">{edit_result.get("focus_keyphrase", "")}</p>

<h3>Meta Headlines (60 characters max)</h3>
{meta_headlines_html}

<h3>Meta Descriptions (120 characters max)</h3>
{meta_desc_html}

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Author</h3>
</div>
<p>{author}</p>

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Copy Edits Made</h3>
</div>
<p style="color: #666; font-size: 14px;">
{copy_edits}
</p>

</div>

<script src="post-script.js"></script>

</body>
</html>
'''
    return html


def slugify(title):
    """Convert title to filename slug."""
    # Remove special characters, lowercase, replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:50]  # Limit length


def update_index(filename, title):
    """Add new post to index.html."""
    if not INDEX_FILE.exists():
        print(f"Warning: {INDEX_FILE} not found. Skipping index update.")
        return

    content = INDEX_FILE.read_text()

    # Find the posts array and the contributor posts section
    # Look for "// Contributor posts (copy edited)" comment
    contributor_marker = "// Contributor posts (copy edited)"

    if contributor_marker in content:
        # Insert after the contributor marker
        new_entry = f"    {{ file: '{filename}', title: '{title.replace(chr(39), chr(92)+chr(39))}' }},\n"
        insert_pos = content.index(contributor_marker) + len(contributor_marker) + 1
        content = content[:insert_pos] + new_entry + content[insert_pos:]
    else:
        # Fallback: insert near the beginning of the posts array
        posts_start = content.find("const posts = [")
        if posts_start != -1:
            insert_pos = content.find("[", posts_start) + 1
            new_entry = f"\n    {{ file: '{filename}', title: '{title.replace(chr(39), chr(92)+chr(39))}' }},"
            content = content[:insert_pos] + new_entry + content[insert_pos:]

    INDEX_FILE.write_text(content)
    print(f"  Added to index.html")


def process_post(post, dry_run=False):
    """Process a single post: copy edit, generate HTML, update index."""
    title = strip_html(post.get("title", {}).get("raw", "Untitled"))
    author = post.get("_author_name", "Unknown")

    print(f"\nProcessing: {title}")
    print(f"  Author: {author}")

    # Copy edit with Claude
    print("  Sending to Claude for copy editing...")
    edit_result = copy_edit_with_claude(post, dry_run)

    if not edit_result:
        print("  Error: Failed to get edit results. Skipping.")
        return None

    # Generate filename
    filename = f"post-{slugify(title)}.html"
    filepath = SCRIPT_DIR / filename

    if dry_run:
        print(f"  [Dry run] Would create: {filename}")
        print(f"  [Dry run] Would add to index.html")
        return filename

    # Generate HTML
    print("  Generating HTML file...")
    html = generate_html(post, edit_result)

    # Write file
    filepath.write_text(html)
    print(f"  Created: {filename}")

    # Update index
    update_index(filename, title)

    return filename


def main():
    parser = argparse.ArgumentParser(description="Process pending WordPress posts")
    parser.add_argument("--process", help="Posts to process: comma-separated numbers or 'all'")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating files")
    args = parser.parse_args()

    # Fetch posts
    print("Fetching pending posts from WordPress...")
    posts = fetch_pending_posts()

    if not posts:
        print("No pending posts found.")
        return

    # Get author names
    username, password = get_credentials()
    auth_string = f"{username}:{password}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    headers = {"Authorization": f"Basic {auth_bytes}"}

    for post in posts:
        author_id = post.get("author")
        post["_author_name"] = fetch_author_name(author_id, headers)

    # Display posts
    display_posts(posts)

    # Process if requested
    if args.process:
        if args.process.lower() == "all":
            indices = list(range(len(posts)))
        else:
            try:
                indices = [int(x.strip()) - 1 for x in args.process.split(",")]
            except ValueError:
                print("Error: Invalid post numbers. Use comma-separated numbers or 'all'.")
                return

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processing {len(indices)} post(s)...")

        created = []
        for i in indices:
            if 0 <= i < len(posts):
                result = process_post(posts[i], args.dry_run)
                if result:
                    created.append(result)
            else:
                print(f"Warning: Post #{i+1} out of range. Skipping.")

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done! Created {len(created)} file(s).")
    else:
        print("\nTo process posts, run:")
        print("  python3 pending.py --process 1,3,5    # Process specific posts")
        print("  python3 pending.py --process all      # Process all posts")
        print("  python3 pending.py --dry-run --process all  # Preview without creating")


if __name__ == "__main__":
    main()
