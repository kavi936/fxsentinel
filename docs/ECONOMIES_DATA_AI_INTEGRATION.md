# Economies Data Integration for AI Analysis

**Status**: Planned for Future Implementation  
**Created**: January 2026  
**Purpose**: Document approaches for integrating economies tab data (central bank rates, economic indicators) into GPT AI analysis prompts

---

## Overview

The Economies tab contains valuable economic data that can significantly enhance AI analysis quality:
- **Central Bank Rates**: Current rates with trends (up/down/stable)
- **Economic Indicators**: Current values for CPI, GDP, Unemployment, NFP, etc.
- **Historical Data**: Chart data showing trends over time
- **Policy Context**: Target levels for inflation and other indicators

This document outlines **5 selected approaches** for integrating this data into the AI analysis system.

---

## Selected Approaches

### ✅ Approach 1: Currency-Specific Context Injection (Recommended)

**Priority**: High  
**Complexity**: Low-Medium  
**Impact**: High

#### Description
Detect the event currency (USD, EUR, GBP, JPY) and inject relevant economy data into the prompt. Provides immediate context for the currency being analyzed.

#### Implementation Strategy

```python
# In gpt_ai_analysis.py - _create_analysis_prompt method

def _get_economy_context(self, currency: str) -> Optional[Dict]:
    """Fetch economy context for a currency"""
    # Map currency codes
    currency_map = {
        'USD': 'US',
        'EUR': 'EUR', 
        'GBP': 'GBP',
        'JPY': 'JPY'
    }
    
    country_code = currency_map.get(currency)
    if not country_code:
        return None
    
    # Fetch from economy indicators API or service
    # This will need to be implemented
    economy_data = self._fetch_economy_indicators(country_code)
    
    if not economy_data:
        return None
    
    # Extract relevant indicators
    return {
        'central_bank_rate': economy_data.get('interest-rate', {}).get('currentValue'),
        'rate_trend': self._get_rate_trend(country_code),
        'cpi': economy_data.get('inflation-YoY', {}).get('currentValue'),
        'core_cpi': economy_data.get('core-inflation-YoY', {}).get('currentValue'),
        'gdp_growth': economy_data.get('gdp-growth', {}).get('currentValue'),
        'unemployment': economy_data.get('unemployment', {}).get('currentValue'),
        'nfp': economy_data.get('nonfarm-payrolls', {}).get('currentValue')
    }

def _create_analysis_prompt(self, event: Dict, market_context: MarketContext, analysis_type: str) -> str:
    # ... existing code ...
    
    currency = event.get('currency', 'USD')
    
    # Get economy context
    economy_context = self._get_economy_context(currency)
    
    # Build prompt
    prompt = f"""
Analyze the following economic event and provide comprehensive market analysis:

EVENT DETAILS:
- Title: {event_title}
- Currency: {currency}
- Impact Level: {impact}
- Previous: {previous}
- Expected: {expected}
- Actual: {actual}
- Analysis Type: {analysis_type}
"""
    
    # Add economy context if available
    if economy_context:
        prompt += f"""

ECONOMIC CONTEXT FOR {currency}:
- Central Bank Rate: {economy_context['central_bank_rate']} (Trend: {economy_context['rate_trend']})
- Current CPI: {economy_context['cpi']}
- Current Core CPI: {economy_context['core_cpi']}
- Current GDP Growth: {economy_context['gdp_growth']}
- Current Unemployment: {economy_context['unemployment']}
"""
        if economy_context.get('nfp'):
            prompt += f"- Last NFP: {economy_context['nfp']}\n"
    
    # ... rest of prompt ...
```

#### Use Cases
- **US NFP Release**: Compare actual vs current Unemployment (3.8%)
- **US CPI Release**: Compare actual vs current CPI (3.2%) and Fed target (2.0%)
- **ECB Rate Decision**: Compare with current Main Refinancing Rate (2.15%)
- **UK CPI Release**: Compare with current CPI (3.2%) vs BoE target (2.0%)

