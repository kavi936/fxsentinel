# FXSentinel Dashboard Onboarding — Plan & Journal

> **Purpose:** A living document to plan and journal the implementation of an onboarding user experience for the FXSentinel dashboard. The goal is to reduce churn by helping users (both new and returning) understand and use the platform effectively.

---

## 1. Context & Rationale

### 1.1 Current User Flow

```
Landing Page → Sign Up / Log In → Dashboard (Overview)
```

- Trial Welcome exists for users who need payment setup but may be bypassed depending on flow.
- Users land directly on the Dashboard Overview with no orientation.

### 1.2 The Problem

- **Founder knows the product; new users don't.** The dashboard is dense: 6 main cards (Economic Calendar, AI Analysis, Market Sentiment, Live News, Prediction Markets, Central Bank), 3 tabs (Overview, Economies, Alerts), plus multiple settings/context popups.
- **High churn hypothesis:** Users leave because they don't understand what they're seeing or how to act on it.
- **Existing help:** `InfoIcon` tooltips exist on card headers but require hover—easy to miss, especially on mobile.

### 1.3 Goals for Onboarding

| Goal | Description |
|------|-------------|
| **Reduce confusion** | Orient users to what each area does and why it matters |
| **Improve discoverability** | Surface core actions (e.g., click event → AI analysis, set up Telegram) |
| **Support all users** | Available for both first-time and returning users |
| **Cross-device** | Seamless on mobile and desktop |

---

## 2. Scope & Requirements

### 2.1 Who Gets Onboarding?

| User Type | First Visit | Return Visit |
|-----------|-------------|--------------|
| **New user** | Auto-prompted (can skip) | Can replay via Profile → "Product tour" |
| **Returning user** | Can replay via Profile → "Product tour" | Same |

- **No restriction to new signups only.** Onboarding is always accessible so users can reorient themselves after time away.
- **Manual replay:** Entry point in **Profile popup** with label **"Product tour"**.

### 2.2 Where Does Onboarding Run?

| Location | Priority |
|----------|----------|
| **Dashboard → Overview tab** | Primary. Main tour (8 steps). |
| **Dashboard → Alerts tab** | Part of main tour (step 8). Includes "Set up Telegram" with "Skip for now" option. |
| **Dashboard → Economies tab** | Separate tab-specific onboarding when user opens Economies for the first time. |

**Scope:** Main tour covers Overview + Alerts. Economies gets its own first-time tour on tab open.

### 2.3 Device Support

| Device | Considerations |
|--------|----------------|
| **Desktop / Laptop** | Spotlight/highlight + overlay; pointer-based tooltips |
| **Mobile / Tablet** | Touch-friendly; avoid small hotspots; full-screen or modal steps if spotlight is awkward on small viewports |
| **Responsive** | Same content, different layout—steps may collapse or simplify on narrow screens |

---

## 3. Design Decisions

### 3.1 Trigger Logic

| Trigger | When | Notes |
|---------|------|------|
| **First-time (auto)** | Dashboard Overview loads + all UI ready; user has no completion flag | Start immediately when ready (no artificial delay). `localStorage` key `fxsentinel_onboarding_${userId}`. |
| **Manual replay** | User clicks "Take tour" / "Help" / similar | Always available; ignores completion flag |

**Decision:** Use `localStorage` with user ID (e.g. `fxsentinel_onboarding_${userId}`). Auto-show when dashboard + UI are loaded (no delay). If user skips: record for analytics; "Product tour" stays in Profile for manual replay.

### 3.2 Tour Length & Steps

**Confirmed order (8 steps):**

