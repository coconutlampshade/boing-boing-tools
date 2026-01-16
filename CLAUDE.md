# Boing Boing Tools

## Menu Command

When the user types `menu`, display this list of available tools:

```
BOING BOING TOOLS
─────────────────
1. memeorandum   — Fetch 20 headlines from memeorandum.com, select articles for posts
2. random-wiki   — Show 20 random articles from Wikipedia's Unusual Articles, select for posts
3. weird         — Show 10 random dark/strange Wikipedia articles, select for posts
4. writepost     — Write a post from a URL or topic the user provides
5. copyedit      — Copy edit a contributor post (paste HTML), generate metadata, add to index
6. pending       — Review and copy edit all pending posts from WordPress
7. newsletter    — Generate daily newsletter (full posts, noon-to-noon)
8. digest        — Generate daily digest (excerpts with "Read more" links)
9. author-stats  — Run author performance report (posts, views, evergreen metrics)
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

# Weird Wiki Script

This tool displays 10 random articles from weird.html — a curated collection of dark, strange, and macabre Wikipedia articles.

## Source

Articles are pulled from the local file `weird.html`, which contains ~500+ curated Wikipedia articles covering mysteries, disasters, crimes, oddities, and strange history.

## Workflow

1. Run `python3 weird_wiki.py` to fetch and display 10 random weird articles
   - Numbered list (1-10)
   - Article title
   - Brief description
   - URL
2. User selects which articles they want posts about (e.g., "2, 5, 8")
3. For each selected article, fetch the full content and generate a ~250 word blog post

## Example Output Format

```
WEIRD WIKIPEDIA ARTICLES
────────────────────────  (490 remaining)
1. Batavia
   One of the most insane stories of shipwreck and mutiny you'll ever read!
   https://en.wikipedia.org/wiki/Batavia_(1628_ship)

2. Carl Tanzler
   Doctor who preserved and kept the corpse of a former patient.
   https://en.wikipedia.org/wiki/Carl_Tanzler

[...continues to 10]
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
- Tighten verbose passages aggressively — concision takes priority over preserving exact phrasing
- Restructure wordy sentences (e.g., "According to a blog post he published earlier this week, X plans on bringing..." → "X plans to bring..., he said in a recent blog post.")
- Clarify confusing sentences
- Improve sentence rhythm and flow
- Remove filler phrases and empty words
- Ensure facts are stated clearly
- Remove gratuitous profanity

### DON'T:
- Change the author's opinions or positions
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

### URL Conversions:
- Always convert YouTube Shorts URLs to regular URLs: `https://www.youtube.com/shorts/VIDEO_ID` → `https://youtu.be/VIDEO_ID`

## Output Format

The HTML post file should include:
- The edited post body with all original formatting, links, and images preserved
- Previously section (MUST search site:boingboing.net for real related articles — broaden search terms until you find matches, never fabricate URLs)
- Source URL
- 5 headline options (70 chars max, sentence case)
- Category tags
- Yoast focus keyphrase
- 5 meta headlines (60 chars max)
- 5 meta descriptions (at least 100 characters and 120 chars max)

---

# Pending Posts Processor

Automated tool to process pending posts from WordPress, copy edit with Claude, and generate HTML files.

## Setup

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
# Show instructions and browser script
python3 pending.py

# Process specific posts (creates HTML files + updates index)
python3 pending.py --process 1,3,5

# Process all pending posts
python3 pending.py --process all

# Preview without creating files
python3 pending.py --dry-run --process all
```

## Workflow

1. Go to WordPress Admin → Posts → All Posts → filter by "Pending"
2. Run `python3 pending.py` to see the browser script
3. Copy/paste the script into browser console
4. Save the JSON output to `pending-posts.json`
5. Run `python3 pending.py --process all`

## What It Does

For each selected post:
- Sends to Claude for copy editing
- Generates SEO metadata (5 headlines, 5 meta headlines, 5 meta descriptions, tags, focus keyphrase)
- Creates HTML file with copy buttons
- Adds entry to index.html

---

# Newsletter Generator

Generates a daily newsletter with full post content from noon PT yesterday to noon PT today.

## Setup

Set environment variables:
```bash
export WP_USER="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Usage

```bash
python3 newsletter.py                    # Generate today's newsletter
python3 newsletter.py --date 2026-01-14  # Generate for a specific date
python3 newsletter.py --open             # Generate and open in browser
```

## What It Does

- Fetches published posts via WordPress REST API
- Filters to noon-to-noon Pacific time window
- Excludes "Boing Boing's Shop" posts
- Generates AI subhead and introduction using Claude
- Outputs styled HTML with full post content
- Saves to `newsletter_YYYY-MM-DD.html`

---

# Digest Generator

Generates a daily digest newsletter with excerpts and "Read more" links.

## Usage

```bash
python3 digest.py                    # Generate today's digest
python3 digest.py --date 2026-01-14  # Generate for a specific date
python3 digest.py --open             # Generate and open in browser
```