#### Benefits
- Provides immediate context for surprise analysis
- Helps assess policy implications
- Improves accuracy of forward scenarios
- Low complexity, high value

---

### ✅ Approach 3: Trend-Based Context

**Priority**: Medium  
**Complexity**: Medium  
**Impact**: Medium-High

#### Description
Use chart data to determine trends (rising/falling/stable) and compare current value vs recent average. Identifies acceleration/deceleration patterns.

#### Implementation Strategy

```python
def _analyze_indicator_trend(self, indicator_data: Dict) -> Optional[Dict]:
    """Analyze trend from chart data"""
    chart_data = indicator_data.get('chartData')
    if not chart_data or len(chart_data) < 3:
        return None
    
    # Get original values (not normalized)
    # Note: May need to fetch original data from API
    values = chart_data  # Assuming these are actual values
    
    # Calculate trend
    recent_avg = sum(values[-3:]) / 3
    older_avg = sum(values[-6:-3]) / 3 if len(values) >= 6 else recent_avg
    
    # Determine trend direction
    if recent_avg > older_avg * 1.02:  # 2% threshold
        trend = 'accelerating'
        direction = 'up'
    elif recent_avg < older_avg * 0.98:
        trend = 'decelerating'
        direction = 'down'
    else:
        trend = 'stable'
        direction = 'stable'
    
    return {
        'trend': trend,
        'direction': direction,
        'current': values[-1] if values else None,
        'recent_avg': recent_avg,
        'older_avg': older_avg,
        'change_pct': ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
    }

def _add_trend_context_to_prompt(self, prompt: str, economy_context: Dict, event_type: str) -> str:
    """Add trend analysis to prompt"""
    trend_info = []
    
    # Analyze relevant indicators based on event type
    if 'employment' in event_type.lower() or 'nfp' in event_type.lower():
        unemployment_trend = self._analyze_indicator_trend(
            economy_context.get('unemployment', {})
        )
        if unemployment_trend:
            trend_info.append(
                f"Unemployment Trend: {unemployment_trend['trend']} "
                f"({unemployment_trend['direction']}) - "
                f"Recent avg: {unemployment_trend['recent_avg']:.2f}%"
            )
    
    elif 'cpi' in event_type.lower() or 'inflation' in event_type.lower():
        cpi_trend = self._analyze_indicator_trend(
            economy_context.get('inflation-YoY', {})
        )
        if cpi_trend:
            trend_info.append(
                f"CPI Trend: {cpi_trend['trend']} ({cpi_trend['direction']}) - "
                f"Recent avg: {cpi_trend['recent_avg']:.2f}%"
            )
    
    if trend_info:
        prompt += "\n\nTREND ANALYSIS:\n" + "\n".join(f"- {info}" for info in trend_info)
    
    return prompt
```

#### Use Cases
- **CPI trending down** → Disinflation → Dovish policy likely
- **Unemployment trending up** → Labor market weakening → Rate cuts likely
- **GDP trending up** → Growth accelerating → Hawkish policy likely

#### Benefits
- Captures momentum, not just absolute levels
- Improves policy prediction accuracy
- Adds forward-looking context
- Helps identify turning points

---

### ✅ Approach 4: Event-Specific Indicator Matching

**Priority**: High  
**Complexity**: Low  
**Impact**: Medium-High

#### Description
Map event types to relevant indicators and only include indicators directly related to the event. Reduces prompt length and improves GPT focus.

#### Implementation Strategy

