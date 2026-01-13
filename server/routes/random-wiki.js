import { Router } from 'express';
import { fetchUnusualWikiArticles, fetchWikiArticleContent } from '../services/scraper.js';
import { generatePost } from '../services/anthropic.js';

const router = Router();

// GET /api/random-wiki - Fetch 20 random unusual articles
router.get('/', async (req, res) => {
  try {
    const articles = await fetchUnusualWikiArticles();
    res.json({ articles });
  } catch (error) {
    console.error('Wiki fetch error:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST /api/random-wiki/generate - Generate post from selected article
router.post('/generate', async (req, res) => {
  try {
    const { url, title } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    // Fetch full Wikipedia article content
    const article = await fetchWikiArticleContent(url);

    // Generate post using Claude
    const post = await generatePost(
      article.content,
      url,
      `This is a Wikipedia "Unusual Article" about: ${title || article.title}.
       Write in a tone of wonder/amusement at the unusual nature of the topic.
       Description: ${article.description}`
    );

    res.json({ post });
  } catch (error) {
    console.error('Post generation error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
