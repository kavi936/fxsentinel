import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMeta } from '../hooks/useMeta';
import { config } from '../config';
import './Auth.css';
import './OnboardingSurvey.css';
import logoPng from '../assets/fxsentinel_logo_nobg.png';
import logoWebp from '../assets/fxsentinel_logo_nobg.webp';
import { BackgroundBeams } from './BackgroundBeams';
import { PRESET_MARKET_INSTRUMENTS } from '../constants/forexPairs';
import {
  PRIMARY_GOALS,
  REFERRAL_SOURCES,
  labelForPrimaryGoal,
  labelForReferralSource,
} from '../constants/onboardingSurveyOptions';
import { parseInstrumentSymbol } from '../utils/instrumentInput';

const TRADING_STYLES = [
  { value: 'day', label: 'Day trading', hint: 'Intraday decisions' },
  { value: 'swing', label: 'Swing trading', hint: 'Positions over days or weeks' },
  { value: 'both', label: 'Both', hint: 'Mix of styles' },
  { value: 'unsure', label: 'Not sure yet', hint: 'Still exploring' },
];

const EXPERIENCE = [
  { value: 'beginner', label: 'Beginner', hint: 'Learning the ropes' },
  { value: 'intermediate', label: 'Intermediate', hint: 'Comfortable with charts & news' },
  { value: 'advanced', label: 'Advanced', hint: 'Experienced with macro & risk' },
];

const STEP_TITLES = [
  'Welcome',
  'How you trade',
  'Your level',
  'Markets you follow',
  'Your goal',
  'How you found us',
  'Almost there',
];

const STEP_COUNT = STEP_TITLES.length;

