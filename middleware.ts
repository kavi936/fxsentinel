// Vercel Routing Middleware to integrate Prerender.io with your Vite + React SPA.
// Bots (Googlebot, social scrapers, etc.) get fully rendered HTML from Prerender.io.
// Normal users keep getting the regular SPA bundle as usual.

const BOT_UA_REGEX =
  /googlebot|bingbot|yandex|baiduspider|duckduckbot|slurp|facebookexternalhit|twitterbot|linkedinbot|slackbot|pinterest|embedly|quora link preview|crawler|spider|robot|prerender/i;

// Skip static assets and non-HTML resources – we only prerender real pages.
const IGNORE_EXT_REGEX =
  /\.(js|css|png|jpg|jpeg|gif|svg|ico|webp|avif|pdf|txt|xml|json|mp4|mp3|ogg|wav|woff|woff2|ttf|eot)$/i;

// Run on all routes except obvious static files; adjust if needed.
export const config = {
  matcher: ['/((?!assets|favicon.ico|robots.txt|sitemap.xml).*)'],
};

export default async function middleware(request: Request): Promise<Response | void> {
  const url = new URL(request.url);
  const ua = request.headers.get('user-agent') || '';

  const isBot = BOT_UA_REGEX.test(ua);
  const isGet = request.method === 'GET';
  const isHtmlLike = !IGNORE_EXT_REGEX.test(url.pathname);
  const hasPrerenderHeader = request.headers.get('x-prerender') === '1';

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