| Step | Target | Message (draft) |
|------|--------|-----------------|
| 1 | Navbar (all main tabs) | Welcome to FXSentinel. Your dashboard has three main areas: Overview, Economies, and Alerts. |
| 2 | Economic Calendar | Track high-impact economic events here. Click an event to see AI analysis. |
| 3 | AI Analysis | AI explains how each release affects major pairs. **Trial: 15 AI analyses/day.** Upgrade for more. |
| 4 | Market Sentiment | Market sentiment and volatility metrics help you gauge risk appetite. |
| 5 | Live News | Real-time news with AI analysis. Stay ahead of breaking moves. |
| 6 | Prediction Markets | See how markets price Fed decisions and other events—useful for positioning. |
| 7 | Central Bank | Official central bank docs and minutes for deeper research. |
| 8 | Alerts tab / Settings | Set up Telegram alerts here. **Skip for now** if you prefer. Timezone in nav. |

**Content guidelines:**
- **Tone:** Professional, educational; works for any experience level.
- **Depth:** Short by default; longer explanations where needed (e.g. AI Analysis, Telegram setup).
- **Trial limit:** Explicitly call out 15 AI analyses/day on the AI Analysis step.
- **Telegram:** Step 8 points to Alerts tab; include "Skip for now" so it's non-blocking.

**Mobile:** Same style and layout. Step targets may differ (buttons in different positions). Implementer decides specifics.

### 3.3 UX Patterns

| Pattern | Desktop | Mobile |
|---------|---------|--------|
| **Spotlight / highlight** | Highlight target element with dimmed backdrop | Same, but ensure touch targets are large enough |
| **Tooltip / popover** | Position beside or below highlighted element | Full-width modal-style step if viewport is small |
| **Navigation** | "Next" / "Back" / "Skip tour" | Same; large tap targets |
| **Dismiss** | "×" or "Got it" on final step | Same |

### 3.4 Persistence & State

| Data | Storage | Purpose |
|------|--------|---------|
| Tour completed | `localStorage` key `fxsentinel_onboarding_${userId}` | Don't auto-show again |
| User ID | From AuthContext | Scoped completion per user |
| Step index | React state | Current step during tour |
| Analytics events | Firebase Analytics / GA4 | See Section 9 |

---

## 4. Technical Approach

### 4.1 Library Evaluation & Recommendation

**Criteria for FXSentinel:** 8 steps, spotlight/highlight, mobile + desktop, touch-friendly (≥44px), resizable grid targets, empty-state highlighting, analytics hooks, dark theme styling, minimal bundle impact.

| Library | Bundle (gzip) | Deps | Weekly DLs | Mobile | Customization | React | Notes |
|---------|---------------|------|-------------|--------|---------------|-------|-------|
| **Driver.js** | ~5 KB | 0 | ~450K | ✅ Good | High | Vanilla (any framework) | Smallest, actively maintained (2025), TypeScript |
| **Intro.js** | ~10–12 KB | 0 | ~80K | ✅ | Basic | Vanilla | Simple API, heavier, older look |
| **Shepherd.js** | ~30+ KB | Floating UI | ~120K | ✅ (Floating UI) | Very high | Recipe/hook | Most flexible, more setup |
| **React Joyride** | ~15 KB | 11 (incl. react-floater) | ~200K | ✅ | Medium | Native React | Last release ~1 yr ago |

**Detailed evaluation:**

| Factor | Driver.js | Intro.js | Shepherd.js |
|--------|-----------|----------|-------------|
| **Bundle impact** | ~5 KB gzipped — smallest of all | ~10–12 KB | ~30+ KB with deps |
| **API** | `driver({ steps })`; `onHighlightStarted`, `onDestroyed` etc. | `introJs().start()` | Tour + Steps; more verbose |
| **Element targeting** | CSS selectors, `element` or `popover`-only steps | `data-intro`, `data-step` | `element`, `attachTo` |
| **Lifecycle hooks** | `onHighlightStarted`, `onHighlighted`, `onDeselected`, `onDestroyStarted` | `oncomplete`, `onexit` | `beforeShow`, `show`, `hide` |
| **Styling** | CSS vars, `popoverClass`, `overlayColor`, `showProgress` | Themes, limited | Full control |
| **Empty / missing element** | Can use `popover`-only step (no highlight) | Similar | Similar |
| **Resizable layout** | Recalculates on step change; `refresh()` if needed | Similar | Similar |
| **License** | MIT | GPLv3 / commercial (v8+) | MIT |