```python
EVENT_TYPE_MAPPING = {
    'employment': ['unemployment', 'nonfarm-payrolls'],
    'inflation': ['inflation-YoY', 'core-inflation-YoY'],
    'gdp': ['gdp-growth'],
    'interest-rate': ['interest-rate'],
    'unemployment': ['unemployment'],
    'cpi': ['inflation-YoY', 'core-inflation-YoY'],
    'nfp': ['unemployment', 'nonfarm-payrolls'],
    'adp': ['unemployment', 'nonfarm-payrolls'],
    'payrolls': ['unemployment', 'nonfarm-payrolls']
}

def _get_relevant_indicators(self, event_title: str, currency: str) -> List[str]:
    """Get only indicators relevant to this event"""
    event_lower = event_title.lower()
    relevant_ids = []
    
    # Check for event type matches
    for event_type, indicator_ids in EVENT_TYPE_MAPPING.items():
        if event_type in event_lower:
            relevant_ids.extend(indicator_ids)
    
    # Remove duplicates
    relevant_ids = list(set(relevant_ids))
    
    # Always include interest rate for policy context
    if 'interest-rate' not in relevant_ids:
        relevant_ids.append('interest-rate')
    
    return relevant_ids

def _get_indicators_by_ids(self, currency: str, indicator_ids: List[str]) -> Dict:
    """Fetch specific indicators by their IDs"""
    economy_data = self._fetch_economy_indicators(currency)
    if not economy_data:
        return {}
    
    relevant_indicators = {}
    for indicator_id in indicator_ids:
        if indicator_id in economy_data:
            relevant_indicators[indicator_id] = economy_data[indicator_id]
    
    return relevant_indicators

# Usage in prompt creation
def _create_analysis_prompt(self, event: Dict, market_context: MarketContext, analysis_type: str) -> str:
    # ... existing code ...
    
    currency = event.get('currency', 'USD')
    event_title = event.get('title', '')
    
    # Get only relevant indicators
    relevant_indicator_ids = self._get_relevant_indicators(event_title, currency)
    relevant_indicators = self._get_indicators_by_ids(currency, relevant_indicator_ids)
    
    # Build context from relevant indicators only
    if relevant_indicators:
        prompt += "\n\nRELEVANT ECONOMIC INDICATORS:\n"
        for indicator_id, indicator_data in relevant_indicators.items():
            title = indicator_data.get('title', indicator_id)
            current_value = indicator_data.get('currentValue', 'N/A')
            prompt += f"- {title}: {current_value}\n"
```

#### Use Cases
- **US ADP Employment**: Include Unemployment (3.8%) and last NFP (119K) only
- **US CPI**: Include CPI (3.2%) and Core CPI (3.0%) only
- **UK GDP**: Include GDP Growth (+1.5%) only
- **ECB Rate Decision**: Include Main Refinancing Rate (2.15%) only

#### Benefits
- Reduces prompt length (saves tokens/cost)
- Focuses GPT on relevant data
- Improves analysis quality
- Faster processing

---

### ✅ Approach 5: Historical Comparison Context

**Priority**: Medium  
**Complexity**: Medium  
**Impact**: Medium

#### Description
Compare current value with chart data (last 3-6 months) to calculate percent change and identify if current value is high/low relative to recent range.

#### Implementation Strategy

