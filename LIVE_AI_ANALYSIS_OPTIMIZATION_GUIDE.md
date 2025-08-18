# AI Analysis Optimization Guide for Live News Articles - FXSentinel

## 🎯 Executive Summary

This document provides a comprehensive strategy for optimizing AI analysis of live news articles for your FXSentinel platform. We'll cover how to analyze news from Reuters, Bloomberg, CNBC, WatcherGuru alerts, political comments, and other sources to extract forex trading implications while minimizing costs and maximizing value.

## 📊 Current State Analysis

### What You Have Now
- **News Aggregation**: RSS feeds from Reuters, Bloomberg, CNBC, MarketWatch
- **WatcherGuru Integration**: Real-time forex alerts and signals
- **Free Sentiment Analyzer**: Basic keyword-based analysis
- **GPT Integration**: Expensive API calls with mixed results
- **Basic Caching**: 2-hour cache with history tracking

### Key Problems Identified
1. **High API Costs**: GPT calls for every news article are expensive
2. **Generic Analysis**: Current prompts don't extract specific forex trading insights
3. **Poor Input Quality**: Not providing GPT with the right context for forex analysis
4. **Inconsistent Output**: Analysis format varies and isn't trader-focused
5. **No Smart Filtering**: Analyzing low-impact news with expensive GPT calls

## 🚀 Optimal AI Analysis Strategy for Live News

### 1. **Smart Input Selection - What News Deserves GPT Analysis**

#### **News Priority System**
```
Priority 1 (Always GPT): High-impact forex news
- Central bank communications (Fed, ECB, BOE, BOJ speeches)
- Major political events affecting currencies (elections, trade wars)
- Significant economic policy announcements
- Major currency intervention news
- WatcherGuru high-confidence alerts
- Trump comments on trade/currency policy

Priority 2 (Conditional GPT): Medium-impact forex news
- Corporate earnings with major forex implications
- Geopolitical events affecting specific currencies
- Economic data commentary from major sources
- Market-moving analyst reports
- WatcherGuru medium-confidence alerts

Priority 3 (Free Analysis Only): Low-impact news
- General market commentary
- Minor corporate news
- Regional economic news
- Technical analysis articles
- WatcherGuru low-confidence alerts
```

#### **Optimal Input Structure for News Analysis**
```json
{
  "news_item": {
    "title": "Trump Says Dollar 'Too Strong', Threatens Currency Intervention",
    "summary": "Former President Trump criticized the strength of the US dollar in a campaign speech, suggesting he would take action to weaken the currency if re-elected. 'The dollar is killing our exports,' Trump said, 'we need to do something about it.'",
    "source": "Reuters",
    "published_at": "2024-01-15T13:30:00Z",
    "impact": "High",
    "currency_pairs": ["EUR/USD", "USD/JPY", "USD/CNY"],
    "news_type": "political_comment"
  },
  "market_context": {
    "current_prices": {
      "EUR/USD": 1.0850,
      "USD/JPY": 148.50,
      "GBP/USD": 1.2650
    },
    "recent_volatility": {
      "EUR/USD": 0.012,
      "USD/JPY": 0.008
    },
    "market_sentiment": {
      "EUR/USD": "bearish",
      "USD/JPY": "bullish"
    },
    "key_levels": {
      "EUR/USD": {
        "support": [1.0800, 1.0750],
        "resistance": [1.0900, 1.0950]
      }
    },
    "upcoming_events": [
      {
        "event": "Fed Rate Decision",
        "time": "2024-01-17T19:00:00Z",
        "impact": "High"
      }
    ]
  },
  "analysis_requirements": {
    "focus_areas": ["immediate_reaction", "trading_opportunities", "political_risk"],
    "timeframe": "1-24_hours",
    "confidence_threshold": 0.7
  }
}
```

### 2. **Cost Minimization Strategy for News Analysis**