const OnboardingSurvey = () => {
  useMeta(
    'Personalize your workspace | FXSentinel',
    'Tell us how you trade so we can tailor defaults and language. Takes about a minute.'
  );
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);
  const [tradingStyle, setTradingStyle] = useState('day');
  const [experienceLevel, setExperienceLevel] = useState('intermediate');
  const [selectedPairs, setSelectedPairs] = useState(() => new Set(['EUR/USD', 'GBP/USD', 'USD/JPY']));
  const [customPair, setCustomPair] = useState('');
  const [primaryGoal, setPrimaryGoal] = useState('stay_informed');
  const [referralSource, setReferralSource] = useState('prefer_not_say');
  const [marketingOptIn, setMarketingOptIn] = useState(false);

  const fetchProfile = useCallback(async () => {
    if (!currentUser) return;
    setLoading(true);
    setError('');
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.message || data.error || `Request failed (${res.status})`);
      }
      if (data.needs_survey === false) {
        navigate('/dashboard', { replace: true });
        return;
      }
      const tp = data.trader_profile || {};
      if (tp.trading_style) setTradingStyle(tp.trading_style);
      if (tp.experience_level) setExperienceLevel(tp.experience_level);
      if (Array.isArray(tp.primary_pairs) && tp.primary_pairs.length) {
        setSelectedPairs(new Set(tp.primary_pairs));
      }
      if (typeof tp.marketing_opt_in === 'boolean') setMarketingOptIn(tp.marketing_opt_in);
      if (tp.primary_goal) setPrimaryGoal(tp.primary_goal);
      if (tp.referral_source) setReferralSource(tp.referral_source);
    } catch (e) {
      setError(e.message || 'Could not load your profile. Try again.');
    } finally {
      setLoading(false);
    }
  }, [currentUser, navigate]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const togglePair = (pair) => {
    setSelectedPairs((prev) => {
      const next = new Set(prev);
      if (next.has(pair)) next.delete(pair);
      else next.add(pair);
      return next;
    });
  };

  const addCustomPair = () => {
    const p = parseInstrumentSymbol(customPair);
    if (!p) {
      setError('Use BASE/QUOTE — e.g. EUR/USD, XAU/USD, US500/USD, GER40/EUR.');
      return;
    }
    setError('');
    setSelectedPairs((prev) => new Set([...prev, p]));
    setCustomPair('');
  };

  const goNext = () => {
    setError('');
    if (step === 3 && selectedPairs.size < 1) {
      setError('Select or add at least one market to continue.');
      return;
    }
    setStep((s) => Math.min(s + 1, STEP_COUNT - 1));
  };

  const goBack = () => {
    setError('');
    setStep((s) => Math.max(s - 1, 0));
  };

  const submitSkip = async () => {
    if (!currentUser) return;
    setSubmitting(true);
    setError('');
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ skipped: true }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.error || 'Save failed');
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setError(e.message || 'Could not save. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const submitComplete = async () => {
    if (!currentUser) return;
    const pairs = [...selectedPairs];
    if (pairs.length < 1) {
      setError('Select or add at least one market.');
      setStep(3);
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      const token = await currentUser.getIdToken();
      const res = await fetch(`${config.API_BASE_URL}/api/user/trader-profile`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          skipped: false,
          trading_style: tradingStyle,
          experience_level: experienceLevel,
          primary_pairs: pairs,
          marketing_opt_in: marketingOptIn,
          primary_goal: primaryGoal,
          referral_source: referralSource,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.message || data.error || 'Save failed');
      navigate('/dashboard', { replace: true });
    } catch (e) {
      setError(e.message || 'Could not save. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!currentUser) {
    return null;
  }

  const progressPct = ((step + 1) / STEP_COUNT) * 100;
  const isLastStep = step === STEP_COUNT - 1;

  return (
    <div className="auth-container onboarding-survey-page">
      <div className="auth-background">
        <BackgroundBeams />
      </div>

      <div className="auth-main-stack onboarding-survey-stack">
        <div className="auth-card onboarding-survey-card">
          <div className="onboarding-survey-brand">
            <Link to="/" className="auth-logo">
              <picture>
                <source srcSet={logoWebp} type="image/webp" />
                <img src={logoPng} alt="FXSentinel Logo" style={{ height: '36px', width: 'auto' }} />
              </picture>
            </Link>
          </div>

          {loading ? (
            <div className="onboarding-survey-loading">
              <div className="onboarding-survey-spinner" />
              <p>Loading…</p>
            </div>
          ) : (
            <div className="onboarding-wizard">
              <div className="onboarding-wizard-header">
                <div className="onboarding-wizard-header-row">
                  <span className="onboarding-step-label">
                    Step {step + 1} of {STEP_COUNT}
                  </span>
                  <button
                    type="button"
                    className="onboarding-skip-btn onboarding-skip-btn--inline"
                    disabled={submitting}
                    onClick={submitSkip}
                  >
                    Skip for now
                  </button>
                </div>
                <div className="onboarding-progress-track" aria-hidden="true">
                  <div className="onboarding-progress-fill" style={{ width: `${progressPct}%` }} />
                </div>
                <p className="onboarding-step-title">{STEP_TITLES[step]}</p>
              </div>

              {error && (
                <div className="auth-error onboarding-wizard-error">
                  <span className="error-icon">⚠️</span>
                  {error}
                </div>
              )}

              <div className="onboarding-step-outer" key={step}>
                <div className="onboarding-step-panel">
                  {step === 0 && (
                    <div className="onboarding-step-welcome">
                      <h1 className="onboarding-welcome-headline">Personalize your workspace</h1>
                      <p className="onboarding-welcome-lead">
                        A short walkthrough helps us set <strong>sensible defaults</strong> and tune explanations to{' '}
                        <strong>how you trade</strong>. You can change everything later in <strong>Profile</strong>.
                      </p>
                      <ul className="onboarding-welcome-list">
                        <li>
                          <strong>Trading style & experience</strong>
                        </li>
                        <li>
                          <strong>Markets you follow</strong> (FX, commodities, indices —{' '}
                          <strong>not single stocks</strong>)
                        </li>
                        <li>
                          <strong>Optional updates</strong> by email
                        </li>
                      </ul>
                      <p className="onboarding-welcome-footnote">Takes about one minute.</p>
                    </div>
                  )}

                  {step === 1 && (
                    <div className="onboarding-survey-section">
                      <p className="onboarding-step-question">How do you usually trade?</p>
                      <div className="onboarding-survey-options">
                        {TRADING_STYLES.map((o) => (
                          <label
                            key={o.value}
                            className={`onboarding-radio ${tradingStyle === o.value ? 'is-selected' : ''}`}
                          >
                            <input
                              type="radio"
                              name="trading_style"
                              value={o.value}
                              checked={tradingStyle === o.value}
                              onChange={() => setTradingStyle(o.value)}
                            />
                            <span className="onboarding-radio-label">{o.label}</span>
                            <span className="onboarding-radio-hint">{o.hint}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 2 && (
                    <div className="onboarding-survey-section">
                      <p className="onboarding-step-question">How would you describe your experience with FX and macro?</p>
                      <div className="onboarding-experience-grid">
                        {EXPERIENCE.map((o) => (
                          <button
                            key={o.value}
                            type="button"
                            className={`onboarding-exp-card ${experienceLevel === o.value ? 'is-selected' : ''}`}
                            onClick={() => setExperienceLevel(o.value)}
                          >
                            <span className="onboarding-exp-card-title">{o.label}</span>
                            <span className="onboarding-exp-card-hint">{o.hint}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 3 && (
                    <div className="onboarding-survey-section onboarding-step-markets">
                      <p className="onboarding-step-question">Which markets do you want to prioritize?</p>
                      <p className="onboarding-survey-sub">
                        FXSentinel focuses on macro: FX, commodities, indices, and related markets — not individual
                        stocks. Pick from the list or add your broker symbol below. Not financial advice.
                      </p>
                      <div className="onboarding-pair-scroll" role="region" aria-label="Preset markets">
                        <div className="onboarding-pair-grid">
                          {PRESET_MARKET_INSTRUMENTS.map((pair) => (
                            <label key={pair} className="onboarding-pair-tile">
                              <input
                                type="checkbox"
                                checked={selectedPairs.has(pair)}
                                onChange={() => togglePair(pair)}
                              />
                              <span>{pair}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                      <div className="onboarding-custom-own">
                        <p className="onboarding-custom-own-title">Not in the list?</p>
                        <p className="onboarding-custom-own-hint">
                          Add your own as <strong>BASE/QUOTE</strong> (e.g. <span className="onboarding-code">US500/USD</span>,{' '}
                          <span className="onboarding-code">XAG/USD</span>, <span className="onboarding-code">GER40/EUR</span>).
                        </p>
                        <div className="onboarding-custom-pair">
                          <input
                            type="text"
                            placeholder="e.g. US500/USD"
                            value={customPair}
                            onChange={(e) => setCustomPair(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCustomPair())}
                            aria-label="Custom market symbol"
                          />
                          <button type="button" className="onboarding-add-btn" onClick={addCustomPair}>
                            Add
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {step === 4 && (
                    <div className="onboarding-survey-section">
                      <p className="onboarding-step-question">What is your primary goal with FXSentinel?</p>
                      <p className="onboarding-survey-sub">Choose the closest match — you still get the full workspace.</p>
                      <div className="onboarding-survey-options onboarding-goal-options">
                        {PRIMARY_GOALS.map((o) => (
                          <label
                            key={o.value}
                            className={`onboarding-radio ${primaryGoal === o.value ? 'is-selected' : ''}`}
                          >
                            <input
                              type="radio"
                              name="primary_goal"
                              value={o.value}
                              checked={primaryGoal === o.value}
                              onChange={() => setPrimaryGoal(o.value)}
                            />
                            <span className="onboarding-radio-label">{o.label}</span>
                            <span className="onboarding-radio-hint">{o.hint}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 5 && (
                    <div className="onboarding-survey-section">
                      <p className="onboarding-step-question">How did you hear about us?</p>
                      <p className="onboarding-survey-sub">Helps us understand what is working. Optional to be specific.</p>
                      <div className="onboarding-referral-grid">
                        {REFERRAL_SOURCES.map((o) => (
                          <button
                            key={o.value}
                            type="button"
                            className={`onboarding-referral-chip ${referralSource === o.value ? 'is-selected' : ''}`}
                            onClick={() => setReferralSource(o.value)}
                          >
                            {o.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {step === 6 && (
                    <div className="onboarding-survey-section onboarding-step-finish">
                      <p className="onboarding-step-question">Stay in the loop?</p>
                      <p className="onboarding-survey-sub">
                        Optional — we will only use this to send product tips and occasional offers. You can change this
                        in Profile anytime.
                      </p>
                      <label className="onboarding-marketing onboarding-marketing--card">
                        <input
                          type="checkbox"
                          checked={marketingOptIn}
                          onChange={(e) => setMarketingOptIn(e.target.checked)}
                        />
                        <span>Email me product tips and occasional offers</span>
                      </label>
                      <div className="onboarding-summary">
                        <p className="onboarding-summary-title">Summary</p>
                        <dl className="onboarding-summary-dl">
                          <dt>Trading style</dt>
                          <dd>{TRADING_STYLES.find((x) => x.value === tradingStyle)?.label ?? tradingStyle}</dd>
                          <dt>Experience</dt>
                          <dd>{EXPERIENCE.find((x) => x.value === experienceLevel)?.label ?? experienceLevel}</dd>
                          <dt>Markets</dt>
                          <dd>{[...selectedPairs].sort().join(', ')}</dd>
                          <dt>Primary goal</dt>
                          <dd>{labelForPrimaryGoal(primaryGoal)}</dd>
                          <dt>How you found us</dt>
                          <dd>{labelForReferralSource(referralSource)}</dd>
                          <dt>Email tips &amp; offers</dt>
                          <dd>{marketingOptIn ? 'Yes' : 'No'}</dd>
                        </dl>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="onboarding-wizard-nav">
                {step > 0 ? (
                  <button
                    type="button"
                    className="onboarding-nav-btn onboarding-nav-btn--back"
                    disabled={submitting}
                    onClick={goBack}
                  >
                    Back
                  </button>
                ) : (
                  <span className="onboarding-nav-spacer" />
                )}
                {!isLastStep ? (
                  <button
                    type="button"
                    className="onboarding-nav-btn onboarding-nav-btn--primary"
                    disabled={submitting}
                    onClick={goNext}
                  >
                    Continue
                  </button>
                ) : (
                  <button
                    type="button"
                    className="onboarding-nav-btn onboarding-nav-btn--primary"
                    disabled={submitting}
                    onClick={submitComplete}
                  >
                    {submitting ? 'Saving…' : 'Save & go to dashboard'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OnboardingSurvey;
