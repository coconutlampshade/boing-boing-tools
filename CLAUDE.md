# Boing Boing Tools

## Menu Command

When the user types `menu`, display this list of available tools:

```
BOING BOING TOOLS
─────────────────
1. memeorandum   — Fetch 20 headlines from memeorandum.com, select articles for posts
2. random-wiki   — Show 20 random articles from Wikipedia's Unusual Articles, select for posts
3. writepost     — Write a post from a URL or topic the user provides
4. copyedit      — Copy edit a contributor post (paste HTML), generate metadata, add to index
5. pending       — Review and copy edit all pending posts from WordPress
6. author-stats  — Run author performance report (posts, views, evergreen metrics)
```

---

# Memeorandum Script

This script scrapes the 20 most recent headlines from memeorandum.com/river.

## Workflow

1. Run the `memeorandum` script to display the 20 most recent headlines with numbered options
2. User selects which articles they want posts about (e.g., "3, 7, 12")
3. For each selected article, fetch the full article content and generate a ~250 word blog post

---

# Random Wiki Script

This tool displays 20 random articles from Wikipedia's Unusual Articles page for the user to select for blog posts.

## Source

Articles MUST be pulled exclusively from: https://en.wikipedia.org/wiki/Wikipedia:Unusual_articles

Do NOT use Wikipedia's general random article feature. Only articles listed on the Unusual Articles page qualify.

## Workflow

1. Run `python3 /Users/mark/Desktop/boing-boing-tools/random_wiki.py` to fetch and display 20 random unusual articles
   - Numbered list (1-20)
   - Article title
   - At least one full sentence describing what makes the article unusual/interesting (not a fragment)
   - URL
2. User selects which articles they want posts about (e.g., "3, 7, 12")
3. For each selected article, fetch the full content and generate a ~250 word blog post

## Example Output Format

```
UNUSUAL WIKIPEDIA ARTICLES
──────────────────────────
1. Tarrare
   Tarrare was an 18th-century French showman with an insatiable appetite who could eat enormous quantities of meat, corks, stones, and live animals.
   https://en.wikipedia.org/wiki/Tarrare

2. Euthanasia Coaster
   A Lithuanian engineer designed a hypothetical roller coaster intended to kill its passengers through prolonged cerebral hypoxia caused by extreme g-forces.
   https://en.wikipedia.org/wiki/Euthanasia_Coaster

[...continues to 20]
```

---

# Copy Edit Tool

This tool processes contributor posts — copy editing for clarity and correctness while preserving the author's voice, then generating all required metadata.

## Workflow

1. User types `copyedit` and pastes the contributor's rendered HTML (with images, hyperlinks, formatting)
2. Copy edit the post:
   - Fix grammar, spelling, punctuation
   - Improve clarity and flow
   - Tighten wordy passages
   - Preserve the author's voice and style
   - Keep all images, hyperlinks, and formatting intact
   - Apply the "Avoiding AI-Sounding Writing" rules to edits
3. Show the edited post to the user for approval
4. Once approved, ask for:
   - Source URL (if not already in the post)
   - Author name (for the filename)
5. Generate all metadata (headlines, tags, meta descriptions, etc.)
6. Create the HTML post file and add to the index

## Copy Editing Guidelines

When editing contributor posts:

### DO:
- Fix objective errors (typos, grammar, punctuation)
- Tighten verbose passages
- Clarify confusing sentences
- Improve sentence rhythm and flow
- Remove filler phrases and empty words
- Ensure facts are stated clearly

### DON'T:
- Change the author's opinions or positions
- Alter their distinctive voice or style
- Remove personality or humor
- Add your own commentary
- Over-polish into generic prose
- Remove quirks that make the writing distinctive

### Preserve:
- All hyperlinks (keep href attributes intact)
- All images (keep src, alt, and any captions)
- Formatting (bold, italic, lists, blockquotes)
- Embedded media (YouTube, tweets, etc.)
- The author's word choices when they're intentional
- Regional spelling variations (British vs American)

## Output Format

The HTML post file should include:
- The edited post body with all original formatting, links, and images preserved
- Previously section (MUST search site:boingboing.net for real related articles — broaden search terms until you find matches, never fabricate URLs)
- Source URL
- 5 headline options (70 chars max, sentence case)
- Category tags
- Yoast focus keyphrase
- 5 meta headlines (60 chars max)
- 5 meta descriptions (120 chars max)

---

# Pending Posts Processor

Automated tool to fetch pending posts from WordPress, copy edit with Claude, and generate HTML files.

## Setup (One-Time)

1. Generate a WordPress Application Password:
   - WordPress Admin → Users → Profile → Application Passwords
   - Enter name: "Boing Boing Tools"
   - Click "Add New Application Password"
   - Copy the password (shown only once)

2. Set environment variables:
   ```bash
   export WP_USERNAME="your-wordpress-username"
   export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

## Usage

```bash
# List all pending posts
python3 pending.py

# Process specific posts (creates HTML files + updates index)
python3 pending.py --process 1,3,5

# Process all pending posts
python3 pending.py --process all