#### **Smart Model Selection for News**
```python
def select_analysis_method(news_item, market_context):
    # Calculate news impact score
    impact_score = calculate_news_impact_score(news_item)
    
    # Check news source credibility
    source_credibility = get_source_credibility(news_item['source'])
    
    # Check for political/central bank content
    has_political_content = check_political_content(news_item)
    
    if impact_score >= 0.8 or has_political_content:
        return "gpt-4-turbo"  # Best quality for major political/economic news
    elif impact_score >= 0.6 and source_credibility >= 0.8:
        return "gpt-3.5-turbo"  # Good quality for credible sources
    else:
        return "free_analysis"  # Use local sentiment analysis
```

#### **Cost-Effective Prompt Engineering for News**
```python
# EXPENSIVE (Current): 2000+ tokens
prompt = f"""
You are a forex market analyst. Analyze this news article: {news_item['title']}
{news_item['summary']}
Consider all market factors and provide comprehensive analysis...
[500+ words of instructions]
"""

# OPTIMIZED: 800-1200 tokens
prompt = f"""
Analyze forex impact of news: {news_item['title']}
Context: {news_item['summary']}
Source: {news_item['source']}
Current EUR/USD: {market_context['current_prices']['EUR/USD']}
Focus: Immediate reaction, trading opportunities, political risk
Format: JSON with specific trading opportunities
"""
```

#### **Smart Caching for News Analysis**
```python
def get_cached_news_analysis(news_hash):
    # Check for similar news analysis (within 48 hours)
    # Use semantic similarity to find relevant cached analysis
    # Consider political context and source credibility
    
    cached_analysis = cache.get_similar_news_analysis(news_hash, similarity_threshold=0.8)
    if cached_analysis and is_recent_enough(cached_analysis, hours=48):
        return cached_analysis, True  # Cache hit
    return None, False  # Cache miss
```

### 3. **MVP Implementation Strategy for News**

#### **Phase 1: Enhanced Free News Analysis (Week 1-2)**
```python
class EnhancedNewsAnalyzer:
    def analyze_news_article(self, news_item):
        # Use existing sentiment analyzer
        sentiment = self.sentiment_analyzer.analyze(news_item)
        
        # Add news-specific patterns
        news_impact = self.analyze_news_impact(news_item)
        
        # Generate trading opportunities
        opportunities = self.generate_opportunities(sentiment, news_impact)
        
        # Add political risk assessment
        political_risk = self.assess_political_risk(news_item)
        
        return {
            "summary": self.create_summary(sentiment, news_impact, political_risk),
            "trading_opportunities": opportunities,
            "political_risk": political_risk,
            "confidence": sentiment.confidence,
            "cost": 0.0
        }
```

#### **Phase 2: Smart GPT Integration for News (Week 3-4)**
```python
class SmartNewsGPTAnalyzer:
    def analyze_news_article(self, news_item):
        # Check if news deserves GPT analysis
        if not self.deserves_gpt_analysis(news_item):
            return self.free_analyzer.analyze_news_article(news_item)
        
        # Use optimized prompts for news
        prompt = self.build_optimized_news_prompt(news_item)
        
        # Call GPT with cost controls
        response = self.call_gpt_with_limits(prompt)
        
        return self.format_news_response(response)
```

### 4. **Optimal Output Format for News Analysis**

