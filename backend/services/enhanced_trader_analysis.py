#!/usr/bin/env python3
"""
Enhanced Trader-Focused AI Analysis Service for FXSentinel
Implements trader-friendly analysis with quick-scan elements and forward scenarios
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
import os

logger = logging.getLogger(__name__)

@dataclass
class EnhancedGPTAnalysisResult:
    """Enhanced GPT analysis result with trader-focused structure"""
    
    # Quick-scan elements
    headline: str
    key_takeaway: str
    
    # Core analysis sections
    event_summary: Dict[str, Any]
    market_reaction: Dict[str, Any]
    forward_scenarios: Dict[str, Any]
    implications_takeaways: Dict[str, Any]
    trading_plan: Dict[str, Any]
    
    # Meta data
    confidence_score: float
    analysis_timestamp: str
    event_id: str
    analysis_type: str
    model_used: str
    cost_estimate: float
    cache_hit: bool = False
    definition_source: str = "internal"

@dataclass
class MarketContext:
    """Enhanced market context with positioning data"""
    current_prices: Dict[str, float]
    recent_volatility: Dict[str, float]
    market_sentiment: Dict[str, str]
    key_levels: Dict[str, Dict[str, float]]
    economic_calendar: List[Dict]
    bond_yields: Dict[str, float]
    equity_indices: Dict[str, float]
    commodity_prices: Dict[str, float]
    retail_sentiment: Dict[str, float]
    futures_positioning: Dict[str, int]
    institutional_flow: Dict[str, float]
    time_to_event: int
    liquidity_level: int
    scenario_probabilities: Dict[str, float]

class EnhancedTraderAnalyzer:
    """Enhanced trader-focused AI analyzer with quick-scan elements"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("✅ Enhanced Trader Analyzer initialized with GPT")
            except Exception as e:
                logger.error(f"❌ Error initializing OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ No OpenAI API key found - will use fallback analysis")
        
        # Cost estimates per 1K tokens
        self.cost_estimates = {
            'gpt-4-turbo': 0.03,
            'gpt-3.5-turbo': 0.002
        }
        self.total_cost = 0.0
        
        # High-impact events for model selection
        self.high_impact_events = [
            'non-farm payrolls', 'nfp', 'employment', 'unemployment',
            'cpi', 'consumer price index', 'inflation',
            'ppi', 'producer price index',
            'gdp', 'gross domestic product',
            'interest rate', 'fomc', 'ecb', 'boe', 'boj',
            'retail sales', 'manufacturing', 'ism'
        ]
        
        # Economic indicators cache
        self.economic_indicators_cache = {}
        self._load_economic_indicators_cache()
    
    def analyze_macro_event(self, event: Dict, market_context: MarketContext, 
                          analysis_type: str = "post_event") -> EnhancedGPTAnalysisResult:
        """Generate enhanced trader-focused macro analysis"""
        
        try:
            # Select appropriate model
            model = self._select_model(event)
            
            # Generate enhanced analysis
            if self.client:
                analysis = self._generate_enhanced_trader_analysis(event, market_context, analysis_type, model)
            else:
                analysis = self._get_fallback_analysis(event, market_context, analysis_type)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced trader analysis: {e}")
            return self._get_error_fallback(event, market_context, analysis_type)
    
    def _select_model(self, event: Dict) -> str:
        """Select appropriate GPT model based on event importance"""
        event_title = event.get('title', '').lower()
        event_type = event.get('type', '').lower()
        
        # Check if this is a high-impact event
        is_high_impact = any(keyword in event_title or keyword in event_type 
                           for keyword in self.high_impact_events)
        
        # Check impact level
        impact_level = event.get('impact', 'medium').lower()
        
        if is_high_impact or impact_level == 'high':
            return 'gpt-4-turbo'
        else:
            return 'gpt-3.5-turbo'
    
    def _build_enhanced_trader_prompt(self, event: Dict, market_context: MarketContext, analysis_type: str) -> str:
        """Build trader-focused prompt with quick-scan elements and forward scenarios"""
        
        economic_context = self.get_economic_indicator_context(event.get('title', 'Unknown Event'))
        
        prompt = f"""
You are a senior Forex market strategist creating concise, actionable {analysis_type} analysis for professional traders.

### OBJECTIVES:
- Provide a quick headline and one-sentence takeaway first
- Add forward-looking scenarios (bullish, bearish, neutral) with ✅ and ❌ icons
- Use positioning data, technical levels, and historical volatility
- Include implications for monetary policy and next catalysts
- Avoid redundancy. Be clear, structured, and trader-focused

---

### OUTPUT FORMAT:

{{
  "headline": "📢 [Short Impact Summary in one line]",
  "key_takeaway": "[One sentence that captures the main implication]",
  "event_summary": {{
    "title": "[Event Title]",
    "currency": "[Currency]",
    "date_time": "[Event Date & Time]",
    "previous": "[Value]",
    "expected": "[Value]",
    "actual": "[Value]",
    "impact_level": "[High/Medium/Low]",
    "outcome": "[Explain surprise or no surprise briefly]"
  }},
  "market_reaction": {{
    "price_action": "[Observed price move]",
    "volatility": "[Historical pip move + current behavior]",
    "reason": "[Why market reacted this way]",
    "positioning_context": "[Retail %, futures positioning, institutional flow summary]"
  }},
  "forward_scenarios": {{
    "bullish": "✅ Above [key level]: target [next level]. Reason: [driver]",
    "bearish": "❌ Below [key level]: target [next level]. Reason: [driver]",
    "neutral": "Range likely between [level] and [level] if no breakout."
  }},
  "implications_takeaways": {{
    "policy": "[What it means for the central bank]",
    "big_picture": "[How it fits into the macro theme]",
    "risk_note": "[Explain risk environment: high/medium/low + reasoning]"
  }},
  "trading_plan": {{
    "best_approach": "[E.g., 'wait for breakout confirmation']",
    "risk_management": "[Stop-loss, position sizing advice]",
    "key_levels": ["[support/resistance levels list]"],
    "next_catalyst": "[Name + date of the next key event]"
  }},
  "confidence_score": "[0-100 based on surprise and data clarity]"
}}

---

### EVENT DETAILS:
Title: {event.get('title', 'Unknown Event')}
Currency: {event.get('currency', 'Unknown')}
Impact Level: {event.get('impact', 'Medium')}
Expected: {event.get('expected', 'Not specified')}
Previous: {event.get('previous', 'Not specified')}
Actual: {event.get('actual', 'N/A') if analysis_type == 'pre_event' else event.get('actual', 'Not specified')}
Date & Time: {event.get('date', 'Not specified')} {event.get('time', 'Not specified')}

### MARKET CONTEXT:
Current Prices: {json.dumps(market_context.current_prices, indent=2)}
Recent Volatility: {json.dumps(market_context.recent_volatility, indent=2)}
Market Sentiment: {json.dumps(market_context.market_sentiment, indent=2)}
Key Technical Levels: {json.dumps(market_context.key_levels, indent=2)}

### POSITIONING DATA:
Retail Sentiment: {json.dumps(market_context.retail_sentiment, indent=2)}
Futures Positioning: {json.dumps(market_context.futures_positioning, indent=2)}
Institutional Flow: {json.dumps(market_context.institutional_flow, indent=2)}
Time to Event: {market_context.time_to_event} seconds
Liquidity Level: {market_context.liquidity_level} (1=High, 2=Medium, 3=Low)

### CROSS-MARKET CONTEXT:
Bond Yields: {json.dumps(market_context.bond_yields, indent=2)}
Equity Indices: {json.dumps(market_context.equity_indices, indent=2)}
Commodities: {json.dumps(market_context.commodity_prices, indent=2)}

### SCENARIO PROBABILITIES:
Higher than Expected: {market_context.scenario_probabilities.get('higher', 0.30):.1%}
Lower than Expected: {market_context.scenario_probabilities.get('lower', 0.50):.1%}
In Line with Expectations: {market_context.scenario_probabilities.get('inline', 0.20):.1%}

### ECONOMIC KNOWLEDGE:
{economic_context}

### ANALYSIS REQUIREMENTS:
1. Start with a catchy headline using emojis
2. Provide one-line key takeaway that captures the essence
3. Generate three forward scenarios with clear ✅/❌ icons
4. Use positioning data to explain market context
5. Include historical volatility context
6. Identify the next key catalyst
7. Keep tone professional but trader-friendly
8. Focus on actionable insights, not academic analysis
"""
        return prompt
    
    def _generate_enhanced_trader_analysis(self, event: Dict, market_context: MarketContext, 
                                         analysis_type: str, model: str) -> EnhancedGPTAnalysisResult:
        """Generate enhanced trader-focused analysis using GPT"""
        
        # Build the enhanced trader prompt
        prompt = self._build_enhanced_trader_prompt(event, market_context, analysis_type)
        
        try:
            # Make GPT API call
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior Forex market strategist creating concise, actionable analysis for professional traders. Focus on quick-scan elements, forward scenarios, and actionable insights. Use emojis and clear structure for trader-friendly output."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=3000,  # Increased for enhanced structure
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            analysis_data = json.loads(response_content)
            
            # Calculate cost estimate
            tokens_used = response.usage.total_tokens
            cost_estimate = (tokens_used / 1000) * self.cost_estimates.get(model, 0.01)
            self.total_cost += cost_estimate
            
            # Create enhanced analysis result
            result = EnhancedGPTAnalysisResult(
                headline=analysis_data.get('headline', f"📊 {event.get('title', 'Unknown Event')} Analysis"),
                key_takeaway=analysis_data.get('key_takeaway', 'Analysis based on current market conditions'),
                event_summary=analysis_data.get('event_summary', {}),
                market_reaction=analysis_data.get('market_reaction', {}),
                forward_scenarios=analysis_data.get('forward_scenarios', {}),
                implications_takeaways=analysis_data.get('implications_takeaways', {}),
                trading_plan=analysis_data.get('trading_plan', {}),
                confidence_score=analysis_data.get('confidence_score', 75.0),
                analysis_timestamp=datetime.now().isoformat(),
                event_id=str(event.get('id', 'unknown')),
                analysis_type=analysis_type,
                model_used=model,
                cost_estimate=cost_estimate
            )
            
            logger.info(f"✅ Enhanced trader analysis generated using {model}, cost: ${cost_estimate:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Enhanced trader analysis failed: {e}")
            raise
    
    def get_economic_indicator_context(self, event_title: str) -> str:
        """Get economic context using hybrid approach"""
        title_lower = event_title.lower()
        
        # Hardcoded patterns for major indicators
        if 'ppi' in title_lower or 'producer price' in title_lower:
            return """
PPI (Producer Price Index) measures the average change over time in the selling prices received by domestic producers for their output. It's a leading indicator of consumer inflation because producers often pass on cost increases to consumers. Higher PPI suggests future CPI increases, which can influence Federal Reserve policy decisions. PPI is particularly important for USD as it affects inflation expectations and interest rate outlook.
"""
        elif 'cpi' in title_lower or 'consumer price' in title_lower:
            return """
CPI (Consumer Price Index) measures the average change over time in the prices paid by urban consumers for a market basket of consumer goods and services. It's the primary gauge of inflation and directly influences Federal Reserve monetary policy decisions. Higher CPI typically leads to expectations of tighter monetary policy, which strengthens the USD. CPI is crucial for forex markets as it affects interest rate expectations.
"""
        elif 'non-farm' in title_lower or 'nfp' in title_lower:
            return """
Non-Farm Payrolls (NFP) measures the change in the number of employed people during the previous month, excluding the farming industry. It's the most important employment indicator and a key driver of Federal Reserve policy decisions. Strong NFP numbers suggest economic strength and potential inflationary pressures, which can lead to higher interest rates and a stronger USD. Weak NFP numbers suggest economic weakness and potential dovish policy.
"""
        elif 'gdp' in title_lower:
            return """
GDP (Gross Domestic Product) measures the total value of all goods and services produced within a country's borders. It's the broadest measure of economic activity and a key indicator of economic health. Higher GDP growth suggests economic strength and can lead to stronger currency valuations. GDP data influences central bank policy decisions and market sentiment about economic prospects.
"""
        elif 'retail sales' in title_lower:
            return """
Retail Sales measures the total receipts at stores that sell merchandise and related services to final consumers. It's a key indicator of consumer spending, which accounts for about 70% of economic activity. Strong retail sales suggest robust consumer demand and economic strength, which can strengthen the currency. Weak retail sales suggest economic weakness and potential dovish policy responses.
"""
        elif 'fomc' in title_lower or ('interest rate' in title_lower and 'decision' in title_lower):
            return """
Interest rate decisions by central banks are the most important drivers of currency valuations. The Federal Open Market Committee (FOMC) sets the federal funds rate, which influences all other interest rates in the economy. Higher interest rates typically strengthen a currency by making it more attractive to investors seeking yield. Lower interest rates typically weaken a currency by reducing its yield appeal. Interest rate decisions also affect inflation expectations and economic growth outlook.
"""
        else:
            return f"""
This economic indicator ({event_title}) provides important insights into economic activity and can influence currency valuations through its impact on economic growth, inflation expectations, and central bank policy decisions. The specific relationship between this data and currency movement depends on the indicator's characteristics and current market conditions. Traders should monitor the actual data release and market reaction for specific trading opportunities.
"""
    
    def _get_fallback_analysis(self, event: Dict, market_context: MarketContext, analysis_type: str) -> EnhancedGPTAnalysisResult:
        """Generate fallback analysis when GPT is unavailable"""
        
        currency = event.get('currency', 'USD')
        title = event.get('title', 'Unknown Event')
        
        # Generate basic fallback content
        headline = f"📊 {title} Analysis"
        key_takeaway = f"Analysis of {title} impact on {currency} currency pairs based on current market conditions."
        
        event_summary = {
            "title": title,
            "currency": currency,
            "date_time": f"{event.get('date', 'N/A')} {event.get('time', 'N/A')}",
            "previous": event.get('previous', 'N/A'),
            "expected": event.get('expected', 'N/A'),
            "actual": event.get('actual', 'N/A'),
            "impact_level": event.get('impact', 'Medium'),
            "outcome": "Analysis based on expected vs previous data"
        }
        
        market_reaction = {
            "price_action": f"Expected price movements in {currency} pairs will depend on the actual data versus expectations.",
            "volatility": "Medium volatility expected around the release",
            "reason": "Market reaction will be driven by the comparison between actual and expected data",
            "positioning_context": "Positioning data indicates current market sentiment and potential reaction intensity."
        }
        
        forward_scenarios = {
            "bullish": f"✅ Above key resistance: potential move higher on positive data surprise",
            "bearish": f"❌ Below key support: potential move lower on negative data surprise",
            "neutral": "Range likely between key support and resistance if no breakout."
        }
        
        implications_takeaways = {
            "policy": "Policy implications will depend on the data outcome and central bank reaction function.",
            "big_picture": "This data fits into the broader economic narrative and policy trajectory.",
            "risk_note": "Medium risk - typical volatility around economic releases"
        }
        
        trading_plan = {
            "best_approach": "Range trading with breakout potential based on surprise factor",
            "risk_management": "Conservative position sizing due to potential volatility",
            "key_levels": ["Key support and resistance levels to be determined"],
            "next_catalyst": "Focus on upcoming central bank meetings and related economic data"
        }
        
        return EnhancedGPTAnalysisResult(
            headline=headline,
            key_takeaway=key_takeaway,
            event_summary=event_summary,
            market_reaction=market_reaction,
            forward_scenarios=forward_scenarios,
            implications_takeaways=implications_takeaways,
            trading_plan=trading_plan,
            confidence_score=75.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type=analysis_type,
            model_used="fallback",
            cost_estimate=0.0
        )
    
    def _get_error_fallback(self, event: Dict, market_context: MarketContext, analysis_type: str) -> EnhancedGPTAnalysisResult:
        """Generate error fallback analysis"""
        
        return EnhancedGPTAnalysisResult(
            headline=f"⚠️ {event.get('title', 'Unknown Event')} Analysis",
            key_takeaway="Analysis temporarily unavailable. Please try again later.",
            event_summary={},
            market_reaction={},
            forward_scenarios={},
            implications_takeaways={},
            trading_plan={},
            confidence_score=0.0,
            analysis_timestamp=datetime.now().isoformat(),
            event_id=str(event.get('id', 'unknown')),
            analysis_type=analysis_type,
            model_used="error_fallback",
            cost_estimate=0.0
        )
    
    def _load_economic_indicators_cache(self):
        """Load cached economic indicators"""
        try:
            cache_file = "economic_indicators_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    self.economic_indicators_cache = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load economic indicators cache: {e}")
            self.economic_indicators_cache = {}

# Global instance
enhanced_trader_analyzer = EnhancedTraderAnalyzer()
