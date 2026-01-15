# Boing Boing Tools - To-Do List

## Waiting On

### Cloudflare Whitelist - Better Solution
**Status:** Waiting on sysadmin

Currently whitelisted by IP (76.86.25.84), but sysadmin offered a more robust solution using User-Agent or custom header.

**Options:**
1. **User-Agent whitelist** (easiest):
   ```
   (http.user_agent eq "BoingBoingTools/1.0")
   ```

2. **Custom header** (more secure):
   Sysadmin provides a secret token, we add header like:
   ```
   X-BB-Secret: <token-he-provides>
   ```

**What we send:**
```
GET https://boingboing.net/wp-json/wp/v2/posts?status=pending&context=edit
Headers:
  User-Agent: BoingBoingTools/1.0
  Authorization: Basic <base64 credentials>
```

Once sysadmin decides, update `pending.py` headers dict accordingly.

---

## Pending

### Add Publish-Back Feature
After copy editing, allow publishing edited posts back to WordPress:
```bash
python3 pending.py --publish post-filename.html
```
Would update the WordPress post via REST API.

---

### Clean Up index.html
Review the posts list in index.html and remove entries for posts that have already been published to Boing Boing.

---

### Improve Previously Links Search
Current approach uses Claude to search for related articles. Could improve by:
- Using direct Google site search API
- Caching previous searches
- Better keyword extraction from post content

---

## Completed

- [x] Cloudflare IP whitelist (76.86.25.84) - sysadmin added it
- [x] Test WordPress API access - works!
- [x] Add --fetch flag to pending.py for direct API calls
- [x] Fix copy button syntax in HTML templates (add `this` parameter)
- [x] Update Claude prompt with aggressive copy editing guidelines
- [x] Add YouTube Shorts URL conversion
- [x] Add Previously section search function
- [x] Move posts to `posts/` subdirectory
- [x] Add weird_wiki.py for dark/strange articles

---

## Quick Reference

### Fetch and process pending posts:
```bash
export WP_USER="Mark Frauenfelder"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
python3 pending.py --fetch --process all
```

### Process specific posts:
```bash
python3 pending.py --fetch --process 1,3,5
```

### Dry run (preview without creating files):
```bash
python3 pending.py --fetch --dry-run --process all
```