#### **Structured News Analysis Response**
```json
{
  "analysis_id": "news_123456789",
  "timestamp": "2024-01-15T14:30:00Z",
  "analysis_type": "gpt_enhanced_news",
  "cost": 0.0023,
  
  "summary": {
    "headline": "Trump Comments Bearish for USD",
    "key_points": [
      "Trump threatens currency intervention if re-elected",
      "Dollar strength concerns for US exports",
      "Political uncertainty may weaken USD sentiment"
    ],
    "confidence": 85
  },
  
  "news_impact": {
    "immediate_reaction": "bearish_usd",
    "expected_volatility": "high",
    "timeframe": "1-24_hours",
    "political_risk": "high",
    "key_levels": {
      "EUR/USD": {
        "support": [1.0800, 1.0750],
        "resistance": [1.0850, 1.0900],
        "breakout_target": 1.0900
      }
    }
  },
  
  "trading_opportunities": [
    {
      "pair": "EUR/USD",
      "strategy": "political_risk_play",
      "direction": "bullish",
      "entry_zone": {
        "min": 1.0850,
        "max": 1.0870
      },
      "stop_loss": 1.0820,
      "take_profit": 1.0950,
      "probability": 70,
      "risk_reward": 2.5,
      "timeframe": "1-24_hours",
      "risk_level": "high"
    }
  ],
  
  "political_risk_assessment": {
    "risk_level": "high",
    "affected_currencies": ["USD", "CNY", "JPY"],
    "political_context": "election_campaign",
    "policy_implications": ["currency_intervention", "trade_policy"],
    "timeline": "medium_term"
  },
  
  "sentiment_analysis": {
    "overall_sentiment": "bearish_usd",
    "confidence": 85,
    "keywords": ["trump", "dollar", "intervention", "exports"],
    "affected_pairs": ["EUR/USD", "USD/JPY", "USD/CNY"]
  }
}
```

## 📝 Example Implementation for News Analysis

### **Example News Item**
```json
{
  "id": 123456789,
  "title": "Trump Says Dollar 'Too Strong', Threatens Currency Intervention",
  "summary": "Former President Trump criticized the strength of the US dollar in a campaign speech, suggesting he would take action to weaken the currency if re-elected. 'The dollar is killing our exports,' Trump said, 'we need to do something about it.' The comments come amid growing concerns about US trade competitiveness and follow similar statements from Trump during his previous administration.",
  "source": "Reuters",
  "url": "https://reuters.com/article/trump-dollar-comments",
  "published_at": "2024-01-15T13:30:00Z",
  "impact": "High",
  "currency_pairs": ["EUR/USD", "USD/JPY", "USD/CNY"],
  "type": "political_comment",
  "status": "PUBLISHED"
}
```

### **Market Context**
```json
{
  "current_prices": {
    "EUR/USD": 1.0850,
    "USD/JPY": 148.50,
    "GBP/USD": 1.2650,
    "USD/CNY": 7.1850
  },
  "recent_volatility": {
    "EUR/USD": 0.012,
    "USD/JPY": 0.008,
    "USD/CNY": 0.005
  },
  "market_sentiment": {
    "EUR/USD": "bearish",
    "USD/JPY": "bullish",
    "USD/CNY": "stable"
  },
  "key_levels": {
    "EUR/USD": {
      "support": [1.0800, 1.0750],
      "resistance": [1.0900, 1.0950]
    },
    "USD/JPY": {
      "support": [147.50, 146.80],
      "resistance": [149.20, 150.00]
    }
  },
  "political_context": {
    "election_cycle": "active",
    "trump_polling": "leading",
    "key_issues": ["trade", "currency", "exports"]
  }
}
```

### **Optimized GPT Prompt for News**
```
You are a senior forex market analyst. Analyze this political news for forex trading implications.

NEWS: Trump threatens currency intervention, says dollar is "too strong" and "killing exports"

MARKET CONTEXT:
- EUR/USD: 1.0850 (bearish sentiment)
- USD/JPY: 148.50 (bullish sentiment)
- Recent EUR/USD volatility: 0.012 (high)
- Political context: Active election cycle, Trump leading polls

ANALYSIS REQUIREMENTS:
1. Immediate market reaction prediction
2. Political risk assessment
3. Specific trading opportunities with entry/exit levels
4. Risk management recommendations

Provide analysis in this exact JSON format:
{
  "summary": "Brief market impact summary",
  "immediate_reaction": "bearish_usd/bullish_usd/neutral",
  "political_risk": {
    "level": "high/medium/low",
    "affected_currencies": ["USD", "CNY"],
    "timeline": "immediate/medium_term/long_term"
  },
  "trading_opportunities": [
    {
      "pair": "EUR/USD",
      "strategy": "political_risk_play",
      "direction": "bullish",
      "entry_zone": {"min": 1.0850, "max": 1.0870},
      "stop_loss": 1.0820,
      "take_profit": 1.0950,
      "probability": 70,
      "timeframe": "1-24_hours"
    }
  ],
  "risk_management": {
    "position_size": "reduced_due_to_political_risk",
    "key_levels": ["1.0800", "1.0900"]
  }
}
```

