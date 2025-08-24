// Test script for Review Banner functionality
console.log('🧪 Testing Review Banner Functionality');

// Test localStorage functions
function testReviewBanner() {
  console.log('=== Review Banner Test ===');
  
  // Clear any existing data
  localStorage.removeItem('reviewBannerLastShown');
  localStorage.removeItem('userHasReviewed');
  localStorage.removeItem('reviewBannerReminder');
  
  console.log('✅ Cleared existing review banner data');
  
  // Test initial state
  const lastShown = localStorage.getItem('reviewBannerLastShown');
  const hasReviewed = localStorage.getItem('userHasReviewed');
  const currentTime = Date.now();
  
  console.log('📊 Initial state:');
  console.log('  - Last shown:', lastShown ? new Date(parseInt(lastShown)).toLocaleString() : 'Never');
  console.log('  - Has reviewed:', hasReviewed);
  console.log('  - Current time:', new Date(currentTime).toLocaleString());
  
  // Test banner visibility logic
  const shouldShow = !hasReviewed && (!lastShown || currentTime - parseInt(lastShown) > 7 * 24 * 60 * 60 * 1000);
  console.log('  - Should show banner:', shouldShow);
  
  // Test random probability (30%)
  const randomChance = Math.random() < 0.3;
  console.log('  - Random chance (30%):', randomChance);
  
  // Test review click simulation
  console.log('\n🎯 Testing review click simulation:');
  
  const platforms = ['producthunt', 'trustpilot', 'twitter', 'linkedin'];
  platforms.forEach(platform => {
    console.log(`  - ${platform}: https://example.com/${platform}`);
  });
  
  // Test reminder functionality
  const reminderTime = currentTime + (3 * 24 * 60 * 60 * 1000);
  localStorage.setItem('reviewBannerReminder', reminderTime.toString());
  console.log('\n⏰ Reminder set for:', new Date(reminderTime).toLocaleString());
  
  console.log('\n✅ Review banner test completed!');
  console.log('\n📋 To test in browser:');
  console.log('1. Open browser console');
  console.log('2. Run: localStorage.clear()');
  console.log('3. Refresh the dashboard page');
  console.log('4. Banner should appear (30% chance)');
}

// Run the test
testReviewBanner();

// Export for use in browser console
if (typeof window !== 'undefined') {
  window.testReviewBanner = testReviewBanner;
}
