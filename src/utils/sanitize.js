/**
 * Content Sanitization Utility
 * Prevents XSS attacks by sanitizing user-generated and external content
 */

import DOMPurify from 'dompurify';

/**
 * Sanitize HTML content - removes all HTML tags and returns plain text
 * @param {string} html - HTML content to sanitize
 * @returns {string} - Sanitized plain text
 */
export const sanitizeHTML = (html) => {
  if (!html || typeof html !== 'string') {
    return '';
  }
  
  // Use DOMPurify to strip all HTML tags and return plain text
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [], // No HTML tags allowed
    ALLOWED_ATTR: [], // No attributes allowed
    KEEP_CONTENT: true // Keep text content
  });
  
  return clean;
};

/**
 * Sanitize plain text - escapes HTML entities
 * @param {string} text - Text to sanitize
 * @returns {string} - Sanitized text with escaped HTML entities
 */
export const sanitizeText = (text) => {
  if (!text || typeof text !== 'string') {
    return '';
  }
  
  // First remove any script tags and dangerous content
  const withoutScripts = text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  
  // Use DOMPurify to sanitize and escape HTML entities
  const clean = DOMPurify.sanitize(withoutScripts, {
    ALLOWED_TAGS: [], // No HTML tags allowed
    ALLOWED_ATTR: [], // No attributes allowed
    KEEP_CONTENT: true // Keep text content
  });
  
  return clean;
};

/**
 * Sanitize URL - validates and sanitizes URLs to prevent javascript: and data: protocols
 * @param {string} url - URL to sanitize
 * @returns {string} - Safe URL or '#' if invalid/dangerous
 */
export const sanitizeURL = (url) => {
  if (!url || typeof url !== 'string') {
    return '#';
  }
  
  // Remove whitespace
  const trimmed = url.trim();
  
  if (!trimmed) {
    return '#';
  }
  
  // Check for dangerous protocols
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:'];
  const lowerUrl = trimmed.toLowerCase();
  
  for (const protocol of dangerousProtocols) {
    if (lowerUrl.startsWith(protocol)) {
      console.warn(`Blocked dangerous URL protocol: ${trimmed}`);
      return '#';
    }
  }
  
  // Validate URL format (basic check)
  try {
    // If it's a relative URL or doesn't start with http/https, allow it but sanitize
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://') && !trimmed.startsWith('/') && !trimmed.startsWith('#')) {
      // Not a valid absolute URL, return safe fallback
      return '#';
    }
    
    // Additional check: ensure no script injection in URL
    if (trimmed.includes('<script') || trimmed.includes('javascript:') || trimmed.includes('onerror=')) {
      console.warn(`Blocked potentially malicious URL: ${trimmed}`);
      return '#';
    }
    
    return trimmed;
  } catch (e) {
    console.warn(`Error validating URL: ${trimmed}`, e);
    return '#';
  }
};

/**
 * Sanitize a news item - sanitizes all text fields and URL
 * @param {object} newsItem - News item object to sanitize
 * @returns {object} - Sanitized news item
 */
export const sanitizeNewsItem = (newsItem) => {
  if (!newsItem || typeof newsItem !== 'object') {
    return newsItem;
  }
  
  // Create a copy to avoid mutating the original
  const sanitized = { ...newsItem };
  
  // Sanitize text fields (only if they exist and are strings)
  if (sanitized.title && typeof sanitized.title === 'string') {
    sanitized.title = sanitizeText(sanitized.title);
  }
  
  if (sanitized.summary && typeof sanitized.summary === 'string') {
    sanitized.summary = sanitizeText(sanitized.summary);
  }
  
  if (sanitized.source && typeof sanitized.source === 'string') {
    sanitized.source = sanitizeText(sanitized.source);
  }
  
  if (sanitized.url && typeof sanitized.url === 'string') {
    sanitized.url = sanitizeURL(sanitized.url);
  }
  
  // Preserve all other fields (id, published_at, added_to_feed_at, impact, currency_pairs, etc.)
  // Sanitize AI analysis fields if present
  if (sanitized.analysis_summary && typeof sanitized.analysis_summary === 'object') {
    if (sanitized.analysis_summary.type && typeof sanitized.analysis_summary.type === 'string') {
      sanitized.analysis_summary.type = sanitizeText(sanitized.analysis_summary.type);
    }
  }
  
  return sanitized;
};

/**
 * Sanitize AI analysis content
 * @param {object} analysis - AI analysis object to sanitize
 * @returns {object} - Sanitized analysis object
 */
export const sanitizeAnalysis = (analysis) => {
  if (!analysis || typeof analysis !== 'object') {
    return analysis;
  }
  
  const sanitized = { ...analysis };
  
  // Sanitize text fields
  const textFields = [
    'news_impact',
    'trading_implications',
    'immediate_reaction',
    'volatility',
    'timeframe'
  ];
  
  textFields.forEach(field => {
    if (sanitized[field] && typeof sanitized[field] === 'string') {
      sanitized[field] = sanitizeText(sanitized[field]);
    }
  });
  
  // Sanitize array fields
  if (Array.isArray(sanitized.key_pairs)) {
    sanitized.key_pairs = sanitized.key_pairs.map(pair => sanitizeText(pair));
  }
  
  // Sanitize risk assessment object
  if (sanitized.risk_assessment && typeof sanitized.risk_assessment === 'object') {
    const riskFields = ['market_volatility', 'liquidity_impact', 'correlation_risk'];
    riskFields.forEach(field => {
      if (sanitized.risk_assessment[field] && typeof sanitized.risk_assessment[field] === 'string') {
        sanitized.risk_assessment[field] = sanitizeText(sanitized.risk_assessment[field]);
      }
    });
  }
  
  return sanitized;
};

