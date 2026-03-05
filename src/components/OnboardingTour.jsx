import React, { useCallback, useEffect, useRef } from 'react';
import { driver } from 'driver.js';
import 'driver.js/dist/driver.css';
import {
  trackOnboardingStarted,
  trackOnboardingCompleted,
  trackOnboardingSkipped,
  trackOnboardingStepViewed
} from '../utils/analytics';
import './OnboardingTour.css';

const TOTAL_STEPS = 9;

const STEPS = [
  {
    element: '[data-onboarding="nav-tabs"]',
    popover: {
      title: 'Welcome to FXSentinel',
      description: 'Your dashboard has three main areas: <strong>Overview</strong>, <strong>Economies</strong>, and <strong>Alerts</strong>. Use the tabs to switch between them.',
      side: 'bottom',
      align: 'center'
    }
  },
  {
    element: '[data-onboarding="economic-calendar"]',
    popover: {
      title: 'Economic Calendar',
      description: 'Track <strong>nearly all major economic events</strong> here. Click an event to see AI analysis of its market impact on the right.',
      side: 'right',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="ai-analysis"]',
    popover: {
      title: 'AI Analysis',
      description: 'AI that <strong>easily explains</strong> how each release affects major currency pairs. <strong>Trial: 15 AI analyses per month.</strong> Upgrade for more.',
      side: 'left',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="market-sentiment"]',
    popover: {
      title: 'Market Sentiment',
      description: '<strong>Market sentiment and volatility metrics</strong> help you gauge risk appetite and positioning across major pairs.',
      side: 'right',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="live-news"]',
    popover: {
      title: 'Live News',
      description: '<strong>Real-time news</strong> with embedded AI analysis. Stay ahead of breaking moves and understand how and which headlines are affecting markets.',
      side: 'left',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="prediction-markets"]',
    popover: {
      title: 'Prediction Markets',
      description: 'See how markets price <strong>key events such as Fed decisions</strong> and other macro events—useful for positioning before releases.',
      side: 'right',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="central-bank"]',
    popover: {
      title: 'Central Bank',
      description: 'Official central bank documents, <strong>meeting minutes, COT reports</strong> and other data for deeper research. <strong>AI analysis coming soon.</strong>',
      side: 'left',
      align: 'start'
    }
  },
  {
    element: '[data-onboarding="nav-economies"]',
    popover: {
      title: 'Economies Tab',
      description: 'View the most important <strong>country-level macro data</strong>: GDP, inflation, interest rates, and key indicators for each economy.',
      side: 'bottom',
      align: 'center',
      popoverOffset: 16
    }
  },
  {
    element: '[data-onboarding="nav-alerts"]',
    popover: {
      title: 'Alerts & Settings',
      description: 'Set up <strong>Telegram alerts</strong> here to get notified on news and events—so you don\'t need to search WHY. <strong>Skip for now</strong> if you prefer. Timezone in nav settings.',
      side: 'bottom',
      align: 'center',
      popoverOffset: 16,
      doneBtnText: "You're all set"
    }
  }
];

/**
 * OnboardingTour - Product tour for FXSentinel Dashboard
 * Uses Driver.js. Triggers on first Dashboard Overview load (unless completed) or manual "Product tour" from Profile.
 * See docs/ONBOARDING_PLAN.md
 */