```python
def _get_historical_context(self, indicator_data: Dict) -> Optional[Dict]:
    """Get historical context for indicator"""
    chart_data = indicator_data.get('chartData')
    if not chart_data or len(chart_data) < 3:
        return None
    
    # Parse current value (handle formats like "3.2%", "+2.1%", "119K")
    current_str = indicator_data.get('currentValue', '')
    try:
        current = float(current_str.replace('%', '').replace('+', '').replace(',', ''))
    except (ValueError, AttributeError):
        return None
    
    # Calculate statistics from chart data
    values = chart_data
    recent_max = max(values[-6:]) if len(values) >= 6 else max(values)
    recent_min = min(values[-6:]) if len(values) >= 6 else min(values)
    recent_avg = sum(values[-6:]) / len(values[-6:]) if len(values) >= 6 else sum(values) / len(values)
    
    # Determine position relative to recent range
    if current > recent_avg * 1.05:
        position = 'above average'
        significance = 'high' if current > recent_max * 0.95 else 'moderate'
    elif current < recent_avg * 0.95:
        position = 'below average'
        significance = 'high' if current < recent_min * 1.05 else 'moderate'
    else:
        position = 'near average'
        significance = 'low'
    
    # Calculate percent from average
    percent_from_avg = ((current - recent_avg) / recent_avg) * 100 if recent_avg > 0 else 0
    
    return {
        'current': current,
        'recent_avg': recent_avg,
        'recent_max': recent_max,
        'recent_min': recent_min,
        'position': position,
        'significance': significance,
        'percent_from_avg': percent_from_avg,
        'range': f"{recent_min:.2f} - {recent_max:.2f}"
    }

def _add_historical_context_to_prompt(self, prompt: str, indicator_data: Dict, indicator_name: str) -> str:
    """Add historical comparison to prompt"""
    historical = self._get_historical_context(indicator_data)
    
    if not historical:
        return prompt
    
    prompt += f"""
    
HISTORICAL CONTEXT FOR {indicator_name}:
- Current: {historical['current']}
- Recent Average (6 months): {historical['recent_avg']:.2f}
- Recent Range: {historical['range']}
- Position: {historical['position']} ({historical['percent_from_avg']:+.1f}% from average)
- Significance: {historical['significance']}
"""
    
    return prompt
```

#### Use Cases
- **CPI at 3.2%** vs recent average 3.5% → Disinflation trend
- **Unemployment at 3.8%** vs recent average 3.6% → Slight deterioration
- **GDP at +2.1%** vs recent average +1.8% → Acceleration

#### Benefits
- Provides relative context (not just absolute)
- Highlights deviations from norm
- Improves surprise assessment
- Identifies outliers

---

### ✅ Approach 6: Policy Target Comparison

**Priority**: High  
**Complexity**: Low-Medium  
**Impact**: High

#### Description
Compare current values with central bank targets, calculate deviation, and assess policy pressure. Directly links data to policy expectations.

#### Implementation Strategy

