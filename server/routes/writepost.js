import { Router } from 'express';
import { fetchArticleContent } from '../services/scraper.js';
import { generatePost } from '../services/anthropic.js';

const router = Router();

// POST /api/writepost - Generate post from URL
router.post('/', async (req, res) => {
  try {
    const { url } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    // Fetch article content
    const article = await fetchArticleContent(url);

    if (!article.content || article.content.length < 100) {
      return res.status(400).json({
        error: 'Could not extract article content. The site may be blocking scrapers.'
      });
    }

    // Generate post using Claude
    const post = await generatePost(
      article.content,
      url,
      `Original title: ${article.title}`
    );

    res.json({ post });
  } catch (error) {
    console.error('Writepost error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
