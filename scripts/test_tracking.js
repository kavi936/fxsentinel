/**
 * GTM/GA4 Tracking Test Script
 * 
 * Run this in browser console to test tracking implementation
 * Copy and paste into browser console at http://localhost:5173
 */

(function() {
  console.log('🧪 Starting GTM/GA4 Tracking Tests...\n');

  // Test 1: Check if analytics tracker exists
  console.log('Test 1: Checking Analytics Tracker...');
  if (typeof window.analyticsTracker !== 'undefined') {
    console.log('✅ Analytics tracker found');
    console.log('   UTM Params:', window.analyticsTracker.getUTMParams());
    console.log('   Session ID:', window.analyticsTracker.getSessionId());
  } else {
    console.log('❌ Analytics tracker not found');
  }

  // Test 2: Check if dataLayer exists
  console.log('\nTest 2: Checking DataLayer...');
  if (typeof window.dataLayer !== 'undefined') {
    console.log('✅ DataLayer found');
    console.log('   Total events:', window.dataLayer.length);
    
    // Count event types
    const eventTypes = {};
    window.dataLayer.forEach(event => {
      const type = event.event || 'unknown';
      eventTypes[type] = (eventTypes[type] || 0) + 1;
    });
    console.log('   Event types:', eventTypes);
  } else {
    console.log('❌ DataLayer not found');
  }

  // Test 3: Check sessionStorage for UTM params
  console.log('\nTest 3: Checking SessionStorage...');
  try {
    const storedUTMs = sessionStorage.getItem('fxsentinel_utm_params');
    if (storedUTMs) {
      console.log('✅ UTM params found in sessionStorage');
      console.log('   Params:', JSON.parse(storedUTMs));
    } else {
      console.log('⚠️  No UTM params in sessionStorage (this is OK if you haven\'t visited with UTM params)');
    }
  } catch (e) {
    console.log('❌ Error reading sessionStorage:', e.message);
  }

  // Test 4: Check for conversion events
  console.log('\nTest 4: Checking for Conversion Events...');
  if (window.dataLayer) {
    const conversionEvents = window.dataLayer.filter(e => 
      e.event === 'conversion' || e.funnel_step === 'signup_completion'
    );
    
    if (conversionEvents.length > 0) {
      console.log(`✅ Found ${conversionEvents.length} conversion event(s)`);
      conversionEvents.forEach((event, index) => {
        console.log(`   Event ${index + 1}:`, {
          event: event.event,
          funnel_step: event.funnel_step,
          conversion_type: event.conversion_type,
          utm_source: event.utm_source,
          utm_medium: event.utm_medium,
          utm_campaign: event.utm_campaign
        });
      });
    } else {
      console.log('⚠️  No conversion events found (this is OK if you haven\'t signed up yet)');
    }
  }

  // Test 5: Check GTM container
  console.log('\nTest 5: Checking GTM Container...');
  const gtmScript = document.querySelector('script[src*="gtm.js"]');
  if (gtmScript) {
    console.log('✅ GTM script found');
    const gtmId = gtmScript.src.match(/GTM-[A-Z0-9]+/);
    if (gtmId) {
      console.log('   Container ID:', gtmId[0]);
    }
  } else {
    console.log('⚠️  GTM script not found (check index.html)');
  }

  // Test 6: Check Firebase Analytics
  console.log('\nTest 6: Checking Firebase Analytics...');
  if (typeof window.firebase !== 'undefined' || typeof window.gtag !== 'undefined') {
    console.log('✅ Firebase/GA4 detected');
  } else {
    console.log('⚠️  Firebase/GA4 not detected in window object (may still be loaded)');
  }

  // Test 7: Simulate UTM params (for testing)
  console.log('\nTest 7: UTM Parameter Test...');
  console.log('   To test UTM persistence, visit:');
  console.log('   http://localhost:5173/signup?utm_source=test&utm_medium=social&utm_campaign=console_test');
  console.log('   Then run this script again to verify UTM params are stored.');

  // Summary
  console.log('\n📊 Test Summary:');
  console.log('   - Analytics Tracker:', typeof window.analyticsTracker !== 'undefined' ? '✅' : '❌');
  console.log('   - DataLayer:', typeof window.dataLayer !== 'undefined' ? '✅' : '❌');
  console.log('   - SessionStorage:', typeof sessionStorage !== 'undefined' ? '✅' : '❌');
  console.log('   - GTM Script:', gtmScript ? '✅' : '⚠️');
  
  console.log('\n💡 Next Steps:');
  console.log('   1. Visit signup page with UTM params');
  console.log('   2. Complete signup (email or Google)');
  console.log('   3. Run this script again to verify conversion events');
  console.log('   4. Check GTM Preview Mode (if configured)');
  
  console.log('\n✅ Test script complete!');
})();
