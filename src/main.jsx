/* global __BUILD_VERSION__:readonly */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './dashboard-tokens.css'
import './analysis-emphasis.css'
import App from './App.jsx'

// When a new deploy is live, the server serves a new build-version.json. We compare it to the
// version this bundle was built with (__BUILD_VERSION__). If different, force reload so the user
// gets the new code/data without manually refreshing. Injected at build time by Vite define.
if (import.meta.env.PROD && typeof __BUILD_VERSION__ !== 'undefined') {
  const CHECK_INTERVAL_MS = 60_000
  const checkForNewDeploy = async () => {
    try {
      const res = await fetch(`/build-version.json?t=${Date.now()}`, { cache: 'no-store' })
      if (!res.ok) return
      const { version } = await res.json()
      if (version && version !== __BUILD_VERSION__) {
        window.location.reload()
      }
    } catch {
      // ignore network errors; will retry on next interval or tab focus
    }
  }
  setInterval(checkForNewDeploy, CHECK_INTERVAL_MS)
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') checkForNewDeploy()
  })
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
