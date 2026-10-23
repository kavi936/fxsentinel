#!/usr/bin/env bash
# Prints which Render env vars you still need after security rotation.
# Does not print secret values.

set -euo pipefail

REQUIRED=(
  LIVE_LITE_MODE
  ALERTS_ENABLED
  TELEGRAM_NEWS_ENABLED
  STRIPE_CHECKOUT_ENABLED
  FIREBASE_PROJECT_ID
  FIREBASE_SERVICE_ACCOUNT_JSON
  OPENAI_API_KEY
)

OPTIONAL=(
  GEMINI_API_KEY
  FINNHUB_API_KEY
  DOME_API_KEY
  POLYROUTER_API_KEY
  RESEND_API_KEY
)

echo "=== Live-lite Render env checklist ==="
echo "Set LIVE_LITE_MODE=true ALERTS_ENABLED=false TELEGRAM_NEWS_ENABLED=false STRIPE_CHECKOUT_ENABLED=false"
echo
echo "Required for Overview + optional AI:"
for k in "${REQUIRED[@]}"; do
  if [[ -n "${!k:-}" ]]; then
    echo "  [set locally] $k"
  else
    echo "  [missing in this shell] $k"
  fi
done
echo
echo "Optional:"
for k in "${OPTIONAL[@]}"; do
  if [[ -n "${!k:-}" ]]; then
    echo "  [set locally] $k"
  else
    echo "  [optional] $k"
  fi
done
echo
echo "Next: Render Dashboard → fxsentinel-api → Environment → add NEW rotated values only."
echo "Then: Vercel → VITE_API_URL=https://<service>.onrender.com → Redeploy."