Keep analysis concise and actionable. Focus on political risk and trading implications.
```

### **Expected GPT Response**
```json
{
  "summary": "Trump's currency intervention threats create bearish USD sentiment. Political uncertainty and potential policy changes may weaken dollar against major pairs, especially if intervention rhetoric intensifies.",
  "immediate_reaction": "bearish_usd",
  "political_risk": {
    "level": "high",
    "affected_currencies": ["USD", "CNY", "JPY"],
    "timeline": "medium_term"
  },
  "trading_opportunities": [
    {
      "pair": "EUR/USD",
      "strategy": "political_risk_play",
      "direction": "bullish",
      "entry_zone": {"min": 1.0850, "max": 1.0870},
      "stop_loss": 1.0820,
      "take_profit": 1.0950,
      "probability": 70,
      "timeframe": "1-24_hours"
    },
    {
      "pair": "USD/JPY",
      "strategy": "momentum_following",
      "direction": "bearish",
      "entry_zone": {"min": 148.30, "max": 148.50},
      "stop_loss": 148.80,
      "take_profit": 147.50,
      "probability": 65,
      "timeframe": "1-24_hours"
    }
  ],
  "risk_management": {
    "position_size": "reduced_due_to_political_risk",
    "key_levels": ["1.0800", "1.0900", "148.80", "147.50"],
    "correlation_risks": ["USD/JPY", "GBP/USD"]
  }
}
```

### **Final Display Format for News**
```jsx
<div className="news-analysis-card">
  <div className="analysis-header">
    <div className="sentiment-badge bearish">
      <Icon name="trending-down" />
      Bearish USD
    </div>
    <div className="political-risk-badge high">
      <Icon name="warning" />
      High Political Risk
    </div>
    <div className="confidence-score">
      Confidence: 70%
    </div>
    <div className="cost-indicator">
      Analysis Cost: $0.0023
    </div>
  </div>
  
  <div className="analysis-summary">
    <h3>News Impact</h3>
    <p>Trump's currency intervention threats create bearish USD sentiment. Political uncertainty and potential policy changes may weaken dollar against major pairs, especially if intervention rhetoric intensifies.</p>
  </div>
  
  <div className="political-risk-assessment">
    <h3>Political Risk Assessment</h3>
    <div className="risk-details">
      <div className="risk-level">Risk Level: High</div>
      <div className="affected-currencies">Affected: USD, CNY, JPY</div>
      <div className="timeline">Timeline: Medium Term</div>
    </div>
  </div>
  
  <div className="trading-opportunities">
    <h3>Trading Opportunities</h3>
    <div className="opportunity-item">
      <div className="pair-info">
        <span className="pair">EUR/USD</span>
        <span className="strategy">Political Risk Play</span>
        <span className="direction bullish">Bullish</span>
      </div>
      <div className="trade-details">
        <div className="entry-zone">
          Entry: 1.0850 - 1.0870
        </div>
        <div className="risk-reward">
          Stop Loss: 1.0820 | Take Profit: 1.0950
        </div>
        <div className="probability">
          Probability: 70% | Timeframe: 1-24 hours
        </div>
      </div>
    </div>
  </div>
  
  <div className="risk-management">
    <h3>Risk Management</h3>
    <ul>
      <li>Reduce position size due to high political risk</li>
      <li>Key levels to watch: 1.0800, 1.0900</li>
      <li>Monitor correlation with USD/JPY and GBP/USD</li>
      <li>Watch for additional political comments</li>
    </ul>
  </div>