# Preview without creating files
python3 pending.py --dry-run --process all
```

## What It Does

1. Fetches all pending posts from WordPress REST API
2. Displays numbered list with title, author, word count
3. For selected posts:
   - Sends to Claude for copy editing
   - Generates SEO metadata (headlines, tags, descriptions)
   - Creates HTML file with copy buttons
   - Adds entry to index.html

## Manual Fallback

If API access fails, use browser console script:

```javascript
const posts = [];
document.querySelectorAll('tr.iedit').forEach(row => {
  const titleLink = row.querySelector('.row-title');
  const authorEl = row.querySelector('.author a');
  if (titleLink) {
    posts.push({
      title: titleLink.textContent.trim(),
      author: authorEl ? authorEl.textContent.trim() : 'Unknown'
    });
  }
});
console.log(JSON.stringify(posts, null, 2));
```

Then manually copy content from each post's edit page.

---

## Blog Post Style

Write in the style of Boing Boing - conversational, witty, slightly irreverent, with a sense of wonder or outrage as appropriate. The tone should be:
- Engaging and opinionated
- Accessible to general readers
- Wry humor where appropriate
- Critical thinking about power structures

## Blog Post Format

Each post should:
- Be approximately 250 words
- Credit the original source naturally within the text (e.g., "As reported in the New York Times, ..." or "According to Politico, ...")
- Have a catchy headline
- Get to the interesting/important point quickly
- NO inline hyperlinks in the post body—the editor will add links manually

## Example Attribution Styles

Lead with the interesting information, put attribution at the end. Do NOT include markdown links in the post body:

- "The agency plans to cut 500 jobs by March, according to The Washington Post..."
- "Lawmakers are preparing a new bill that would..., Axios reports."
- "Climate scientists have discovered a troubling trend, according to The Guardian..."
- "The company knowingly chose revenue over users, a Reuters investigation reveals."

DON'T write: "According to CNN, prosecutors say Cole placed the bombs..."
DO write: "Cole placed the bombs on the night of January 5, say prosecutors, according to CNN."

The URL goes only in the Source section at the bottom. The editor will add the hyperlink where appropriate.

## Avoiding AI-Sounding Writing

To keep posts sounding human, follow these rules:

### Words and Phrases to AVOID
- delve, tapestry, multifaceted, underscore, leverage, embark, navigate, unlock, foster, realm, myriad, plethora, testament, pivotal, encompasses, intricacies
- "marking a pivotal moment in..."
- "representing a significant shift toward..."
- "highlighting the importance of..."
- "underscoring the significance of..."
- "In today's ever-evolving world..."
- "In the realm of..."
- "It's important to note that..."
- "This serves as a reminder that..."
- "At its core..."
- "rich cultural heritage," "vibrant community," "enduring legacy," "cutting-edge," "revolutionary," "unprecedented"
- "because nothing says X like Y"
- "The timing feels notable"
- "It's worth noting"
- "What's particularly interesting"

### Structural Rules
- Em dashes must have a space before and after ( — not —)
- Don't overuse em dashes for artificial drama
- Vary paragraph lengths (some short, some longer)
- Don't always use three examples — two or four is fine
- Avoid "not only X but also Y" constructions
- Don't hedge everything with "it can be argued" or "one might say"
- Skip significance inflation — don't tell readers how important something is, just show them

### What TO Do
- Use concrete, specific details (dates, names, numbers)
- Take actual positions rather than hedging
- Let prose have texture — short sentences, longer ones, fragments
- Trust the reader to understand significance without being told
- State facts directly instead of attributing to vague "experts"

### Avoiding "Smooth but Empty" Writing
Avoid lines that sound good but lack substance, specificity, or verifiable content. This prevents "drift" — places where writing becomes vague or platitudinous.

- Every sentence should contain specific, checkable information or a genuine insight
- If a sentence doesn't add concrete facts, cut it
- No filler phrases that pad word count without adding information
- When in doubt, ask: "What specific claim is this sentence making?"

### Sentence Rhythm and Flow
- Avoid too many short, punchy sentences in a row — it becomes exhausting to read
- Mix sentence lengths: follow a short sentence with a longer one that breathes
- Use conjunctions (and, but, so, because) to connect ideas rather than always starting new sentences
- Let some paragraphs unspool a bit — not everything needs to be staccato
- Occasional longer sentences with clauses and asides create a more natural, conversational rhythm
- Read it back: if it sounds like a series of punches, smooth it out

## Full Post Output Format

Each post (from memeorandum, random-wiki, and writeposts) should include all of the following sections:

### 1. Post Body
The ~250 word blog post with attribution. Mention the publication by name in plain text. Do NOT include any markdown links—the editor adds links manually.

### 2. Source
`Source: [full URL]`

### 3. Headlines (70 characters max)
Provide 5 headline options, each 70 characters or fewer. Use sentence case, NOT title case.
- CORRECT: "Scientists discover new way to predict earthquakes"
- WRONG: "Scientists Discover New Way To Predict Earthquakes"

### 4. Category Tags
3-5 tags separated by commas (not bullet points), ordered broadest to most specific:
1. Primary broad category (news, technology, etc.)
2. Secondary categories (health, science, etc.)
3. Specific topic tags (microplastics, climate change, etc.)
4. Relevant institutions/organizations
5. Key people mentioned

### 5. Meta Headlines (60 characters max)
Provide 5 meta headline options, each 60 characters or fewer. Use sentence case, NOT title case (same rule as headlines).

### 6. Meta Descriptions (120 characters max)
Provide 5 meta description options, each 120 characters or fewer.

### Example Output Structure

```
## [Headline]

[Post body with attribution like "according to Publication Name, the key detail..." - no inline links]

Source: https://example.com/article

HEADLINES (70 characters max)
1. First headline option
2. Second headline option
3. Third headline option
4. Fourth headline option
5. Fifth headline option

CATEGORY TAGS
news, politics, specific topic, Organization Name, Person Name

META HEADLINES (60 characters max)
1. First meta headline
2. Second meta headline
3. Third meta headline
4. Fourth meta headline
5. Fifth meta headline

META DESCRIPTIONS (120 characters max)
1. First meta description that summarizes the post in under 120 characters
2. Second meta description option
3. Third meta description option
4. Fourth meta description option
5. Fifth meta description option
```
