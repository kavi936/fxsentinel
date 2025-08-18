// Quick Fix Script for React App Analysis Issues
// Run this in your React app's browser console

console.log('🔧 Quick Fix Script Started');

// Fix 1: Force refresh the page to clear any cached issues
function forceRefresh() {
    console.log('🔧 Force refreshing page...');
    window.location.reload(true);
}

// Fix 2: Clear browser cache for this site
function clearCache() {
    console.log('🔧 Clearing browser cache...');
    if ('caches' in window) {
        caches.keys().then(names => {
            names.forEach(name => {
                caches.delete(name);
            });
        });
    }
    console.log('🔧 Cache cleared. Please refresh the page.');
}

// Fix 3: Test and fix API configuration
async function testAndFixAPI() {
    console.log('🔧 Testing API configuration...');
    
    const API_BASE_URL = 'http://localhost:5001';
    const testUrl = `${API_BASE_URL}/api/news`;
    
    try {
        const response = await fetch(testUrl);
        if (response.ok) {
            console.log('🔧 API is working correctly');
            return true;
        } else {
            console.error('🔧 API returned error:', response.status);
            return false;
        }
    } catch (error) {
        console.error('🔧 API connection failed:', error.message);
        return false;
    }
}

// Fix 4: Manual API test with detailed logging
async function manualAPITest() {
    console.log('🔧 Running manual API test...');
    
    const API_BASE_URL = 'http://localhost:5001';
    
    // Test 1: News API
    try {
        console.log('🔧 Testing news API...');
        const newsResponse = await fetch(`${API_BASE_URL}/api/news`);
        console.log('🔧 News API status:', newsResponse.status);
        console.log('🔧 News API headers:', Object.fromEntries(newsResponse.headers.entries()));
        
        if (newsResponse.ok) {
            const newsData = await newsResponse.json();
            console.log('🔧 News API success, found', newsData.news?.length || 0, 'items');
            
            // Test 2: Analysis API with first news item
            if (newsData.news && newsData.news.length > 0) {
                const firstNewsId = newsData.news[0].id;
                console.log('🔧 Testing analysis API with news ID:', firstNewsId);
                
                const analysisResponse = await fetch(`${API_BASE_URL}/api/analysis/${firstNewsId}`);
                console.log('🔧 Analysis API status:', analysisResponse.status);
                console.log('🔧 Analysis API headers:', Object.fromEntries(analysisResponse.headers.entries()));
                
                if (analysisResponse.ok) {
                    const analysisData = await analysisResponse.json();
                    console.log('🔧 Analysis API success:', analysisData.analysis_type, analysisData.confidence + '%');
                    console.log('🔧 Full analysis data:', analysisData);
                } else {
                    console.error('🔧 Analysis API failed:', analysisResponse.status, analysisResponse.statusText);
                }
            }
        } else {
            console.error('🔧 News API failed:', newsResponse.status, newsResponse.statusText);
        }
    } catch (error) {
        console.error('🔧 Manual API test failed:', error);
    }
}

// Fix 5: Check if backend is running
async function checkBackend() {
    console.log('🔧 Checking if backend is running...');
    
    try {
        const response = await fetch('http://localhost:5001/api/hello');
        if (response.ok) {
            console.log('🔧 Backend is running');
            return true;
        } else {
            console.error('🔧 Backend responded with error:', response.status);
            return false;
        }
    } catch (error) {
        console.error('🔧 Backend is not running or not accessible:', error.message);
        console.log('🔧 Please make sure the backend is running on port 5001');
        return false;
    }
}

// Fix 6: Simulate the exact React app fetch
async function simulateReactFetch() {
    console.log('🔧 Simulating exact React app fetch...');
    
    // This is exactly what your React app does
    const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
    const requestUrl = `${API_BASE_URL}/api/news`;
    
    console.log('🔧 React app would fetch from:', requestUrl);
    console.log('🔧 Current origin:', window.location.origin);
    
    try {
        const response = await fetch(requestUrl);
        console.log('🔧 Simulated fetch status:', response.status);
        console.log('🔧 Simulated fetch headers:', Object.fromEntries(response.headers.entries()));
        
        if (response.ok) {
            const data = await response.json();
            console.log('🔧 Simulated fetch success, found', data.news?.length || 0, 'items');
            
            // Now test analysis
            if (data.news && data.news.length > 0) {
                const analysisUrl = `${API_BASE_URL}/api/analysis/${data.news[0].id}`;
                console.log('🔧 Testing analysis at:', analysisUrl);
                
                const analysisResponse = await fetch(analysisUrl);
                console.log('🔧 Analysis response status:', analysisResponse.status);
                
                if (analysisResponse.ok) {
                    const analysisData = await analysisResponse.json();
                    console.log('🔧 Analysis success:', analysisData.analysis_type);
                } else {
                    console.error('🔧 Analysis failed:', analysisResponse.status);
                }
            }
        } else {
            console.error('🔧 Simulated fetch failed:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('🔧 Simulated fetch error:', error);
    }
}

// Make all functions available
window.quickFix = {
    forceRefresh,
    clearCache,
    testAndFixAPI,
    manualAPITest,
    checkBackend,
    simulateReactFetch
};

console.log('🔧 Quick fix functions available as window.quickFix');
console.log('🔧 Run: window.quickFix.checkBackend() to check if backend is running');
console.log('🔧 Run: window.quickFix.simulateReactFetch() to test exact React app behavior');
console.log('🔧 Run: window.quickFix.manualAPITest() for detailed API testing');
