#!/usr/bin/env python3
"""
Random Wikipedia Unusual Articles fetcher.

Usage:
  python3 random_wiki.py              # List 20 random unusual articles
  python3 random_wiki.py "Article"    # Fetch full content for an article
  python3 random_wiki.py url          # Fetch content from a Wikipedia URL
"""
import urllib.request
import urllib.parse
import re
import sys
import random
from html import unescape


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


def list_unusual_articles():
    """Fetch and display 20 random unusual articles."""
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
        desc = unescape(desc.strip().rstrip('.'))[:100]
        articles.append((slug, title, desc))

    count = min(20, len(articles))
    if count == 0:
        print("No articles found - page structure may have changed")
    else:
        print("UNUSUAL WIKIPEDIA ARTICLES")
        print("──────────────────────────")
        for i, (slug, title, desc) in enumerate(random.sample(articles, count), 1):
            print(f'{i}. {title}')
            print(f'   {desc}.')
            print(f'   https://en.wikipedia.org/wiki/{slug}')
            print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = ' '.join(sys.argv[1:])
        # Check if it's a URL
        if 'wikipedia.org/wiki/' in arg:
            title = extract_title_from_url(arg)
            if title:
                print(f"=== {title} ===\n")
                print(fetch_article_content(title))
            else:
                print("Could not parse Wikipedia URL")
        else:
            # Treat as article title
            print(f"=== {arg} ===\n")
            print(fetch_article_content(arg))
    else:
        list_unusual_articles()
