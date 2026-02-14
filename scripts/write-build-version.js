/**
 * Writes public/build-version.json with the current build version.
 * Used so the deployed app can tell clients "this is the live version";
 * the client compares it to the version it was built with and reloads if different.
 *
 * Version source (first available):
 * - VERCEL_GIT_COMMIT_SHA (set by Vercel on deploy)
 * - git rev-parse --short HEAD (local/CI)
 * - timestamp (fallback when not in git)
 */
import { writeFileSync, mkdirSync } from 'fs'
import { dirname, join } from 'path'
import { execSync } from 'child_process'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')
const outPath = join(root, 'public', 'build-version.json')

function getVersion() {
  if (process.env.VERCEL_GIT_COMMIT_SHA) {
    return process.env.VERCEL_GIT_COMMIT_SHA.slice(0, 12)
  }
  try {
    return execSync('git rev-parse --short=12 HEAD', { cwd: root, encoding: 'utf-8' }).trim()
  } catch {
    return `t${Date.now()}`
  }
}

const version = getVersion()
mkdirSync(dirname(outPath), { recursive: true })
writeFileSync(outPath, JSON.stringify({ version }) + '\n', 'utf-8')
console.log('Build version:', version)