**Recommendation: Driver.js**

- **Smallest footprint** — ~5 KB fits our performance goals.
- **Zero dependencies** — no extra bloat.
- **Lifecycle hooks** — `onHighlightStarted`, `onDestroyed` support analytics (start, complete, skip, step viewed).
- **Popover-only steps** — handles empty state or hidden elements via `popover: { ... }` without `element`.
- **Active maintenance** — releases in 2025.
- **Framework-agnostic** — works with React; import and drive from a `useEffect` or component.

**Fallback:** If Driver.js hits layout or resizable-grid issues, Shepherd.js is the next option for maximum flexibility; Intro.js is simpler but heavier and AGPL-licensed for recent versions.

### 4.2 Component Structure

```
Dashboard.jsx
  └── OnboardingTour.jsx (or useDriver.js setup)
        - Wraps / drives steps when active
        - Reads user from AuthContext
        - Uses localStorage for completion
        - Renders trigger button for manual replay
```

**Integration points:**
- Mount `OnboardingTour` inside `Dashboard` (or at App level with dashboard context).
- Trigger on: (a) first Dashboard Overview load for user without completion flag, or (b) manual "Take tour" click.
- Steps target DOM elements via selectors (e.g. `data-onboarding="economic-calendar"`).

### 4.3 Selectors Strategy

Add `data-onboarding` attributes to key elements so the tour can reliably target them even if classes change:

```html
<!-- Example -->
<div data-onboarding="nav-overview" ...>Overview</div>
<div data-onboarding="economic-calendar" ...>...</div>
<div data-onboarding="ai-analysis" ...>...</div>
...
```

**Fallback:** If an element isn't in DOM (e.g. different tab), skip that step or show a generic message.

### 4.4 Mobile Considerations

| Issue | Approach |
|------|----------|
| Elements off-screen | Scroll target into view before highlighting, or use a generic "floating" step |
| Resizable grid | Cards may move; use stable parent containers or section wrappers for targets |
| Touch targets | Ensure buttons are ≥44px; add padding to step CTAs |
| Viewport | Test on 320px–768px widths |
| Orientation change | Pause/resume or recalc step position if needed |
| **MobileWarningBanner** | **Remove.** Onboarding replaces it. Tour runs without banner clutter. |

### 4.5 Edge Cases

| Case | Behavior |
|------|----------|
| **Tab switching** | If user lands on Alerts or Economies (not Overview): show short "Start here" prompt and guide them to Overview for the full tour. (Implementation TBD: redirect + tour, or overlay CTA.) |
| **Resized/collapsed grid** | Highlight target anyway, or reset to default layout before tour. New users typically have default grid. |
| **Empty state** | Highlight regardless. No data? Still show the step—e.g. "Events will appear here when scheduled." |

---

## 5. Implementation Phases

### Phase 1: Planning & Setup (Current)
- [x] Create this journal/plan document
- [x] Capture product decisions from Q&A
- [x] Choose library — **Driver.js** (see Section 4.1)
- [ ] Finalise step copy
- [ ] Add `data-onboarding` attributes to Overview, nav, Alerts

### Phase 2: Core Tour
- [ ] Remove `MobileWarningBanner` component
- [ ] Install and wire Driver.js (or equivalent)
- [ ] Implement `OnboardingTour` component
- [ ] Implement first-time trigger + localStorage completion
- [ ] Add "Product tour" link in Profile popup
- [ ] Add onboarding analytics (Section 9)
- [ ] Desktop testing

### Phase 3: Mobile Polish
- [ ] Responsive step positioning (step targets may differ on mobile)
- [ ] Touch-friendly buttons (≥44px)
- [ ] Test on real devices / emulators

