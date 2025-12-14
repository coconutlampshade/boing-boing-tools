#!/usr/bin/env python3
"""
Random Wikipedia Unusual Articles fetcher.

Usage:
  python3 random_wiki.py                      # Show next 20 unusual articles
  python3 random_wiki.py "Article"            # Fetch full content for an article
  python3 random_wiki.py url                  # Fetch content from a Wikipedia URL
  python3 random_wiki.py --preview "Article"  # Quick 2-3 sentence summary
  python3 random_wiki.py -p "Article"         # Short form of --preview
  python3 random_wiki.py --refresh            # Rebuild the article index
  python3 random_wiki.py --reset              # Reshuffle and start from beginning
  python3 random_wiki.py --remaining          # Show how many unseen articles remain
"""
import urllib.request
import urllib.parse
import json
import re
import sys
import os
import random
from html import unescape
from pathlib import Path
from datetime import datetime

INDEX_FILE = Path.home() / '.random_wiki_index.json'


def fetch_article_summary(title):
    """Fetch a quick 2-3 sentence summary via Wikipedia API."""
    encoded = urllib.parse.quote(title.replace(' ', '_'))
    api_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}'
    req = urllib.request.Request(api_url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; BoingBoingBot/1.0)',
        'Accept': 'application/json'
    })
    try:
        response = urllib.request.urlopen(req).read().decode('utf-8')
        data = json.loads(response)
        extract = data.get('extract', 'No summary available.')
        url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
        return extract, url
    except urllib.error.HTTPError as e:
        return f"Error fetching summary: {e.code} {e.reason}", ""


def fetch_article_content(title):
    """Fetch article content via Wikipedia API (avoids 403 errors)."""
    encoded = urllib.parse.quote(title.replace(' ', '_'))
    api_url = f'https://en.wikipedia.org/api/rest_v1/page/html/{encoded}'
    req = urllib.request.Request(api_url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; BoingBoingBot/1.0)',
        'Accept': 'text/html'
    })
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
        # Strip HTML tags for plain text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = unescape(text)
        return text
    except urllib.error.HTTPError as e:
        return f"Error fetching article: {e.code} {e.reason}"


def extract_title_from_url(url):
    """Extract article title from Wikipedia URL."""
    match = re.search(r'wikipedia\.org/wiki/([^#?]+)', url)
    if match:
        return urllib.parse.unquote(match.group(1).replace('_', ' '))
    return None


def build_index():
    """Fetch all unusual articles and build a shuffled index."""
    print("Building article index from Wikipedia:Unusual_articles...")
    req = urllib.request.Request(
        'https://en.wikipedia.org/wiki/Wikipedia:Unusual_articles',
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    html = urllib.request.urlopen(req).read().decode('utf-8')

    # The page uses tables: <td><b><a href="/wiki/...">Title</a></b></td><td>Description</td>
    pattern = r'<td><b><a href="/wiki/([^":#]+)"[^>]*>([^<]+)</a></b>\s*</td>\s*<td>([^<]+)'

    articles, seen = [], set()
    matches = re.findall(pattern, html)
    for slug, title, desc in matches:
        if title in seen or len(title) < 2 or len(desc.strip()) < 10:
            continue
        seen.add(title)
        desc = unescape(desc.strip().rstrip('.'))
        # Get first complete sentence if possible
        if '. ' in desc:
            desc = desc.split('. ')[0]
        if len(desc) > 150:
            desc = desc[:147] + '...'
        articles.append({
            'slug': slug,
            'title': title,
            'desc': desc
        })

    # Shuffle the articles
    random.shuffle(articles)

    index_data = {
        'articles': articles,
        'position': 0,
        'created': datetime.now().isoformat(),
        'total': len(articles)
    }

    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, indent=2)

    print(f"Index created with {len(articles)} articles.")
    return index_data


def load_index():
    """Load the index, creating it if it doesn't exist."""
    if not INDEX_FILE.exists():
        return build_index()

    with open(INDEX_FILE, 'r') as f:
        return json.load(f)


def save_index(index_data):
    """Save the index with updated position."""
    with open(INDEX_FILE, 'w') as f:
        json.dump(index_data, f, indent=2)


def reset_index():
    """Reshuffle the index and reset position to 0."""
    index_data = load_index()
    random.shuffle(index_data['articles'])
    index_data['position'] = 0
    index_data['created'] = datetime.now().isoformat()
    save_index(index_data)
    print(f"Index reshuffled. {index_data['total']} articles ready.")


def show_remaining():
    """Show how many unseen articles remain."""
    index_data = load_index()
    remaining = index_data['total'] - index_data['position']
    print(f"{remaining} unseen articles remaining out of {index_data['total']} total.")
    if remaining == 0:
        print("Run with --reset to reshuffle and start over.")


def list_unusual_articles(count=20):
    """Show the next N articles from the shuffled index."""
    index_data = load_index()

    position = index_data['position']
    total = index_data['total']
    articles = index_data['articles']

    # Check if we've exhausted the list
    if position >= total:
        print(f"You've seen all {total} articles!")
        print("Run with --reset to reshuffle and start over.")
        return

    # Get the next batch
    end_pos = min(position + count, total)
    batch = articles[position:end_pos]

    # Update position
    index_data['position'] = end_pos
    save_index(index_data)

    remaining = total - end_pos

    print("UNUSUAL WIKIPEDIA ARTICLES")
    print(f"──────────────────────────  ({remaining} remaining)")
    for i, article in enumerate(batch, 1):
        print(f"{i}. {article['title']}")
        print(f"   {article['desc']}.")
        print(f"   https://en.wikipedia.org/wiki/{article['slug']}")
        print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        # Handle flags
        if arg == '--refresh':
            build_index()
        elif arg == '--reset':
            reset_index()
        elif arg == '--remaining':
            show_remaining()
        elif arg in ('--preview', '-p'):
            if len(sys.argv) > 2:
                query = ' '.join(sys.argv[2:])
                # Handle URL or title
                if 'wikipedia.org/wiki/' in query:
                    title = extract_title_from_url(query)
                else:
                    title = query
                if title:
                    summary, url = fetch_article_summary(title)
                    print(f"=== {title} ===\n")
                    print(summary)
                    if url:
                        print(f"\n{url}")
                else:
                    print("Could not parse input")
            else:
                print("Usage: random_wiki.py --preview \"Article Title\"")
        else:
            # Check if it's a URL or article title
            query = ' '.join(sys.argv[1:])
            if 'wikipedia.org/wiki/' in query:
                title = extract_title_from_url(query)
                if title:
                    print(f"=== {title} ===\n")
                    print(fetch_article_content(title))
                else:
                    print("Could not parse Wikipedia URL")
            else:
                # Treat as article title
                print(f"=== {query} ===\n")
                print(fetch_article_content(query))
    else:
        list_unusual_articles()
