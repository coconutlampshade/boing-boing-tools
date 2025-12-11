#!/usr/bin/env python3
import json
import sys
from datetime import datetime

# Read stats and posts from temp files
with open("/tmp/stats.json") as f:
    stats_data = json.load(f)
with open("/tmp/posts.json") as f:
    posts_data = json.load(f)

# Build post ID to author mapping and count posts per author from the posts API
post_to_author = {}
author_post_counts = {}
for post in posts_data.get("posts", []):
    post_id = post["ID"]
    author_name = post.get("author", {}).get("name", "Unknown")
    post_to_author[post_id] = author_name
    author_post_counts[author_name] = author_post_counts.get(author_name, 0) + 1

# Get the month key from stats data (first key in days dict)
month_key = list(stats_data["days"].keys())[0]
authors_data = stats_data["days"][month_key]["authors"]

# Format the month name
month_date = datetime.strptime(month_key, "%Y-%m-%d")
month_name = month_date.strftime("%B %Y")

print("=" * 70)
print("BOING BOING AUTHOR PERFORMANCE REPORT - {}".format(month_name))
print("=" * 70)
print()

# Build views per author from stats (use total views from stats API, not summing posts)
results = []
for author in authors_data:
    name = author["name"]

    # Skip "Boing Boing" and "Boing Boing's Shop" as authors
    if name in ["Boing Boing", "Boing Boing's Shop"]:
        continue

    # Use actual post count from posts API
    num_posts = author_post_counts.get(name, 0)

    if num_posts == 0:
        continue

    # Use total views from stats API (this is accurate)
    total_views = author["views"]
    avg_views = total_views / num_posts

    results.append((name, num_posts, total_views, avg_views))

# Sort by average views descending
results.sort(key=lambda x: x[3], reverse=True)

header = "{:<25} {:>8} {:>14} {:>16}".format("Author", "Posts", "Total Views", "Avg Views/Post")
print(header)
print("-" * 70)

for name, num_posts, total_views, avg_views in results:
    row = "{:<25} {:>8} {:>14,} {:>16,.0f}".format(name, num_posts, total_views, avg_views)
    print(row)

print()
print("=" * 70)
