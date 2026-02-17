// Vercel serverless function to serve robots.txt
export default function handler(req, res) {
  const robots = `User-agent: *
Allow: /

# Sitemap
Sitemap: https://fxsentinel.io/sitemap.xml

# Allow all pages to be indexed
Allow: /blog/
Allow: /login
Allow: /signup
Allow: /disclaimer
Allow: /privacy

# Allow /dashboard so it can appear as a sitelink (crawler hits login if not authenticated)
# Disallow other private/auth flows only
Disallow: /trial-welcome
Disallow: /auth-redirect
Disallow: /forgot-password

# Allow assets
Allow: /assets/
Allow: /*.png
Allow: /*.jpg
Allow: /*.jpeg
Allow: /*.gif
Allow: /*.svg
Allow: /*.webp`;

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.status(200).send(robots);
}