### Phase 4: Economies Tab Tour (Later)
- [ ] First-time trigger when user opens Economies tab
- [ ] Separate step sequence for Economies content

### Phase 5: Iterate
- [ ] Ship after full testing + feedback
- [ ] Measure: tour completion rate, feature usage, GA4 churn

---

## 6. Journal Entries

### 2025-03-04 — Document Created

**Decisions:**
- Onboarding for all users (new + returning), not just new signups.
- Starts on Dashboard Overview; optional expansion to Economies and Alerts later.
- Must work on mobile and desktop.
- Will use `localStorage` with user ID for completion state; manual replay always available.

### 2025-03-04 — Product Q&A Integrated

**Decisions captured:**
- Auto-show when dashboard + UI loaded (no delay). Entry: Profile popup, label "Product tour".
- Tone: Professional, educational. Depth: short by default, longer where needed.
- Trial limit: 15 AI analyses/day on AI Analysis step.
- Step order: Navbar → Economic Calendar → AI Analysis → Market Sentiment → News → Prediction Markets → Central Bank → Alerts (Telegram "Skip for now").
- Economies: Separate first-time tab onboarding. Mobile: Remove MobileWarningBanner.
- Analytics: tour_started, tour_completed, tour_skipped, step_viewed. English only v1.

**Next steps:** Choose library, implement tour, add "Product tour" to Profile.

### 2025-03-04 — Library Evaluation

**Compared:** Driver.js, Intro.js, Shepherd.js, React Joyride.

**Chosen:** Driver.js — ~5 KB gzipped, 0 deps, lifecycle hooks for analytics, popover-only steps for empty state, active maintenance. See Section 4.1.

---

## 7. Resolved / Open Items

| Item | Status |
|------|--------|
| "Product tour" location | Profile popup |
| Analytics events | All 4: started, completed, skipped, step_viewed |
| Economies tour | Separate, on first tab open (Phase 4) |
| Tab switching (land on Alerts/Economies) | Show "Start here" → guide to Overview (impl TBD) |
| Languages | English only for v1 |

---

## 8. File Checklist (For Implementation)

| File | Action |
|------|--------|
| `docs/ONBOARDING_PLAN.md` | This document — update as we go |
| `src/components/OnboardingTour.jsx` | New component |
| `src/components/OnboardingTour.css` | Styles (if needed beyond library) |
| `src/components/Dashboard.jsx` | Integrate OnboardingTour, remove MobileWarningBanner |
| `src/components/Overview.jsx` | Add `data-onboarding` attributes to cards |
| `src/components/Alerts.jsx` | Add `data-onboarding` for Alerts step |
| `src/components/ProfilePopup.jsx` | Add "Product tour" link |
| `src/components/MobileWarningBanner.jsx` | Remove (or stop rendering in Dashboard) |
| `src/utils/analytics.js` | Add onboarding event helpers |
| `package.json` | Add driver.js (or chosen lib) |

---

## 9. Analytics Implementation

**Storage:** Firebase Analytics (client-side) → GA4. No backend storage. Use existing `src/utils/analytics.js` pattern.

**Events to add:**

| Event | When | Suggested payload |
|-------|------|-------------------|
| `onboarding_tour_started` | User sees first step (auto or manual) | `{ trigger: 'auto' \| 'manual', step_index: 0 }` |
| `onboarding_tour_completed` | User finishes last step | `{ total_steps: 8 }` |
| `onboarding_tour_skipped` | User clicks "Skip tour" | `{ step_index, total_steps }` |
| `onboarding_step_viewed` | Each step is shown | `{ step_index, step_target, total_steps }` |

**Implementation:** Add helpers to analytics.js or use `trackEngagement` with these event names. Call from `OnboardingTour`.

**Success metrics (GA4):** Tour completion rate, churn/retention, feature usage (calendar, AI analysis, alerts).

---

*Last updated: 2025-03-04*

---

*All Q&A responses were integrated into sections 2–9.*
