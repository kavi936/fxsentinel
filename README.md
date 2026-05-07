# FXSentinel

FXSentinel is a forex market analysis platform with a React frontend and Flask backend.

## New Developer Start Here

If you are onboarding to this project, read these files first:

1. `CONTRIBUTING.md` - team workflow, PR flow, and setup steps
2. `docs/BRANCH_NAMING.md` - branch naming rules
3. `.github/pull_request_template.md` - required PR format and checklist
4. `docs/README.md` - detailed project and environment setup

## Quick Project Map

- `src/` - frontend (React + Vite)
- `backend/` - Flask backend
- `backend/services/` - backend service logic
- `env.example` - environment variable names
- `.env` - local secrets (do not commit)

## Run Locally

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## Team Collaboration Rules

- `main` is the production branch.
- No direct pushes to `main`.
- All changes must go through Pull Requests.
- Keep PRs small and focused.
- Never commit API keys or secrets.

## Deployment

- Backend: Railway
- Frontend: Vercel

