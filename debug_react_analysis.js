// Debug script to test React component analysis functionality
console.log('🔍 Debug script loaded');

// Test the config
const API_BASE_URL = window.location.hostname === 'localhost' ? 'http://localhost:5001' : 'https://fxsentinel-production.up.railway.app';
const endpoints = {
    news: `${API_BASE_URL}/api/news`,
    analysis: (id) => `${API_BASE_URL}/api/analysis/${id}`
};

console.log('🔍 API Configuration:', {
    API_BASE_URL,
    newsEndpoint: endpoints.news,
    analysisEndpoint: endpoints.analysis('test')
});

// Test function to simulate the React component's analyzeNews function
async function testAnalyzeNews(newsId) {
    console.log('🔍 Testing analyzeNews function for news ID:', newsId);
    
    try {
        const requestUrl = endpoints.analysis(newsId) + '?t=' + Date.now();
        console.log('🔍 Making analysis request to:', requestUrl);
        
        const response = await fetch(requestUrl);
        console.log('🔍 Response status:', response.status);
        console.log('🔍 Response headers:', Object.fromEntries(response.headers.entries()));
        
        const analysis = await response.json();
        console.log('🔍 Analysis received:', analysis);
        console.log('🔍 Analysis type:', analysis.analysis_type);
        console.log('🔍 News impact:', analysis.news_impact);
        console.log('🔍 Trading implications:', analysis.trading_implications);
        console.log('🔍 Analysis structure:', Object.keys(analysis));
        
        if (response.ok) {
            console.log('🔍 ✅ Analysis successful!');
            console.log('🔍 Analysis data looks valid for frontend display');
            return analysis;
        } else {
            console.error('🔍 ❌ Analysis failed:', response.status, response.statusText);
            return null;
        }
    } catch (error) {
        console.error('🔍 ❌ Error in analyzeNews:', error);
        return null;
    }
}

// Test function to simulate the React component's conditional rendering logic
function testConditionalRendering(selectedNews, aiAnalysis, analyzing, error) {
    console.log('🔍 Testing conditional rendering logic');
    console.log('🔍 Input values:', {
        selectedNews: selectedNews,
        hasAiAnalysis: !!aiAnalysis,
        isAnalyzing: analyzing,
        hasError: !!error
    });
    
    const shouldShow = selectedNews && (aiAnalysis || analyzing || error);
    console.log('🔍 Should show analysis section:', shouldShow);
    
    if (shouldShow) {
        console.log('🔍 ✅ Analysis section should be visible');
        if (aiAnalysis) {
            console.log('🔍 ✅ Analysis content should be displayed');
            console.log('🔍 Analysis data for display:', {
                analysis_type: aiAnalysis.analysis_type,
                confidence: aiAnalysis.confidence,
                immediate_reaction: aiAnalysis.immediate_reaction,
                news_impact_length: aiAnalysis.news_impact?.length || 0,
                trading_implications_length: aiAnalysis.trading_implications?.length || 0
            });
        } else if (analyzing) {
            console.log('🔍 ✅ Loading state should be displayed');
        } else if (error) {
            console.log('🔍 ✅ Error state should be displayed');
        }
    } else {
        console.log('🔍 ❌ Analysis section should NOT be visible');
    }
    
    return shouldShow;
}

// Make functions available globally for testing
window.testAnalyzeNews = testAnalyzeNews;
window.testConditionalRendering = testConditionalRendering;

console.log('🔍 Debug functions available:');
console.log('🔍 - testAnalyzeNews(newsId)');
console.log('🔍 - testConditionalRendering(selectedNews, aiAnalysis, analyzing, error)');

// Auto-test if we have a news item
async function autoTest() {
    console.log('🔍 Running auto-test...');
    
    try {
        const newsResponse = await fetch(endpoints.news);
        const newsData = await newsResponse.json();
        
        if (newsResponse.ok && newsData.news && newsData.news.length > 0) {
            const testNews = newsData.news[0];
            console.log('🔍 Found test news item:', testNews.title);
            
            // Test analysis
            const analysis = await testAnalyzeNews(testNews.id);
            
            if (analysis) {
                // Test conditional rendering
                testConditionalRendering(
                    { id: testNews.id, title: testNews.title },
                    analysis,
                    false,
                    null
                );
            }
        } else {
            console.log('🔍 No news items available for auto-test');
        }
    } catch (error) {
        console.error('🔍 Auto-test failed:', error);
    }
}

// Run auto-test after a short delay
setTimeout(autoTest, 1000);
