// Test script to verify frontend integration with AI analysis
const API_BASE_URL = 'http://localhost:5001';

async function testFrontendIntegration() {
    console.log('🧪 Testing Frontend Integration with AI Analysis');
    console.log('=' .repeat(60));
    
    // Test 1: Basic Analysis
    console.log('\n1️⃣ Testing Basic Analysis...');
    try {
        const response = await fetch(`${API_BASE_URL}/api/analysis/1`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Basic Analysis Working!');
            console.log(`   Summary: ${data.summary?.substring(0, 100)}...`);
            console.log(`   Confidence: ${data.confidence}`);
        } else {
            console.log(`❌ Basic Analysis Failed: ${response.status}`);
        }
    } catch (error) {
        console.log(`❌ Basic Analysis Error: ${error.message}`);
    }
    
    // Test 2: Enhanced Analysis
    console.log('\n2️⃣ Testing Enhanced Analysis...');
    try {
        const response = await fetch(`${API_BASE_URL}/api/enhanced-analysis/1`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Enhanced Analysis Working!');
            console.log(`   Type: ${data.analysis_type}`);
            console.log(`   Sentiment: ${data.sentiment_analysis?.sentiment}`);
            console.log(`   Technical Pairs: ${Object.keys(data.technical_analyses || {}).length}`);
        } else {
            console.log(`❌ Enhanced Analysis Failed: ${response.status}`);
        }
    } catch (error) {
        console.log(`❌ Enhanced Analysis Error: ${error.message}`);
    }
    
    // Test 3: News Sentiment
    console.log('\n3️⃣ Testing News Sentiment...');
    try {
        const testData = {
            news_items: [{
                title: "US CPI Data Better Than Expected",
                content: "Consumer Price Index rose 0.3% in December, beating expectations."
            }]
        };
        
        const response = await fetch(`${API_BASE_URL}/api/news-sentiment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testData)
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ News Sentiment Working!');
            console.log(`   Sentiment: ${data.overall_sentiment}`);
            console.log(`   Keywords: ${data.top_keywords?.slice(0, 3).join(', ')}`);
        } else {
            console.log(`❌ News Sentiment Failed: ${response.status}`);
        }
    } catch (error) {
        console.log(`❌ News Sentiment Error: ${error.message}`);
    }
    
    // Test 4: Technical Analysis
    console.log('\n4️⃣ Testing Technical Analysis...');
    try {
        const response = await fetch(`${API_BASE_URL}/api/technical-analysis/EUR_USD`);
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Technical Analysis Working!');
            console.log(`   Pair: ${data.pair}`);
            console.log(`   Sentiment: ${data.sentiment?.sentiment}`);
            console.log(`   Signals: ${data.signals?.length || 0}`);
        } else {
            console.log(`❌ Technical Analysis Failed: ${response.status}`);
        }
    } catch (error) {
        console.log(`❌ Technical Analysis Error: ${error.message}`);
    }
    
    console.log('\n' + '=' .repeat(60));
    console.log('🎯 Frontend Integration Test Complete!');
}

// Run the test
testFrontendIntegration();
