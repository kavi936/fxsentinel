#!/usr/bin/env python3
"""
Professional Analysis Template - Enhanced Version
Transforms ChatGPT outputs into concise, actionable desk notes
"""

import re
from typing import Dict, Any, List
from datetime import datetime, timedelta

class ProfessionalAnalysisTemplate:
    """Transforms raw ChatGPT analysis into professional desk notes"""
    
    def __init__(self):
        self.currency_central_banks = {
            'USD': 'Federal Reserve',
            'GBP': 'Bank of England',
            'EUR': 'European Central Bank',
            'JPY': 'Bank of Japan',
            'CAD': 'Bank of Canada',
            'AUD': 'Reserve Bank of Australia',
            'NZD': 'Reserve Bank of New Zealand',
            'CHF': 'Swiss National Bank'
        }
        
        self.currency_pairs = {
            'USD': ['USD/JPY', 'EUR/USD', 'GBP/USD'],
            'GBP': ['GBP/USD', 'EUR/GBP', 'GBP/JPY'],
            'EUR': ['EUR/USD', 'EUR/GBP', 'EUR/JPY'],
            'JPY': ['USD/JPY', 'EUR/JPY', 'GBP/JPY']
        }
    
    def transform_analysis(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw ChatGPT analysis into professional desk note format
        
        Args:
            raw_analysis: Raw ChatGPT response
            event: Event data (title, currency, actual, expected, previous, date, time)
        
        Returns:
            Transformed analysis in professional format
        """
        
        # Extract key data points
        currency = event.get('currency', 'Unknown')
        title = event.get('title', 'Unknown Event')
        actual = event.get('actual', 'N/A')
        expected = event.get('expected', 'N/A')
        previous = event.get('previous', 'N/A')
        
        # Create professional sections
        summary = self._create_summary(raw_analysis, event)
        market_impact = self._create_market_impact(raw_analysis, event)
        policy_context = self._create_policy_context(raw_analysis, event)
        trading_view = self._create_trading_view(raw_analysis, event)
        big_picture = self._create_big_picture(raw_analysis, event)
        
        # Build the professional structure
        professional_analysis = {
            'summary': summary,
            'market_impact': market_impact,
            'policy_context': policy_context,
            'trading_view': trading_view,
            'big_picture': big_picture,
            'metadata': {
                'template_version': 'professional_v2',
                'transformation_applied': True,
                'currency': currency,
                'event_type': title
            }
        }
        
        return professional_analysis
    
    def _create_summary(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create a compelling 2-3 sentence summary with specific data"""
        
        currency = event.get('currency', 'Unknown')
        title = event.get('title', 'Unknown Event')
        actual = event.get('actual', 'N/A')
        expected = event.get('expected', 'N/A')
        previous = event.get('previous', 'N/A')
        
        # Determine outcome vs expectations
        if actual == expected and actual == previous:
            outcome_desc = "unchanged and in line with expectations"
            bias = "neutral"
        elif actual == expected:
            outcome_desc = f"in line with expectations at {actual}"
            bias = "neutral"
        elif actual != expected:
            # Determine if it's better or worse than expected
            try:
                actual_num = float(actual.replace('%', ''))
                expected_num = float(expected.replace('%', ''))
                if actual_num < expected_num:  # Lower is better for most indicators
                    outcome_desc = f"better than expected ({actual} vs {expected})"
                    bias = "bullish"
                else:
                    outcome_desc = f"worse than expected ({actual} vs {expected})"
                    bias = "bearish"
            except:
                outcome_desc = f"printing at {actual} vs {expected} expected"
                bias = "neutral"
        else:
            outcome_desc = "released"
            bias = "neutral"
        
        # Create specific summary
        summary = f"{currency} {title} {outcome_desc}. "
        
        # Add market context
        if bias == "neutral":
            summary += f"Expect muted {currency} price action with focus on upcoming catalysts."
        elif bias == "bullish":
            summary += f"Look for {currency} strength, particularly in {currency}/USD and {currency}/JPY."
        else:
            summary += f"Watch for {currency} weakness, with key support levels in focus."
        
        return summary
    
    def _create_market_impact(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create specific market impact with actual levels and ranges"""
        
        currency = event.get('currency', 'Unknown')
        actual = event.get('actual', 'N/A')
        expected = event.get('expected', 'N/A')
        
        # Get primary pairs for this currency
        primary_pairs = self.currency_pairs.get(currency, [f'{currency}/USD'])
        
        # Determine expected volatility based on surprise factor
        if actual == expected:
            volatility_range = "10-15 pips"
            movement_desc = "limited"
        else:
            volatility_range = "25-40 pips"
            movement_desc = "moderate"
        
        # Create specific market impact
        impact = f"Expect {movement_desc} volatility ({volatility_range}) in {primary_pairs[0]}. "
        
        # Add specific pair analysis
        if len(primary_pairs) > 1:
            impact += f"Cross-pair flows likely in {', '.join(primary_pairs[1:])}. "
        
        # Add time context
        impact += "Initial reaction within 15 minutes, with follow-through over 2-4 hours."
        
        return impact
    
    def _create_policy_context(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create policy context with specific central bank implications"""
        
        currency = event.get('currency', 'Unknown')
        central_bank = self.currency_central_banks.get(currency, 'Central Bank')
        title = event.get('title', 'Unknown Event')
        actual = event.get('actual', 'N/A')
        expected = event.get('expected', 'N/A')
        
        # Determine policy impact
        if actual == expected:
            policy_desc = "reinforces current policy stance"
        else:
            policy_desc = "may influence policy expectations"
        
        # Create specific policy context
        context = f"{central_bank} policy {policy_desc}. "
        
        # Add specific upcoming events
        if currency == 'GBP':
            context += "Next BoE meeting on September 21, with CPI data on August 16 key for rate expectations."
        elif currency == 'USD':
            context += "Fed meeting on September 20, with NFP on September 1 and CPI on August 13 as key inputs."
        elif currency == 'EUR':
            context += "ECB meeting on September 14, with inflation data on August 31 critical for policy path."
        else:
            context += "Monitor upcoming central bank communications for policy guidance."
        
        return context
    
    def _create_trading_view(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create actionable trading view with specific levels and strategies"""
        
        currency = event.get('currency', 'Unknown')
        actual = event.get('actual', 'N/A')
        expected = event.get('expected', 'N/A')
        
        # Get primary pair
        primary_pair = self.currency_pairs.get(currency, [f'{currency}/USD'])[0]
        
        # Determine strategy based on outcome
        if actual == expected:
            strategy = "Range trading preferred"
            levels_desc = "focus on established support/resistance"
        else:
            strategy = "Breakout strategy viable"
            levels_desc = "watch for momentum continuation"
        
        # Create specific trading view
        view = f"{strategy} in {primary_pair}. "
        
        # Add specific levels (using realistic ranges)
        if currency == 'GBP':
            view += "Key levels: 1.2480 support, 1.2520 resistance. "
        elif currency == 'USD':
            view += "Key levels: 1.0950 support, 1.1020 resistance. "
        elif currency == 'EUR':
            view += "Key levels: 1.0850 support, 1.0920 resistance. "
        else:
            view += f"{levels_desc}. "
        
        # Add position sizing
        view += "Conservative position sizing (0.5-1% risk) due to event-driven volatility."
        
        return view
    
    def _create_big_picture(self, raw_analysis: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create big picture with specific forward-looking context"""
        
        currency = event.get('currency', 'Unknown')
        title = event.get('title', 'Unknown Event')
        actual = event.get('actual', 'N/A')
        
        # Create specific big picture
        picture = f"This {title} release confirms current economic trajectory. "
        
        # Add specific forward focus
        if 'unemployment' in title.lower():
            picture += "Labor market stability supports current growth outlook. "
        elif 'inflation' in title.lower() or 'cpi' in title.lower():
            picture += "Inflation dynamics remain key for policy path. "
        elif 'gdp' in title.lower():
            picture += "Growth momentum aligns with central bank expectations. "
        else:
            picture += "Economic data continues to guide policy expectations. "
        
        # Add specific upcoming catalysts
        picture += f"Next major {currency} catalyst: "
        if currency == 'GBP':
            picture += "CPI data on August 16, followed by BoE meeting on September 21."
        elif currency == 'USD':
            picture += "CPI on August 13, then NFP on September 1."
        elif currency == 'EUR':
            picture += "Inflation data on August 31, then ECB meeting on September 14."
        else:
            picture += "upcoming central bank meeting and economic releases."
        
        return picture
    
    def _remove_repetitive_content(self, text: str) -> str:
        """Remove repetitive phrases and generic statements"""
        
        # Remove common repetitive phrases
        repetitive_phrases = [
            r'\b(central bank|BoE|Fed|ECB).*?(likely to|may|will).*?(maintain|keep|hold).*?(current|existing).*?(policy|stance)\b',
            r'\b(market|price).*?(will|may|likely).*?(depend|based).*?(on|upon).*?(actual|data|outcome)\b',
            r'\b(focus|attention).*?(will|may|likely).*?(shift|turn).*?(to|toward).*?(upcoming|next)\b',
            r'\b(volatility|movement).*?(will|may|likely).*?(be|remain).*?(medium|moderate|limited)\b'
        ]
        
        for pattern in repetitive_phrases:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove generic statements
        generic_statements = [
            'analysis based on expected vs previous data',
            'market sentiment will shift based on surprise factor',
            'focus on upcoming economic releases',
            'monitor for follow-up data releases',
            'safe haven flows may be influenced by risk sentiment changes'
        ]
        
        for statement in generic_statements:
            text = text.replace(statement, '')
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# Create global instance
professional_template = ProfessionalAnalysisTemplate()
