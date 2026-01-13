import { Router } from 'express';
import { fetchMemeorandum, fetchArticleContent } from '../services/scraper.js';
import { generatePost } from '../services/anthropic.js';

const router = Router();

// GET /api/memeorandum - Fetch headlines
router.get('/', async (req, res) => {
  try {
    const headlines = await fetchMemeorandum();
    res.json({ headlines });
  } catch (error) {
    console.error('Memeorandum fetch error:', error);
    res.status(500).json({ error: error.message });
  }
});

// POST /api/memeorandum/generate - Generate post from selected article
router.post('/generate', async (req, res) => {
  try {
    const { url, title } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    // Fetch article content
    const article = await fetchArticleContent(url);

    // Generate post using Claude
    const post = await generatePost(
      article.content,
      url,
      `Original headline: ${title || article.title}`
    );

    res.json({ post });
  } catch (error) {
    console.error('Post generation error:', error);
    res.status(500).json({ error: error.message });
  }
});

export default router;
