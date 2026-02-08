/**
 * Updated GTM/GA4 Tracking Test Script
 * 
 * Run this in browser console after page reload
 * Copy and paste into browser console at http://localhost:5173
 */

(function() {
  console.log('🧪 Testing Tracking Implementation...\n');
  
  // Test 1: Check analytics tracker
  const hasTracker = typeof window.analyticsTracker !== 'undefined';
  console.log('Test 1: Analytics Tracker');
  if (hasTracker) {
    console.log('✅ Analytics tracker found');
    console.log('   UTM Params:', window.analyticsTracker.getUTMParams());
    console.log('   Session ID:', window.analyticsTracker.getSessionId());
  } else {
    console.log('⚠️  Analytics tracker not found - try reloading the page');
  }

  // Test 2: Check dataLayer
  console.log('\nTest 2: DataLayer');
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
  console.log('\nTest 3: SessionStorage UTM Params');
  try {
    const storedUTMs = sessionStorage.getItem('fxsentinel_utm_params');
    if (storedUTMs) {
      console.log('✅ UTM params found in sessionStorage');
      const params = JSON.parse(storedUTMs);
      console.log('   Params:', params);
    } else {
      console.log('⚠️  No UTM params in sessionStorage');
      console.log('   💡 Visit: /signup?utm_source=test&utm_medium=social');
    }
  } catch (e) {
    console.log('❌ Error reading sessionStorage:', e.message);
  }

  // Test 4: Check for conversion events
  console.log('\nTest 4: Conversion Events');
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
      console.log('⚠️  No conversion events found yet');
      console.log('   💡 Complete a signup to generate conversion events');
    }
  }

  // Test 5: Check GTM container
  console.log('\nTest 5: GTM Container');
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
  console.log('\nTest 6: Firebase Analytics');
  if (typeof window.firebase !== 'undefined' || typeof window.gtag !== 'undefined') {
    console.log('✅ Firebase/GA4 detected');
  } else {
    console.log('⚠️  Firebase/GA4 not detected in window object (may still be loaded)');
  }

  // Summary
  console.log('\n📊 Test Summary:');
  console.log('   - Analytics Tracker:', hasTracker ? '✅' : '⚠️  (reload page)');
  console.log('   - DataLayer:', typeof window.dataLayer !== 'undefined' ? '✅' : '❌');
  console.log('   - SessionStorage:', typeof sessionStorage !== 'undefined' ? '✅' : '❌');
  console.log('   - UTM Params Stored:', sessionStorage.getItem('fxsentinel_utm_params') ? '✅' : '⚠️');
  console.log('   - GTM Script:', gtmScript ? '✅' : '⚠️');
  
  console.log('\n💡 Next Steps:');
  if (!sessionStorage.getItem('fxsentinel_utm_params')) {
    console.log('   1. Visit: /signup?utm_source=test&utm_medium=social');
  }
  console.log('   2. Complete signup (email or Google)');
  console.log('   3. Run this script again to verify conversion events');
  console.log('   4. Check GTM Preview Mode (if configured)');
  
  console.log('\n✅ Test script complete!');
})();
