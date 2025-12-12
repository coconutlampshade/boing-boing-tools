#!/usr/bin/env python3
import urllib.request
import re
import random
from html import unescape

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
    for i, (slug, title, desc) in enumerate(random.sample(articles, count), 1):
        print(f'{i}. {title}')
        print(f'   {desc}.')
        print(f'   https://en.wikipedia.org/wiki/{slug}')
        print()