</div>
```

## 💰 Cost Optimization for News Analysis

### **Current Costs (Estimated)**
- **GPT-4 calls**: $0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)
- **Average news analysis**: 2000 tokens = $0.18 per analysis
- **Daily cost**: 30 news analyses × $0.18 = $5.40/day
- **Monthly cost**: $162/month

### **Optimized Costs (Target)**
- **Smart filtering**: Only 25% of news gets GPT analysis
- **Optimized prompts**: 800 tokens = $0.07 per analysis
- **Daily cost**: 8 GPT analyses × $0.07 = $0.56/day
- **Monthly cost**: $17/month
- **Savings**: 90% cost reduction

### **News-Specific Cost Control**
```python
class NewsCostController:
    def __init__(self):
        self.daily_budget = 3.0  # $3 per day for news analysis
        self.daily_spent = 0.0
        self.analysis_count = 0
        self.political_news_count = 0
        
    def can_afford_news_analysis(self, news_item, estimated_cost):
        # Prioritize political news and high-impact sources
        if self.is_political_news(news_item) or self.is_high_impact_source(news_item):
            return (self.daily_spent + estimated_cost) <= self.daily_budget
        else:
            # Lower priority for general news
            return (self.daily_spent + estimated_cost) <= (self.daily_budget * 0.5)
    
    def record_news_analysis_cost(self, news_item, actual_cost):
        self.daily_spent += actual_cost
        self.analysis_count += 1
        
        if self.is_political_news(news_item):
            self.political_news_count += 1
```

## 🎯 Implementation Roadmap for News Analysis

### **Week 1: Enhanced News Analysis Foundation**
- [ ] Implement smart news filtering system
- [ ] Create news-specific prompt templates
- [ ] Set up political risk assessment
- [ ] Enhance free sentiment analyzer for news

### **Week 2: Smart GPT Integration for News**
- [ ] Implement conditional GPT analysis for news
- [ ] Create structured news output format
- [ ] Set up news caching with similarity matching
- [ ] Build news-specific cost control system

### **Week 3: News Source Optimization**
- [ ] Implement source credibility scoring
- [ ] Add WatcherGuru integration
- [ ] Create political news detection
- [ ] Optimize news prompt engineering

### **Week 4: Testing & Refinement**
- [ ] Test with real news data from all sources
- [ ] Monitor costs and quality for news analysis
- [ ] Refine prompts based on news analysis results
- [ ] Implement user feedback system for news

## 📊 Success Metrics for News Analysis

### **Cost Metrics**
- **Target**: <$20/month for news GPT analysis
- **Current**: ~$162/month (estimated)
- **Savings Goal**: 90%+ cost reduction

### **Quality Metrics**
- **News Analysis Relevance**: >80% of analyses provide actionable insights
- **Political Risk Accuracy**: >75% of political risk assessments accurate
- **Trading Accuracy**: >65% of predicted directions correct

### **Performance Metrics**
- **Response Time**: <5 seconds for news analysis generation
- **Cache Hit Rate**: >50% for similar news analysis
- **Source Coverage**: Support for 10+ major news sources

## 🔧 Technical Implementation for News

### **Smart News Filtering**
```python
def should_use_gpt_for_news(news_item):
    # Calculate news impact score
    impact_score = calculate_news_impact_score(news_item)
    
    # Check for political content
    political_keywords = ['trump', 'biden', 'fed', 'ecb', 'boe', 'boj', 'intervention']
    has_political_content = any(keyword in news_item['title'].lower() for keyword in political_keywords)
    
    # Check source credibility
    credible_sources = ['reuters', 'bloomberg', 'cnbc', 'watcherguru']
    is_credible_source = news_item['source'].lower() in credible_sources
    
    # Check currency pair relevance
    currency_pairs = news_item.get('currency_pairs', [])
    has_major_pairs = any(pair in ['EUR/USD', 'USD/JPY', 'GBP/USD'] for pair in currency_pairs)
    
    # Decision logic
    if has_political_content or impact_score >= 0.8:
        return True
    elif impact_score >= 0.6 and is_credible_source:
        return True
    else:
        return False
