/**
 * Generates crawler-visible static HTML for /blog and /blog/<slug>.
 * Output: public/crawler-snapshots/*.html (NOT under /blog/ — that would override the SPA for humans).
 * middleware.ts serves these HTML files to bots and LLM crawlers on /blog and /blog/<slug> requests.
 *
 * Run automatically via: npm run build
 */

import { mkdirSync, writeFileSync, rmSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { blogCrawlerPosts, BASE_URL } from '../src/data/blogCrawlerManifest.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT_DIR = join(__dirname, '..', 'public', 'crawler-snapshots');

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function buildPage({ title, description, canonicalPath, bodyHtml, schemaExtra }) {
  const canonical = `${BASE_URL}${canonicalPath}`;
  const schema = {
    '@context': 'https://schema.org',
    ...schemaExtra,
  };

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${escapeHtml(title)}</title>
  <meta name="description" content="${escapeHtml(description)}" />
  <meta name="robots" content="index, follow" />
  <link rel="canonical" href="${canonical}" />
  <meta property="og:type" content="article" />
  <meta property="og:url" content="${canonical}" />
  <meta property="og:title" content="${escapeHtml(title)}" />
  <meta property="og:description" content="${escapeHtml(description)}" />
  <meta property="og:site_name" content="FXSentinel" />
  <meta property="og:image" content="${BASE_URL}/og-image.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="${escapeHtml(title)}" />
  <meta name="twitter:description" content="${escapeHtml(description)}" />
  <script type="application/ld+json">${JSON.stringify(schema)}</script>
</head>
<body>
  <header>
    <p><a href="${BASE_URL}/">FXSentinel</a> · <a href="${BASE_URL}/blog">Blog</a></p>
  </header>
  <main>
    ${bodyHtml}
  </main>
  <footer>
    <p>FXSentinel provides macro tools and education—we are not a broker and do not provide personalised financial advice.</p>
    <p><a href="${BASE_URL}/signup">Sign up</a> · <a href="${BASE_URL}/disclaimer">Disclaimer</a></p>
  </footer>
</body>
</html>
`;
}

function generatePostPage(post) {
  const pageTitle = `${post.title} | FXSentinel Blog`;
  const bodyHtml = `
    <article>
      <p><span>${escapeHtml(post.category)}</span> · <time datetime="${post.dateIso}">${escapeHtml(post.date)}</time> · ${escapeHtml(post.readTime)}</p>
      <h1>${escapeHtml(post.title)}</h1>
      <p>${escapeHtml(post.excerpt)}</p>
      <p>By ${escapeHtml(post.author)}</p>
      ${post.crawlerHtml}
    </article>
  `;

  return buildPage({
    title: pageTitle,
    description: post.excerpt,
    canonicalPath: `/blog/${post.slug}`,
    bodyHtml,
    schemaExtra: {
      '@type': 'BlogPosting',
      headline: post.title,
      description: post.excerpt,
      datePublished: post.dateIso,
      author: { '@type': 'Organization', name: post.author },
      mainEntityOfPage: { '@type': 'WebPage', '@id': `${BASE_URL}/blog/${post.slug}` },
      url: `${BASE_URL}/blog/${post.slug}`,
      articleSection: post.category,
      keywords: ['forex trading', 'economic news', 'AI market analysis', 'FXSentinel', post.category].join(', '),
    },
  });
}

function generateBlogIndexPage() {
  const listItems = blogCrawlerPosts
    .map(
      (post) => `
    <li>
      <a href="${BASE_URL}/blog/${post.slug}">${escapeHtml(post.title)}</a>
      <p>${escapeHtml(post.excerpt)}</p>
      <p><time datetime="${post.dateIso}">${escapeHtml(post.date)}</time> · ${escapeHtml(post.category)}</p>
    </li>`,
    )
    .join('\n');

  const bodyHtml = `
    <h1>FXSentinel Blog — macro &amp; FX education</h1>
    <p>Long-form guides on central banks, economic calendars, AI-assisted news context, volatility, and macro themes for retail forex traders.</p>
    <ul>
      ${listItems}
    </ul>
  `;

  return buildPage({
    title: 'Forex & Macro Education | FXSentinel Blog',
    description:
      'In-depth articles on central banks, FX volatility, economic calendars, AI news context, and how macro headlines move major pairs and gold. Education—not financial advice.',
    canonicalPath: '/blog',
    bodyHtml,
    schemaExtra: {
      '@type': 'Blog',
      name: 'FXSentinel Blog',
      description:
        'Educational forex and macro articles for retail traders from FXSentinel.',
      url: `${BASE_URL}/blog`,
      publisher: { '@type': 'Organization', name: 'FXSentinel', url: BASE_URL },
    },
  });
}

function main() {
  if (existsSync(OUT_DIR)) {
    rmSync(OUT_DIR, { recursive: true, force: true });
  }
  mkdirSync(OUT_DIR, { recursive: true });

  writeFileSync(join(OUT_DIR, 'blog-index.html'), generateBlogIndexPage(), 'utf-8');

  for (const post of blogCrawlerPosts) {
    writeFileSync(join(OUT_DIR, `${post.slug}.html`), generatePostPage(post), 'utf-8');
  }

  console.log(
    `[generate-blog-static-html] Wrote ${blogCrawlerPosts.length + 1} files under public/crawler-snapshots/`,
  );
}

main();
