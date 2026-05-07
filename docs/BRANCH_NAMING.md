# FXSentinel Branch Naming Guide

## Why this exists

Consistent branch names make collaboration easier, especially when multiple developers open PRs at the same time.

## Format

`<type>/<short-description>`

Where:

- `type` is one of `feat`, `fix`, `chore`, `docs`
- `short-description` is lowercase words separated by hyphens

## Allowed Types

- `feat` - new functionality
- `fix` - bug fixes
- `chore` - refactors, cleanup, configuration, tooling
- `docs` - markdown/docs only

## Examples

- `feat/landing-page-cta-improvement`
- `feat/landing-mobile-layout`
- `fix/landing-navbar-overflow`
- `chore/remove-unused-components`
- `docs/update-onboarding-guide`

## Rules

- Keep branch names short and clear.
- One branch should map to one PR goal.
- Do not reuse old branches for unrelated tasks.
- Create new branches from the latest `main`.

## Recommended First Branch For New Developer

`feat/landing-page-improvements`