## What It Does

- Same WordPress API fetch as newsletter.py
- Extracts first 1-2 paragraphs as excerpt
- Adds "Read more →" link for each post
- Generates AI subhead and introduction
- Saves to `digest_YYYY-MM-DD.html`

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
- Include a hyperlink to the source in the post body where the attribution appears

## Example Attribution Styles

**Most important information goes first.** Lead with the interesting content, put attribution at the end. Include a hyperlink to the source where the attribution appears:

- "The agency plans to cut 500 jobs by March, according to The Washington Post..."
- "Lawmakers are preparing a new bill that would..., Axios reports."
- "Climate scientists have discovered a troubling trend, according to The Guardian..."
- "The company knowingly chose revenue over users, a Reuters investigation reveals."

DON'T write: "According to CNN, prosecutors say Cole placed the bombs..."
DO write: "Cole placed the bombs on the night of January 5, say prosecutors, according to CNN."

DON'T write: "According to The Conversation, natural fibers like cotton and linen contain millions of tiny cellulose molecules..."
DO write: "Natural fibers like cotton and linen contain millions of tiny cellulose molecules that naturally exist in coiled, crinkled shapes, reports The Conversation."

The URL also appears in the Source section at the bottom for easy copying.

## Avoiding AI-Sounding Writing

To keep posts sounding human, follow these rules:

### Words and Phrases to AVOID

**Overused AI Words:**
- delve, tapestry, multifaceted, underscore, leverage, embark, navigate, unlock, foster, realm, myriad, plethora, testament, pivotal, encompasses, intricacies
- rich cultural heritage, vibrant community, enduring legacy, cutting-edge, revolutionary, unprecedented
- key insight, nuanced, straightforward

**Significance Inflation Phrases:**
- "marking a pivotal moment in..."
- "representing a significant shift toward..."
- "highlighting the importance of..."
- "underscoring the significance of..."
- "In today's ever-evolving world..."
- "In the realm of..."
- "It's important to note that..."
- "This serves as a reminder that..."
- "At its core..."
- "because nothing says X like Y"
- "The timing feels notable"
- "It's worth noting"
- "What's particularly interesting"

**Therapist-Mode Phrases:**
- "and honestly?" (as sentence starter)
- "you're not imagining it"
- "you're not alone"
- "you're right to push back on that"
- "that really resonates with me"
- "do you want to sit with that for a while"
- "are you ready to go deeper"

**Artificial Drama/Signposting:**
- "here's the kicker"
- "and the best part?"
- "here's the breakdown:"
- "let's decode it plainly"
- "I'll be blunt"
- "let me be direct"

**Overused Sentence Structures:**
- "It's not X, it's Y" / "It's not just X, it's Y"
- "That kind of [distance/trust/loyalty]..."
- "There's something [adjective] about..."
- "The [noun] isn't [X] — it's [Y]"

**The "Quietly" Problem:**
Avoid using "quietly" or "quiet" to add false profundity:
- "quiet truth," "quiet confidence," "quiet power," "quiet defiance"
- "quietly revolutionary," "quietly devastating"
- Any "quietly [verb]ing" construction meant to sound deep

### Structural Rules
- Em dashes must have a space before and after ( — not —)
- Don't overuse em dashes for artificial drama
- Vary paragraph lengths (some short, some longer)
- Don't always use three examples — two or four is fine
- Avoid "not only X but also Y" constructions
- Don't hedge everything with "it can be argued" or "one might say"
- Skip significance inflation — don't tell readers how important something is, just show them
- Don't use rapid-fire short sentences to create fake punch: "He knew. She saw. They understood." reads as AI
- Avoid compulsive signposting followed by verbose elaboration (announcing what you'll say, then saying it)

### Avoiding Sycophancy
AI often validates excessively or mirrors the user's framing too eagerly. Avoid:
- Starting responses by agreeing: "You're absolutely right..." "Great question..."
- Forced reassurance: "That makes total sense" "You're spot on"
- Mirroring emotion: "I can see why you'd feel that way"
- Over-acknowledging: "That's a really important point"
- Padding with agreement before making your actual point

### Metaphor Misuse
AI often uses metaphors that don't quite fit or feel forced:
- Don't force metaphors where plain language works better
- Avoid extended metaphors that collapse under scrutiny
- If a metaphor doesn't clarify, cut it
- Generic metaphors ("a tapestry of," "a symphony of," "a dance between") signal AI

### What TO Do
- Use concrete, specific details (dates, names, numbers)
- Take actual positions rather than hedging
- Let prose have texture — short sentences, longer ones, fragments
- Trust the reader to understand significance without being told
- State facts directly instead of attributing to vague "experts"
- Be specific rather than profound — facts beat philosophy

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
The ~250 word blog post with attribution. Include a hyperlink to the source where the attribution appears.

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

[Post body with attribution like "according to <a href="URL">Publication Name</a>, the key detail..."]

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
