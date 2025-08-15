# Enhanced Macroeconomic Analyzer - Integration Guide

## 🚀 **Quick Start Guide**

### **1. Basic Usage**

```python
from backend.services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext

# Initialize the analyzer
analyzer = GPTAIAnalyzer()

# Create market context with positioning data
market_context = MarketContext(
    current_prices={'EUR/USD': 1.0850, 'USD/JPY': 148.50},
    recent_volatility={'EUR/USD': 0.008, 'USD/JPY': 0.012},
    market_sentiment={'EUR/USD': 'bullish', 'USD/JPY': 'bearish'},
    key_levels={'EUR/USD': {'support': [1.0800], 'resistance': [1.0900]}},
    economic_calendar=[],
    bond_yields={'US_10Y': 4.25, 'US_2Y': 4.75},
    equity_indices={'SPX': 4850, 'NDX': 17200},
    commodity_prices={'GOLD': 2050, 'OIL': 75.50},
    # NEW positioning data
    retail_sentiment={'EUR/USD': 0.65, 'USD/JPY': 0.35},
    futures_positioning={'EUR/USD': 15000, 'USD/JPY': -8000},
    institutional_flow={'EUR/USD': 25.5, 'USD/JPY': -15.2},
    time_to_event=3600,  # 1 hour until event
    liquidity_level=2,   # Medium liquidity
    scenario_probabilities={'higher': 0.30, 'lower': 0.50, 'inline': 0.20}
)

# Economic event data
event = {
    'id': 'ppi_2024_01_15',
    'title': 'US PPI Data Release',
    'currency': 'USD',
    'impact': 'High',
    'expected': '0.3%',
    'previous': '0.2%',
    'time': '13:30',
    'date': '2024-01-15'
}

# Generate pre-event analysis
result = analyzer.analyze_macro_event(event, market_context, "pre_event")

# Access the enhanced analysis
print(f"Model Used: {result.model_used}")
print(f"Cost: ${result.cost_estimate:.4f}")
print(f"Confidence: {result.confidence_score}")

# Access specific sections
print(f"Indicator Explanation: {result.general_overview['indicator_explanation']}")
print(f"Bullish Scenario: {result.market_logic['bullish_scenario']}")
print(f"Risk Score: {result.risk_metrics['volatility_risk_score']}")
```

### **2. Post-Event Analysis**

```python
# For post-event analysis, include actual data
event_with_actual = {
    'id': 'ppi_2024_01_15',
    'title': 'US PPI Data Release',
    'currency': 'USD',
    'impact': 'High',
    'actual': '0.4%',      # Actual result
    'expected': '0.3%',    # Expected result
    'previous': '0.2%',
    'time': '13:30',
    'date': '2024-01-15'
}

# Generate post-event analysis
result = analyzer.analyze_macro_event(event_with_actual, market_context, "post_event")

# Access post-event specific analysis
surprise_analysis = result.scenario_analysis['actual_vs_expected']
print(f"Surprise Factor: {surprise_analysis['surprise_factor']}")
print(f"Market Reaction: {surprise_analysis['market_reaction']}")
```

---

## 📊 **Enhanced Analysis Structure**

### **Complete Output Structure:**

```python
result = analyzer.analyze_macro_event(event, market_context, "pre_event")

# Access all sections
analysis_sections = {
    'general_overview': result.general_overview,
    'market_logic': result.market_logic,
    'scenario_analysis': result.scenario_analysis,
    'short_term_impact': result.short_term_impact,
    'long_term_impact': result.long_term_impact,
    'sentiment_analysis': result.sentiment_analysis,
    'cross_market_links': result.cross_market_links,
    'trading_framework': result.trading_framework,
    'big_picture': result.big_picture,
    'risk_metrics': result.risk_metrics,
    'historical_context': result.historical_context
}

# Example: Access scenario probabilities
scenarios = result.scenario_analysis['scenario_analysis']
for scenario_name, scenario_data in scenarios.items():
    if isinstance(scenario_data, dict) and 'probability' in scenario_data:
        print(f"{scenario_name}: {scenario_data['probability']:.1%} probability")
        print(f"  Implication: {scenario_data['implication']}")
        print(f"  Currency Impact: {scenario_data['currency_impact']}")
        print(f"  Volatility Risk: {scenario_data['volatility_risk']}/10")
```

---

## 🔧 **Configuration Options**

### **1. Environment Variables**

```bash
# Required for GPT analysis
export OPENAI_API_KEY="your_openai_api_key_here"

# Optional for Redis caching
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

### **2. Rate Limiting Configuration**

```python
analyzer = GPTAIAnalyzer()

# Customize rate limits
analyzer.max_calls_per_hour = 100  # Default: 50
analyzer.cost_estimates = {
    'gpt-4-turbo': 0.03,    # per 1K tokens
    'gpt-3.5-turbo': 0.002  # per 1K tokens
}
```

### **3. Cache Configuration**

```python
# Cache durations (in seconds)
PRE_EVENT_CACHE_DURATION = 3600    # 1 hour
POST_EVENT_CACHE_DURATION = 86400  # 24 hours
INDICATOR_CACHE_DURATION = 2592000 # 30 days
```

---

## 📈 **Usage Statistics**

### **Monitor Performance:**

```python
# Get usage statistics
stats = analyzer.get_usage_stats()
print(f"Total Cost: ${stats['total_cost']:.4f}")
print(f"API Calls This Hour: {stats['api_calls_this_hour']}")
print(f"Cache Hit Rate: {stats['cache_hit_rate']:.1%}")

