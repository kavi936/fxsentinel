// Test file to verify timezone functionality
// Run this in the browser console to test

// Mock localStorage for testing
if (typeof localStorage === 'undefined') {
  global.localStorage = {
    getItem: (key) => {
      if (key === 'fxSentinel_userTimezone') return 'America/New_York';
      return null;
    },
    setItem: (key, value) => console.log(`Setting ${key} to ${value}`)
  };
}

// Test timezone conversion
const testTimestamp = '2024-01-15T14:30:00Z'; // UTC time
const testDate = new Date(testTimestamp);

console.log('Testing timezone functionality...');
console.log('Original UTC timestamp:', testTimestamp);
console.log('Original UTC date:', testDate.toISOString());

// Test different timezone conversions
const timezones = ['UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo'];

timezones.forEach(timezone => {
  try {
    const localDate = new Date(testDate.toLocaleString('en-US', { timeZone: timezone }));
    console.log(`${timezone}:`, localDate.toLocaleString('en-US', { timeZone: timezone }));
  } catch (error) {
    console.error(`Error with ${timezone}:`, error);
  }
});

console.log('Test completed. Check the console output above.');
