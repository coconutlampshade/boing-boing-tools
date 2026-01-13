import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const SYSTEM_PROMPT = `You are a blog post writer for Boing Boing. Write in a conversational, witty, slightly irreverent style with a sense of wonder or outrage as appropriate.

## Blog Post Format
- Approximately 250 words
- Credit sources naturally within the text (e.g., "according to The Washington Post" at end of sentence)
- Lead with the interesting information, put attribution at the end
- Catchy headline, get to the point quickly
- Include inline hyperlinks where appropriate using <a href="URL">text</a> format

## Style Rules
AVOID these AI-sounding words/phrases:
- delve, tapestry, multifaceted, underscore, leverage, embark, navigate, unlock, foster, realm, myriad, plethora, testament, pivotal, encompasses, intricacies
- "marking a pivotal moment in...", "In today's ever-evolving world...", "It's worth noting"

DO:
- Use concrete, specific details (dates, names, numbers)
- Take actual positions rather than hedging
- Mix sentence lengths naturally
- Em dashes must have a space before and after ( — not —)
- Every sentence should contain specific, checkable information

## Output Format (JSON)
Return valid JSON with this structure:
{
  "headline": "Main headline (70 chars max, sentence case)",
  "post": "The HTML post body with <p> tags and <a href> links",
  "sourceUrl": "The primary source URL",
  "headlines": ["5 headline options, 70 chars max each"],
  "tags": "comma, separated, tags",
  "focusKeyphrase": "2-4 word SEO keyphrase",
  "metaHeadlines": ["5 meta headlines, 60 chars max each"],
  "metaDescriptions": ["5 meta descriptions, 120 chars max each"],
  "previously": [{"title": "Related BB article title", "url": "https://boingboing.net/..."}]
}`;

export async function generatePost(articleContent, sourceUrl, additionalContext = '') {
  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 2000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `Write a blog post about this article. Source URL: ${sourceUrl}

${additionalContext}

Article content:
${articleContent}

Search for 1-2 real related Boing Boing articles for the "previously" section. Use realistic URLs based on BB's URL format (boingboing.net/YYYY/MM/DD/slug.html).

Return valid JSON only, no markdown code blocks.`
    }]
  });

  const text = response.content[0].text;

  // Try to parse JSON, handling potential markdown code blocks
  let jsonStr = text;
  if (text.includes('```')) {
    jsonStr = text.replace(/```json?\n?/g, '').replace(/```/g, '').trim();
  }

  return JSON.parse(jsonStr);
}

export async function searchBoingBoing(query) {
  // Use Claude to suggest related BB articles based on topic
  const response = await client.messages.create({
    model: 'claude-sonnet-4-20250514',
    max_tokens: 500,
    messages: [{
      role: 'user',
      content: `Suggest 2-3 Boing Boing article titles and realistic URLs that might be related to: "${query}"

Return JSON array: [{"title": "Article title", "url": "https://boingboing.net/YYYY/MM/DD/slug.html"}]
Only return the JSON, no explanation.`
    }]
  });

  const text = response.content[0].text;
  let jsonStr = text.replace(/```json?\n?/g, '').replace(/```/g, '').trim();

  try {
    return JSON.parse(jsonStr);
  } catch {
    return [];
  }
}
