// Test script to check frontend data processing
async function testFrontendData() {
    console.log('🔍 Testing Frontend Data Processing...');
    
    try {
        // Simulate the same API call the frontend makes
        const response = await fetch('http://localhost:5001/api/enhanced-analysis/1');
        const analysis = await response.json();
        
        console.log('📊 Raw API Response:', analysis);
        
        // Simulate the frontend data transformation
        const transformedAnalysis = {
            event: { id: 1, title: 'Test Event' },
            // Enhanced analysis structure
            immediate_impact: analysis.immediate_impact,
            long_term_impact: analysis.long_term_impact,
            context_expectations: analysis.context_expectations,
            sentiment_analysis: analysis.sentiment_analysis,
            cross_market_links: analysis.cross_market_links,
            market_shifts: analysis.market_shifts,
            big_picture: analysis.big_picture,
            confidence_score: analysis.confidence_score,
            analysis_type: analysis.analysis_type,
            data_warning: analysis.data_warning,
            // Legacy fields for compatibility
            marketConfidence: analysis.confidence_score > 80 ? 'High' : analysis.confidence_score > 60 ? 'Medium' : 'Low',
            confidenceScore: analysis.confidence_score || 75,
            sentiment: analysis.sentiment_analysis?.sentiment || 'neutral',
            predictions: [
                {
                    type: 'positive',
                    icon: '🎯',
                    text: analysis.immediate_impact?.summary || 'Enhanced AI analysis available'
                }
            ],
            insights: (analysis.market_shifts?.key_levels || []).map(level => ({
                type: 'positive',
                icon: '📊',
                text: `Watch ${level.level} level`
            })).concat(
                (analysis.cross_market_links?.correlations || []).map(corr => ({
                    type: 'info',
                    icon: '🔗',
                    text: `${corr.asset} correlation: ${corr.strength}`
                }))
            ),
            tradingOpportunities: []
        };
        
        console.log('🔄 Transformed Analysis:', transformedAnalysis);
        
        // Check conditional rendering conditions
        console.log('🎯 Conditional Rendering Checks:');
        console.log('- aiAnalysis.immediate_impact:', !!transformedAnalysis.immediate_impact);
        console.log('- aiAnalysis.market_shifts:', !!transformedAnalysis.market_shifts);
        console.log('- aiAnalysis.cross_market_links:', !!transformedAnalysis.cross_market_links);
        console.log('- aiAnalysis.context_expectations:', !!transformedAnalysis.context_expectations);
        console.log('- aiAnalysis.big_picture:', !!transformedAnalysis.big_picture);
        console.log('- aiAnalysis.predictions:', !!transformedAnalysis.predictions);
        console.log('- aiAnalysis.insights:', !!transformedAnalysis.insights);
        
        // Check specific field access
        console.log('🔍 Field Access Tests:');
        console.log('- immediate_impact.event_significance:', transformedAnalysis.immediate_impact?.event_significance);
        console.log('- market_shifts.strategy_confidence:', transformedAnalysis.market_shifts?.strategy_confidence);
        console.log('- cross_market_links.cross_market_confidence:', transformedAnalysis.cross_market_links?.cross_market_confidence);
        console.log('- big_picture.overall_risk_level:', transformedAnalysis.big_picture?.overall_risk_level);
        
        // Check if any sections would render
        const wouldRender = {
            immediateImpact: !!(transformedAnalysis.immediate_impact || transformedAnalysis.predictions),
            marketShifts: !!(transformedAnalysis.market_shifts || transformedAnalysis.insights),
            crossMarket: !!transformedAnalysis.cross_market_links,
            contextExpectations: !!transformedAnalysis.context_expectations,
            bigPicture: !!transformedAnalysis.big_picture
        };
        
        console.log('✅ Would Render Sections:', wouldRender);
        
        const totalSections = Object.values(wouldRender).filter(Boolean).length;
        console.log(`📊 Total sections that would render: ${totalSections}/5`);
        
    } catch (error) {
        console.error('❌ Error testing frontend data:', error);
    }
}

// Run the test
testFrontendData();
