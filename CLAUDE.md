# Boing Boing Tools

## Menu Command

When the user types `menu`, display this list of available tools:

```
BOING BOING TOOLS
─────────────────
1. memeorandum   — Fetch 20 headlines from memeorandum.com, select articles for posts
2. random-wiki   — Show 10 random articles from Wikipedia's Unusual Articles, select for posts
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
- Include a hyperlink to the original article
- Have a catchy headline
- Get to the interesting/important point quickly

## Example Attribution Styles

- "As reported in [The Washington Post](url), ..."
- "According to [Axios](url), ..."
- "[The Guardian reports](url) that ..."
- "Over at [Politico](url), they're reporting ..."

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
The ~250 word blog post with attribution. Link should be on the publication name only:
- CORRECT: `according to [HuffPost](url)`
- WRONG: showing the raw URL in the text

### 2. Source
`Source: [full URL]`

### 3. Headlines (70 characters max)
Provide 5 headline options, each 70 characters or fewer.

### 4. Category Tags
3-5 tags separated by commas (not bullet points), ordered broadest to most specific:
1. Primary broad category (news, technology, etc.)
2. Secondary categories (health, science, etc.)
3. Specific topic tags (microplastics, climate change, etc.)
4. Relevant institutions/organizations
5. Key people mentioned

### 5. Meta Headlines (60 characters max)
Provide 5 meta headline options, each 60 characters or fewer.

### 6. Meta Descriptions (120 characters max)
Provide 5 meta description options, each 120 characters or fewer.

### Example Output Structure

```
## [Headline]

[Post body with attribution like "according to [Publication](url)"]

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
