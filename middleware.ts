function blogSnapshotPath(pathname: string): string | null {
  const path = pathname.replace(/\/$/, '') || '/';
  if (path === '/blog') return '/crawler-snapshots/blog-index.html';
  if (path.startsWith('/blog/')) {
    const slug = path.slice('/blog/'.length);
    if (slug && !slug.includes('/') && /^[a-z0-9-]+$/.test(slug)) {
      return `/crawler-snapshots/${slug}.html`;
    }
  }
  return null;
}

// Vercel Routing Middleware: static HTML snapshots for /blog (bots), Prerender.io for other bot routes.
// Humans always get the React SPA; bots on /blog/* get crawler-snapshots from the build step.

const BOT_UA_REGEX =
  /googlebot|bingbot|yandex|baiduspider|duckduckbot|slurp|facebookexternalhit|twitterbot|linkedinbot|slackbot|pinterest|embedly|quora link preview|crawler|spider|robot|prerender|gptbot|chatgpt-user|oai-searchbot|claudebot|claude-web|anthropic-ai|perplexitybot|perplexity-user|cohere-ai|meta-externalagent|amazonbot|bytespider|ccbot|diffbot|youbot/i;

// Skip static assets and non-HTML resources – we only prerender real pages.
const IGNORE_EXT_REGEX =
  /\.(js|css|png|jpg|jpeg|gif|svg|ico|webp|avif|pdf|txt|xml|json|mp4|mp3|ogg|wav|woff|woff2|ttf|eot)$/i;

// Run on all routes except obvious static files; adjust if needed.
export const config = {
  matcher: ['/((?!assets|favicon.ico|robots.txt|sitemap.xml|crawler-snapshots).*)'],
};

export default async function middleware(request: Request): Promise<Response | void> {
  const url = new URL(request.url);
  const ua = request.headers.get('user-agent') || '';

  const isBot = BOT_UA_REGEX.test(ua);
  const isGet = request.method === 'GET';
  const isHtmlLike = !IGNORE_EXT_REGEX.test(url.pathname);
  const hasPrerenderHeader = request.headers.get('x-prerender') === '1';

  // Bots on /blog routes: serve build-time static HTML snapshots (no JS required).
  // Humans keep the React SPA from index.html + client router.
  if (isGet && isHtmlLike && (isBot || hasPrerenderHeader)) {
    const snapshotPath = blogSnapshotPath(url.pathname);
    if (snapshotPath) {
      const snapshotUrl = new URL(snapshotPath, url.origin);
      const snapshotRes = await fetch(snapshotUrl.toString());
      if (snapshotRes.ok) {
        const headers = new Headers(snapshotRes.headers);
        headers.set('content-type', 'text/html; charset=utf-8');
        headers.set('x-fxsentinel-crawler-snapshot', '1');
        return new Response(snapshotRes.body, { status: 200, headers });
      }
    }
  }

  // For normal users or non-HTML requests, do nothing – Vercel serves your SPA as usual.
  // Also allow Prerender's own verification (x-prerender: 1) to force prerendering.
  if (!hasPrerenderHeader && (!isBot || !isGet || !isHtmlLike)) {
    return;
  }

  const token = process.env.PRERENDER_TOKEN;
  if (!token) {
    // Fail open if token is missing: better to serve SPA than break the site.
    return;
  }

  const prerenderTargetUrl = url.toString();
  const prerenderServiceUrl = `https://service.prerender.io/${encodeURIComponent(
    prerenderTargetUrl,
  )}`;

  const headers = new Headers();
  headers.set('User-Agent', ua);
  headers.set('X-Prerender-Token', token);

  const prerenderResponse = await fetch(prerenderServiceUrl, {
    method: 'GET',
    headers,
  });

  const responseHeaders = new Headers(prerenderResponse.headers);
  if (!responseHeaders.get('content-type')) {
    responseHeaders.set('content-type', 'text/html; charset=utf-8');
  }

  return new Response(prerenderResponse.body, {
    status: prerenderResponse.status,
    headers: responseHeaders,
  });
}

