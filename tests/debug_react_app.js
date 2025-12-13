// Debug script for React app API issues
// Run this in the browser console of your React app

console.log('🔍 React App Debug Script Started');

// Test 1: Check if config is loaded correctly
console.log('🔍 Testing config...');
try {
    // This should match your React app's config
    const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
    console.log('🔍 API_BASE_URL:', API_BASE_URL);
    console.log('🔍 Current origin:', window.location.origin);
    console.log('🔍 Current hostname:', window.location.hostname);
} catch (error) {
    console.error('🔍 Config error:', error);
}

// Test 2: Test news API
console.log('🔍 Testing news API...');
async function testNewsAPI() {
    try {
        const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
        const response = await fetch(`${API_BASE_URL}/api/news`);
        console.log('🔍 News API response status:', response.status);
        console.log('🔍 News API response headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.ok) {
            const data = await response.json();
            console.log('🔍 News API success, found', data.news?.length || 0, 'items');
            return data.news?.[0]?.id; // Return first news ID for analysis test
        } else {
            console.error('🔍 News API failed:', response.status, response.statusText);
            return null;
        }
    } catch (error) {
        console.error('🔍 News API error:', error);
        return null;
    }
}

// Test 3: Test analysis API
async function testAnalysisAPI(newsId) {
    if (!newsId) {
        console.log('🔍 No news ID available for analysis test');
        return;
    }
    
    try {
        const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
        const response = await fetch(`${API_BASE_URL}/api/analysis/${newsId}`);
        console.log('🔍 Analysis API response status:', response.status);
        console.log('🔍 Analysis API response headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.ok) {
            const data = await response.json();
            console.log('🔍 Analysis API success:', data.analysis_type, data.confidence + '%');
            return data;
        } else {
            console.error('🔍 Analysis API failed:', response.status, response.statusText);
            return null;
        }
    } catch (error) {
        console.error('🔍 Analysis API error:', error);
        return null;
    }
}

// Test 4: Test CORS
async function testCORS() {
    try {
        const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
        const response = await fetch(`${API_BASE_URL}/api/news`, {
            method: 'GET',
            headers: {
                'Origin': window.location.origin,
                'Content-Type': 'application/json'
            }
        });
        
        const corsHeader = response.headers.get('Access-Control-Allow-Origin');
        console.log('🔍 CORS test - Origin:', window.location.origin);
        console.log('🔍 CORS test - Access-Control-Allow-Origin:', corsHeader);
        console.log('🔍 CORS test - Status:', response.status);
        
        if (corsHeader === '*' || corsHeader === window.location.origin) {
            console.log('🔍 CORS is properly configured');
        } else {
            console.error('🔍 CORS may be blocking requests');
        }
    } catch (error) {
        console.error('🔍 CORS test error:', error);
    }
}

// Run all tests
async function runAllTests() {
    console.log('🔍 Running all tests...');
    
    // Test CORS first
    await testCORS();
    
    // Test news API
    const newsId = await testNewsAPI();
    
    // Test analysis API if we have a news ID
    if (newsId) {
        await testAnalysisAPI(newsId);
    }
    
    console.log('🔍 All tests completed');
}

// Make functions available globally
window.debugReactApp = {
    testNewsAPI,
    testAnalysisAPI,
    testCORS,
    runAllTests
};

console.log('🔍 Debug functions available as window.debugReactApp');
console.log('🔍 Run: window.debugReactApp.runAllTests() to test everything');
