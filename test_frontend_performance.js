// Frontend Performance Test
// Run this in the browser console to test dashboard loading performance

async function testDashboardPerformance() {
    console.log('🚀 Testing Dashboard Performance...');
    
    const baseUrl = 'http://localhost:8000';
    
    // Test individual endpoints
    console.log('\n📊 Testing Individual Endpoints:');
    const individualStart = performance.now();
    
    const promises = [
        fetch(`${baseUrl}/api/news`),
        fetch(`${baseUrl}/api/trading-data`),
        fetch(`${baseUrl}/api/alerts`),
        fetch(`${baseUrl}/api/ai-insights`),
        fetch(`${baseUrl}/api/alert-settings`)
    ];
    
    try {
        const responses = await Promise.all(promises);
        const individualEnd = performance.now();
        const individualTime = individualEnd - individualStart;
        
        console.log(`✅ Individual endpoints: ${individualTime.toFixed(2)}ms`);
        
        // Test optimized endpoint
        console.log('\n🎯 Testing Optimized Endpoint:');
        const optimizedStart = performance.now();
        
        const optimizedResponse = await fetch(`${baseUrl}/api/dashboard-data`);
        const optimizedData = await optimizedResponse.json();
        
        const optimizedEnd = performance.now();
        const optimizedTime = optimizedEnd - optimizedStart;
        
        console.log(`✅ Optimized endpoint: ${optimizedTime.toFixed(2)}ms`);
        console.log(`📰 News articles: ${optimizedData.news?.length || 0}`);
        console.log(`💾 Cache status: ${optimizedData.newsCacheStatus}`);
        
        // Calculate improvement
        const improvement = ((individualTime - optimizedTime) / individualTime) * 100;
        console.log(`\n📈 Performance Improvement: ${improvement.toFixed(1)}%`);
        
        if (improvement > 0) {
            console.log('✅ Optimized endpoint is faster!');
        } else {
            console.log('⚠️ Optimized endpoint is slower (this might be due to caching)');
        }
        
        // Test cache effectiveness
        console.log('\n💾 Testing Cache Effectiveness:');
        const cacheStart = performance.now();
        const cacheResponse = await fetch(`${baseUrl}/api/dashboard-data`);
        const cacheEnd = performance.now();
        const cacheTime = cacheEnd - cacheStart;
        
        console.log(`✅ Cached response: ${cacheTime.toFixed(2)}ms`);
        
        return {
            individualTime,
            optimizedTime,
            cacheTime,
            improvement,
            newsCount: optimizedData.news?.length || 0,
            cacheStatus: optimizedData.newsCacheStatus
        };
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        return null;
    }
}

// Run the test
testDashboardPerformance().then(results => {
    if (results) {
        console.log('\n✨ Test completed successfully!');
        console.log('Results:', results);
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { testDashboardPerformance };
}
