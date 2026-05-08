# FXSentinel - First Contribution Flow (Landing Page)

Use this exact process for your first task.  
Goal: make a safe landing page update without touching production directly.

---

## 0) Before you start

Read these files first:

- `README.md`
- `CONTRIBUTING.md`
- `docs/BRANCH_NAMING.md`

Why: these files define how we work together and prevent accidental mistakes.

---

## 1) Get latest code from `main`

```bash
git checkout main
git pull origin main
```

### What this does

- `git checkout main` moves you to the main branch.
- `git pull origin main` downloads and applies the newest commits from GitHub.

### Why this matters

You should always branch from the latest `main` so your work starts from the most recent stable version.

---

## 2) Create your working branch (landing page task)

```bash
git checkout -b feat/landing-page-improvements
```

### What this does

- Creates a new branch.
- Switches you to that branch immediately.

### Why this matters

You can safely work without changing `main`.  
All your edits stay isolated until reviewed in a PR.

---

## 3) Make your changes (landing page only)

### Scope for this task

- Edit only landing page related files.
- Example areas: `src/components/` and related CSS.

### Avoid for this task

- Backend files (`backend/`)
- Unrelated components/pages
- Large refactors

### Why this matters

Small focused changes are easier to review, test, and merge safely.

---

## 4) Save your work with a commit

```bash
git add .
git commit -m "Improve landing page hero and CTA"
```

### What this does

- `git add .` stages changed files for commit.
- `git commit -m "..."` creates a saved checkpoint in your branch history.

### Commit message example style

- Good: `Improve landing page hero and CTA`
- Good: `Fix landing page mobile spacing`
- Avoid: `update`, `changes`, `wip`

### Why this matters

Clear commit messages help reviewers understand intent quickly.

---

## 5) Push your branch to GitHub

```bash
git push -u origin feat/landing-page-improvements
```

### What this does

- Uploads your local branch to GitHub.
- `-u` sets upstream tracking so future pushes can be just `git push`.

### Why this matters

Your teammate cannot review your work until it is on GitHub.

---

## 6) Open a Pull Request (PR) to `main`

In GitHub:

- Base branch: `main`
- Compare branch: `feat/landing-page-improvements`

Fill the PR template:

- What changed
- Why it was changed
- How you tested

Also add:

- Before/after screenshots for UI changes

### Why this matters

PR is the review gate before production branch updates.

---

## Rules (must follow)

- Do **NOT** push directly to `main`.
- Keep PR small (landing page only for this first task).
- Do not commit API keys, `.env`, or any secrets.

---

## If `main` gets new commits while you are still working

Run:

```bash
git checkout main
git pull origin main
git checkout feat/landing-page-improvements
git merge main
```

### What this does

- Updates your branch with latest `main` changes.

### Why this matters

Keeps your PR current and reduces merge conflicts later.

---

## If you hit a merge conflict

1. Open conflicted files and resolve the marked sections.
2. Save files.
3. Stage and commit conflict resolution:

```bash
git add .
git commit -m "Resolve merge conflicts with main"
git push
```

If unsure, ask before resolving blindly.

