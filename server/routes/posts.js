import { Router } from 'express';
import { writeFile, readFile } from 'fs/promises';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..', '..');

const router = Router();

// POST /api/posts/save - Save a generated post to HTML file
router.post('/save', async (req, res) => {
  try {
    const { post, filename } = req.body;

    if (!post || !filename) {
      return res.status(400).json({ error: 'Post data and filename are required' });
    }

    // Sanitize filename
    const safeFilename = filename
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 50);

    const fullFilename = `post-${safeFilename}.html`;
    const filePath = join(ROOT_DIR, fullFilename);

    // Generate HTML content
    const html = generatePostHtml(post);

    // Write file
    await writeFile(filePath, html, 'utf-8');

    // Update index.html
    await addToIndex(fullFilename, post.headline);

    res.json({
      success: true,
      filename: fullFilename,
      path: filePath
    });
  } catch (error) {
    console.error('Save post error:', error);
    res.status(500).json({ error: error.message });
  }
});

function generatePostHtml(post) {
  const previouslyHtml = post.previously?.length
    ? `<div class="previously" id="previously">
<strong>Previously:</strong>
<ul>
${post.previously.map(p => `<li><a href="${p.url}">${p.title}</a></li>`).join('\n')}
</ul>
</div>`
    : '';

  // Wrap post paragraphs in WordPress blocks
  const postBody = post.post
    .split('</p>')
    .filter(p => p.trim())
    .map(p => `<!-- wp:paragraph -->\n${p}</p>\n<!-- /wp:paragraph -->`)
    .join('\n\n');

  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Post Preview</title>
    <link rel="stylesheet" href="post-style.css">
</head>
<body>

<div class="headline-row">
    <h1 id="headline">${escapeHtml(post.headline)}</h1>
    <button class="copy-btn" onclick="copyText('headline')">copy</button>
</div>

<article id="postBody">
${postBody}

${previouslyHtml}
</article>

<div class="post-actions">
    <button class="copy-btn" onclick="copyPostOnly()">Copy post</button>
    <button class="copy-btn" onclick="copyPreviouslyOnly()">Copy previously</button>
</div>

<hr>

<div class="metadata">

<div class="section-header">
    <h3>Source</h3>
    <button class="copy-btn" onclick="copyText('sourceUrl')">copy</button>
</div>
<p class="source-url" id="sourceUrl">${escapeHtml(post.sourceUrl)}</p>

<h3>Headlines (70 characters max)</h3>
${post.headlines.map(h => `<div class="item-row"><span>${escapeHtml(h)}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>`).join('\n')}

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Category Tags</h3>
    <button class="copy-btn" onclick="copyText('tags')">copy</button>
</div>
<p id="tags">${escapeHtml(post.tags)}</p>

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Yoast Focus Keyphrase</h3>
    <button class="copy-btn" onclick="copyText('focusKeyphrase')">copy</button>
</div>
<p id="focusKeyphrase">${escapeHtml(post.focusKeyphrase)}</p>

<h3>Meta Headlines (60 characters max)</h3>
${post.metaHeadlines.map(h => `<div class="item-row"><span>${escapeHtml(h)}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>`).join('\n')}

<h3>Meta Descriptions (120 characters max)</h3>
${post.metaDescriptions.map(d => `<div class="item-row"><span>${escapeHtml(d)}</span><button class="copy-btn" onclick="copyThis(this)">copy</button></div>`).join('\n')}

<div class="section-header" style="margin-top: 1.5em;">
    <h3>Author</h3>
</div>
<p>Mark Frauenfelder</p>

</div>

<script src="post-script.js"></script>

</body>
</html>
`;
}

function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function addToIndex(filename, title) {
  const indexPath = join(ROOT_DIR, 'index.html');
  let content = await readFile(indexPath, 'utf-8');

  // Escape single quotes in title for JS
  const safeTitle = title.replace(/'/g, "\\'");

  // Find the posts array and add new entry at the top
  const marker = '// New posts';
  const newEntry = `{ file: '${filename}', title: '${safeTitle}' },`;

  if (content.includes(marker)) {
    content = content.replace(
      marker,
      `${marker}\n    ${newEntry}`
    );
  } else {
    // Fallback: find const posts = [ and add after it
    content = content.replace(
      'const posts = [',
      `const posts = [\n    ${newEntry}`
    );
  }

  await writeFile(indexPath, content, 'utf-8');
}

export default router;
