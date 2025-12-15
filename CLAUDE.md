# Boing Boing Tools

## Menu Command

When the user types `menu`, display this list of available tools:

```
BOING BOING TOOLS
─────────────────
1. memeorandum   — Fetch 20 headlines from memeorandum.com, select articles for posts
2. random-wiki   — Show 20 random articles from Wikipedia's Unusual Articles, select for posts
3. writepost     — Write a post from a URL or topic the user provides
4. author-stats  — Run author performance report (posts, views, evergreen metrics)
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

Mention the publication by name in plain text. Do NOT include markdown links in the post body:

- "As reported by The Washington Post, the agency plans to cut 500 jobs by March..."
- "According to Axios, lawmakers are preparing a new bill that would..."
- "The Guardian reports that climate scientists have discovered a troubling trend..."
- "A Reuters investigation reveals the company knowingly chose revenue over users..."

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
- Don't overuse em dashes for artificial drama
- Vary paragraph lengths (some short, some longer)
- Don't always use three examples—two or four is fine
- Avoid "not only X but also Y" constructions
- Don't hedge everything with "it can be argued" or "one might say"
- Skip significance inflation—don't tell readers how important something is, just show them

### What TO Do
- Use concrete, specific details (dates, names, numbers)
- Take actual positions rather than hedging
- Let prose have texture—short sentences, longer ones, fragments
- Trust the reader to understand significance without being told
- State facts directly instead of attributing to vague "experts"

### Sentence Rhythm and Flow
- Avoid too many short, punchy sentences in a row—it becomes exhausting to read
- Mix sentence lengths: follow a short sentence with a longer one that breathes
- Use conjunctions (and, but, so, because) to connect ideas rather than always starting new sentences
- Let some paragraphs unspool a bit—not everything needs to be staccato
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
