# Contributing to FXSentinel (Beginner Guide)

This file explains how two beginner developers can safely work together on this project.

## 1) Quick Project Map

Use this map to understand where to edit:

- `src/` = frontend (React + Vite)
- `src/components/` = UI components (landing page work is usually here)
- `backend/` = Flask backend
- `backend/services/` = most backend business logic
- `env.example` = list of environment variable names
- `.env` = your local keys (never commit this file)

If you are changing the landing page, you will mostly work in `src/components/` and related CSS files.

## 2) Team Rules (Simple)

- `main` is the live deployment branch.
- Do not push directly to `main`.
- Every change goes through a Pull Request (PR).
- Both developers can review and merge, but only after checking the change.

Why this rule exists: if `main` breaks, production can break.

## 3) Collaborator vs Fork

- **Collaborator**: your friend is added directly to this private repo and can push branches here.
- **Fork**: your friend works in a separate copy of the repo and sends PRs back.

For your 2-person setup, use **collaborator access** because it is easier to manage.

## 4) First-Time Setup

1. Clone the repository.
2. Create local environment file:
   - `cp env.example .env`
3. Add local values to `.env` (use mock values if needed for non-critical features).
4. Install frontend dependencies:
   - `npm install`
5. Install backend dependencies:
   - `cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
6. Run the app:
   - Backend: `cd backend && python3 app.py`
   - Frontend: `npm run dev`

## 5) Branch Naming

Use:

- `feat/<name>` for new feature
- `fix/<name>` for bug fix
- `chore/<name>` for cleanup/config
- `docs/<name>` for documentation

Examples:

- `feat/landing-page-improvements`
- `fix/landing-mobile-overlap`
- `docs/update-contributing-guide`

Why this matters: branch names tell your teammate what type of change is in progress.

## 6) Daily Workflow (Every Task)

1. Pull latest `main`.
2. Create a new branch.
3. Make changes for one small goal.
4. Test locally.
5. Run `npm run lint` for frontend changes.
6. Open PR using `.github/pull_request_template.md`.
7. Request review.
8. Merge only after review and checks are done.

## 7) PR Size Rule

Keep PRs small:

- Good: "Improve landing hero section spacing and CTA copy"
- Too big: "Landing page + dashboard + backend refactor in one PR"

Why this matters: small PRs are easier to review and safer to merge.

## 8) Security Rules (Very Important)

- Never commit `.env`, API keys, tokens, service-account files, or secrets.
- If any secret is exposed, rotate it immediately.
- Sharing variable names is safe (example: `OPENAI_API_KEY`).
- Sharing secret values in git is not safe.

## 9) First Shared Task Recommendation

For your first collaboration task:

- Branch: `feat/landing-page-improvements`
- Scope: landing page only
- Avoid backend changes unless absolutely required

This keeps risk low while both developers learn the workflow.

## 10) Run the App (Quick Commands)

Backend:

`cd backend`
`python3 app.py`

Frontend:

`npm run dev`

## 11) Deployment Notes

- Backend is deployed on Railway.
- Frontend is deployed on Vercel.
- `main` is the production branch, so merge carefully.
