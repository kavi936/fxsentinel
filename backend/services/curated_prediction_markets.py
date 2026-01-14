"""
Curated list of important prediction markets for forex traders
These are high-value markets that provide actionable trading signals
"""

CURATED_MARKETS = [
    # Federal Reserve / FOMC
    {
        "keywords": ["fed", "federal reserve", "fomc", "interest rate", "rate cut", "rate hike"],
        "priority": 1,
        "description": "Fed rate decisions and FOMC meetings",
        "affected_pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"]
    },
    
    # CPI / Inflation
    {
        "keywords": ["cpi", "consumer price index", "inflation", "ppi"],
        "priority": 1,
        "description": "Inflation data releases",
        "affected_pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"]
    },
    
    # GDP
    {
        "keywords": ["gdp", "gross domestic product"],
        "priority": 2,
        "description": "GDP releases",
        "affected_pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"]
    },
    
    # Employment / NFP
    {
        "keywords": ["nfp", "non-farm payrolls", "employment", "jobs report", "unemployment"],
        "priority": 1,
        "description": "Employment data releases",
        "affected_pairs": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD", "NZD/USD", "USD/CAD"]
    },
    
    # ECB
    {
        "keywords": ["ecb", "european central bank", "lagarde"],
        "priority": 1,
        "description": "ECB policy decisions",
        "affected_pairs": ["EUR/USD", "EUR/GBP", "EUR/JPY", "EUR/CHF"]
    },
    
    # Bank of England
    {
        "keywords": ["boe", "bank of england", "bailey", "andrew bailey"],
        "priority": 1,
        "description": "BOE policy decisions",
        "affected_pairs": ["GBP/USD", "EUR/GBP", "GBP/JPY", "GBP/CHF"]
    },
    
    # Bank of Japan
    {
        "keywords": ["boj", "bank of japan", "ueda", "kazuo ueda"],
        "priority": 1,
        "description": "BOJ policy decisions",
        "affected_pairs": ["USD/JPY", "EUR/JPY", "GBP/JPY", "AUD/JPY"]
    },
    
    # Political Events (High Impact)
    {
        "keywords": ["trump", "biden", "election", "presidential"],
        "priority": 2,
        "description": "Major political events",
        "affected_pairs": ["EUR/USD", "GBP/USD", "USD/JPY"]
    },
    
    # Gold / Commodities
    {
        "keywords": ["gold", "xau", "commodity"],
        "priority": 3,
        "description": "Gold and commodity markets",
        "affected_pairs": ["XAU/USD"]
    }
]

def get_curated_keywords():
    """Get all keywords from curated markets"""
    keywords = []
    for market in CURATED_MARKETS:
        keywords.extend(market["keywords"])
    return keywords

def get_market_priority(keywords_matched):
    """Get priority score for a market based on matched keywords"""
    priority = 0
    for market in CURATED_MARKETS:
        if any(kw in keywords_matched for kw in market["keywords"]):
            priority = max(priority, market["priority"])
    return priority

def get_affected_pairs_for_keywords(keywords_matched):
    """Get affected currency pairs for matched keywords"""
    pairs = set()
    for market in CURATED_MARKETS:
        if any(kw in keywords_matched for kw in market["keywords"]):
            pairs.update(market["affected_pairs"])
    return list(pairs)

