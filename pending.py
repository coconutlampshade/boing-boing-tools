#!/usr/bin/env python3
"""
Automated Pending Posts Processor

Processes pending posts from WordPress, copy edits with Claude API,
generates HTML files with SEO metadata, and updates index.html.

Usage:
    python3 pending.py                     # Fetch and display pending posts
    python3 pending.py --process all       # Fetch and process all pending posts
    python3 pending.py --process 1,3       # Fetch and process specific posts
    python3 pending.py --cached            # Use cached JSON file instead of fetching
    python3 pending.py --dry-run --process all   # Preview without creating files

Environment variables:
    WP_USER          Your WordPress username
    WP_APP_PASSWORD  WordPress application password (from User → Profile)
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
from dotenv import load_dotenv

# Configuration
SCRIPT_DIR = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(SCRIPT_DIR / ".env")
INDEX_FILE = SCRIPT_DIR / "index.html"
DEFAULT_INPUT = SCRIPT_DIR / "pending-posts.json"

# WordPress API Configuration
WP_SITE = "https://boingboing.net"
WP_USER = os.environ.get("WP_USER", "")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "")

BROWSER_SCRIPT = '''
// Run this in your browser console on the WordPress Pending Posts page
// (Posts → All Posts → filter by Pending)

(async function() {
    const posts = [];
    const rows = document.querySelectorAll('tr.iedit');

    for (const row of rows) {
        const titleLink = row.querySelector('.row-title');
        const authorEl = row.querySelector('.author a');
        const editLink = row.querySelector('.row-actions .edit a');

        if (titleLink && editLink) {
            const postId = editLink.href.match(/post=(\\d+)/)?.[1];
            posts.push({
                id: postId,
                title: titleLink.textContent.trim(),
                author: authorEl ? authorEl.textContent.trim() : 'Unknown',
                editUrl: editLink.href,
                content: '' // Will be filled below
            });
        }
    }

    console.log(`Found ${posts.length} pending posts. Fetching content...`);

    // Fetch content for each post using the nonce from the page
    for (const post of posts) {
        try {
            const response = await fetch(`/wp-json/wp/v2/posts/${post.id}?context=edit`, {
                credentials: 'same-origin',
                headers: { 'X-WP-Nonce': wpApiSettings.nonce }
            });
            if (response.ok) {
                const data = await response.json();
                post.content = data.content?.raw || '';
                post.title = data.title?.raw || post.title;
            }
        } catch (e) {
            console.log(`Could not fetch post ${post.id}: ${e.message}`);
        }
    }

    // Output as JSON
    const json = JSON.stringify(posts, null, 2);
    console.log('\\n' + json);
    console.log('\\nCopy the JSON above and save to pending-posts.json');
})();
'''


def strip_html(html):
    """Remove HTML tags and decode entities."""
    if not html:
        return ""
    text = re.sub(r'<[^>]+>', '', str(html))
    return unescape(text).strip()


def word_count(text):
    """Count words in text."""
    return len(strip_html(text).split())


def display_posts(posts):
    """Display numbered list of pending posts."""
    print("\nPENDING POSTS")
    print("─" * 60)

    for i, post in enumerate(posts, 1):
        title = strip_html(post.get("title", "Untitled"))
        author = post.get("author", "Unknown")
        content = post.get("content", "")
        words = word_count(content)
        has_content = "✓" if content else "✗"

        print(f"{i:2}. {title[:50]}")
        print(f"    Author: {author} | Words: {words} | Content: {has_content}")
        print()

    print(f"Total: {len(posts)} pending posts")
    print("─" * 60)


def search_previously_links(title, content, dry_run=False):
    """Search boingboing.net for related articles for Previously section."""
    if dry_run:
        return [
            {"title": "Related Article 1", "url": "https://boingboing.net/example1"},
            {"title": "Related Article 2", "url": "https://boingboing.net/example2"},
            {"title": "Related Article 3", "url": "https://boingboing.net/example3"},
        ]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return []

    client = Anthropic(api_key=api_key)

    # Extract key topics from title and content
    text_sample = strip_html(content)[:500]

    prompt = f"""Find 3 related articles from boingboing.net for a "Previously" section.

