#!/usr/bin/env python3
"""
Automated Pending Posts Processor

Processes pending posts from WordPress (via browser console JSON),
copy edits with Claude API, generates HTML files with SEO metadata,
and updates index.html.

Usage:
    python3 pending.py                      # Show browser script instructions
    python3 pending.py --input posts.json   # Process posts from JSON file
    python3 pending.py --process 1,3,5      # Process specific posts from JSON
    python3 pending.py --process all        # Process all posts from JSON
    python3 pending.py --dry-run            # Preview without creating files
"""

import os
import sys
import re
import json
import argparse
from html import unescape
from pathlib import Path

from anthropic import Anthropic

# Configuration
SCRIPT_DIR = Path(__file__).parent
INDEX_FILE = SCRIPT_DIR / "index.html"
DEFAULT_INPUT = SCRIPT_DIR / "pending-posts.json"

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
            "copy_edits_made": "Dry run - no edits made"
        }

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    client = Anthropic(api_key=api_key)

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


def generate_html(post, edit_result, source_url=""):
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
    else:
        previously_html = '''
<div class="previously" id="previously">
<strong>Previously:</strong>
<ul>
<li>[Add related boingboing.net articles]</li>
</ul>
</div>'''

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
{previously_html}
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

    new_entry = f"    {{ file: '{filename}', title: '{escaped_title}' }},\n"

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


def main():
    parser = argparse.ArgumentParser(description="Process pending WordPress posts")
    parser.add_argument("--input", "-i", type=Path, default=DEFAULT_INPUT,
                        help=f"JSON file with posts (default: {DEFAULT_INPUT.name})")
    parser.add_argument("--process", "-p", help="Posts to process: comma-separated numbers or 'all'")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview without creating files")
    args = parser.parse_args()

    # Check for input file
    posts = load_posts(args.input)

    if not posts:
        print("PENDING POSTS PROCESSOR")
        print("═" * 60)
        print("\nNo posts file found. To get started:")
        print(f"\n1. Run this script in your browser console on the WordPress")
        print("   pending posts page (Posts → All Posts → Pending):\n")
        print(BROWSER_SCRIPT)
        print(f"\n2. Copy the JSON output and save to: {args.input}")
        print(f"\n3. Run: python3 pending.py --process all")
        print("   Or:   python3 pending.py --dry-run --process all")
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
