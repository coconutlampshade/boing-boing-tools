import * as cheerio from 'cheerio';

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';

export async function fetchPage(url) {
  const response = await fetch(url, {
    headers: {
      'User-Agent': USER_AGENT,
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch ${url}: ${response.status}`);
  }

  return response.text();
}

export async function fetchMemeorandum() {
  const html = await fetchPage('https://memeorandum.com/river');
  const $ = cheerio.load(html);

  const headlines = [];

  // Memeorandum river format: each story is in a div with headline links
  $('a').each((i, el) => {
    const $el = $(el);
    const href = $el.attr('href');
    const text = $el.text().trim();

    // Filter for actual article links (external URLs with meaningful text)
    if (href &&
        href.startsWith('http') &&
        !href.includes('memeorandum.com') &&
        text.length > 20 &&
        text.length < 200 &&
        headlines.length < 20) {

      // Avoid duplicates
      if (!headlines.some(h => h.url === href)) {
        headlines.push({
          title: text,
          url: href,
          source: new URL(href).hostname.replace('www.', '')
        });
      }
    }
  });

  return headlines.slice(0, 20);
}

export async function fetchArticleContent(url) {
  const html = await fetchPage(url);
  const $ = cheerio.load(html);

  // Remove script, style, nav, footer, aside elements
  $('script, style, nav, footer, aside, .ad, .advertisement, .social-share, .comments').remove();

  // Try to find main content
  let content = '';
  const selectors = ['article', '[role="main"]', 'main', '.post-content', '.article-content', '.entry-content', '.story-body'];

  for (const selector of selectors) {
    const $main = $(selector);
    if ($main.length && $main.text().trim().length > 200) {
      content = $main.text().trim();
      break;
    }
  }

  // Fallback to body text
  if (!content) {
    content = $('body').text().trim();
  }

  // Get title
  const title = $('title').text().trim() ||
                $('h1').first().text().trim() ||
                $('meta[property="og:title"]').attr('content') ||
                '';

  // Clean up whitespace
  content = content.replace(/\s+/g, ' ').substring(0, 10000);

  return { title, content };
}

export async function fetchUnusualWikiArticles() {
  const html = await fetchPage('https://en.wikipedia.org/wiki/Wikipedia:Unusual_articles');
  const $ = cheerio.load(html);

  const articles = [];

  // Find all links in the content area that point to Wikipedia articles
  $('#mw-content-text a').each((i, el) => {
    const $el = $(el);
    const href = $el.attr('href');
    const title = $el.attr('title');

    // Filter for article links
    if (href &&
        href.startsWith('/wiki/') &&
        !href.includes(':') &&
        !href.includes('#') &&
        title &&
        title.length > 2) {

      // Get the parent text for context/description
      const parentText = $el.parent().text().trim();

      articles.push({
        title: title,
        url: `https://en.wikipedia.org${href}`,
        description: parentText.substring(0, 300)
      });
    }
  });

  // Remove duplicates and shuffle
  const unique = [...new Map(articles.map(a => [a.title, a])).values()];
  const shuffled = unique.sort(() => Math.random() - 0.5);

  return shuffled.slice(0, 20);
}

export async function fetchWikiArticleContent(url) {
  // Use Wikipedia API for cleaner content
  const title = url.split('/wiki/')[1];
  const apiUrl = `https://en.wikipedia.org/api/rest_v1/page/summary/${title}`;

  const response = await fetch(apiUrl, {
    headers: { 'User-Agent': USER_AGENT }
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch Wikipedia article: ${response.status}`);
  }

  const data = await response.json();

  // Also fetch full extract for more content
  const extractUrl = `https://en.wikipedia.org/api/rest_v1/page/mobile-html/${title}`;
  let fullContent = data.extract || '';

  try {
    const fullResponse = await fetch(extractUrl, {
      headers: { 'User-Agent': USER_AGENT }
    });
    if (fullResponse.ok) {
      const html = await fullResponse.text();
      const $$ = cheerio.load(html);
      $$('script, style, .mw-ref, .noprint').remove();
      fullContent = $$('section').text().trim().substring(0, 8000);
    }
  } catch (e) {
    // Fall back to summary
  }

  return {
    title: data.title,
    content: fullContent || data.extract,
    description: data.description || '',
    thumbnail: data.thumbnail?.source || null
  };
}