Post title: {title}
Post excerpt: {text_sample}

Search boingboing.net for related articles. Return ONLY a JSON array with exactly 3 objects, each having "title" and "url" keys. URLs must be real boingboing.net URLs you find.

Example format:
[
  {{"title": "Article title here", "url": "https://boingboing.net/2024/01/01/article-slug.html"}},
  {{"title": "Another article", "url": "https://boingboing.net/2023/05/15/another-slug.html"}},
  {{"title": "Third article", "url": "https://boingboing.net/2022/08/20/third-slug.html"}}
]

Return ONLY the JSON array, no other text."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text

        # Try to parse JSON array
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            links = json.loads(json_match.group())
            # Validate URLs are boingboing.net
            valid_links = [
                link for link in links
                if isinstance(link, dict)
                and link.get("url", "").startswith("https://boingboing.net/")
            ]
            return valid_links[:3]

    except Exception as e:
        print(f"  Warning: Could not search for Previously links: {e}")

    return []


def copy_edit_with_claude(post, dry_run=False):
    """Send post to Claude for copy editing and metadata generation."""
    title = post.get("title", "Untitled")
    content = post.get("content", "")
    author = post.get("author", "Unknown")

    if dry_run:
        return {
            "edited_content": content,
            "headlines": [f"{title[:60]}" for _ in range(5)],
            "meta_headlines": [f"{title[:50]}" for _ in range(5)],
            "meta_descriptions": [f"Description for {title[:80]}" for _ in range(5)],
            "tags": "tag1, tag2, tag3",
            "focus_keyphrase": title[:30].lower(),
            "copy_edits_made": "Dry run - no edits made",
            "previously_links": []
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

    prompt = f"""Copy edit this Boing Boing contributor post following these guidelines:

## Copy Editing Rules
DO:
- Fix objective errors (typos, grammar, punctuation)
- Tighten verbose passages aggressively — concision takes priority over preserving exact phrasing
- Restructure wordy sentences (e.g., "According to a blog post he published earlier this week, X plans on bringing..." → "X plans to bring..., he said in a recent blog post.")
- Clarify confusing sentences
- Improve sentence rhythm and flow
- Remove filler phrases and empty words
- Convert YouTube Shorts URLs to regular format: https://www.youtube.com/shorts/VIDEO_ID → https://youtu.be/VIDEO_ID

DON'T:
- Change the author's opinions or positions
- Remove personality or humor
- Add your own commentary
- Over-polish into generic prose

PRESERVE:
- All hyperlinks (keep href attributes intact)
- All images (keep src, alt, and any captions)
- Formatting (bold, italic, lists, blockquotes)
- Embedded media (YouTube, tweets, etc.)
- WordPress block comments (<!-- wp:paragraph --> etc.)

---

TITLE: {title}
AUTHOR: {author}

CONTENT:
{content}

---

Please provide:

1. EDITED_CONTENT: The copy-edited post with all WordPress block comments, hyperlinks, images, and embeds preserved

2. COPY_EDITS_MADE: Brief list of changes (e.g., "- Fixed typo: 'teh' → 'the'")

3. HEADLINES: 5 headline options (70 chars max each, sentence case NOT title case)

4. TAGS: 3-5 category tags, comma-separated, broadest to most specific

5. FOCUS_KEYPHRASE: Yoast SEO focus keyphrase (3-5 words)

6. META_HEADLINES: 5 meta headline options (60 chars max each, sentence case)

7. META_DESCRIPTIONS: 5 meta description options (100-120 chars each)

Output as JSON with these exact keys: edited_content, copy_edits_made, headlines (array), tags, focus_keyphrase, meta_headlines (array), meta_descriptions (array)"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

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


def generate_html(post, edit_result, source_url="", previously_links=None):
    """Generate HTML file content for the post."""
    title = strip_html(post.get("title", "Untitled"))
    author = post.get("author", "Unknown")
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

    copy_edits = edit_result.get("copy_edits_made", "")
    if isinstance(copy_edits, str):
        copy_edits = copy_edits.replace("\n", "<br>\n")

    # Check if content already has Previously or See also section
    has_previously = 'Previously:' in content or 'See also:' in content or 'previously' in content.lower()

    # Only add Previously section wrapper if content doesn't have one
    if has_previously:
        previously_html = ""
    elif previously_links:
        links_html = "\n".join([
            f'<li><a href="{link["url"]}">{link["title"]}</a></li>'
            for link in previously_links
        ])
        previously_html = f'''
<div class="previously" id="previously">
<strong>Previously:</strong>
<ul>
{links_html}
</ul>
</div>'''
    else:
        # No placeholder - omit Previously section entirely if no links found
        previously_html = ''

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
    <button class="copy-btn" onclick="copyText('headline', this)">copy</button>
</div>

<article id="postBody">
{content}
{previously_html}
</article>

<div class="post-actions">
    <button class="copy-btn" onclick="copyPostOnly(this)">Copy post</button>
    <button class="copy-btn" onclick="copyPreviouslyOnly(this)">Copy previously</button>
</div>

<hr>

<div class="metadata">

<div class="section-header">
    <h3>Source</h3>
    <button class="copy-btn" onclick="copyText('sourceUrl', this)">copy</button>
</div>
<p class="source-url" id="sourceUrl">{source_url}</p>

<h3>Headlines (70 characters max)</h3>
{headlines_html}

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Category Tags</h3>
    <button class="copy-btn" onclick="copyText('tags', this)">copy</button>
</div>
<p id="tags">{edit_result.get("tags", "")}</p>

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Yoast Focus Keyphrase</h3>
    <button class="copy-btn" onclick="copyText('focusKeyphrase', this)">copy</button>
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
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug[:50]


def update_index(filename, title):
    """Add new post to index.html."""
    if not INDEX_FILE.exists():
        print(f"Warning: {INDEX_FILE} not found. Skipping index update.")
        return

    content = INDEX_FILE.read_text()

    # Escape single quotes in title
    escaped_title = title.replace("'", "\\'")

    # Find the posts array and insert at the beginning (after the opening bracket)
    # Look for "// Contributor posts" or "// New posts" marker
    contributor_marker = "// Contributor posts (copy edited)"
    new_posts_marker = "// New posts"

    new_entry = f"    {{ file: 'posts/{filename}', title: '{escaped_title}' }},\n"

    if contributor_marker in content:
        insert_pos = content.index(contributor_marker) + len(contributor_marker) + 1
        content = content[:insert_pos] + new_entry + content[insert_pos:]
    elif new_posts_marker in content:
        insert_pos = content.index(new_posts_marker) + len(new_posts_marker) + 1
        content = content[:insert_pos] + new_entry + content[insert_pos:]
    else:
        # Fallback: insert after "const posts = ["
        posts_start = content.find("const posts = [")
        if posts_start != -1:
            insert_pos = content.find("[", posts_start) + 1
            content = content[:insert_pos] + "\n" + new_entry + content[insert_pos:]

    INDEX_FILE.write_text(content)
    print(f"  Added to index.html")


def process_post(post, dry_run=False):
    """Process a single post: copy edit, generate HTML, update index."""
    title = strip_html(post.get("title", "Untitled"))
    author = post.get("author", "Unknown")
    content = post.get("content", "")

    print(f"\nProcessing: {title}")
    print(f"  Author: {author}")

    if not content:
        print("  Warning: No content found. Skipping.")
        return None

    # Copy edit with Claude
    print("  Sending to Claude for copy editing...")
    edit_result = copy_edit_with_claude(post, dry_run)

    if not edit_result:
        print("  Error: Failed to get edit results. Skipping.")
        return None

    # Search for Previously links (skip if content already has them)
    previously_links = []
    has_previously = 'Previously:' in content or 'See also:' in content
    if not has_previously:
        print("  Searching for Previously links...")
        previously_links = search_previously_links(title, content, dry_run)
        if previously_links:
            print(f"  Found {len(previously_links)} related articles")

    # Generate filename
    filename = f"post-{slugify(title)}.html"
    filepath = SCRIPT_DIR / "posts" / filename

    if dry_run:
        print(f"  [Dry run] Would create: {filename}")
        print(f"  [Dry run] Would add to index.html")
        return filename

    # Generate HTML
    print("  Generating HTML file...")
    html = generate_html(post, edit_result, previously_links=previously_links)

    # Write file (ensure posts directory exists)
    filepath.parent.mkdir(exist_ok=True)
    filepath.write_text(html)
    print(f"  Created: {filename}")

    # Update index
    update_index(filename, title)

    return filename


def load_posts(input_file):
    """Load posts from JSON file."""
    if not input_file.exists():
        return None

    try:
        with open(input_file) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        return None


def fetch_pending_posts(save_to=None):
    """Fetch pending posts directly from WordPress REST API."""
    if not WP_USER or not WP_APP_PASSWORD:
        print("Error: WP_USER and WP_APP_PASSWORD environment variables required.")
        print("\nSet them with:")
        print('  export WP_USER="your-username"')
        print('  export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"')
        return None

    # Create Basic Auth header
    credentials = f"{WP_USER}:{WP_APP_PASSWORD}"
    auth_header = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "User-Agent": "BoingBoingTools/1.0"
    }

    print(f"Fetching pending posts from {WP_SITE}...")

    try:
        response = requests.get(
            f"{WP_SITE}/wp-json/wp/v2/posts",
            params={"status": "pending", "context": "edit", "per_page": 50},
            headers=headers,
            timeout=30
        )

        if response.status_code == 401:
            print("Error: Authentication failed. Check your WP_USER and WP_APP_PASSWORD.")
            return None

        if response.status_code == 403:
            print("Error: Access forbidden. Your IP may need to be whitelisted in Cloudflare.")
            return None

        response.raise_for_status()
        wp_posts = response.json()

        # Convert to our format
        posts = []
        for wp in wp_posts:
            posts.append({
                "id": str(wp.get("id", "")),
                "title": wp.get("title", {}).get("raw", "Untitled"),
                "author": wp.get("yoast_head_json", {}).get("author", "Unknown"),
                "content": wp.get("content", {}).get("raw", ""),
                "editUrl": f"{WP_SITE}/wp-admin/post.php?post={wp.get('id')}&action=edit"
            })

        print(f"Found {len(posts)} pending post(s)")

        # Optionally save to file
        if save_to and posts:
            with open(save_to, 'w') as f:
                json.dump(posts, f, indent=2)
            print(f"Saved to {save_to}")

        return posts

    except requests.exceptions.Timeout:
        print("Error: Request timed out. Try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Process pending WordPress posts")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT,
                        help=f"JSON file with posts (default: {DEFAULT_INPUT.name})")
    parser.add_argument("--cached", "-c", action="store_true",
                        help="Use cached posts from JSON file instead of fetching fresh")
    parser.add_argument("--process", "-p", help="Posts to process: comma-separated numbers or 'all'")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview without creating files")
    args = parser.parse_args()

    # Fetch fresh from API by default, or load from cached file if --cached
    if args.cached:
        posts = load_posts(args.input)
    else:
        posts = fetch_pending_posts(save_to=args.input)

    if posts is None:
        # API fetch failed
        if args.cached:
            print(f"No cached posts file found at {args.input}")
            print("Run without --cached to fetch fresh from WordPress API.")
        else:
            print("\nFailed to fetch posts from WordPress API.")
            print("\nMake sure these environment variables are set (or add to .env):")
            print('  WP_USER="your-username"')
            print('  WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"')
        return

    if len(posts) == 0:
        print("\nNo pending posts in WordPress.")
        return

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

        # Filter to posts with content
        valid_indices = [i for i in indices if 0 <= i < len(posts) and posts[i].get("content")]
        skipped = len(indices) - len(valid_indices)

        if skipped:
            print(f"\nSkipping {skipped} post(s) without content.")

        if not valid_indices:
            print("No posts with content to process.")
            return

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Processing {len(valid_indices)} post(s)...")

        created = []
        for i in valid_indices:
            result = process_post(posts[i], args.dry_run)
            if result:
                created.append(result)

        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Done! Created {len(created)} file(s).")
    else:
        print("\nTo process posts, run:")
        print("  python3 pending.py --process 1,3,5    # Process specific posts")
        print("  python3 pending.py --process all      # Process all posts")
        print("  python3 pending.py --dry-run --process all  # Preview without creating")


if __name__ == "__main__":
    main()
