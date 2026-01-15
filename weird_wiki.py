#!/usr/bin/env python3
"""
Weird Wikipedia Articles fetcher.

Pulls random articles from weird.html (a curated list of dark/strange Wikipedia articles).

Usage:
  python3 weird_wiki.py                      # Show 10 random weird articles
  python3 weird_wiki.py "Article"            # Fetch full content for an article
  python3 weird_wiki.py url                  # Fetch content from a Wikipedia URL
  python3 weird_wiki.py --preview "Article"  # Quick 2-3 sentence summary
  python3 weird_wiki.py -p "Article"         # Short form of --preview
  python3 weird_wiki.py --reset              # Reshuffle and start from beginning
  python3 weird_wiki.py --remaining          # Show how many unseen articles remain
"""
import urllib.request
import urllib.parse
import json
import re
import sys
import random
from html import unescape
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
ARCHIVE_FILE = SCRIPT_DIR / "weird.html"
INDEX_FILE = Path.home() / '.weird_wiki_index.json'


def parse_archive():
    """Parse weird.html and extract articles."""
    if not ARCHIVE_FILE.exists():
        print(f"Error: {ARCHIVE_FILE} not found")
        sys.exit(1)

    html = ARCHIVE_FILE.read_text()

    # Pattern to match: <a href="URL"><b>Title</b></a>: Description
    pattern = r'<a href="(https://en\.wikipedia\.org/wiki/[^"]+)"[^>]*><b>([^<]+)</b></a>(?:<sup>.*?</sup>)?:\s*([^<]+)'

    articles = []
    seen = set()

    for match in re.finditer(pattern, html):
        url, title, desc = match.groups()
        title = unescape(title.strip())
        desc = unescape(desc.strip().rstrip('.'))

        if title in seen:
            continue
        seen.add(title)

        # Clean up description
        if len(desc) > 150:
            desc = desc[:147] + '...'

        articles.append({
            'url': url,
            'title': title,
            'desc': desc
        })

    return articles


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
    """Fetch article content via Wikipedia API."""
    encoded = urllib.parse.quote(title.replace(' ', '_'))
    api_url = f'https://en.wikipedia.org/api/rest_v1/page/html/{encoded}'
    req = urllib.request.Request(api_url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; BoingBoingBot/1.0)',
        'Accept': 'text/html'
    })
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
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
    """Build a shuffled index from the archive."""
    print("Building article index from weird.html...")
    articles = parse_archive()

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


def list_weird_articles(count=10):
    """Show the next N articles from the shuffled index."""
    index_data = load_index()

    position = index_data['position']
    total = index_data['total']
    articles = index_data['articles']

    if position >= total:
        print(f"You've seen all {total} articles!")
        print("Run with --reset to reshuffle and start over.")
        return

    end_pos = min(position + count, total)
    batch = articles[position:end_pos]

    index_data['position'] = end_pos
    save_index(index_data)

    remaining = total - end_pos

    print("WEIRD WIKIPEDIA ARTICLES")
    print(f"────────────────────────  ({remaining} remaining)")
    for i, article in enumerate(batch, 1):
        print(f"{i}. {article['title']}")
        print(f"   {article['desc']}.")
        print(f"   {article['url']}")
        print()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == '--reset':
            reset_index()
        elif arg == '--remaining':
            show_remaining()
        elif arg in ('--preview', '-p'):
            if len(sys.argv) > 2:
                query = ' '.join(sys.argv[2:])
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
                print("Usage: weird_wiki.py --preview \"Article Title\"")
        else:
            query = ' '.join(sys.argv[1:])
            if 'wikipedia.org/wiki/' in query:
                title = extract_title_from_url(query)
                if title:
                    print(f"=== {title} ===\n")
                    print(fetch_article_content(title))
                else:
                    print("Could not parse Wikipedia URL")
            else:
                print(f"=== {query} ===\n")
                print(fetch_article_content(query))
    else:
        list_weird_articles()
