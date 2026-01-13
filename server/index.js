import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

import memeorandumRouter from './routes/memeorandum.js';
import randomWikiRouter from './routes/random-wiki.js';
import writepostRouter from './routes/writepost.js';
import postsRouter from './routes/posts.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = join(__dirname, '..');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json({ limit: '1mb' }));
app.use(express.static(join(ROOT_DIR, 'public')));

// Serve post HTML files from root
app.use(express.static(ROOT_DIR, {
  extensions: ['html'],
  index: false
}));

// API Routes
app.use('/api/memeorandum', memeorandumRouter);
app.use('/api/random-wiki', randomWikiRouter);
app.use('/api/writepost', writepostRouter);
app.use('/api/posts', postsRouter);

// Serve the main app
app.get('/', (req, res) => {
  res.sendFile(join(ROOT_DIR, 'public', 'app.html'));
});

// Serve existing index.html for post list
app.get('/posts', (req, res) => {
  res.sendFile(join(ROOT_DIR, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n🚀 Boing Boing Tools running at http://localhost:${PORT}\n`);
  console.log(`   Dashboard:  http://localhost:${PORT}/`);
  console.log(`   Post List:  http://localhost:${PORT}/posts\n`);
});
