import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import prerenderStatic from 'vite-plugin-prerender-static'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'

// Read build version written by scripts/write-build-version.js (run before build).
// Used so the client can compare to /build-version.json and reload when a new deploy is live.
function getBuildVersion() {
  const path = join(process.cwd(), 'public', 'build-version.json')
  if (!existsSync(path)) return 'dev'
  try {
    const { version } = JSON.parse(readFileSync(path, 'utf-8'))
    return version || 'dev'
  } catch {
    return 'dev'
  }
}

// Simple static HTML snippets for prerendered routes.
// These do not need to match the full React UI; they just need to give Google
// real, crawlable content per URL so indexing and understanding improve.
function renderStaticHtml(path) {
  if (path === '/') {
    return `
      <main>
        <section>
          <h1>FXSentinel – Smarter Market Dashboard, Powered by AI</h1>
          <p>FXSentinel helps retail traders make sense of fundamentals and macroeconomics with real-time alerts, AI-powered news analysis, and actionable market insights in one place.</p>
        </section>
        <section>
          <h2>Stay Ahead of Market-Moving Events</h2>
          <p>Track economic calendars, central bank decisions, geopolitical risk and macro data without drowning in headlines. FXSentinel surfaces what matters so you can focus on decisions, not noise.</p>
        </section>
      </main>
    `
  }

  if (path === '/blog') {
    return `
      <main>
        <h1>FXSentinel Blog – AI, Macro and Trading Workflows</h1>
        <p>Deep dives on how to blend macroeconomics, news and AI into a practical trading workflow. Guides, explainers and case studies written for serious retail traders.</p>
      </main>
    `
  }

  if (path.startsWith('/blog/')) {
    return `
      <main>
        <h1>FXSentinel Insights – In-Depth Market Analysis</h1>
        <p>This article is part of the FXSentinel blog, where we explain how macro events, central banks, sentiment and AI-driven analysis come together inside the FXSentinel dashboard.</p>
      </main>
    `
  }

  if (path === '/dashboard') {
    return `
      <main>
        <h1>FXSentinel Dashboard</h1>
        <p>The FXSentinel dashboard brings your macro calendar, news feeds, alerts and AI analysis together in one view. Log in to see your personalized market workspace.</p>
      </main>
    `
  }

  if (path === '/login') {
    return `
      <main>
        <h1>Log In to FXSentinel</h1>
        <p>Access your FXSentinel dashboard, alerts and analysis. Existing users can sign in securely to continue where they left off.</p>
      </main>
    `
  }

  if (path === '/signup') {
    return `
      <main>
        <h1>Create Your FXSentinel Account</h1>
        <p>Start your FXSentinel trial to experience an AI-powered market dashboard built for fundamentals, macro and news-driven trading.</p>
      </main>
    `
  }

  if (path === '/disclaimer') {
    return `
      <main>
        <h1>FXSentinel Disclaimer</h1>
        <p>FXSentinel does not provide investment advice or guarantee trading results. All information is for educational and informational purposes only. Trading foreign exchange involves risk.</p>
      </main>
    `
  }

  if (path === '/privacy') {
    return `
      <main>
        <h1>FXSentinel Privacy Policy</h1>
        <p>Learn how FXSentinel collects, uses and protects your data, including account information, analytics and third-party services.</p>
      </main>
    `
  }

  if (path === '/terms') {
    return `
      <main>
        <h1>FXSentinel Terms of Service</h1>
        <p>Review the terms and conditions that govern your use of the FXSentinel application, including subscriptions, acceptable use and limitations of liability.</p>
      </main>
    `
  }

  if (path === '/feedback') {
    return `
      <main>
        <h1>Share Feedback with FXSentinel</h1>
        <p>Tell us what is working well, what is confusing and what you would like to see next in FXSentinel. Your feedback directly shapes the product roadmap.</p>
      </main>
    `
  }

  // Generic fallback for any additional routes we decide to prerender.
  return `
    <main>
      <h1>FXSentinel</h1>
      <p>Smarter market dashboard powered by AI, focused on fundamentals, macroeconomics and news-driven trading.</p>
    </main>
  `
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Static prerendering for key public routes so crawlers get real HTML per URL.
    prerenderStatic({
      dist: 'dist',
      routes: [
        {
          path: '/',
          tags: {
            title: 'FXSentinel - Smarter Market Dashboard | Powered with AI',
            description:
              'Fundamentals and macroeconomics, simplified for retail traders. Get real-time alerts, AI-powered news analysis, and actionable market insights in one place.',
            url: 'https://fxsentinel.io/',
            canonical: 'https://fxsentinel.io/',
          },
        },
        {
          path: '/blog',
          tags: {
            title: 'FXSentinel Blog - AI, Macro & Market Insights',
            description:
              'In-depth articles on macroeconomics, news-driven trading and AI workflows for serious retail traders using FXSentinel.',
            url: 'https://fxsentinel.io/blog',
            canonical: 'https://fxsentinel.io/blog',
          },
        },
        {
          path: '/blog/ai-powered-news-analysis-future-of-trading',
          tags: {
            title: 'AI-Powered News Analysis: The Future of Trading | FXSentinel',
            description:
              'How AI transforms news analysis into tradable insight, and how FXSentinel integrates AI into your macro workflow.',
            url: 'https://fxsentinel.io/blog/ai-powered-news-analysis-future-of-trading',
            canonical: 'https://fxsentinel.io/blog/ai-powered-news-analysis-future-of-trading',
          },
        },
        {
          path: '/blog/central-bank-decisions-currency-pairs',
          tags: {
            title: 'Central Bank Decisions & Currency Pairs | FXSentinel',
            description:
              'Understand how central bank decisions move FX markets and how FXSentinel keeps you ahead of policy surprises.',
            url: 'https://fxsentinel.io/blog/central-bank-decisions-currency-pairs',
            canonical: 'https://fxsentinel.io/blog/central-bank-decisions-currency-pairs',
          },
        },
        {
          path: '/blog/understanding-forex-market-sentiment',
          tags: {
            title: 'Understanding Forex Market Sentiment | FXSentinel',
            description:
              'A practical guide to reading sentiment in FX markets and combining it with macro signals inside FXSentinel.',
            url: 'https://fxsentinel.io/blog/understanding-forex-market-sentiment',
            canonical: 'https://fxsentinel.io/blog/understanding-forex-market-sentiment',
          },
        },
        {
          path: '/blog/turning-news-actionable-signals',
          tags: {
            title: 'Turning News into Actionable Signals | FXSentinel',
            description:
              'How to go from raw headlines to concrete trade awareness using FXSentinel’s alerts and filters.',
            url: 'https://fxsentinel.io/blog/turning-news-actionable-signals',
            canonical: 'https://fxsentinel.io/blog/turning-news-actionable-signals',
          },
        },
        {
          path: '/blog/traders-guide-decoding-market-volatility',
          tags: {
            title: 'A Trader’s Guide to Decoding Market Volatility | FXSentinel',
            description:
              'Frameworks for understanding and navigating volatility in FX markets, with workflows you can build in FXSentinel.',
            url: 'https://fxsentinel.io/blog/traders-guide-decoding-market-volatility',
            canonical: 'https://fxsentinel.io/blog/traders-guide-decoding-market-volatility',
          },
        },
        {
          path: '/blog/ai-detects-hidden-patterns-macroeconomic-news',
          tags: {
            title: 'How AI Detects Hidden Patterns in Macroeconomic News | FXSentinel',
            description:
              'Explore how AI can surface patterns in macro news that humans miss, and how FXSentinel uses this to power alerts.',
            url: 'https://fxsentinel.io/blog/ai-detects-hidden-patterns-macroeconomic-news',
            canonical: 'https://fxsentinel.io/blog/ai-detects-hidden-patterns-macroeconomic-news',
          },
        },
        {
          path: '/blog/geopolitical-tensions-forex-trading-2025',
          tags: {
            title: 'Geopolitical Tensions & Forex Trading in 2025 | FXSentinel',
            description:
              'How geopolitical risk bleeds into FX markets and how FXSentinel helps you track the moving pieces.',
            url: 'https://fxsentinel.io/blog/geopolitical-tensions-forex-trading-2025',
            canonical: 'https://fxsentinel.io/blog/geopolitical-tensions-forex-trading-2025',
          },
        },
        {
          path: '/blog/fed-ecb-rate-divergence-currency-markets',
          tags: {
            title: 'Fed vs ECB: Rate Divergence in Currency Markets | FXSentinel',
            description:
              'Understand how diverging central bank paths shape FX trends, with dashboards and alerts in FXSentinel.',
            url: 'https://fxsentinel.io/blog/fed-ecb-rate-divergence-currency-markets',
            canonical: 'https://fxsentinel.io/blog/fed-ecb-rate-divergence-currency-markets',
          },
        },
        {
          path: '/blog/gold-rally-safe-haven-inflation-hedge',
          tags: {
            title: 'Gold Rallies, Safe Haven and Inflation Hedge | FXSentinel',
            description:
              'A look at gold as a safe haven and inflation hedge, and how FXSentinel helps you track cross-asset moves.',
            url: 'https://fxsentinel.io/blog/gold-rally-safe-haven-inflation-hedge',
            canonical: 'https://fxsentinel.io/blog/gold-rally-safe-haven-inflation-hedge',
          },
        },
        {
          path: '/blog/bitcoin-institutional-adoption-forex-traders',
          tags: {
            title: 'Bitcoin, Institutional Adoption and Forex Traders | FXSentinel',
            description:
              'How institutional adoption of Bitcoin interacts with FX markets and what traders should monitor.',
            url: 'https://fxsentinel.io/blog/bitcoin-institutional-adoption-forex-traders',
            canonical: 'https://fxsentinel.io/blog/bitcoin-institutional-adoption-forex-traders',
          },
        },
        {
          path: '/dashboard',
          tags: {
            title: 'FXSentinel Dashboard',
            description:
              'Your personalized FXSentinel workspace for macro calendars, alerts, news and AI-powered analysis.',
            url: 'https://fxsentinel.io/dashboard',
            canonical: 'https://fxsentinel.io/dashboard',
          },
        },
        {
          path: '/login',
          tags: {
            title: 'Log In | FXSentinel',
            description: 'Sign in to your FXSentinel account and access your dashboard and alerts.',
            url: 'https://fxsentinel.io/login',
            canonical: 'https://fxsentinel.io/login',
          },
        },
        {
          path: '/signup',
          tags: {
            title: 'Sign Up | FXSentinel',
            description: 'Create your FXSentinel account and start your AI-powered macro dashboard trial.',
            url: 'https://fxsentinel.io/signup',
            canonical: 'https://fxsentinel.io/signup',
          },
        },
        {
          path: '/disclaimer',
          tags: {
            title: 'Disclaimer | FXSentinel',
            description:
              'Important risk disclosures and disclaimers about using FXSentinel for market awareness and analysis.',
            url: 'https://fxsentinel.io/disclaimer',
            canonical: 'https://fxsentinel.io/disclaimer',
          },
        },
        {
          path: '/privacy',
          tags: {
            title: 'Privacy Policy | FXSentinel',
            description: 'How FXSentinel collects, uses and protects your personal data.',
            url: 'https://fxsentinel.io/privacy',
            canonical: 'https://fxsentinel.io/privacy',
          },
        },
        {
          path: '/terms',
          tags: {
            title: 'Terms of Service | FXSentinel',
            description:
              'The terms and conditions that govern your use of the FXSentinel application and services.',
            url: 'https://fxsentinel.io/terms',
            canonical: 'https://fxsentinel.io/terms',
          },
        },
        {
          path: '/feedback',
          tags: {
            title: 'Feedback | FXSentinel',
            description: 'Tell the FXSentinel team what is working well and what you would like to see improved.',
            url: 'https://fxsentinel.io/feedback',
            canonical: 'https://fxsentinel.io/feedback',
          },
        },
      ],
      render: (route) => renderStaticHtml(route.path),
    }),
  ],
  define: {
    __BUILD_VERSION__: JSON.stringify(getBuildVersion()),
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    assetsDir: 'assets',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Removes all console.* calls in production builds
        drop_debugger: true, // Removes debugger statements
      },
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.')
          const ext = info[info.length - 1]
          const name = info[0]

          // Keep sitemap.xml, robots.txt, and og-image.png at root, don't hash them
          if (name === 'sitemap' || name === 'robots' || name === 'og-image') {
            return `[name][extname]`
          }

          if (/png|jpe?g|svg|gif|tiff|bmp|ico|webp/i.test(ext)) {
            return `assets/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        }
      }
    },
    // Ensure public folder files are copied correctly
    publicDir: 'public',
    copyPublicDir: true
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5001',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
