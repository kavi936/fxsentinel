// Vercel serverless function to serve robots.txt
export default function handler(req, res) {
  const robots = `User-agent: *
Allow: /

# Only block auth/private flows; everything else (blog, login, signup, etc.) is allowed
Disallow: /trial-welcome
Disallow: /auth-redirect
Disallow: /forgot-password

# Sitemap
Sitemap: https://fxsentinel.io/sitemap.xml`;

  res.setHeader('Content-Type', 'text/plain; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=3600');
  res.status(200).send(robots);
}