```

### **Political Risk Assessment**
```python
def assess_political_risk(news_item):
    political_indicators = {
        'trump_comments': ['trump', 'donald', 'president trump'],
        'central_bank': ['fed', 'ecb', 'boe', 'boj', 'central bank'],
        'trade_policy': ['tariffs', 'trade war', 'trade deal'],
        'currency_intervention': ['intervention', 'weaken', 'strengthen', 'currency'],
        'election_impact': ['election', 'campaign', 'polls', 'vote']
    }
    
    risk_score = 0
    risk_factors = []
    
    for indicator, keywords in political_indicators.items():
        if any(keyword in news_item['title'].lower() for keyword in keywords):
            risk_score += 0.2
            risk_factors.append(indicator)
    
    if risk_score >= 0.6:
        risk_level = "high"
    elif risk_score >= 0.3:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors
    }
```

### **News-Specific Prompt Builder**
```python
def build_optimized_news_prompt(news_item, market_context):
    # Extract key information
    title = news_item['title']
    summary = news_item['summary'][:300]  # Limit length
    source = news_item['source']
    currency_pairs = news_item.get('currency_pairs', [])
    
    # Assess political risk
    political_risk = assess_political_risk(news_item)
    
    # Build concise prompt
    prompt = f"""
Analyze forex impact of news: {title}
Source: {source}
Context: {summary}
Pairs: {', '.join(currency_pairs)}
Political Risk: {political_risk['risk_level']}
Current EUR/USD: {market_context.get('current_prices', {}).get('EUR/USD', 'N/A')}

Provide JSON analysis with:
1. Immediate reaction (bearish_usd/bullish_usd/neutral)
2. Political risk assessment
3. Trading opportunities with entry/exit levels
4. Risk management recommendations

Keep analysis concise and actionable.
"""
    return prompt
```

## 🎉 Conclusion

This optimization strategy transforms your news analysis from an expensive, generic system into a cost-effective, trader-focused tool specifically designed for analyzing live news articles from Reuters, Bloomberg, CNBC, WatcherGuru, and political sources.

**Key Benefits:**
- **90% cost reduction** while maintaining quality
- **News-focused analysis** with political risk assessment
- **Source credibility scoring** for better filtering
- **Professional output** that enhances user experience

**Next Steps:**
1. Implement the smart news filtering system
2. Create news-specific prompt templates
3. Set up political risk assessment
4. Test with real news data from all sources
5. Monitor and refine based on results

This approach ensures your MVP provides maximum value for news analysis while keeping costs under control, setting you up for sustainable growth and profitability.

---

## 🔑 How to Make It Good for MVP

### **Standardized Output Template**

Create a consistent, professional output format that works for both GPT and free analysis:

#### **Paragraph 1: News Impact Summary**
```
[News Title] has significant implications for forex markets. [Explain what the news means in simple, professional language]. This development [increases/decreases] the probability of [currency movement] as markets anticipate [specific outcome]. The [source credibility] of this news and [political/economic context] suggests [market reaction].
```

#### **Paragraph 2: Trading Implications**
```
**Immediate Reaction:** [Bullish/Bearish/Neutral] [Currency]
**Key Pairs Affected:** [List major pairs]
**Expected Volatility:** [High/Medium/Low]
**Trading Strategy 1:** [Strategy name] - [Direction] on [Pair] with entry zone [levels], stop loss at [level], take profit at [level]. Risk level: [High/Medium/Low].
**Trading Strategy 2:** [Alternative strategy] - [Direction] on [Pair] with entry zone [levels], stop loss at [level], take profit at [level]. Risk level: [High/Medium/Low].
```

#### **Highlight Essentials**
Use **bold keywords** and quick callouts for immediate scanning:
- **Immediate Reaction:** Bearish USD
- **Key Level:** 1.0900
- **Political Risk:** High
- **Timeframe:** 1-24 hours
- **Confidence:** 75%

### **Smart Prompting for MVP**

#### **Optimized JSON Prompt Format**
```python
def build_mvp_news_prompt(news_item, market_context):
    prompt = f"""
Analyze this news for forex trading: {news_item['title']}
Source: {news_item['source']}
Context: {news_item['summary'][:200]}
Current EUR/USD: {market_context.get('current_prices', {}).get('EUR/USD', 'N/A')}

Provide analysis in this exact format:
{{
  "news_impact": "Explain what the news means for markets in 2-3 sentences",
  "immediate_reaction": "bullish_usd/bearish_usd/neutral",
  "key_pairs": ["EUR/USD", "USD/JPY"],
  "volatility": "high/medium/low",
  "trading_strategies": [
    {{
      "name": "strategy_name",
      "pair": "EUR/USD",
      "direction": "bullish/bearish",
      "entry_zone": {{"min": 1.0850, "max": 1.0870}},
      "stop_loss": 1.0820,
      "take_profit": 1.0950,
      "risk_level": "high/medium/low"
    }}
  ],
  "key_levels": ["1.0800", "1.0900"],
  "timeframe": "1-24_hours",
  "confidence": 75
}}
"""
    return prompt