const OnboardingTour = ({
  userId,
  activeTab,
  isOverviewReady,
  onStartTour,
  trigger = 'manual'
}) => {
  const driverRef = useRef(null);
  const hasTrackedStart = useRef(false);
  const hasAutoStarted = useRef(false);
  const startTourRef = useRef(null);

  const startTour = useCallback((triggerOverride = null) => {
    if (!userId) return;
    const effectiveTrigger = triggerOverride ?? trigger;

    // Expand nav tabs so step 1 and 8 targets are visible (Dashboard does this for auto; ensure for manual)
    onStartTour?.();

    const performDestroy = (opts) => {
      // Defer to next tick—avoids re-entry issues when Driver.js is mid-callback.
      setTimeout(() => opts.driver.destroy(), 0);
    };

    const driverObj = driver({
      showProgress: true,
      progressText: '{{current}} of {{total}}',
      nextBtnText: 'Next',
      prevBtnText: 'Back',
      doneBtnText: "You're all set",
      allowClose: true,
      overlayColor: 'rgba(0, 0, 0, 0.75)',
      popoverClass: 'fxsentinel-onboarding-popover',
      stagePadding: 12,
      steps: STEPS,
      onHighlightStarted: (element, step, opts) => {
        const index = opts.state?.activeIndex ?? 0;
        const target = STEPS[index]?.element || 'unknown';
        // Ensure nav is expanded for Economies/Alerts steps (8 & 9)—targets are hidden when collapsed.
        if ((index === 7 || index === 8) && onStartTour) onStartTour();
        if (index === 0 && !hasTrackedStart.current) {
          trackOnboardingStarted(effectiveTrigger);
          hasTrackedStart.current = true;
        }
        trackOnboardingStepViewed(index, target, TOTAL_STEPS);
      },
      onDestroyStarted: (element, step, opts) => {
        const index = opts.state?.activeIndex ?? 0;
        if (index === TOTAL_STEPS - 1) {
          trackOnboardingCompleted(TOTAL_STEPS);
          try {
            localStorage.setItem(`fxsentinel_onboarding_${userId}`, 'completed');
          } catch (e) {
            console.warn('Onboarding: localStorage set failed', e);
          }
        } else {
          trackOnboardingSkipped(index, TOTAL_STEPS);
        }
        // Driver.js returns early when onDestroyStarted is used—we must call destroy() to actually close.
        performDestroy(opts);
      },
      onCloseClick: (element, step, opts) => {
        // Explicit close handler: track skip, then destroy. Ensures × button always closes the tour.
        const index = opts.state?.activeIndex ?? 0;
        trackOnboardingSkipped(index, TOTAL_STEPS);
        performDestroy(opts);
      }
    });

    driverRef.current = driverObj;
    // Defer drive so nav expansion (onStartTour) has time to paint—prevents step 1 flickering
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        driverObj.drive();
      });
    });
  }, [userId, trigger, onStartTour]);

  startTourRef.current = startTour;

  // Auto-start for first-time users when Overview is ready
  // Note: Intentionally omit startTour from deps - Dashboard re-renders (e.g. time tick) would reset the timeout and cause flicker
  useEffect(() => {
    if (trigger !== 'auto' || !userId || !isOverviewReady || activeTab !== 'overview') return;
    const completed = localStorage.getItem(`fxsentinel_onboarding_${userId}`);
    if (completed) return;
    if (hasAutoStarted.current) return;

    const t = setTimeout(() => {
      if (document.body.classList.contains('driver-active')) return;
      hasAutoStarted.current = true;
      startTourRef.current?.();
    }, 300);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- startTour omitted to prevent effect re-runs on Dashboard re-renders
  }, [userId, isOverviewReady, activeTab, trigger]);

  // Expose startTour and reset for manual replay / dev (Profile uses startOnboardingTour())
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.__fxsentinelStartOnboardingTour = () => {
        hasTrackedStart.current = false;
        startTour('manual');
      };
      window.__fxsentinelResetOnboarding = () => {
        const keys = [];
        for (let i = 0; i < localStorage.length; i++) {
          const k = localStorage.key(i);
          if (k?.startsWith('fxsentinel_onboarding_')) keys.push(k);
        }
        keys.forEach(k => localStorage.removeItem(k));
        console.log('Onboarding reset. Refresh the page to run the tour again.');
      };
    }
    return () => {
      if (typeof window !== 'undefined') {
        delete window.__fxsentinelStartOnboardingTour;
        delete window.__fxsentinelResetOnboarding;
      }
    };
  }, [startTour]);

  return null;
};

export default OnboardingTour;

/**
 * Helper: call from Profile or anywhere to start the tour manually.
 * Requires OnboardingTour to be mounted (Dashboard).
 */
export const startOnboardingTour = () => {
  if (typeof window !== 'undefined' && window.__fxsentinelStartOnboardingTour) {
    window.__fxsentinelStartOnboardingTour();
  }
};