```python
POLICY_TARGETS = {
    'USD': {
        'inflation': 2.0,  # Fed target
        'unemployment': 4.0,  # Fed's "natural rate" estimate
        'central_bank': 'Federal Reserve'
    },
    'EUR': {
        'inflation': 2.0,  # ECB target
        'unemployment': None,  # ECB doesn't have explicit target
        'central_bank': 'European Central Bank'
    },
    'GBP': {
        'inflation': 2.0,  # BoE target
        'unemployment': None,  # BoE doesn't have explicit target
        'central_bank': 'Bank of England'
    },
    'JPY': {
        'inflation': 2.0,  # BoJ target
        'unemployment': None,  # BoJ doesn't have explicit target
        'central_bank': 'Bank of Japan'
    }
}

def _get_policy_pressure(self, currency: str, indicator_type: str, current_value: float) -> Optional[Dict]:
    """Calculate policy pressure based on target deviation"""
    targets = POLICY_TARGETS.get(currency, {})
    target = targets.get(indicator_type)
    
    if not target:
        return None
    
    deviation = current_value - target
    central_bank = targets.get('central_bank', f'{currency} Central Bank')
    
    # Determine policy pressure based on indicator type
    if indicator_type == 'inflation':
        if deviation > 1.0:
            pressure = 'strong hawkish pressure'
            pressure_level = 'high'
        elif deviation > 0.5:
            pressure = 'moderate hawkish pressure'
            pressure_level = 'medium'
        elif deviation < -0.5:
            pressure = 'moderate dovish pressure'
            pressure_level = 'medium'
        elif deviation < -1.0:
            pressure = 'strong dovish pressure'
            pressure_level = 'high'
        else:
            pressure = 'near target'
            pressure_level = 'low'
    
    elif indicator_type == 'unemployment':
        # Lower unemployment = tighter labor market = hawkish pressure
        if deviation < -0.5:
            pressure = 'strong hawkish pressure (tight labor market)'
            pressure_level = 'high'
        elif deviation < -0.2:
            pressure = 'moderate hawkish pressure'
            pressure_level = 'medium'
        elif deviation > 0.5:
            pressure = 'moderate dovish pressure (slack in labor market)'
            pressure_level = 'medium'
        elif deviation > 1.0:
            pressure = 'strong dovish pressure'
            pressure_level = 'high'
        else:
            pressure = 'near target'
            pressure_level = 'low'
    
    return {
        'target': target,
        'current': current_value,
        'deviation': deviation,
        'deviation_pct': (deviation / target * 100) if target > 0 else 0,
        'pressure': pressure,
        'pressure_level': pressure_level,
        'central_bank': central_bank
    }

def _add_policy_context_to_prompt(self, prompt: str, currency: str, economy_context: Dict, event_type: str) -> str:
    """Add policy target comparison to prompt"""
    policy_info = []
    
    # Check inflation if relevant
    if 'cpi' in event_type.lower() or 'inflation' in event_type.lower():
        cpi_str = economy_context.get('cpi', '')
        try:
            cpi_value = float(cpi_str.replace('%', ''))
            policy_pressure = self._get_policy_pressure(currency, 'inflation', cpi_value)
            if policy_pressure:
                policy_info.append(
                    f"Inflation Policy Pressure: {policy_pressure['pressure']}\n"
                    f"  - Current: {policy_pressure['current']:.2f}%\n"
                    f"  - Target: {policy_pressure['target']:.2f}%\n"
                    f"  - Deviation: {policy_pressure['deviation']:+.2f}pp ({policy_pressure['deviation_pct']:+.1f}%)"
                )
        except (ValueError, AttributeError):
            pass
    
    # Check unemployment if relevant
    if 'employment' in event_type.lower() or 'unemployment' in event_type.lower() or 'nfp' in event_type.lower():
        unemployment_str = economy_context.get('unemployment', '')
        try:
            unemployment_value = float(unemployment_str.replace('%', ''))
            policy_pressure = self._get_policy_pressure(currency, 'unemployment', unemployment_value)
            if policy_pressure:
                policy_info.append(
                    f"Unemployment Policy Pressure: {policy_pressure['pressure']}\n"
                    f"  - Current: {policy_pressure['current']:.2f}%\n"
                    f"  - Target: {policy_pressure['target']:.2f}%\n"
                    f"  - Deviation: {policy_pressure['deviation']:+.2f}pp"
                )
        except (ValueError, AttributeError):
            pass
    
    if policy_info:
        prompt += "\n\nPOLICY TARGET ANALYSIS:\n"
        for info in policy_info:
            prompt += f"{info}\n"
    
    return prompt
```

#### Use Cases
- **US CPI at 3.2%** vs 2.0% target → +1.2pp above target → Hawkish pressure
- **US Unemployment at 3.8%** vs 4.0% target → -0.2pp below target → Tight labor market
- **EUR HICP at 2.4%** vs 2.0% target → +0.4pp above target → Moderate hawkish pressure

#### Benefits
- Directly links to policy expectations
- Quantifies policy pressure
- Improves rate prediction accuracy
- Clear, actionable insights

---

## Implementation Phases

### Phase 1: Basic Integration (High Priority)
**Timeline**: After easier data integration  
**Approaches**: 1, 4, 6

1. **Create Economy Context Service**
   - Similar to `live_market_data_service`
   - Fetches from `/api/economy-indicators/<country_code>` or static data
   - Handles caching and fallbacks

2. **Implement Approach 1** (Currency-Specific Context)
   - Add `_get_economy_context()` method
   - Inject into prompt

3. **Implement Approach 4** (Event-Specific Matching)
   - Create event type mapping
   - Filter indicators by relevance

4. **Implement Approach 6** (Policy Target Comparison)
   - Add policy target constants
   - Calculate deviations and pressure

### Phase 2: Enhanced Context (Medium Priority)
**Timeline**: After Phase 1  
**Approaches**: 3, 5