# Check cache status
print(f"Economic Indicators Cached: {len(analyzer.economic_indicators_cache)}")
```

---

## 🎯 **Best Practices**

### **1. Market Context Preparation**

```python
def create_comprehensive_market_context():
    """Create a comprehensive market context with all positioning data"""
    return MarketContext(
        # Essential data
        current_prices=get_current_prices(),
        recent_volatility=calculate_volatility(),
        market_sentiment=analyze_sentiment(),
        key_levels=get_technical_levels(),
        
        # Positioning data (if available)
        retail_sentiment=get_retail_sentiment(),
        futures_positioning=get_futures_positioning(),
        institutional_flow=get_institutional_flow(),
        
        # Event-specific data
        time_to_event=calculate_time_to_event(),
        liquidity_level=assess_liquidity(),
        scenario_probabilities=calculate_probabilities()
    )
```

### **2. Error Handling**

```python
try:
    result = analyzer.analyze_macro_event(event, market_context, "pre_event")
    
    if result.model_used == "fallback":
        print("⚠️ Using fallback analysis - check API key and connectivity")
    
    # Always check confidence score
    if result.confidence_score < 70:
        print("⚠️ Low confidence analysis - consider manual review")
        
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    # Handle gracefully - maybe use cached analysis or manual review
```

### **3. Cost Optimization**

```python
# Use caching effectively
# First call for new indicator: ~$0.001
# Subsequent calls: $0.00 (cached)

# Monitor costs
stats = analyzer.get_usage_stats()
if stats['total_cost'] > 10.0:  # $10 threshold
    print("⚠️ High API costs detected - review usage patterns")
```

---

## 🔄 **Integration with Existing Systems**

### **1. Flask Backend Integration**

```python
from flask import Flask, request, jsonify
from backend.services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext

app = Flask(__name__)
analyzer = GPTAIAnalyzer()

@app.route('/api/analyze', methods=['POST'])
def analyze_event():
    data = request.json
    
    # Extract data
    event = data['event']
    market_data = data['market_context']
    
    # Create market context
    market_context = MarketContext(**market_data)
    
    # Generate analysis
    result = analyzer.analyze_macro_event(
        event, 
        market_context, 
        data.get('analysis_type', 'pre_event')
    )
    
    # Return structured response
    return jsonify({
        'success': True,
        'analysis': {
            'general_overview': result.general_overview,
            'market_logic': result.market_logic,
            'scenario_analysis': result.scenario_analysis,
            'short_term_impact': result.short_term_impact,
            'long_term_impact': result.long_term_impact,
            'sentiment_analysis': result.sentiment_analysis,
            'cross_market_links': result.cross_market_links,
            'trading_framework': result.trading_framework,
            'big_picture': result.big_picture,
            'risk_metrics': result.risk_metrics,
            'historical_context': result.historical_context
        },
        'metadata': {
            'model_used': result.model_used,
            'cost_estimate': result.cost_estimate,
            'confidence_score': result.confidence_score,
            'cache_hit': result.cache_hit,
            'definition_source': result.definition_source
        }
    })
```

### **2. Frontend Integration**

```javascript
// Example frontend integration
async function getMacroAnalysis(eventData, marketContext) {
    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            event: eventData,
            market_context: marketContext,
            analysis_type: 'pre_event'
        })
    });
    
    const data = await response.json();
    
    if (data.success) {
        // Display enhanced analysis
        displayAnalysis(data.analysis);
        displayMetadata(data.metadata);
    } else {
        console.error('Analysis failed:', data.error);
    }
}

function displayAnalysis(analysis) {
    // Display each section
    displayGeneralOverview(analysis.general_overview);
    displayMarketLogic(analysis.market_logic);
    displayScenarioAnalysis(analysis.scenario_analysis);
    displayRiskMetrics(analysis.risk_metrics);
    // ... etc
}
```

---

## 🚀 **Production Deployment**

### **1. Environment Setup**

```bash
# Install dependencies
pip install openai redis

# Set environment variables
export OPENAI_API_KEY="your_key_here"

# Optional: Start Redis for caching
redis-server
```

### **2. Monitoring**

```python
# Regular health checks
def health_check():
    stats = analyzer.get_usage_stats()
    
    # Check API key
    if not analyzer.api_key:
        return {"status": "error", "message": "API key missing"}
    
    # Check rate limits
    if stats['api_calls_this_hour'] >= stats['max_calls_per_hour']:
        return {"status": "warning", "message": "Rate limit approaching"}
    
    # Check costs
    if stats['total_cost'] > 50.0:
        return {"status": "warning", "message": "High costs detected"}
    
    return {"status": "healthy", "stats": stats}
```

### **3. Scaling Considerations**

- **Redis Caching**: Use Redis for production caching
- **Load Balancing**: Multiple analyzer instances
- **Rate Limiting**: Implement application-level rate limiting
- **Cost Monitoring**: Set up alerts for high API costs
- **Error Tracking**: Monitor fallback usage rates

---

## ✅ **Ready to Use**

The enhanced macroeconomic analyzer is now ready for production use with comprehensive documentation, robust error handling, and scalable architecture. It provides professional-grade analysis for any economic indicator with cost efficiency and reliability.
