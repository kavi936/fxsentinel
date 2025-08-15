// Test script to check AI analysis display
async function testAIAnalysisDisplay() {
    console.log('🔍 Testing AI Analysis Display...');
    
    try {
        // Test the API endpoint
        const response = await fetch('http://localhost:5001/api/enhanced-analysis/1');
        const data = await response.json();
        
        console.log('✅ API Response received:', {
            hasData: !!data,
            analysisType: data.analysis_type,
            confidenceScore: data.confidence_score,
            hasImmediateImpact: !!data.immediate_impact,
            hasMarketShifts: !!data.market_shifts,
            hasCrossMarket: !!data.cross_market_links,
            hasBigPicture: !!data.big_picture,
            hasContextExpectations: !!data.context_expectations,
            hasLongTermImpact: !!data.long_term_impact
        });
        
        // Check if the data structure matches what the frontend expects
        console.log('📊 Data Structure Check:');
        console.log('- immediate_impact:', data.immediate_impact ? 'Present' : 'Missing');
        console.log('- market_shifts:', data.market_shifts ? 'Present' : 'Missing');
        console.log('- cross_market_links:', data.cross_market_links ? 'Present' : 'Missing');
        console.log('- big_picture:', data.big_picture ? 'Present' : 'Missing');
        console.log('- context_expectations:', data.context_expectations ? 'Present' : 'Missing');
        console.log('- long_term_impact:', data.long_term_impact ? 'Present' : 'Missing');
        
        // Check specific fields that the frontend is trying to access
        console.log('🎯 Frontend Field Access Check:');
        console.log('- immediate_impact.event_significance:', data.immediate_impact?.event_significance);
        console.log('- immediate_impact.current_market_context?.current_trend:', data.immediate_impact?.current_market_context?.current_trend);
        console.log('- market_shifts.strategy_confidence:', data.market_shifts?.strategy_confidence);
        console.log('- market_shifts.timing_strategy?.avoid_trading:', data.market_shifts?.timing_strategy?.avoid_trading);
        console.log('- sentiment_analysis.current_sentiment?.overall_sentiment:', data.sentiment_analysis?.current_sentiment?.overall_sentiment);
        console.log('- big_picture.overall_risk_level:', data.big_picture?.overall_risk_level);
        
        // Check if there are any null or undefined values that might cause display issues
        console.log('⚠️ Potential Display Issues:');
        const issues = [];
        if (!data.immediate_impact) issues.push('No immediate_impact data');
        if (!data.market_shifts) issues.push('No market_shifts data');
        if (!data.cross_market_links) issues.push('No cross_market_links data');
        if (!data.big_picture) issues.push('No big_picture data');
        if (!data.context_expectations) issues.push('No context_expectations data');
        if (!data.long_term_impact) issues.push('No long_term_impact data');
        
        if (issues.length > 0) {
            console.log('Issues found:', issues);
        } else {
            console.log('✅ No obvious data issues found');
        }
        
    } catch (error) {
        console.error('❌ Error testing AI analysis display:', error);
    }
}

// Run the test
testAIAnalysisDisplay();
