import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMeta } from '../hooks/useMeta';
import analyticsTracker from '../utils/analytics';
import { config } from '../config';
import './FeedbackForm.css';

const FeedbackForm = () => {
  useMeta('Feedback - FXSentinel | Help Us Improve', 'Share your feedback to help us improve FXSentinel. We read every message and respond within 24 hours.');
  useEffect(() => {
    analyticsTracker.trackPageView('feedback');
  }, []);
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    category: 'general',
    message: '',
    rating: null
  });

  // Sync name/email when currentUser loads (auth can resolve after mount)
  useEffect(() => {
    if (currentUser) {
      setFormData(prev => ({
        ...prev,
        name: prev.name || currentUser.displayName || currentUser.email?.split('@')[0] || '',
        email: prev.email || currentUser.email || ''
      }));
    }
  }, [currentUser?.uid, currentUser?.email, currentUser?.displayName]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState(null);
  const [errors, setErrors] = useState({});
  const [hoveredRating, setHoveredRating] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleRatingClick = (rating) => {
    setFormData(prev => ({
      ...prev,
      rating: rating
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email || !formData.email.includes('@')) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.message || formData.message.trim().length < 10) {
      newErrors.message = 'Please provide at least 10 characters of feedback';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitStatus(null);

    try {
      const response = await fetch(`${config.endpoints.submitFeedback}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name || 'Anonymous',
          email: formData.email,
          category: formData.category,
          message: formData.message,
          rating: formData.rating,
          userId: currentUser?.uid || null,
          timestamp: new Date().toISOString()
        }),
      });

      let data = {};
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        try {
          data = await response.json();
        } catch (_) {
          data = { error: 'Invalid response from server' };
        }
      } else if (!response.ok) {
        data = { error: `Request failed (${response.status}). Please try again.` };
      }

      if (response.ok && data.success) {
        setSubmitStatus('success');
        // Reset form after successful submission (keep pre-filled name/email if logged in)
        setTimeout(() => {
          setFormData({
            name: currentUser?.displayName || currentUser?.email?.split('@')[0] || '',
            email: currentUser?.email || '',
            category: 'general',
            message: '',
            rating: null
          });
        }, 2000);
      } else {
        setSubmitStatus('error');
        console.error('Feedback submission error:', data.error || data.message);
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="feedback-form-page">
      <div className="feedback-form-container">
        <div className="feedback-form-header">
          <button className="back-button" onClick={() => navigate(-1)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            Back
          </button>
          <h1>Share Your Feedback</h1>
          <p>Your thoughts help us improve FXSentinel. We read every submission.</p>
        </div>

        {submitStatus === 'success' ? (
          <div className="feedback-success">
            <div className="success-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
            </div>
            <h2>Thank You!</h2>
            <p>Your feedback has been submitted successfully. We appreciate you taking the time to help us improve.</p>
          </div>
        ) : (
          <form className="feedback-form" onSubmit={handleSubmit}>
            <div className="form-section">
              <label htmlFor="rating">How would you rate your experience? (Optional)</label>
              <div className="rating-buttons">
                {[1, 2, 3, 4, 5].map((rating) => {
                  const isSelected = formData.rating !== null && rating <= formData.rating;
                  const isHovered = hoveredRating !== null && rating <= hoveredRating;
                  const isActive = isSelected || isHovered;
                  
                  return (
                    <button
                      key={rating}
                      type="button"
                      className={`rating-btn ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''}`}
                      onClick={() => handleRatingClick(rating)}
                      onMouseEnter={() => setHoveredRating(rating)}
                      onMouseLeave={() => setHoveredRating(null)}
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                      </svg>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="form-section">
              <label htmlFor="category">Category</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="form-select"
              >
                <option value="general">General Feedback</option>
                <option value="feature">Feature Request</option>
                <option value="bug">Bug Report</option>
                <option value="improvement">Improvement Suggestion</option>
                <option value="ui">UI/UX Feedback</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-section">
              <label htmlFor="name">Name (Optional)</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="form-input"
                placeholder="Your name"
              />
            </div>

            <div className="form-section">
              <label htmlFor="email">Email <span className="required">*</span></label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`form-input ${errors.email ? 'error' : ''}`}
                placeholder="your.email@example.com"
                required
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>

            <div className="form-section">
              <label htmlFor="message">Your Feedback <span className="required">*</span></label>
              <textarea
                id="message"
                name="message"
                value={formData.message}
                onChange={handleChange}
                className={`form-textarea ${errors.message ? 'error' : ''}`}
                placeholder="Tell us what you think, what you'd like to see improved, or any issues you've encountered..."
                rows="8"
                required
              />
              {errors.message && <span className="error-message">{errors.message}</span>}
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="submit-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>

            {submitStatus === 'error' && (
              <div className="error-banner">
                <p>There was an error submitting your feedback. Please try again or contact us directly at fxsentinelapp@gmail.com</p>
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
};

export default FeedbackForm;

