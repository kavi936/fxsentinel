/**
 * Timezone utility functions for FXSentinel
 * Handles conversion of UTC timestamps to user's local timezone
 */

/**
 * Get the user's saved timezone from localStorage
 * @returns {string} The user's timezone (defaults to 'UTC')
 */
export const getUserTimezone = () => {
  return localStorage.getItem('fxSentinel_userTimezone') || 'UTC';
};

/**
 * Convert a UTC timestamp to the user's local timezone
 * @param {string|Date} timestamp - The UTC timestamp to convert
 * @param {string} timezone - The target timezone (optional, uses user's saved timezone if not provided)
 * @returns {Date} The converted date object
 */
export const convertToUserTimezone = (timestamp, timezone = null) => {
  try {
    const targetTimezone = timezone || getUserTimezone();
    const utcDate = new Date(timestamp);
    
    // If timezone is UTC, return the original date
    if (targetTimezone === 'UTC') {
      return utcDate;
    }
    
    // For now, we'll use the direct timezone formatting approach
    // This function is kept for compatibility but not actively used
    return utcDate;
  } catch (error) {
    console.error('Error converting timezone:', error);
    return new Date(timestamp);
  }
};

/**
 * Format a timestamp for display in the user's timezone
 * @param {string|Date} timestamp - The UTC timestamp to format
 * @param {string} timezone - The target timezone (optional, uses user's saved timezone if not provided)
 * @param {string} format - The format type ('relative', 'time', 'datetime', 'date')
 * @returns {string} The formatted time string
 */
export const formatTimeForTimezone = (timestamp, timezone = null, format = 'relative') => {
  try {
    const targetTimezone = timezone || getUserTimezone();
    const utcDate = new Date(timestamp);
    const now = new Date();
    
    switch (format) {
      case 'relative':
        // For relative time, we'll use the original UTC time for calculation
        // but display the time in the target timezone for older dates
        const diffMs = now - utcDate;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / (24 * 3600000));
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        // For older dates, show the actual date in user's timezone
        return utcDate.toLocaleDateString('en-US', {
          timeZone: targetTimezone,
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        });
        
      case 'time':
        return utcDate.toLocaleTimeString('en-US', {
          timeZone: targetTimezone,
          hour12: false,
          hour: '2-digit',
          minute: '2-digit'
        });
        
      case 'datetime':
        return utcDate.toLocaleString('en-US', {
          timeZone: targetTimezone,
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
        
      case 'date':
        return utcDate.toLocaleDateString('en-US', {
          timeZone: targetTimezone,
          weekday: 'short',
          month: 'short',
          day: 'numeric'
        });
        
      case 'full':
        return utcDate.toLocaleString('en-US', {
          timeZone: targetTimezone,
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        });
        
      default:
        return utcDate.toLocaleString('en-US', { timeZone: targetTimezone });
    }
  } catch (error) {
    console.error('Error formatting time for timezone:', error);
    return 'Unknown';
  }
};

/**
 * Get timezone abbreviation for display
 * @param {string} timezone - The timezone identifier
 * @returns {string} The timezone abbreviation
 */
export const getTimezoneAbbreviation = (timezone) => {
  const abbreviations = {
    'UTC': 'UTC',
    'America/New_York': 'EST/EDT',
    'America/Chicago': 'CST/CDT',
    'America/Denver': 'MST/MDT',
    'America/Los_Angeles': 'PST/PDT',
    'Europe/London': 'GMT/BST',
    'Europe/Paris': 'CET/CEST',
    'Europe/Berlin': 'CET/CEST',
    'Asia/Tokyo': 'JST',
    'Asia/Shanghai': 'CST',
    'Asia/Singapore': 'SGT',
    'Australia/Sydney': 'AEST/AEDT',
    'Australia/Melbourne': 'AEST/AEDT',
    'Pacific/Auckland': 'NZST/NZDT',
    'Asia/Dubai': 'GST',
    'Asia/Kolkata': 'IST',
    'Asia/Seoul': 'KST',
    'Asia/Bangkok': 'ICT',
    'Europe/Moscow': 'MSK',
    'Africa/Johannesburg': 'SAST'
  };
  
  return abbreviations[timezone] || timezone;
};

/**
 * Format news time with timezone indicator
 * @param {string|Date} timestamp - The UTC timestamp
 * @param {string} timezone - The target timezone (optional)
 * @returns {string} The formatted time with timezone info
 */
export const formatNewsTime = (timestamp, timezone = null) => {
  const targetTimezone = timezone || getUserTimezone();
  const utcDate = new Date(timestamp);
  const now = new Date();
  

  
  // If timezone is UTC, use the original relative time logic
  if (targetTimezone === 'UTC') {
    const diffMs = now - utcDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / (24 * 3600000));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return utcDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }
  
  // For non-UTC timezones, convert the time and show it
  try {
    const tzAbbr = getTimezoneAbbreviation(targetTimezone);
    
    // Calculate time difference for recent items
    const diffMs = now - utcDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / (24 * 3600000));
    
    // For very recent items (within 1 hour), show the actual time
    if (diffMins < 60) {
      const convertedTime = utcDate.toLocaleTimeString('en-US', {
        timeZone: targetTimezone,
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      });
      return `${convertedTime} ${tzAbbr}`;
    }
    
    // For recent items (within 24 hours), show relative time with timezone
    if (diffHours < 24) {
      return `${diffHours}h ago (${tzAbbr})`;
    }
    
    // For older items, show the date and time in user's timezone
    if (diffDays < 7) {
      const convertedDateTime = utcDate.toLocaleString('en-US', {
        timeZone: targetTimezone,
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      });
      return `${convertedDateTime} ${tzAbbr}`;
    }
    
    // For very old items, show just the date
    const convertedDate = utcDate.toLocaleDateString('en-US', {
      timeZone: targetTimezone,
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
    return `${convertedDate} ${tzAbbr}`;
    
  } catch (error) {
    console.error('Error formatting news time:', error);
    return 'Unknown';
  }
};

/**
 * Get current time in user's timezone
 * @param {string} timezone - The target timezone (optional)
 * @returns {string} The current time string
 */
export const getCurrentTimeInTimezone = (timezone = null) => {
  const targetTimezone = timezone || getUserTimezone();
  const now = new Date();
  
  return now.toLocaleTimeString('en-US', {
    timeZone: targetTimezone,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

/**
 * Get current date in user's timezone
 * @param {string} timezone - The target timezone (optional)
 * @returns {string} The current date string
 */
export const getCurrentDateInTimezone = (timezone = null) => {
  const targetTimezone = timezone || getUserTimezone();
  const now = new Date();
  
  return now.toLocaleDateString('en-US', {
    timeZone: targetTimezone,
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};
