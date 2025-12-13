// Test file to demonstrate news timezone conversion
// Run this in the browser console to test the functionality

// Mock the timezone utilities for testing
const mockLocalStorage = {
  getItem: (key) => {
    if (key === 'fxSentinel_userTimezone') return 'America/New_York';
    return null;
  },
  setItem: (key, value) => console.log(`Setting ${key} to ${value}`)
};

// Mock the timezone utilities
const getUserTimezone = () => {
  return mockLocalStorage.getItem('fxSentinel_userTimezone') || 'UTC';
};

const getTimezoneAbbreviation = (timezone) => {
  const abbreviations = {
    'UTC': 'UTC',
    'America/New_York': 'EST/EDT',
    'Europe/London': 'GMT/BST',
    'Asia/Tokyo': 'JST'
  };
  return abbreviations[timezone] || timezone;
};

const formatNewsTime = (timestamp, timezone = null) => {
  const targetTimezone = timezone || getUserTimezone();
  
  try {
    const utcDate = new Date(timestamp);
    const now = new Date();
    
    // Convert to user's timezone
    const localDate = new Date(utcDate.toLocaleString('en-US', { timeZone: targetTimezone }));
    
    // Calculate relative time
    const diffMs = now - localDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / (24 * 3600000));
    
    let formattedTime;
    if (diffMins < 1) formattedTime = 'Just now';
    else if (diffMins < 60) formattedTime = `${diffMins}m ago`;
    else if (diffHours < 24) formattedTime = `${diffHours}h ago`;
    else if (diffDays < 7) formattedTime = `${diffDays}d ago`;
    else {
      formattedTime = localDate.toLocaleDateString('en-US', {
        timeZone: targetTimezone,
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    }
    
    // Only show timezone if it's not UTC and the time is not relative
    if (targetTimezone !== 'UTC' && !formattedTime.includes('ago') && !formattedTime.includes('Just now')) {
      const tzAbbr = getTimezoneAbbreviation(targetTimezone);
      return `${formattedTime} ${tzAbbr}`;
    }
    
    return formattedTime;
  } catch (error) {
    console.error('Error formatting time:', error);
    return 'Unknown';
  }
};

// Test news timestamps
const testNewsItems = [
  {
    id: 1,
    title: "US Non-Farm Payrolls Report",
    published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
    source: "Reuters"
  },
  {
    id: 2,
    title: "ECB Interest Rate Decision",
    published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    source: "Bloomberg"
  },
  {
    id: 3,
    title: "Bank of Japan Policy Meeting",
    published_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    source: "CNBC"
  },
  {
    id: 4,
    title: "Australian Employment Data",
    published_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week ago
    source: "FXStreet"
  }
];

console.log('🌍 Testing News Timezone Conversion');
console.log('=====================================');
console.log('Current user timezone:', getUserTimezone());
console.log('Current time:', new Date().toLocaleString());
console.log('');

// Test with different timezones
const testTimezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'];

testTimezones.forEach(timezone => {
  console.log(`📅 Testing with timezone: ${timezone}`);
  console.log(`Timezone abbreviation: ${getTimezoneAbbreviation(timezone)}`);
  console.log('');
  
  testNewsItems.forEach(newsItem => {
    const formattedTime = formatNewsTime(newsItem.published_at, timezone);
    console.log(`  ${newsItem.source}: ${newsItem.title}`);
    console.log(`  Published: ${formattedTime}`);
    console.log('');
  });
  
  console.log('---');
  console.log('');
});

console.log('✅ Test completed!');
console.log('');
console.log('💡 How to test in your app:');
console.log('1. Open the dashboard');
console.log('2. Click the settings button (gear icon)');
console.log('3. Select your timezone');
console.log('4. Check that news times now display in your local timezone');
console.log('5. Look for the timezone indicator (e.g., "EST") next to times');