```

#### **Political Risk Scoring for MVP**
```python
def assess_mvp_political_risk(news_item):
    risk_indicators = {
        'trump': ['trump', 'donald', 'president'],
        'central_bank': ['fed', 'ecb', 'boe', 'boj'],
        'intervention': ['intervention', 'weaken', 'strengthen'],
        'trade_policy': ['tariffs', 'trade war', 'trade deal']
    }
    
    risk_score = 0
    for indicator, keywords in risk_indicators.items():
        if any(keyword in news_item['title'].lower() for keyword in keywords):
            risk_score += 0.25
    
    return "high" if risk_score >= 0.5 else "medium" if risk_score >= 0.25 else "low"
```

### **Hybrid Analysis Layer for MVP**

#### **Low-Priority News: Enhanced Free Analysis**
```python
class MVPFreeNewsAnalyzer:
    def analyze_low_priority_news(self, news_item):
        # Use existing sentiment analyzer
        sentiment = self.sentiment_analyzer.analyze(news_item)
        
        # Generate simple summary
        summary = self.generate_simple_summary(news_item, sentiment)
        
        # Create basic trading implications
        implications = self.create_basic_implications(sentiment)
        
        return {
            "analysis_type": "free_enhanced",
            "news_impact": summary,
            "immediate_reaction": sentiment.sentiment,
            "key_pairs": news_item.get('currency_pairs', ['EUR/USD']),
            "volatility": "medium",
            "trading_strategies": implications,
            "confidence": int(sentiment.confidence * 100),
            "cost": 0.0
        }
    
    def generate_simple_summary(self, news_item, sentiment):
        title = news_item['title']
        source = news_item['source']
        
        if sentiment.sentiment == 'positive':
            return f"{title} from {source} suggests positive market sentiment. This news may support bullish positions on affected currency pairs."
        elif sentiment.sentiment == 'negative':
            return f"{title} from {source} indicates negative market sentiment. This news may support bearish positions on affected currency pairs."
        else:
            return f"{title} from {source} shows neutral market sentiment. Monitor for clear directional signals before taking positions."
    
    def create_basic_implications(self, sentiment):
        if sentiment.sentiment == 'positive':
            return [{
                "name": "sentiment_following",
                "pair": "EUR/USD",
                "direction": "bullish",
                "entry_zone": {"min": "current_price", "max": "current_price + 10_pips"},
                "stop_loss": "current_price - 20_pips",
                "take_profit": "current_price + 30_pips",
                "risk_level": "medium"
            }]
        elif sentiment.sentiment == 'negative':
            return [{
                "name": "sentiment_following",
                "pair": "EUR/USD",
                "direction": "bearish",
                "entry_zone": {"min": "current_price - 10_pips", "max": "current_price"},
                "stop_loss": "current_price + 20_pips",
                "take_profit": "current_price - 30_pips",
                "risk_level": "medium"
            }]
        else:
            return [{
                "name": "wait_for_confirmation",
                "pair": "EUR/USD",
                "direction": "neutral",
                "entry_zone": {"min": "wait", "max": "wait"},
                "stop_loss": "N/A",
                "take_profit": "N/A",
                "risk_level": "low"
            }]
