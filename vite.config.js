import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
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

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
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