1. **Implement Approach 3** (Trend Analysis)
   - Analyze chart data for trends
   - Calculate acceleration/deceleration

2. **Implement Approach 5** (Historical Comparison)
   - Compare current vs recent averages
   - Identify position in range

---

## Data Structure Requirements

### Economy Context Service Interface

```python
class EconomyContextService:
    def get_economy_context(self, currency: str) -> Optional[Dict]:
        """
        Returns:
        {
            'currency': 'USD',
            'central_bank_rate': {
                'value': 3.75,
                'trend': 'down',
                'bank_name': 'Fed'
            },
            'indicators': {
                'interest-rate': {
                    'id': 'interest-rate',
                    'title': 'Federal Funds Rate',
                    'currentValue': '4.25%',
                    'chartData': [85, 78, 82, 88, 92, 89, 87, 90],
                    'description': '...'
                },
                'inflation-YoY': {
                    'id': 'inflation-YoY',
                    'title': 'Inflation YoY (CPI)',
                    'currentValue': '3.2%',
                    'chartData': [45, 52, 48, 41, 38, 42, 39, 35],
                    'description': '...'
                },
                # ... other indicators
            }
        }
        """
```

### Data Sources
1. **Primary**: `/api/economy-indicators/<country_code>` endpoint
2. **Fallback**: Static JSON file (`economyIndicators.json`)
3. **Future**: Google Sheets API (already partially implemented)

---

## Example: Enhanced Prompt Output

### Before (Current)
```
EVENT DETAILS:
- Title: US CPI YoY
- Currency: USD
- Expected: 3.0%
- Actual: 3.2%
```

### After (With All Approaches)
```
EVENT DETAILS:
- Title: US CPI YoY
- Currency: USD
- Expected: 3.0%
- Actual: 3.2%

ECONOMIC CONTEXT FOR USD:
- Central Bank Rate: 3.75% (Trend: down)
- Current CPI: 3.2%
- Current Core CPI: 3.0%
- Current GDP Growth: +2.1%
- Current Unemployment: 3.8%
- Last NFP: 119K

RELEVANT ECONOMIC INDICATORS:
- Inflation YoY (CPI): 3.2%
- Core Inflation YoY: 3.0%
- Federal Funds Rate: 4.25%

POLICY TARGET ANALYSIS:
Inflation Policy Pressure: moderate hawkish pressure
  - Current: 3.20%
  - Target: 2.00%
  - Deviation: +1.20pp (+60.0%)

TREND ANALYSIS:
- CPI Trend: stable (stable) - Recent avg: 3.25%

HISTORICAL CONTEXT FOR Inflation YoY (CPI):
- Current: 3.2
- Recent Average (6 months): 3.25
- Recent Range: 3.00 - 3.50
- Position: near average (-1.5% from average)
- Significance: low
```

---

## Next Steps

1. **Complete easier data integration first** (trading sessions, VIX, risk appetite)
2. **Create Economy Context Service** in backend
3. **Move economy data to backend** (currently in frontend)
4. **Implement Phase 1 approaches** (1, 4, 6)
5. **Test and refine** prompt enhancements
6. **Implement Phase 2 approaches** (3, 5)
7. **Monitor GPT response quality** and adjust

---

## Notes

- **Approach 2 (Comparative Analysis)** was explicitly excluded - focus on single currency analysis
- All approaches should be **optional** - gracefully handle missing data
- **Cache economy data** to reduce API calls
- **Update frequency**: Economy data changes monthly/quarterly, so caching is safe
- **Error handling**: Always provide fallback if economy data unavailable

---

## Related Files

- `backend/services/gpt_ai_analysis.py` - Main AI analysis service
- `backend/app.py` - API endpoints
- `backend/services/google_sheets_service.py` - Economy data source
- `src/components/Economies.jsx` - Frontend economies tab
- `src/data/economyIndicators.json` - Static fallback data

---

**Last Updated**: January 2026