```

#### **High-Priority News: GPT Analysis**
```python
class MVPGPTNewsAnalyzer:
    def analyze_high_priority_news(self, news_item, market_context):
        # Use optimized prompt
        prompt = self.build_mvp_news_prompt(news_item, market_context)
        
        # Call GPT with cost controls
        response = self.call_gpt_with_limits(prompt)
        
        # Parse and format response
        analysis = self.parse_gpt_response(response)
        
        return {
            "analysis_type": "gpt_enhanced",
            "cost": self.calculate_cost(response),
            **analysis
        }
```

### **MVP Display Format**

#### **Unified News Analysis Card**
```jsx
<div className="news-analysis-card">
  <div className="analysis-header">
    <div className="sentiment-badge">
      <Icon name={getSentimentIcon(analysis.immediate_reaction)} />
      {analysis.immediate_reaction.replace('_', ' ').toUpperCase()}
    </div>
    <div className="analysis-type-badge">
      {analysis.analysis_type === 'gpt_enhanced' ? 'AI Enhanced' : 'Free Analysis'}
    </div>
    <div className="confidence-score">
      Confidence: {analysis.confidence}%
    </div>
    {analysis.cost > 0 && (
      <div className="cost-indicator">
        Cost: ${analysis.cost.toFixed(4)}
      </div>
    )}
  </div>
  
  <div className="news-impact">
    <h3>Market Impact</h3>
    <p>{analysis.news_impact}</p>
  </div>
  
  <div className="trading-essentials">
    <div className="essentials-grid">
      <div className="essential-item">
        <span className="label">Immediate Reaction:</span>
        <span className="value bold">{analysis.immediate_reaction.replace('_', ' ').toUpperCase()}</span>
      </div>
      <div className="essential-item">
        <span className="label">Key Pairs:</span>
        <span className="value">{analysis.key_pairs.join(', ')}</span>
      </div>
      <div className="essential-item">
        <span className="label">Volatility:</span>
        <span className="value">{analysis.volatility.toUpperCase()}</span>
      </div>
      <div className="essential-item">
        <span className="label">Timeframe:</span>
        <span className="value">{analysis.timeframe}</span>
      </div>
    </div>
  </div>
  
  <div className="trading-strategies">
    <h3>Trading Strategies</h3>
    {analysis.trading_strategies.map((strategy, index) => (
      <div key={index} className="strategy-item">
        <div className="strategy-header">
          <span className="strategy-name">{strategy.name.replace('_', ' ').toUpperCase()}</span>
          <span className="pair">{strategy.pair}</span>
          <span className={`direction ${strategy.direction}`}>
            {strategy.direction.toUpperCase()}
          </span>
        </div>
        <div className="strategy-details">
          <div className="entry-zone">
            Entry: {strategy.entry_zone.min} - {strategy.entry_zone.max}
          </div>
          <div className="risk-reward">
            Stop Loss: {strategy.stop_loss} | Take Profit: {strategy.take_profit}
          </div>
          <div className="risk-level">
            Risk Level: {strategy.risk_level.toUpperCase()}
          </div>
        </div>
      </div>
    ))}
  </div>
  
  {analysis.key_levels && analysis.key_levels.length > 0 && (
    <div className="key-levels">
      <h3>Key Levels to Watch</h3>
      <div className="levels-list">
        {analysis.key_levels.map((level, index) => (
          <span key={index} className="level-badge">{level}</span>
        ))}
      </div>
    </div>
  )}
</div>
```

### **MVP Implementation Priority**

#### **Phase 1: Core MVP (Week 1)**
- [ ] Implement standardized output template
- [ ] Create hybrid analysis system (free + GPT)
- [ ] Build basic news filtering
- [ ] Set up cost tracking

#### **Phase 2: Enhanced MVP (Week 2)**
- [ ] Add political risk scoring
- [ ] Implement source credibility
- [ ] Create optimized prompts
- [ ] Add caching system

#### **Phase 3: Production MVP (Week 3)**
- [ ] Test with real news data
- [ ] Optimize prompts based on results
- [ ] Add user feedback system
- [ ] Monitor and refine
