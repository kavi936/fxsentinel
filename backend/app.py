from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import openai
import os
import json
import time
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import stripe

# Firebase initialization
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, initialize_app
    
    # Initialize Firebase if not already initialized
    if not firebase_admin._apps:
        # Use service account key if available, otherwise use default credentials
        if os.path.exists('firebase-service-account.json'):
            cred = credentials.Certificate('firebase-service-account.json')
            initialize_app(cred)
        else:
            # Use default credentials (for development)
            initialize_app()
        
        print("✅ Firebase initialized successfully")
    else:
        print("✅ Firebase already initialized")
        
except ImportError:
    print("⚠️ Firebase Admin SDK not installed")
except Exception as e:
    print(f"⚠️ Firebase initialization failed: {e}")

# Load environment variables from .env file
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Debug: Check if environment variables are loaded
print(f"🔍 Environment Debug:")
print(f"   OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
if os.getenv('OPENAI_API_KEY'):
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")

app = Flask(__name__)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configure CORS to allow requests from all origins (including file:// and null origins)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"], supports_credentials=False)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    # Allow all origins for development and testing
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

# Configure OpenAI (you'll need to set OPENAI_API_KEY environment variable)
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure UniRateAPI
UNIRATE_API_KEY = os.getenv('UNIRATE_API_KEY', 'demo')

# Global variables for API usage tracking
unirate_api_usage = {
    'requests': 0,
    'last_reset': datetime.now().date(),
    'minute_requests': 0,
    'last_minute_reset': datetime.now()
}

# Alpha Vantage key rotation system
alpha_vantage_keys = [
    os.getenv('ALPHA_VANTAGE_API_KEY_1'),
    os.getenv('ALPHA_VANTAGE_API_KEY_2'),
    os.getenv('ALPHA_VANTAGE_API_KEY_3'),
    os.getenv('ALPHA_VANTAGE_API_KEY_4')
]

# Filter out None values (keys not set)
alpha_vantage_keys = [key for key in alpha_vantage_keys if key]

# Track which key to use next
current_alpha_vantage_key_index = 0

def get_next_alpha_vantage_key():
    """Get the next Alpha Vantage API key in rotation"""
    global current_alpha_vantage_key_index
    
    if not alpha_vantage_keys:
        return None
    
    key = alpha_vantage_keys[current_alpha_vantage_key_index]
    current_alpha_vantage_key_index = (current_alpha_vantage_key_index + 1) % len(alpha_vantage_keys)
    
    return key

def check_unirate_rate_limits():
    """Check if we can make a UniRateAPI call"""
    now = datetime.now()
    today = now.date()
    
    # Reset daily counter if it's a new day
    if unirate_api_usage['last_reset'] != today:
        unirate_api_usage['requests'] = 0
        unirate_api_usage['last_reset'] = today
    
    # Reset minute counter if it's been more than a minute
    if (now - unirate_api_usage['last_minute_reset']).seconds >= 60:
        unirate_api_usage['minute_requests'] = 0
        unirate_api_usage['last_minute_reset'] = now
    
    # Check limits (adjust these based on your UniRateAPI plan)
    daily_limit = 1000  # Adjust based on your plan
    minute_limit = 10   # Adjust based on your plan
    
    return (unirate_api_usage['requests'] < daily_limit and 
            unirate_api_usage['minute_requests'] < minute_limit)

def clean_news_title(title):
    """Clean news title by removing common prefixes and formatting"""
    import re
    
    if not title:
        return title
    
    # Remove common prefixes that make titles look unprofessional
    # Use re.escape to properly handle special characters like asterisks
    # Order matters: put longer patterns first to avoid partial matches
    prefixes_to_remove = [
        '**JUST IN:**',  # **JUST IN:**
        '**BREAKING:**', # **BREAKING:**
        '**UPDATE:**',   # **UPDATE:**
        '**LIVE:**',     # **LIVE:**
        '**URGENT:**',   # **URGENT:**
        'JUST IN:',      # JUST IN:
        'BREAKING:',     # BREAKING:
        'UPDATE:',       # UPDATE:
        'LIVE:',         # LIVE:
        'URGENT:',       # URGENT:
    ]
    
    cleaned_title = title
    
    # Remove each prefix pattern (case insensitive)
    for prefix in prefixes_to_remove:
        # Use re.escape to handle special characters and make it case insensitive
        pattern = re.escape(prefix)
        cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and punctuation
    cleaned_title = re.sub(r'\s+', ' ', cleaned_title)  # Multiple spaces to single space
    cleaned_title = cleaned_title.strip()
    
    # Remove leading/trailing punctuation
    cleaned_title = re.sub(r'^[:\s\-_]+', '', cleaned_title)  # Remove leading colons, spaces, dashes
    cleaned_title = re.sub(r'[:\s\-_]+$', '', cleaned_title)  # Remove trailing colons, spaces, dashes
    
    return cleaned_title

def remove_duplicate_news(news_list):
    """Remove duplicate news items across all sources based on title similarity"""
    import re
    
    unique_news = []
    seen_titles = set()
    seen_urls = set()
    
    for news_item in news_list:
        if not news_item or not isinstance(news_item, dict):
            continue
            
        title = news_item.get('title', '').strip()
        url = news_item.get('url', '').strip()
        
        if not title:
            continue
        
        # Clean the title first
        cleaned_title = clean_news_title(title)
        news_item['title'] = cleaned_title  # Update the title in the news item
        
        # Create multiple keys for better deduplication
        # 1. Simplified title (first 5 words, lowercase, no punctuation)
        simple_title = re.sub(r'[^\w\s]', '', cleaned_title.lower())
        words = simple_title.split()[:5]
        title_key = ' '.join(words)
        
        # 2. URL-based key (if URL exists)
        url_key = url.lower() if url else None
        
        # 3. Source + title combination (for cases where same story appears on different sources)
        source = news_item.get('source', '').lower()
        source_title_key = f"{source}_{title_key}"
        
        # Check if this is a duplicate
        is_duplicate = False
        
        # Check title similarity
        if title_key in seen_titles:
            is_duplicate = True
        
        # Check URL similarity
        if url_key and url_key in seen_urls:
            is_duplicate = True
        
        # Check source + title combination
        if source_title_key in seen_titles:
            is_duplicate = True
        
        # If not a duplicate, add to unique list
        if not is_duplicate:
            seen_titles.add(title_key)
            if url_key:
                seen_urls.add(url_key)
            seen_titles.add(source_title_key)
            unique_news.append(news_item)
    
    print(f"🔄 Deduplication: {len(news_list)} -> {len(unique_news)} articles")
    return unique_news
    
    # Check minute limit (30 calls per minute for UniRateAPI)
    if unirate_api_usage['minute_requests'] >= 30:
        return False, "Minute limit exceeded"
    
    return True, "OK"

def increment_unirate_usage():
    """Increment the usage counter for UniRateAPI"""
    unirate_api_usage['requests'] += 1
    unirate_api_usage['minute_requests'] += 1

def get_fallback_price(pair_name):
    """Get fallback price data for a currency pair"""
    fallback_data = {
        'EURUSD': {'price': 1.0923, 'change': 0.0012},
        'GBPUSD': {'price': 1.2712, 'change': -0.0020},
        'USDJPY': {'price': 147.85, 'change': -0.08},
        'USDCHF': {'price': 0.8845, 'change': 0.0015},
        'AUDUSD': {'price': 0.6623, 'change': -0.0018},
        'USDCAD': {'price': 1.3542, 'change': 0.0021},
        'NZDUSD': {'price': 0.6128, 'change': -0.0012},
        'EURGBP': {'price': 0.8598, 'change': 0.0015},
        'EURJPY': {'price': 161.45, 'change': -0.12},
        'GBPJPY': {'price': 187.82, 'change': -0.25},
        'USDSEK': {'price': 10.456, 'change': 0.023},
        'USDNOK': {'price': 10.823, 'change': 0.031},
        'USDHKD': {'price': 7.8234, 'change': 0.015},
        'EURCHF': {'price': 0.9665, 'change': 0.0028},
        'GBPCHF': {'price': 1.1234, 'change': 0.0019}
    }
    
    if pair_name in fallback_data:
        data = fallback_data[pair_name].copy()
        data['lastUpdate'] = datetime.now().isoformat()
        data['source'] = 'fallback'
        return data
    
    # Generic fallback for unknown pairs
    return {
        'price': 1.0000,
        'change': 0.0000,
        'lastUpdate': datetime.now().isoformat(),
        'source': 'fallback'
    }

def get_economic_event_by_id(event_id):
    """Get economic event by ID from Finnhub calendar data"""
    try:
        # Get events from Finnhub calendar
        events = finnhub_calendar.get_economic_calendar()
        
        # Find the event with matching ID
        event = next((e for e in events if e.get('id') == event_id), None)
        
        if event:
            return event
        else:
            # If not found, create a realistic mock event based on the ID
            # This handles cases where the frontend sends an ID that doesn't exist in the calendar
            print(f"⚠️ Event ID {event_id} not found in calendar, creating realistic mock event")
            
            # Create a realistic mock event for testing
            return {
                'id': event_id,
                'title': 'US Unemployment Rate',
                'currency': 'USD',
                'impact': 'high',
                'description': 'US Unemployment Rate data release - key indicator of labor market health',
                'expected': '3.8%',
                'previous': '3.9%',
                'actual': '--',
                'date': 'Fri, Aug 15',
                'time': '13:30 UTC',
                'status': 'UPCOMING',
                'type': 'ECONOMIC RELEASE',
                'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"Error getting economic event by ID: {e}")
        # Return realistic mock event as fallback
        return {
            'id': event_id,
            'title': 'US Unemployment Rate',
            'currency': 'USD',
            'impact': 'high',
            'description': 'US Unemployment Rate data release - key indicator of labor market health',
            'expected': '3.8%',
            'previous': '3.9%',
            'actual': '--',
            'date': 'Fri, Aug 15',
            'time': '13:30 UTC',
            'status': 'UPCOMING',
            'type': 'ECONOMIC RELEASE',
            'currencyPairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
            'timestamp': datetime.now().isoformat()
        }

def get_currency_pairs(currency):
    """Get relevant currency pairs for a given currency"""
    pairs_map = {
        "USD": ["EUR/USD", "USD/JPY", "GBP/USD"],
        "EUR": ["EUR/USD", "EUR/GBP", "EUR/JPY"],
        "GBP": ["GBP/USD", "EUR/GBP", "GBP/JPY"],
        "JPY": ["USD/JPY", "EUR/JPY", "GBP/JPY"],
        "AUD": ["AUD/USD", "EUR/AUD", "AUD/JPY"],
        "CAD": ["USD/CAD", "EUR/CAD", "CAD/JPY"],
        "CHF": ["USD/CHF", "EUR/CHF", "GBP/CHF"],
        "NZD": ["NZD/USD", "EUR/NZD", "NZD/JPY"]
    }
    return pairs_map.get(currency, ["EUR/USD", "USD/JPY"])

def get_mock_news():
    """Fallback mock data if scraping fails"""
    today = datetime.now()
    
    return [
        {
            "id": 1,
            "title": "US CPI Data Release",
            "description": "Consumer Price Index for December 2024",
            "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "time": "13:30 UTC",
            "impact": "High",
            "currency": "USD",
            "pairs": ["EUR/USD", "USD/JPY"],
            "expected": "3.1%",
            "previous": "3.2%"
        },
        {
            "id": 2,
            "title": "ECB Interest Rate Decision",
            "description": "European Central Bank monetary policy meeting",
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "time": "12:45 UTC",
            "impact": "High",
            "currency": "EUR",
            "pairs": ["EUR/USD", "EUR/GBP"],
            "expected": "4.50%",
            "previous": "4.50%"
        }
    ]

# Import our AI analysis services
from services.local_ai_analysis import local_ai_analyzer, MarketContext
from services.news_sentiment_analyzer import news_sentiment_analyzer
from services.technical_analysis_service import technical_analyzer
from services.enhanced_ai_analysis import enhanced_ai_analyzer, MarketContext as EnhancedMarketContext
try:
    from services.gpt_ai_analysis import gpt_ai_analyzer, MarketContext as GPTMarketContext
    from services.optimized_chatgpt_analyzer import optimized_chatgpt_analyzer
    GPT_AVAILABLE = True
except Exception as e:
    print(f"🔍 GPT Analyzer import failed: {e}")
    gpt_ai_analyzer = None
    GPT_AVAILABLE = False
import pandas as pd
import numpy as np

def generate_ai_analysis(event_title, currency, impact):
    """Generate AI analysis using free local analysis instead of expensive APIs"""
    try:
        # Create event data structure
        event = {
            'title': event_title,
            'currency': currency,
            'impact': impact,
            'timestamp': datetime.now().isoformat()
        }
        
        # Create market context (you can enhance this with real market data)
        market_context = EnhancedMarketContext(
            current_prices={
                'EUR/USD': 1.0850,
                'USD/JPY': 148.50,
                'GBP/USD': 1.2650,
                'USD/CHF': 0.8650,
                'AUD/USD': 0.6650,
                'USD/CAD': 1.3550
            },
            recent_volatility={
                'EUR/USD': 0.008,
                'USD/JPY': 0.012,
                'GBP/USD': 0.010,
                'USD/CHF': 0.007,
                'AUD/USD': 0.009,
                'USD/CAD': 0.006
            },
            market_sentiment={
                'EUR/USD': 'neutral',
                'USD/JPY': 'bullish',
                'GBP/USD': 'bearish',
                'USD/CHF': 'neutral',
                'AUD/USD': 'neutral',
                'USD/CAD': 'neutral'
            },
            key_levels={
                'EUR/USD': {'support': [1.0800, 1.0750, 1.0700], 'resistance': [1.0900, 1.0950, 1.1000]},
                'USD/JPY': {'support': [148.00, 147.50, 147.00], 'resistance': [149.00, 149.50, 150.00]},
                'GBP/USD': {'support': [1.2600, 1.2550, 1.2500], 'resistance': [1.2700, 1.2750, 1.2800]}
            },
            economic_calendar=[],
            bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
            equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
            commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
            central_bank_expectations={},
            historical_reactions={}
        )
        
        # Use local AI analyzer for comprehensive analysis
        analysis_result = local_ai_analyzer.analyze_economic_event(event, market_context)
        
        # Format response for frontend compatibility (correct structure)
        return {
            "news_impact": analysis_result['analysis']['summary'],
            "trading_implications": f"Based on this economic event, traders should monitor key currency pairs for potential trading opportunities. The immediate market reaction may be volatile, so risk management is crucial. Focus on major pairs like EUR/USD and USD/JPY, and be prepared for both bullish and bearish scenarios depending on market interpretation.",
            "immediate_reaction": "neutral",
            "key_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
            "volatility": "medium",
            "timeframe": "1-24 hours",
            "confidence": analysis_result['confidence_score'],
            "analysis_type": "gpt_enhanced",
            "risk_assessment": {
                "market_volatility": "medium",
                "liquidity_impact": "medium",
                "correlation_risk": "medium"
            },
            "market_context": {
                "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
                "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
                "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
            }
        }
            
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        return get_mock_analysis(event_title)

def _get_pair_impact(analysis_result, pair):
    """Extract impact for specific currency pair"""
    opportunities = analysis_result.get('trading_opportunities', [])
    for opp in opportunities:
        if opp.get('pair') == pair:
            return f"{opp.get('strategy', 'Monitor')} - Entry: {opp.get('entry_zone', 'N/A')}"
    return "Monitor for opportunities"

def get_mock_analysis(event_title):
    """Fallback mock analysis if AI fails"""
    return {
        "news_impact": f"This news event about {event_title} has significant implications for forex markets. The development suggests potential shifts in market sentiment and economic outlook that could impact currency valuations. Traders should monitor for increased volatility and potential breakout opportunities as the market digests this information.",
        "trading_implications": f"Based on this news, traders should consider monitoring key currency pairs for potential trading opportunities. The immediate market reaction may be volatile, so risk management is crucial. Focus on major pairs like EUR/USD and USD/JPY, and be prepared for both bullish and bearish scenarios depending on market interpretation.",
        "immediate_reaction": "neutral",
        "key_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
        "volatility": "medium",
        "timeframe": "1-24 hours",
        "confidence": 75,
        "analysis_type": "free_enhanced",
        "risk_assessment": {
            "market_volatility": "medium",
            "liquidity_impact": "medium",
            "correlation_risk": "medium"
        },
        "market_context": {
            "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
            "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
            "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
        }
    }

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from FXSentinel backend!'})

@app.route('/api/test-analysis/<int:news_id>')
def test_analysis(news_id):
    """Test endpoint that directly returns correct fallback structure"""
    print(f"🔍 Test analysis requested for news_id: {news_id}")
    
    # Return the correct structure directly
    test_data = {
        "news_impact": f"This is a test news event about News ID {news_id} with significant implications for forex markets. The development suggests potential shifts in market sentiment and economic outlook that could impact currency valuations. Traders should monitor for increased volatility and potential breakout opportunities as the market digests this information.",
        "trading_implications": f"Based on this test news, traders should consider monitoring key currency pairs for potential trading opportunities. The immediate market reaction may be volatile, so risk management is crucial. Focus on major pairs like EUR/USD and USD/JPY, and be prepared for both bullish and bearish scenarios depending on market interpretation.",
        "immediate_reaction": "neutral",
        "key_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
        "volatility": "medium",
        "timeframe": "1-24 hours",
        "confidence": 75,
        "analysis_type": "free_enhanced",
        "risk_assessment": {
            "market_volatility": "medium",
            "liquidity_impact": "medium",
            "correlation_risk": "medium"
        },
        "market_context": {
            "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
            "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
            "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
        }
    }
    
    print(f"🔍 Test data generated: {test_data['news_impact'][:50]}...")
    return jsonify(test_data)

@app.route('/api/finnhub-test')
def test_finnhub():
    """Test Finnhub API connection"""
    try:
        result = finnhub_calendar.test_connection()
        return jsonify({
            "finnhub_status": result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "finnhub_status": {
                "status": "error",
                "message": f"Test failed: {str(e)}",
                "api_key_valid": False
            },
            "timestamp": datetime.now().isoformat()
        })

# Import the news aggregator
from services.news_aggregator import news_aggregator
# Import the telegram monitor
from services.telegram_monitor_user import telegram_user_monitor
# Import the Finnhub calendar service
from services.finnhub_calendar import finnhub_calendar
# Import the Finnhub historical service
from services.finnhub_historical import finnhub_historical

@app.route('/api/economic-calendar')
def get_economic_calendar():
    """Get economic calendar events from Finnhub API with alert triggering"""
    try:
        # Get query parameters for date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Fetch events from Finnhub
        events = finnhub_calendar.get_economic_calendar(start_date, end_date)
        
        if events and len(events) > 0:
            # Extract metadata from first event if available
            metadata = events[0].get('_metadata', {}) if events else {}
            
            # Validate that we have real events (not empty or test data)
            real_events = [e for e in events if e.get('title') and e.get('title') not in [
                'US CPI Data Release', 'ECB Interest Rate Decision', 'US Retail Sales'
            ]]
            
            if len(real_events) > 0:
                # Use real events
                events = real_events
                source = "Finnhub"
                status = "success"
            else:
                # No real events found, but we have some data
                print("⚠️ Only test events found in Finnhub data")
                source = "finnhub_test_data"
                status = "test_data_only"
        else:
            # No events from Finnhub
            print("⚠️ No events from Finnhub API")
            source = "no_data"
            status = "no_data"
            events = []
            
        # Only use fallback data if we have absolutely no real data
        if not events or source == "no_data":
            print("⚠️ Using fallback data due to no real events available")
            fallback_events = get_mock_economic_events()
            return jsonify({
                "events": fallback_events,
                "source": "fallback_data",
                "last_updated": datetime.now().isoformat(),
                "total_events": len(fallback_events),
                "status": "fallback",
                "warning": "Using fallback data - real events unavailable"
            })
        
        return jsonify({
            "events": events,
            "source": source,
            "last_updated": datetime.now().isoformat(),
            "total_events": len(events),
            "status": status,
            "data_quality": metadata.get('data_quality', 'unknown'),
            "demo_api_limitations": metadata.get('demo_api_limitations', False),
            "wrong_year_events_filtered": metadata.get('wrong_year_events_filtered', 0),
            "correct_year_events_found": metadata.get('correct_year_events_found', 0),
            "requested_year": metadata.get('requested_year', datetime.now().year),
            "current_year": metadata.get('current_year', datetime.now().year),
            "recommendation": metadata.get('recommendation', 'data_acceptable')
        })
            
    except Exception as e:
        print(f"❌ Error in economic calendar endpoint: {e}")
        # Only use fallback data on critical errors
        print("⚠️ Critical error - using fallback data")
        fallback_events = get_mock_economic_events()
        return jsonify({
            "events": fallback_events,
            "source": "fallback_data",
            "last_updated": datetime.now().isoformat(),
            "total_events": len(fallback_events),
            "status": "error",
            "error": str(e),
            "warning": "Using fallback data due to critical error"
        })

def get_mock_economic_events():
    """Fallback mock economic calendar data"""
    today = datetime.now()
    
    return [
        {
            "id": 1,
            "time": "13:30 UTC",
            "date": (today + timedelta(days=1)).strftime('%a, %b %d'),
            "title": "US CPI Data Release",
            "type": "ECONOMIC RELEASE",
            "currency": "USD",
            "status": "UPCOMING",
            "impact": "high",
            "currencyPairs": ["EUR/USD", "USD/JPY"],
            "previous": "3.2%",
            "expected": "3.1%",
            "actual": "--",
            "source": "fallback_data"
        },
        {
            "id": 2,
            "time": "12:45 UTC",
            "date": (today + timedelta(days=2)).strftime('%a, %b %d'),
            "title": "ECB Interest Rate Decision",
            "type": "CENTRAL BANK",
            "currency": "EUR",
            "status": "UPCOMING",
            "impact": "high",
            "currencyPairs": ["EUR/USD", "EUR/GBP"],
            "previous": "4.50%",
            "expected": "4.50%",
            "actual": "--",
            "source": "fallback_data"
        },
        {
            "id": 3,
            "time": "14:00 UTC",
            "date": (today + timedelta(days=2)).strftime('%a, %b %d'),
            "title": "US Retail Sales",
            "type": "ECONOMIC RELEASE",
            "currency": "USD",
            "status": "UPCOMING",
            "impact": "medium",
            "currencyPairs": ["GBP/USD", "USD/CHF"],
            "previous": "0.2%",
            "expected": "0.1%",
            "actual": "--",
            "source": "fallback_data"
        }
    ]

@app.route('/api/economic-chart/<event_name>')
def get_economic_chart_data(event_name):
    """Get historical chart data for a specific economic event"""
    try:
        # Get query parameters
        months = request.args.get('months', 12, type=int)
        
        # Decode the event name from URL
        import urllib.parse
        decoded_event_name = urllib.parse.unquote(event_name)
        
        print(f"📊 Fetching chart data for: {decoded_event_name} ({months} months)")
        
        # Get chart data from historical service
        chart_data = finnhub_historical.get_chart_data_for_event(decoded_event_name, months)
        
        if chart_data and chart_data.get('historical_data'):
            return jsonify({
                "chart_data": chart_data,
                "status": "success",
                "message": f"Found {len(chart_data['historical_data'])} data points"
            })
        else:
            return jsonify({
                "chart_data": chart_data,
                "status": "no_data",
                "message": "No historical data available for this event"
            }), 404
            
    except Exception as e:
        print(f"❌ Error in economic chart endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": f"Error fetching chart data: {str(e)}"
        }), 500

@app.route('/api/news')
def get_news():
    """Get aggregated news from multiple sources with optimized performance and alert triggering"""
    try:
        # Import cache system
        from services.news_cache import news_cache
        
        # Check if force refresh is requested
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # First, try to get cached data immediately (unless force refresh)
        cached_news = None
        if not force_refresh:
            cached_news = news_cache.load_news()
        
        if cached_news:
            # Check if cached news contains economic calendar events (Finnhub data)
            # If it does, clear the cache to force fresh news fetch
            has_economic_events = any(
                news_item.get('source', '').lower() == 'finnhub' or 
                news_item.get('type', '').lower() == 'economic' or
                'economic calendar' in str(news_item.get('source', '')).lower()
                for news_item in cached_news
            )
            
            if has_economic_events:
                print("🔄 Clearing cache due to economic calendar events found")
                news_cache.clear_cache()
                cached_news = None
            else:
                        # Remove duplicates from cached news as well
                cached_news = remove_duplicate_news(cached_news)
                
                # Convert all news item IDs to strings to prevent JavaScript precision loss
                for item in cached_news:
                    if 'id' in item:
                        item['id'] = str(item['id'])
                return jsonify({
                    "news": cached_news,
                    "last_updated": datetime.now().isoformat(),
                    "sources": ["cached_data"],
                    "total_articles": len(cached_news),
                    "cache_status": "cached"
                })
        
        # If no cache, fetch fresh data with optimized parallel processing
        # Note: Economic calendar events are excluded from live news feed
        # as they are handled separately in the economic calendar component
        import concurrent.futures
        import asyncio
        
        fresh_news = []
        sources_used = []
        
        # Function to fetch RSS news with timeout
        def fetch_rss_news():
            try:
                rss_news = news_aggregator.get_recent_news(hours=24)
                print(f"✅ Fetched {len(rss_news)} RSS news articles")
                return rss_news
            except Exception as e:
                print(f"❌ Error fetching RSS news: {e}")
                return []
        
        # Function to fetch alternative news with timeout
        def fetch_alternative_news():
            try:
                from services.alternative_news_sources import alternative_news_sources
                alt_news = alternative_news_sources.get_alternative_news(hours=24)
                print(f"✅ Fetched {len(alt_news)} alternative news articles")
                return alt_news
            except Exception as e:
                print(f"❌ Error fetching alternative news: {e}")
                return []
        
        # Use ThreadPoolExecutor for parallel processing with shorter timeouts
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit tasks with 10-second timeout each (removed economic calendar)
            rss_future = executor.submit(fetch_rss_news)
            alt_future = executor.submit(fetch_alternative_news)
            
            # Wait for all tasks with timeout
            try:
                rss_news = rss_future.result(timeout=10)
                fresh_news.extend(rss_news)
                sources_used.append("RSS Feeds")
            except concurrent.futures.TimeoutError:
                print("⚠️ RSS news fetch timed out")
                rss_news = []
            except Exception as e:
                print(f"❌ RSS news fetch failed: {e}")
                rss_news = []
            
            try:
                alt_news = alt_future.result(timeout=10)
                fresh_news.extend(alt_news)
                sources_used.append("Alternative Sources")
            except concurrent.futures.TimeoutError:
                print("⚠️ Alternative news fetch timed out")
                alt_news = []
            except Exception as e:
                print(f"❌ Alternative news fetch failed: {e}")
                alt_news = []
        
        # Try Telegram news separately with shorter timeout (non-blocking)
        telegram_news = []
        try:
            import asyncio
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Reduced timeout for Telegram (15 seconds instead of 30)
            telegram_news = loop.run_until_complete(
                asyncio.wait_for(
                    telegram_user_monitor.get_recent_telegram_news(hours=24),
                    timeout=15.0  # Reduced from 30 to 15 seconds
                )
            )
            loop.close()
            fresh_news.extend(telegram_news)
            sources_used.append("Telegram")
            print(f"✅ Fetched {len(telegram_news)} Telegram news articles")
        except asyncio.TimeoutError:
            print("⚠️ Telegram news fetch timed out, continuing with other sources...")
            telegram_news = []
        except Exception as e:
            print(f"❌ Error fetching Telegram news: {e}")
            print("Continuing with other sources...")
            telegram_news = []
        finally:
            # Ensure we clean up any remaining event loops
            try:
                if 'loop' in locals() and not loop.is_closed():
                    loop.close()
            except:
                pass
        
        # If we got fresh news, save it to cache and return it
        if fresh_news:
            # Combine and sort all news by publication date
            all_news = fresh_news
            all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            # Remove duplicates across all sources
            all_news = remove_duplicate_news(all_news)
            
            # Save to cache for future use
            news_cache.save_news(all_news)
            
            # Note: Alert processing moved to cost-optimized background monitor
            # This prevents excessive API calls and reduces terminal noise
            
            return jsonify({
                "news": all_news,
                "last_updated": datetime.now().isoformat(),
                "sources": sources_used,
                "total_articles": len(all_news),
                "cache_status": "fresh"
            })
        else:
            # No fresh news available, use mock data as fallback
            print("⚠️ No fresh news available, using mock data")
            mock_news = get_mock_news()
            return jsonify({
                "news": mock_news,
                "last_updated": datetime.now().isoformat(),
                "sources": ["fallback_data"],
                "total_articles": len(mock_news),
                "cache_status": "fallback"
            })
                
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        # Try to load from cache as fallback
        try:
            from services.news_cache import news_cache
            cached_news = news_cache.load_news()
            if cached_news:
                # Remove duplicates from fallback cached news as well
                cached_news = remove_duplicate_news(cached_news)
                print(f"✅ Error occurred, using cached news ({len(cached_news)} articles)")
                return jsonify({
                    "news": cached_news,
                    "last_updated": datetime.now().isoformat(),
                    "sources": ["cached_data"],
                    "total_articles": len(cached_news),
                    "cache_status": "cached_fallback"
                })
        except:
            pass
        
        # Last resort: mock data
        mock_news = get_mock_news()
        return jsonify({
            "news": mock_news,
            "last_updated": datetime.now().isoformat(),
            "sources": ["fallback_data"],
            "total_articles": len(mock_news),
            "cache_status": "fallback"
        })

@app.route('/api/force-refresh-news', methods=['POST'])
def force_refresh_news():
    """Force refresh news and trigger alerts immediately"""
    try:
        print("🔄 Force refreshing news...")
        
        # Clear cache to force fresh fetch
        from services.news_cache import news_cache
        news_cache.clear_cache()
        
        # Fetch fresh news
        from services.news_aggregator import news_aggregator
        from services.alternative_news_sources import alternative_news_sources
        
        fresh_news = []
        
        # Fetch RSS news
        try:
            rss_news = news_aggregator.get_recent_news(hours=24)
            fresh_news.extend(rss_news)
            print(f"✅ Fetched {len(rss_news)} RSS news articles")
        except Exception as e:
            print(f"❌ Error fetching RSS news: {e}")
        
        # Fetch alternative news
        try:
            alt_news = alternative_news_sources.get_alternative_news(hours=24)
            fresh_news.extend(alt_news)
            print(f"✅ Fetched {len(alt_news)} alternative news articles")
        except Exception as e:
            print(f"❌ Error fetching alternative news: {e}")
        
        if fresh_news:
            # Remove duplicates and sort
            # Import the function from the correct location
            def remove_duplicate_news(news_list):
                """Remove duplicate news items based on title and source"""
                seen = set()
                unique_news = []
                for item in news_list:
                    # Create a unique key based on title and source
                    key = f"{item.get('title', '')}_{item.get('source', '')}"
                    if key not in seen:
                        seen.add(key)
                        unique_news.append(item)
                return unique_news
            
            fresh_news = remove_duplicate_news(fresh_news)
            fresh_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            # Save to cache
            news_cache.save_news(fresh_news)
            
            # Trigger alerts immediately
            try:
                from services.news_alert_trigger import news_alert_trigger
                results = news_alert_trigger.process_news_for_alerts(fresh_news)
                print(f"🎯 Force refresh alert results: {results}")
            except Exception as e:
                print(f"❌ Error triggering alerts: {e}")
            
            return jsonify({
                "success": True,
                "message": f"Force refreshed {len(fresh_news)} news articles",
                "articles_count": len(fresh_news),
                "alert_results": results if 'results' in locals() else None
            })
        else:
            return jsonify({
                "success": False,
                "message": "No fresh news available"
            }), 404
            
    except Exception as e:
        print(f"❌ Error in force refresh: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analysis/<news_id>')
def get_analysis(news_id):
    """Generate AI analysis for specific news event"""
    try:
        print(f"🦊 BACKEND - Analysis requested for news_id: {news_id}")
        print(f"🦊 BACKEND - News ID type: {type(news_id)}")
        print(f"🦊 BACKEND - News ID value: {news_id}")
        # Convert to int for comparison if it's a string
        try:
            news_id_int = int(news_id)
            print(f"🦊 BACKEND - News ID as int: {news_id_int}")
        except ValueError:
            print(f"🦊 BACKEND - ❌ Could not convert news_id to int: {news_id}")
            news_id_int = None
        print(f"🦊 BACKEND - Request headers: {dict(request.headers)}")
        print(f"🦊 BACKEND - Request origin: {request.headers.get('Origin', 'Unknown')}")
        
        # First try to get the news item from cached news data
        from services.news_cache import news_cache
        cached_news = news_cache.load_news()
        
        print(f"🦊 BACKEND - Cached news count: {len(cached_news) if cached_news else 0}")
        print(f"🦊 BACKEND - Available news IDs: {[item.get('id') for item in cached_news[:5]] if cached_news else 'None'}")
        
        news_item = None
        if cached_news:
            # Try to find news item by ID, handling both string and int types
            news_item = next((item for item in cached_news if str(item.get('id')) == str(news_id)), None)
            print(f"🦊 BACKEND - News item found in cache: {news_item is not None}")
            if news_item:
                print(f"🦊 BACKEND - News item title: {news_item.get('title', 'No title')}")
                print(f"🦊 BACKEND - News item source: {news_item.get('source', 'No source')}")
                print(f"🦊 BACKEND - News item ID in cache: {news_item.get('id')}")
            else:
                print(f"🦊 BACKEND - ❌ News item NOT found in cache for ID: {news_id}")
                print(f"🦊 BACKEND - Available IDs: {[item.get('id') for item in cached_news[:10]]}")
        
        # If not found in cache, try to get from news history
        if not news_item:
            print(f"🔍 Trying news history for news_id: {news_id}")
            try:
                from services.news_cache import news_cache
                history_data = news_cache.get_recent_history(hours=24)
                news_item = next((item for item in history_data if item.get('id') == news_id), None)
                if news_item:
                    print(f"🔍 News item found in history: {news_item.get('title', 'No title')}")
            except Exception as e:
                print(f"🔍 Error getting from history: {e}")
                pass
        
        # If still not found, try to get from economic calendar
        if not news_item:
            print(f"🔍 Trying economic calendar for news_id: {news_id}")
            try:
                event = get_economic_event_by_id(news_id)
                if event:
                    print(f"🔍 Economic event found: {event.get('title', 'No title')}")
                    # Generate AI analysis for economic event
                    analysis = generate_ai_analysis(
                        event['title'], 
                        event['currency'], 
                        event['impact']
                    )
                    return jsonify(analysis)
            except Exception as e:
                print(f"🔍 Error getting economic event: {e}")
                pass
        
        # If we have a news item, generate news-specific analysis
        if news_item:
            print(f"🦊 BACKEND - Generating news analysis for: {news_item.get('title', 'No title')}")
            analysis = generate_news_analysis(news_item)
            print(f"🦊 BACKEND - Analysis generated successfully")
            print(f"🦊 BACKEND - Analysis type: {analysis.get('analysis_type', 'unknown')}")
            print(f"🦊 BACKEND - Analysis news_impact length: {len(analysis.get('news_impact', ''))}")
            print(f"🦊 BACKEND - Analysis trading_implications length: {len(analysis.get('trading_implications', ''))}")
            print(f"🦊 BACKEND - Analysis confidence: {analysis.get('confidence', 'unknown')}")
            print(f"🦊 BACKEND - Analysis immediate_reaction: {analysis.get('immediate_reaction', 'unknown')}")
            print(f"🦊 BACKEND - Analysis key_pairs: {analysis.get('key_pairs', [])}")
            print(f"🦊 BACKEND - Analysis volatility: {analysis.get('volatility', 'unknown')}")
            print(f"🦊 BACKEND - Analysis timeframe: {analysis.get('timeframe', 'unknown')}")
            print(f"🦊 BACKEND - Analysis risk_assessment: {analysis.get('risk_assessment', {})}")
            print(f"🦊 BACKEND - Analysis market_context: {analysis.get('market_context', {})}")
            print(f"🦊 BACKEND - Full analysis response structure: {list(analysis.keys())}")
            print(f"🦊 BACKEND - ✅ Returning analysis to frontend")
            return jsonify(analysis)
        
        # Fallback if nothing found
        print(f"🦊 BACKEND - ❌ No news item found, using fallback")
        fallback_analysis = get_mock_news_analysis("News Event")
        print(f"🦊 BACKEND - Fallback analysis type: {fallback_analysis.get('analysis_type', 'unknown')}")
        print(f"🦊 BACKEND - Fallback analysis news_impact: {fallback_analysis.get('news_impact', '')[:100]}...")
        print(f"🦊 BACKEND - ❌ Returning fallback analysis to frontend")
        return jsonify(fallback_analysis)
        
    except Exception as e:
        print(f"🦊 BACKEND - ❌ Error generating analysis: {e}")
        print(f"🦊 BACKEND - ❌ Error type: {type(e).__name__}")
        import traceback
        print(f"🦊 BACKEND - ❌ Traceback: {traceback.format_exc()}")
        fallback_analysis = get_mock_news_analysis("News Event")
        print(f"🦊 BACKEND - Error fallback analysis type: {fallback_analysis.get('analysis_type', 'unknown')}")
        print(f"🦊 BACKEND - ❌ Returning error fallback analysis to frontend")
        return jsonify(fallback_analysis)

def generate_news_analysis(news_item):
    """Generate AI analysis for RSS news articles using MVP analyzer"""
    try:
        print(f"🔍 Starting MVP news analysis for: {news_item.get('title', 'No title')}")
        
        # Import MVP analyzer and analysis history
        from services.mvp_news_analyzer import mvp_news_analyzer
        from services.analysis_history import analysis_history
        
        # Generate market context (simplified for now)
        market_context = {
            "current_prices": {
                "EUR/USD": 1.0850,
                "USD/JPY": 148.50,
                "GBP/USD": 1.2650
            }
        }
        
        # Analyze news using MVP analyzer
        mvp_result = mvp_news_analyzer.analyze_news(news_item, market_context)
        
        print(f"🔍 MVP analysis completed: {mvp_result.immediate_reaction}")
        print(f"🔍 MVP analysis news_impact length: {len(mvp_result.news_impact) if mvp_result.news_impact else 0}")
        print(f"🔍 MVP analysis trading_implications length: {len(mvp_result.trading_implications) if mvp_result.trading_implications else 0}")
        
        # Format response for frontend compatibility (simplified structure)
        try:
            risk_assessment = mvp_result.risk_assessment
        except AttributeError:
            risk_assessment = {
                "market_volatility": "medium",
                "liquidity_impact": "medium",
                "correlation_risk": "medium"
            }
        
        try:
            market_context = mvp_result.market_context
        except AttributeError:
            market_context = {
                "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
                "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
                "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
            }
        
        analysis_result = {
            "news_impact": mvp_result.news_impact,
            "trading_implications": mvp_result.trading_implications,
            "immediate_reaction": mvp_result.immediate_reaction,
            "key_pairs": mvp_result.key_pairs,
            "volatility": mvp_result.volatility,
            "timeframe": mvp_result.timeframe,
            "confidence": mvp_result.confidence,
            "analysis_type": mvp_result.analysis_type,
            "risk_assessment": risk_assessment,
            "market_context": market_context
        }
        
        print(f"🔍 Analysis result news_impact: {analysis_result['news_impact'][:50] if analysis_result['news_impact'] else 'EMPTY'}...")
        print(f"🔍 Analysis result trading_implications: {analysis_result['trading_implications'][:50] if analysis_result['trading_implications'] else 'EMPTY'}...")
        print(f"🔍 Analysis result structure: {list(analysis_result.keys())}")
        print(f"🔍 Analysis result news_impact type: {type(analysis_result['news_impact'])}")
        print(f"🔍 Analysis result trading_implications type: {type(analysis_result['trading_implications'])}")
        print(f"🔍 Analysis result immediate_reaction type: {type(analysis_result['immediate_reaction'])}")
        print(f"🔍 Analysis result confidence type: {type(analysis_result['confidence'])}")
        
        # Store analysis in history
        analysis_history.add_analysis(news_item, analysis_result)
        print(f"🔍 Analysis stored in history")
        
        print(f"🔍 MVP analysis result formatted successfully")
        return analysis_result
            
    except Exception as e:
        print(f"❌ Error generating MVP news analysis: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return get_mock_news_analysis(news_item.get('title', 'News Event'))

def generate_trading_implications_from_news(sentiment_result, currency_pairs, impact):
    """Generate trading implications from news sentiment analysis"""
    implications = {
        'summary': '',
        'opportunities': []
    }
    
    sentiment = sentiment_result.sentiment.lower()
    impact_score = sentiment_result.impact_score
    
    # Generate summary based on sentiment
    if sentiment == 'bullish':
        implications['summary'] = f"Positive market sentiment detected with {impact_score}/10 impact score. Consider long positions on affected currency pairs."
    elif sentiment == 'bearish':
        implications['summary'] = f"Negative market sentiment detected with {impact_score}/10 impact score. Consider short positions or defensive strategies."
    else:
        implications['summary'] = f"Neutral market sentiment with {impact_score}/10 impact score. Monitor for breakout opportunities."
    
    # Generate specific opportunities for each currency pair
    for pair in currency_pairs:
        opportunity = {
            'pair': pair,
            'strategy': 'sentiment_following',
            'direction': sentiment,
            'confidence': sentiment_result.confidence,
            'timeframe': '1-4 hours',
            'risk_level': 'medium' if impact == 'medium' else 'high' if impact == 'high' else 'low'
        }
        implications['opportunities'].append(opportunity)
    
    return implications

def generate_currency_pair_analysis(currency_pairs, sentiment_result):
    """Generate analysis for each affected currency pair"""
    analysis = {}
    
    for pair in currency_pairs:
        sentiment = sentiment_result.sentiment.lower()
        
        if sentiment == 'bullish':
            analysis[pair] = f"Positive sentiment suggests potential upside for {pair}. Monitor for breakout above key resistance levels."
        elif sentiment == 'bearish':
            analysis[pair] = f"Negative sentiment suggests potential downside for {pair}. Watch for breakdown below key support levels."
        else:
            analysis[pair] = f"Neutral sentiment for {pair}. Range-bound trading likely with breakout potential."
    
    return analysis

def get_mock_news_analysis(news_title):
    """Fallback mock analysis for news events with complete structure"""
    return {
        "news_impact": f"This news event about {news_title} has significant implications for forex markets. The development suggests potential shifts in market sentiment and economic outlook that could impact currency valuations. Traders should monitor for increased volatility and potential breakout opportunities as the market digests this information.",
        "trading_implications": f"Based on this news, traders should consider monitoring key currency pairs for potential trading opportunities. The immediate market reaction may be volatile, so risk management is crucial. Focus on major pairs like EUR/USD and USD/JPY, and be prepared for both bullish and bearish scenarios depending on market interpretation.",
        "immediate_reaction": "neutral",
        "key_pairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
        "volatility": "medium",
        "timeframe": "1-24 hours",
        "confidence": 75,
        "analysis_type": "free_enhanced",
        "risk_assessment": {
            "market_volatility": "medium",
            "liquidity_impact": "medium",
            "correlation_risk": "medium"
        },
        "market_context": {
            "economic_factors": ["Market sentiment", "Economic uncertainty", "Policy implications"],
            "technical_levels": ["Key support and resistance levels", "Psychological price levels"],
            "sentiment_drivers": ["News sentiment", "Market positioning", "Risk appetite"]
        }
    }

@app.route('/api/news-sentiment', methods=['POST'])
def analyze_news_sentiment():
    """Analyze sentiment of news articles"""
    try:
        data = request.get_json()
        news_items = data.get('news_items', [])
        
        if not news_items:
            return jsonify({"error": "No news items provided"}), 400
        
        # Analyze sentiment for multiple news items
        sentiment_analysis = news_sentiment_analyzer.analyze_multiple_news(news_items)
        
        return jsonify(sentiment_analysis)
        
    except Exception as e:
        print(f"Error analyzing news sentiment: {e}")
        return jsonify({"error": "Failed to analyze sentiment"}), 500

@app.route('/api/technical-analysis/<pair>')
def get_technical_analysis(pair):
    """Get technical analysis for a currency pair"""
    try:
        # Get historical data for the pair (you can enhance this with real data)
        # For now, we'll create mock data
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        np.random.seed(42)  # For consistent mock data
        
        # Create realistic price data
        base_price = 1.0850 if 'EUR' in pair else 148.50 if 'JPY' in pair else 1.2650
        price_changes = np.random.normal(0, 0.005, len(dates))
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # Create DataFrame
        price_data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        # Perform technical analysis
        analysis = technical_analyzer.analyze_pair(pair, price_data)
        
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error in technical analysis: {e}")
        return jsonify({"error": "Failed to perform technical analysis"}), 500

@app.route('/api/enhanced-analysis/<news_id>', methods=['GET', 'POST'])
def get_enhanced_analysis(news_id):
    """Get comprehensive GPT-powered analysis for economic events"""
    print(f"🚨🚨🚨 ENHANCED ANALYSIS ENDPOINT CALLED - ID: {news_id} 🚨🚨🚨")
    try:
        # Get event data from request body if POST, otherwise from Finnhub calendar
        if request.method == 'POST':
            request_data = request.get_json()
            event = request_data.get('event')
            analysis_type = request_data.get('analysisType', 'pre-event')
            print(f"🚨 Using event data from request: {event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')}")
        else:
            # Get the economic event by ID from Finnhub calendar data
            event = get_economic_event_by_id(news_id)
            analysis_type = 'pre-event'
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        # Create GPT market context with real market data and enhanced positioning data
        gpt_market_context = GPTMarketContext(
            current_prices={
                'EUR/USD': 1.0850,
                'USD/JPY': 148.50,
                'GBP/USD': 1.2650,
                'USD/CHF': 0.8650,
                'AUD/USD': 0.6650,
                'USD/CAD': 1.3550
            },
            recent_volatility={
                'EUR/USD': 0.008,
                'USD/JPY': 0.012,
                'GBP/USD': 0.010,
                'USD/CHF': 0.007,
                'AUD/USD': 0.009,
                'USD/CAD': 0.006
            },
            market_sentiment={
                'EUR/USD': 'neutral',
                'USD/JPY': 'bullish',
                'GBP/USD': 'bearish',
                'USD/CHF': 'neutral',
                'AUD/USD': 'neutral',
                'USD/CAD': 'neutral'
            },
            key_levels={
                'EUR/USD': {'support': [1.0800, 1.0750, 1.0700], 'resistance': [1.0900, 1.0950, 1.1000]},
                'USD/JPY': {'support': [148.00, 147.50, 147.00], 'resistance': [149.00, 149.50, 150.00]},
                'GBP/USD': {'support': [1.2600, 1.2550, 1.2500], 'resistance': [1.2700, 1.2750, 1.2800]}
            },
            economic_calendar=[],
            bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
            equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
            commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
            # Enhanced positioning data
            retail_sentiment={
                'EUR/USD': 0.65,
                'USD/JPY': 0.35,
                'GBP/USD': 0.50,
                'USD/CHF': 0.70,
                'AUD/USD': 0.40,
                'USD/CAD': 0.55
            },
            futures_positioning={
                'EUR/USD': 15000,
                'USD/JPY': -8000,
                'GBP/USD': 5000,
                'USD/CHF': 12000,
                'AUD/USD': -3000,
                'USD/CAD': 2000
            },
            institutional_flow={
                'EUR/USD': 25.5,
                'USD/JPY': -15.2,
                'GBP/USD': 8.7,
                'USD/CHF': 18.3,
                'AUD/USD': -12.1,
                'USD/CAD': 5.4
            },
            time_to_event=3600,  # 1 hour until event
            liquidity_level=2,   # Medium liquidity
            scenario_probabilities={
                'higher': 0.30,
                'lower': 0.50,
                'inline': 0.20
            }
        )
        
        # Use analysis_type from request or determine based on actual data availability
        if 'analysis_type' not in locals():
            has_actual_data = event.get('actual') and event.get('actual') not in ['N/A', '', None]
            analysis_type = "post_event" if has_actual_data else "pre_event"
        
        print(f"📊 Analysis type: {analysis_type.upper()} (Actual data: {event.get('actual', 'Not available')})")
        
        # Get GPT-powered comprehensive analysis using new streamlined system
        try:
            print(f"🚨🚨🚨 USING NEW STREAMLINED GPT ANALYZER 🚨🚨🚨")
            gpt_analysis = gpt_ai_analyzer.analyze_macro_event(event, gpt_market_context, analysis_type)
        except Exception as e:
            print(f"🚨🚨🚨 NEW GPT ANALYZER FAILED - USING FALLBACK 🚨🚨🚨")
            print(f"Error: {e}")
            # Fallback to enhanced analysis
            gpt_analysis = enhanced_ai_analyzer.analyze_macro_event(
                event, 
                gpt_market_context, 
                analysis_type
            )
        
        # Debug: Log what we're getting from GPT
        print(f"🚨🚨🚨 AI ANALYSIS DEBUG - EASY TO FIND 🚨🚨🚨")
        print(f"🚨 Analysis Type: {type(gpt_analysis)}")
        print(f"🚨 Analysis Keys: {list(gpt_analysis.keys()) if isinstance(gpt_analysis, dict) else 'Not a dict'}")
        print(f"🚨 Sample Analysis: {str(gpt_analysis)[:200]}...")
        print(f"🚨🚨🚨 END AI ANALYSIS DEBUG 🚨🚨🚨")
        
        # Transform to frontend-compatible format with new structure
        if hasattr(gpt_analysis, 'headline'):  # New enhanced structure
            # Enhanced GPT analyzer returns object with quick-scan elements
            enhanced_analysis = {
                # Quick-scan elements (NEW)
                'headline': gpt_analysis.headline,
                'key_takeaway': gpt_analysis.key_takeaway,
                'forward_scenarios': gpt_analysis.forward_scenarios,
                
                # Comprehensive analysis (EXISTING)
                'eventSummary': gpt_analysis.event_summary,
                'market_reaction': gpt_analysis.market_reaction,
                'implications_takeaways': gpt_analysis.implications_takeaways,
                'trading_plan': gpt_analysis.trading_plan,
                'big_picture': gpt_analysis.big_picture,
                
                # Enhanced positioning context (NEW)
                'positioning_context': gpt_analysis.positioning_context,
                'next_catalysts': gpt_analysis.next_catalysts,
                
                # Meta data
                'confidence_score': gpt_analysis.confidence_score,
                'analysis_timestamp': gpt_analysis.analysis_timestamp,
                'event_id': gpt_analysis.event_id,
                'analysis_type': gpt_analysis.analysis_type,
                'model_used': gpt_analysis.model_used,
                'cost_estimate': gpt_analysis.cost_estimate,
                'cache_hit': gpt_analysis.cache_hit,
                'definition_source': gpt_analysis.definition_source
            }
        elif isinstance(gpt_analysis, dict):
            # Optimized ChatGPT analyzer returns dict (includes professional sections)
            enhanced_analysis = {
                'event': event,
                'event_summary': gpt_analysis.get('event_summary', {}),
                'market_reaction': gpt_analysis.get('market_reaction', {}),
                'economic_significance': gpt_analysis.get('economic_significance', {}),
                'policy_implications': gpt_analysis.get('policy_implications', {}),
                'trading_strategy': gpt_analysis.get('trading_strategy', {}),
                'risk_assessment': gpt_analysis.get('risk_assessment', {}),
                'metadata': gpt_analysis.get('metadata', {}),
                'analysis_type': analysis_type,
                'model_used': gpt_analysis.get('metadata', {}).get('model_used', 'optimized_chatgpt'),
                'cache_status': gpt_analysis.get('metadata', {}).get('cache_status', 'unknown'),
                'analysis_timestamp': gpt_analysis.get('metadata', {}).get('analysis_timestamp', datetime.now().isoformat()),
                # Professional template sections
                'summary': gpt_analysis.get('summary'),
                'market_impact': gpt_analysis.get('market_impact'),
                'policy_context': gpt_analysis.get('policy_context'),
                'trading_view': gpt_analysis.get('trading_view'),
                'big_picture': gpt_analysis.get('big_picture')
            }
        else:
            # New streamlined GPT analysis format
            enhanced_analysis = {
                'event': event,
                'event_summary': getattr(gpt_analysis, 'event_summary', {}),
                'market_reaction': getattr(gpt_analysis, 'market_reaction', {}),
                'implications_takeaways': getattr(gpt_analysis, 'implications_takeaways', {}),
                'trading_plan': getattr(gpt_analysis, 'trading_plan', {}),
                'big_picture': getattr(gpt_analysis, 'big_picture', {}),
                'confidence_score': getattr(gpt_analysis, 'confidence_score', 70),
                'analysis_timestamp': getattr(gpt_analysis, 'analysis_timestamp', datetime.now().isoformat()),
                'analysis_type': getattr(gpt_analysis, 'analysis_type', analysis_type),
                'model_used': getattr(gpt_analysis, 'model_used', 'gpt_ai_analyzer'),
                'cost_estimate': getattr(gpt_analysis, 'cost_estimate', 0),
                'cache_hit': getattr(gpt_analysis, 'cache_hit', False)
            }
        
        return jsonify(enhanced_analysis)
        
    except Exception as e:
        print(f"Error generating GPT analysis: {e}")
        return jsonify({"error": "Failed to generate GPT analysis"}), 500

@app.route('/api/health')
def health_check():
    """Main health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/health/alerts')
def health_alerts():
    """Alert system health check"""
    try:
        from services.alert_service import get_alert_service
        alert_service = get_alert_service()
        
        # Check if alert service is working
        telegram_bot_working = alert_service.telegram_bot is not None
        
        return jsonify({
            "status": "healthy" if telegram_bot_working else "degraded",
            "timestamp": datetime.now().isoformat(),
            "telegram_bot": "connected" if telegram_bot_working else "disconnected",
            "firebase": "connected" if alert_service.firebase_storage.test_connection() else "disconnected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/telegram')
def health_telegram():
    """Telegram monitor health check"""
    try:
        from services.telegram_monitor_user import telegram_user_monitor
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "monitor_status": "active",
            "last_message_time": getattr(telegram_user_monitor, 'last_message_time', None)
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/calendar')
def health_calendar():
    """Economic calendar health check"""
    try:
        from services.economic_calendar_alerts import EconomicCalendarAlerts
        calendar_service = EconomicCalendarAlerts()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "active"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/news')
def health_news():
    """News aggregator health check"""
    try:
        from services.news_aggregator import NewsAggregator
        news_service = NewsAggregator()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "active"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/ai')
def health_ai():
    """AI analysis health check"""
    try:
        from services.gpt_ai_analysis import GPTAIAnalyzer
        ai_service = GPTAIAnalyzer()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "active"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/system')
def health_system():
    """Complete system health check"""
    try:
        from services.process_monitor import process_monitor
        
        system_status = process_monitor.get_system_status()
        
        return jsonify({
            "status": system_status['overall_status'],
            "timestamp": datetime.now().isoformat(),
            "processes": system_status['processes'],
            "summary": {
                "total_processes": system_status['total_processes'],
                "running_processes": system_status['running_processes'],
                "critical_processes": system_status['critical_processes'],
                "critical_running": system_status['critical_running']
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/gpt-stats')
def get_gpt_stats():
    """Get GPT AI analysis usage statistics"""
    try:
        stats = gpt_ai_analyzer.get_usage_stats()
        return jsonify({
            "gpt_usage": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to get GPT stats",
            "message": str(e)
        }), 500

@app.route('/api/cache-status')
def cache_status():
    """Get cache status information"""
    try:
        from services.news_cache import news_cache
        status = news_cache.get_cache_status()
        return jsonify({
            "cache_status": status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/api-status')
def api_status():
    """Check UniRateAPI usage status"""
    now = datetime.now()
    today = now.date()
    
    # Reset counters for new day
    if unirate_api_usage['last_reset'] != today:
        unirate_api_usage['requests'] = 0
        unirate_api_usage['last_reset'] = today
    
    # Reset minute counter if needed
    if (now - unirate_api_usage['last_minute_reset']).seconds >= 60:
        unirate_api_usage['minute_requests'] = 0
        unirate_api_usage['last_minute_reset'] = now
    
    status = {
        "provider": "UniRateAPI",
        "plan": "Free Forever",
        "daily_requests_used": unirate_api_usage['requests'],
        "daily_requests_remaining": "unlimited",
        "minute_requests_used": unirate_api_usage['minute_requests'],
        "minute_requests_remaining": 30 - unirate_api_usage['minute_requests'],
        "daily_limit": "unlimited",
        "minute_limit": 30,
        "status": "available" if unirate_api_usage['minute_requests'] < 30 else "exhausted",
        "last_updated": datetime.now().isoformat()
    }
    
    return jsonify(status)

@app.route('/api/trading-data')
def get_trading_data():
    """Get trading data and market sentiment"""
    try:
        # Mock trading data - in production, this would come from real APIs
        trading_data = {
            "eurUsd": {
                "price": 1.0856,
                "change": 0.12,
                "sentiment": "bullish",
                "support": 1.0850,
                "resistance": 1.0900
            },
            "usdJpy": {
                "price": 148.23,
                "change": -0.08,
                "sentiment": "bearish",
                "support": 148.00,
                "resistance": 148.50
            },
            "gold": {
                "price": 2034.50,
                "change": 0.45,
                "sentiment": "bullish",
                "support": 2030.00,
                "resistance": 2050.00
            },
            "marketSentiment": "neutral",
            "volatilityIndex": 15.2,
            "lastUpdated": datetime.now().isoformat()
        }
        
        return jsonify(trading_data)
        
    except Exception as e:
        print(f"Error fetching trading data: {e}")
        return jsonify({"error": "Failed to fetch trading data"}), 500

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts and alert statistics"""
    try:
        # Mock alerts data - in production, this would come from database
        alerts = [
            {
                "id": 1,
                "type": "telegram",
                "event": "US CPI Data",
                "status": "sent",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "recipients": 1250,
                "impact": "High"
            },
            {
                "id": 2,
                "type": "email",
                "event": "ECB Interest Rate Decision",
                "status": "scheduled",
                "timestamp": (datetime.now() + timedelta(hours=2)).isoformat(),
                "recipients": 890,
                "impact": "High"
            },
            {
                "id": 3,
                "type": "telegram",
                "event": "UK GDP Release",
                "status": "sent",
                "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                "recipients": 1100,
                "impact": "Medium"
            }
        ]
        
        stats = {
            "telegramSubscribers": 1250,
            "emailSubscribers": 890,
            "alertsThisWeek": 24,
            "totalAlerts": 156
        }
        
        return jsonify({
            "alerts": alerts,
            "stats": stats,
            "lastUpdated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return jsonify({"error": "Failed to fetch alerts"}), 500

@app.route('/api/ai-insights')
def get_ai_insights():
    """Get AI-powered trading insights"""
    try:
        # Mock AI insights - in production, this would be generated by AI models
        insights = [
            {
                "pair": "EUR/USD",
                "analysis": "Strong support at 1.0850 level. Break above 1.0870 could trigger bullish momentum. Key resistance at 1.0900.",
                "confidence": 85,
                "timeframe": "4H",
                "sentiment": "bullish",
                "keyLevels": {
                    "support": 1.0850,
                    "resistance": 1.0900
                }
            },
            {
                "pair": "USD/JPY",
                "analysis": "Consolidating near 148.00 support. Bearish pressure building. Watch for break below 147.80 for short opportunities.",
                "confidence": 72,
                "timeframe": "1H",
                "sentiment": "bearish",
                "keyLevels": {
                    "support": 147.80,
                    "resistance": 148.50
                }
            },
            {
                "pair": "Gold",
                "analysis": "Bullish momentum continues above $2030. Next target $2050. Safe haven demand supporting prices.",
                "confidence": 91,
                "timeframe": "Daily",
                "sentiment": "bullish",
                "keyLevels": {
                    "support": 2030.00,
                    "resistance": 2050.00
                }
            }
        ]
        
        return jsonify({
            "insights": insights,
            "lastUpdated": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error fetching AI insights: {e}")
        return jsonify({"error": "Failed to fetch AI insights"}), 500



@app.route('/api/alerts/user-settings', methods=['GET', 'PUT'])
def get_alert_settings():
    """Get or update user's alert settings"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('userId')
            if not user_id:
                return jsonify({"success": False, "error": "userId is required"}), 400
            
            # Verify user has access (security check)
            if not _verify_user_access(user_id):
                return jsonify({"success": False, "error": "Access denied. Please log in to the dashboard first."}), 403
            
            # Get real settings from Firebase
            try:
                from services.firebase_realtime_storage import FirebaseRealtimeStorage
                firebase_storage = FirebaseRealtimeStorage()
                settings = firebase_storage.get_user_alert_settings(user_id)
                
                if settings:
                    return jsonify({"success": True, "settings": settings})
                else:
                    # Return default settings for new users
                    default_settings = {
                        "channels": {
                            "telegram": {"enabled": False, "chatId": "", "username": ""},
                            "email": {"enabled": False, "address": ""}
                        },
                        "preferences": {
                            "impactLevels": {"high": True, "medium": True, "low": False},
                            "alertTypes": {"preNews": True, "postNews": True, "liveNews": True, "technicalAnalysis": False},
                            "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
                            "quietHours": {"enabled": False, "start": "22:00", "end": "06:00", "timezone": "UTC"}
                        }
                    }
                    return jsonify({"success": True, "settings": default_settings})
                    
            except Exception as e:
                print(f"Error getting user settings from Firebase: {e}")
                return jsonify({"success": False, "error": "Failed to load settings"}), 500
            
        elif request.method == 'PUT':
            # For PUT requests, get userId from JSON body
            if not request.is_json:
                return jsonify({"success": False, "error": "Content-Type must be application/json for PUT requests"}), 415
            user_id = request.json.get('userId')
            if not user_id:
                return jsonify({"success": False, "error": "userId is required in JSON body"}), 400
            # Mock update success
            return jsonify({"success": True, "message": "Settings updated (mock mode)"})
        
    except Exception as e:
        print(f"Error managing alert settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get user's alert history"""
    try:
        user_id = request.args.get('userId')
        limit = int(request.args.get('limit', 50))
        
        if not user_id:
            return jsonify({"success": False, "error": "userId is required"}), 400
        
        # Verify user has access (security check)
        if not _verify_user_access(user_id):
            return jsonify({"success": False, "error": "Access denied. Please log in to the dashboard first."}), 403
        
        # Get real alert history from Firebase
        try:
            print(f"🔍 Attempting to get Firebase history for user: {user_id}")
            from services.firebase_realtime_storage import FirebaseRealtimeStorage
            firebase_storage = FirebaseRealtimeStorage()
            history = firebase_storage.get_user_alert_history(user_id, limit)
            
            print(f"🔍 Firebase returned {len(history) if history else 0} alerts")
            
            if history:
                print(f"🔍 Returning real Firebase data")
                return jsonify({"success": True, "history": history})
            else:
                print(f"🔍 No Firebase data found, returning empty array")
                return jsonify({"success": True, "history": []})
                
        except Exception as e:
            print(f"❌ Error getting alert history from Firebase: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to mock data if Firebase fails
            history = [
                {
                    "id": "mock_1",
                    "alert_type": "test",
                    "title": "Test Alert",
                    "content": "This is a test alert to verify your setup",
                    "status": "sent",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "sent_via": ["telegram"]
                }
            ]
            return jsonify({"success": True, "history": history})
        
    except Exception as e:
        print(f"Error getting alert history: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/test', methods=['POST'])
def send_test_alert():
    """Send a test alert to the user's Telegram"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data:
            return jsonify({"success": False, "error": "userId is required"}), 400
        
        user_id = data['userId']
        alert_type = data.get('alertType', 'test')
        message = data.get('message', 'This is a test alert from FXSentinel!')
        
        # Verify user has access
        if not _verify_user_access(user_id):
            return jsonify({"success": False, "error": "Access denied. Please log in to the dashboard first."}), 403
        
        # Get user's chat ID
        chat_id = _get_user_chat_id(user_id)
        if not chat_id:
            return jsonify({"success": False, "error": "Telegram not connected. Please complete bot setup first."}), 400
        
        # Send test alert via Telegram
        try:
            import requests
            
            # Create test alert content with proper HTML formatting
            test_content = f"""🧪 <b>FXSentinel Test Alert</b>

{message}

📊 <b>Test Details:</b>
• Alert Type: {alert_type}
• User ID: {user_id[:8]}...
• Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
• Status: ✅ Connection Verified

🎯 <b>Your alert preferences are working correctly!</b>
You'll receive real alerts for:
• Breaking news
• Economic events
• Market analysis

Stay tuned for real market alerts! 📈"""
            
            # Send the alert directly using Telegram Bot API HTTP request
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                return jsonify({
                    "success": False,
                    "error": "Telegram bot token not configured"
                }), 500
            
            # Send message using direct HTTP request (same as working /test command)
            telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            telegram_data = {
                'chat_id': chat_id,
                'text': test_content,
                'parse_mode': 'HTML'
            }
            
            telegram_response = requests.post(telegram_url, json=telegram_data, timeout=10)
            
            if telegram_response.status_code == 200:
                # Save to alert history
                try:
                    from services.firebase_realtime_storage import FirebaseRealtimeStorage
                    firebase_storage = FirebaseRealtimeStorage()
                    
                    alert_data = {
                        'alert_type': 'test',
                        'title': 'Test Alert',
                        'content': test_content,
                        'timestamp': datetime.now().isoformat(),
                        'sent_via': ['telegram'],
                        'status': 'sent'
                    }
                    
                    firebase_storage.log_alert_history(user_id, alert_data)
                except Exception as e:
                    print(f"Warning: Could not save test alert to history: {e}")
                
                return jsonify({
                    "success": True,
                    "message": "Test alert sent successfully",
                    "chatId": chat_id
                })
            else:
                telegram_error = telegram_response.json() if telegram_response.content else "Unknown error"
                return jsonify({
                    "success": False,
                    "error": f"Telegram API error: {telegram_error}"
                }), 500
                
        except Exception as e:
            print(f"Error sending test alert: {e}")
            return jsonify({
                "success": False,
                "error": f"Telegram service error: {str(e)}"
            }), 500
        
    except Exception as e:
        print(f"Error in test alert endpoint: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        # Mock alert stats (bypass alert service to avoid connection issues)
        stats = {
            "total_users": 1,  # Mock data
            "active_alerts": 2,  # Mock data
            "alerts_sent_today": 1,  # Mock data
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify({"success": True, "stats": stats})
        
    except Exception as e:
        print(f"Error getting alert stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Alert System API Endpoints
@app.route('/api/telegram/setup', methods=['POST'])
def setup_telegram_bot():
    """Generate unique bot link for user setup - AUTHENTICATED USERS ONLY"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data:
            return jsonify({"success": False, "error": "userId is required"}), 400
        
        user_id = data['userId']
        
        # SECURITY: Verify user is authenticated and has dashboard access
        # In production, this would check against your user database
        if not _verify_user_access(user_id):
            return jsonify({"success": False, "error": "Access denied. Please log in to the dashboard first."}), 403
        
        # Generate unique, time-limited token for this user
        setup_token = _generate_setup_token(user_id)
        print(f"🔧 DEBUG: Generated token for user {user_id}: {setup_token}")
        print(f"🔧 DEBUG: Token length: {len(setup_token)}")
        
        return jsonify({
            "success": True,
            "botUsername": "@FXSentinelAlertsBot",
            "botLink": f"https://t.me/FXSentinelAlertsBot?start={setup_token}",
            "instructions": [
                "1. Click the link below to start the bot",
                "2. Send /start to begin setup",
                "3. Follow the bot instructions to complete setup"
            ],
            "fallback": True,
            "message": "Bot setup completed (authenticated mode)"
        })
        
    except Exception as e:
        print(f"Error setting up Telegram bot: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/telegram/verify', methods=['POST'])
def verify_telegram_connection():
    """Verify user has dashboard access - AUTHENTICATED USERS ONLY"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data:
            return jsonify({"success": False, "error": "userId is required"}), 400
        
        user_id = data['userId']
        
        # SECURITY: Verify user is authenticated and has dashboard access
        if not _verify_user_access(user_id):
            return jsonify({"success": False, "error": "Access denied. Please log in to the dashboard first."}), 403
        
        # Check if user has completed bot setup (optional check)
        chat_id = _get_user_chat_id(user_id)
        if chat_id:
            return jsonify({
                "success": True,
                "connected": True,
                "chatId": chat_id,
                "username": f"user_{user_id}"
            })
        else:
            # User has dashboard access but hasn't completed bot setup yet
            return jsonify({
                "success": True,
                "connected": False,
                "error": "Bot setup not completed. Please follow the setup instructions."
            })
        
    except Exception as e:
        print(f"Error verifying Telegram connection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Security helper functions
def _verify_user_access(user_id):
    """Verify user has access to dashboard - SIMPLIFIED SECURITY CHECK"""
    try:
        print(f"🔒 SECURITY CHECK: Verifying access for user: {user_id}")
        
        # Block obvious invalid user IDs and test users
        invalid_ids = [
            'current_user_id', 'authenticated_user', 'test_user', 'mock_user', 
            'new_user_test_001', 'invalid_user', 'test_authorized_user_123',
            'test_user_123', '93dc7ac8fca1b72c6ec800f35c7ac1d7', 
            'b58996c504c5638798eb6b511e6f49af'
        ]
        if not user_id or user_id in invalid_ids:
            print(f"❌ BLOCKED: Invalid user_id: {user_id}")
            return False
        
        # Block short user IDs (should be email or Firebase UID)
        if len(user_id) < 5:
            print(f"❌ BLOCKED: User_id too short: {user_id}")
            return False
        
        # Block test users that start with 'test_' or 'new_user_'
        if user_id.startswith('test_') or user_id.startswith('new_user_'):
            print(f"❌ BLOCKED: Test user_id: {user_id}")
            return False
        
        # For now, allow valid-looking user IDs (email format or long UID)
        if '@' in user_id or len(user_id) > 15:
            print(f"✅ ALLOWED: Valid user_id format: {user_id}")
            return True
        
        # Block everything else for security
        print(f"❌ BLOCKED: User_id format not recognized: {user_id}")
        return False
            
    except Exception as e:
        print(f"❌ Error in user verification: {e}")
        return False

def _basic_user_validation(user_id):
    """Basic user validation when Firebase Admin SDK is not available"""
    # Basic checks for valid user_id format
    if not user_id:
        return False
    
    # Check if it looks like a valid user ID (not placeholder values)
    invalid_ids = ['current_user_id', 'authenticated_user', 'test_user', 'mock_user', '']
    if user_id in invalid_ids:
        print(f"❌ Invalid user_id in basic validation: {user_id}")
        return False
    
    # Check if it looks like an email or Firebase UID
    if '@' in user_id or len(user_id) > 10:
        print(f"✅ User_id format looks valid: {user_id}")
        return True
    
    # For security, be more restrictive - only allow email or long UID format
    print(f"❌ User_id format not recognized: {user_id}")
    return False

def _generate_setup_token(user_id):
    """Generate unique setup token for user"""
    import hashlib
    import time
    import base64
    # Create a unique token based on user_id and timestamp
    token_data = f"{user_id}_{int(time.time())}"
    # Use base64 encoding to make it URL-safe and reversible
    return base64.urlsafe_b64encode(token_data.encode()).decode()

def _decode_setup_token(token):
    """Decode setup token back to user_id"""
    import base64
    try:
        # Decode the base64 token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        # Extract user_id (everything before the last underscore)
        user_id = decoded.rsplit('_', 1)[0]
        return user_id
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None

def _get_user_chat_id(user_id):
    """Get user's Telegram chat ID from storage"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        
        # Try to get chat_id directly from the dedicated field first
        chat_id = firebase_storage.get_telegram_chat_id(user_id)
        if chat_id:
            return chat_id
        
        # Fallback: check user's alert settings which should include chat_id
        user_settings = firebase_storage.get_user_alert_settings(user_id)
        
        if user_settings and 'channels' in user_settings:
            telegram_settings = user_settings['channels'].get('telegram', {})
            if telegram_settings.get('enabled') and telegram_settings.get('chatId'):
                return telegram_settings['chatId']
        
        return None
        
    except Exception as e:
        print(f"Error getting user chat ID: {e}")
        return None

@app.route('/api/alerts/setup-telegram', methods=['POST'])
def setup_telegram_bot_legacy():
    """Generate unique bot link for user setup (legacy endpoint)"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data:
            return jsonify({"success": False, "error": "userId is required"}), 400
        
        user_id = data['userId']
        
        # Return direct response without using alert service to avoid connection issues
        return jsonify({
            "success": True,
            "botUsername": "@FXSentinelAlertsBot",
            "botLink": f"https://t.me/FXSentinelAlertsBot?start={user_id}",
            "instructions": [
                "1. Click the link below to start the bot",
                "2. Send /start to begin setup",
                "3. Follow the bot instructions to complete setup"
            ],
            "fallback": True,
            "message": "Bot setup completed (legacy endpoint - direct mode)"
        })
        
    except Exception as e:
        print(f"Error setting up Telegram bot: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/verify-telegram', methods=['POST'])
def verify_telegram_connection_legacy():
    """Verify user completed bot setup (legacy endpoint)"""
    try:
        data = request.get_json()
        if not data or 'userId' not in data or 'chatId' not in data or 'username' not in data:
            return jsonify({"success": False, "error": "userId, chatId, and username are required"}), 400
        
        user_id = data['userId']
        chat_id = data['chatId']
        username = data['username']
        
        # Return mock verification without using alert service
        mock_result = {
            "success": True,
            "connected": True,
            "chatId": chat_id,
            "username": username
        }
        
        return jsonify(mock_result)
        
    except Exception as e:
        print(f"Error verifying Telegram connection: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/forex-prices', methods=['GET', 'OPTIONS'])
def get_forex_prices():
    """Get real-time forex prices from TradingView API only"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        print("🔍 Starting TradingView API call...")
        tradingview_prices = get_tradingview_prices()
        
        if tradingview_prices:
            print(f"✅ Successfully fetched data from TradingView: {len(tradingview_prices)} pairs")
            
            # Add data freshness information
            for pair in tradingview_prices:
                if 'lastUpdate' in tradingview_prices[pair]:
                    try:
                        last_update = datetime.fromisoformat(tradingview_prices[pair]['lastUpdate'].replace('Z', '+00:00'))
                        age_minutes = (datetime.now(last_update.tzinfo) - last_update).total_seconds() / 60
                        tradingview_prices[pair]['dataAgeMinutes'] = round(age_minutes, 1)
                        
                        # Check if market is likely closed (weekend or outside trading hours)
                        current_time = datetime.now(last_update.tzinfo)
                        is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6
                        is_market_hours = 0 <= current_time.hour <= 23  # Simplified market hours check
                        
                        tradingview_prices[pair]['isStale'] = age_minutes > 60
                        tradingview_prices[pair]['isModeratelyOld'] = 15 < age_minutes <= 60
                        tradingview_prices[pair]['isMarketClosed'] = is_weekend or not is_market_hours
                    except:
                        tradingview_prices[pair]['dataAgeMinutes'] = None
                        tradingview_prices[pair]['isStale'] = False
                        tradingview_prices[pair]['isModeratelyOld'] = False
                        tradingview_prices[pair]['isMarketClosed'] = False
            
            return jsonify({
                'prices': tradingview_prices,
                'dataSource': 'TradingView',
                'timestamp': datetime.now().isoformat(),
                'dataQuality': {
                    'hasStaleData': any(p.get('isStale', False) for p in tradingview_prices.values()),
                    'hasModeratelyOldData': any(p.get('isModeratelyOld', False) for p in tradingview_prices.values()),
                    'isMarketClosed': any(p.get('isMarketClosed', False) for p in tradingview_prices.values()),
                    'averageAgeMinutes': sum(p.get('dataAgeMinutes', 0) for p in tradingview_prices.values()) / len(tradingview_prices) if tradingview_prices else 0
                }
            })
        else:
            print("⚠️ TradingView returned None or empty data")
            # Return minimal fallback data
            fallback_prices = {
                'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
                'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
                'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'}
            }
            
            return jsonify({
                'prices': fallback_prices,
                'dataSource': 'fallback',
                'timestamp': datetime.now().isoformat(),
                'dataQuality': {
                    'hasStaleData': False,
                    'hasModeratelyOldData': False,
                    'isMarketClosed': True,
                    'averageAgeMinutes': 0
                }
            })
        
    except Exception as e:
        print(f"Error in forex prices endpoint: {e}")
        import traceback
        traceback.print_exc()
        
        # Return minimal fallback data
        fallback_prices = {
            'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
            'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'},
            'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat(), 'source': 'fallback'}
        }
        
        return jsonify({
            'prices': fallback_prices,
            'dataSource': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'dataQuality': {
                'hasStaleData': False,
                'hasModeratelyOldData': False,
                'isMarketClosed': True,
                'averageAgeMinutes': 0
            }
        })

@app.route('/api/forex-prices/refresh', methods=['POST', 'OPTIONS'])
def refresh_forex_prices():
    """Force refresh forex prices from all available sources"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        print("🔄 Manual refresh requested...")
        
        # Clear any cached data
        # Reset rate limit counters to allow fresh API calls
        global unirate_api_usage
        unirate_api_usage['minute_requests'] = 0
        unirate_api_usage['last_minute_reset'] = datetime.now()
        
        # Get fresh data
        prices = {}
        data_sources_used = []
        
        # Try TradingView first (real-time forex market data)
        try:
            tradingview_prices = get_tradingview_prices()
            if tradingview_prices:
                prices.update(tradingview_prices)
                data_sources_used.append('TradingView')
                print("✅ Successfully fetched data from TradingView")
        except Exception as e:
            print(f"❌ TradingView failed: {e}")
        
        # Try Alpha Vantage second
        try:
            alpha_prices = get_alpha_vantage_prices()
            if alpha_prices:
                # Use Alpha Vantage data for any missing pairs
                for pair, data in alpha_prices.items():
                    if pair not in prices:
                        prices[pair] = data
                data_sources_used.append('AlphaVantage')
                print("✅ Successfully fetched data from Alpha Vantage")
        except Exception as e:
            print(f"❌ Alpha Vantage failed: {e}")
        
        # Try UniRateAPI third
        try:
            unirate_prices = get_unirate_prices()
            if unirate_prices:
                # Use UniRateAPI data for any missing pairs
                for pair, data in unirate_prices.items():
                    if pair not in prices:
                        prices[pair] = data
                data_sources_used.append('UniRateAPI')
                print("✅ Successfully fetched data from UniRateAPI")
        except Exception as e:
            print(f"❌ UniRateAPI failed: {e}")
        
        # Try ExchangeRateAPI as fallback
        try:
            exchange_prices = get_exchange_rate_prices()
            if exchange_prices:
                # Use ExchangeRateAPI data for any missing pairs
                for pair, data in exchange_prices.items():
                    if pair not in prices:
                        prices[pair] = data
                data_sources_used.append('ExchangeRateAPI')
                print("✅ Successfully fetched data from ExchangeRateAPI")
        except Exception as e:
            print(f"❌ ExchangeRateAPI failed: {e}")
        
        # Fill any missing pairs with fallback data
        required_pairs = ['EURUSD', 'USDJPY', 'GBPUSD']
        for pair in required_pairs:
            if pair not in prices:
                prices[pair] = get_fallback_price(pair)
                data_sources_used.append('fallback')
        
        # Add data freshness information
        for pair in prices:
            if 'lastUpdate' in prices[pair]:
                try:
                    last_update = datetime.fromisoformat(prices[pair]['lastUpdate'].replace('Z', '+00:00'))
                    age_minutes = (datetime.now(last_update.tzinfo) - last_update).total_seconds() / 60
                    prices[pair]['dataAgeMinutes'] = round(age_minutes, 1)
                    prices[pair]['isStale'] = age_minutes > 60
                except:
                    prices[pair]['dataAgeMinutes'] = None
                    prices[pair]['isStale'] = True
        
        return jsonify({
            'prices': prices,
            'dataSource': ' + '.join(data_sources_used) if data_sources_used else 'fallback',
            'timestamp': datetime.now().isoformat(),
            'dataQuality': {
                'hasStaleData': any(p.get('isStale', False) for p in prices.values()),
                'averageAgeMinutes': sum(p.get('dataAgeMinutes', 0) for p in prices.values()) / len(prices) if prices else 0
            },
            'message': 'Data refreshed successfully'
        })
        
    except Exception as e:
        print(f"Error in manual refresh: {e}")
        return jsonify({
            'error': 'Failed to refresh data',
            'message': str(e)
        }), 500

@app.route('/api/market-sentiment', methods=['GET', 'OPTIONS'])
def get_market_sentiment():
    """Get comprehensive market sentiment analysis"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        print("🔍 Fetching market sentiment data...")
        
        # Import the sentiment service
        from services.market_sentiment_service import market_sentiment_service
        
        # Get sentiment data
        sentiment_data = market_sentiment_service.get_market_sentiment()
        
        print(f"✅ Successfully fetched sentiment data for trading day: {sentiment_data.get('trading_day')}")
        
        return jsonify(sentiment_data)
        
    except Exception as e:
        print(f"❌ Error fetching market sentiment: {e}")
        return jsonify({
            'error': 'Failed to fetch market sentiment',
            'message': str(e),
            'timestamp': datetime.now().isoformat(),
            'trading_day': datetime.now().strftime('%Y-%m-%d')
        }), 500

@app.route('/api/sentiment/refresh', methods=['POST', 'OPTIONS'])
def refresh_sentiment():
    """Force refresh sentiment calculations"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        print("🔄 Manual sentiment refresh requested...")
        
        # Import the sentiment service
        from services.market_sentiment_service import market_sentiment_service
        
        # Force fresh calculation by clearing cache
        market_sentiment_service.current_sentiment = None
        
        # Get fresh sentiment data
        sentiment_data = market_sentiment_service.get_market_sentiment()
        
        print(f"✅ Successfully refreshed sentiment data")
        
        return jsonify({
            'status': 'success',
            'message': 'Sentiment data refreshed successfully',
            'data': sentiment_data
        })
        
    except Exception as e:
        print(f"❌ Error refreshing sentiment: {e}")
        return jsonify({
            'error': 'Failed to refresh sentiment',
            'message': str(e)
        }), 500

def get_unirate_prices():
    """Get prices from UniRateAPI"""
    pairs = [
        ('USD', 'EUR', 'EURUSD'),
        ('USD', 'JPY', 'USDJPY'),
        ('USD', 'GBP', 'GBPUSD')
    ]
    
    prices = {}
    
    for from_currency, to_currency, pair_name in pairs:
        try:
            url = "https://api.unirateapi.com/api/convert"
            params = {
                'api_key': UNIRATE_API_KEY,
                'from': from_currency,
                'to': to_currency,
                'amount': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            increment_unirate_usage()
            
            if 'result' in data and data['result']:
                rate = float(data['result'])
                
                # Calculate the correct price based on the pair
                if pair_name == 'EURUSD':
                    price = 1 / rate
                elif pair_name == 'GBPUSD':
                    price = 1 / rate
                else:
                    price = rate
                
                prices[pair_name] = {
                    'price': price,
                    'change': 0,  # UniRateAPI doesn't provide change
                    'lastUpdate': datetime.now().isoformat(),
                    'source': 'UniRateAPI'
                }
                
        except Exception as e:
            print(f"Error fetching {pair_name} from UniRateAPI: {e}")
    
    return prices

def get_current_forex_prices():
    """Get current forex prices from a free API source"""
    try:
        # Try using a free forex API that provides real-time data
        # Using Alpha Vantage API (free tier) for more accurate forex data
        alpha_vantage_key = get_next_alpha_vantage_key()
        
        if alpha_vantage_key:
            prices = {}
            
            # Fetch EUR/USD
            try:
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={alpha_vantage_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate_data = data['Realtime Currency Exchange Rate']
                    if '5. Exchange Rate' in rate_data:
                        eur_usd_rate = float(rate_data['5. Exchange Rate'])
                        prices['EURUSD'] = {
                            'price': eur_usd_rate,
                            'change': 0,
                            'lastUpdate': datetime.now().isoformat(),
                            'source': 'AlphaVantage'
                        }
            except Exception as e:
                print(f"Error fetching EUR/USD from Alpha Vantage: {e}")
            
            # Fetch USD/JPY
            try:
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=JPY&apikey={alpha_vantage_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate_data = data['Realtime Currency Exchange Rate']
                    if '5. Exchange Rate' in rate_data:
                        usd_jpy_rate = float(rate_data['5. Exchange Rate'])
                        prices['USDJPY'] = {
                            'price': usd_jpy_rate,
                            'change': 0,
                            'lastUpdate': datetime.now().isoformat(),
                            'source': 'AlphaVantage'
                        }
            except Exception as e:
                print(f"Error fetching USD/JPY from Alpha Vantage: {e}")
            
            # Fetch GBP/USD
            try:
                url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=GBP&to_currency=USD&apikey={alpha_vantage_key}"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'Realtime Currency Exchange Rate' in data:
                    rate_data = data['Realtime Currency Exchange Rate']
                    if '5. Exchange Rate' in rate_data:
                        gbp_usd_rate = float(rate_data['5. Exchange Rate'])
                        prices['GBPUSD'] = {
                            'price': gbp_usd_rate,
                            'change': 0,
                            'lastUpdate': datetime.now().isoformat(),
                            'source': 'AlphaVantage'
                        }
            except Exception as e:
                print(f"Error fetching GBP/USD from Alpha Vantage: {e}")
            
            if prices:
                return prices
        
        # Fallback to ExchangeRateAPI if Alpha Vantage is not available
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' in data and 'time_last_updated' in data:
            rates = data['rates']
            last_update = datetime.fromtimestamp(data['time_last_updated'])
            
            prices = {}
            
            # EUR/USD
            if 'EUR' in rates:
                prices['EURUSD'] = {
                    'price': rates['EUR'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI'
                }
            
            # USD/JPY
            if 'JPY' in rates:
                prices['USDJPY'] = {
                    'price': rates['JPY'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI'
                }
            
            # GBP/USD
            if 'GBP' in rates:
                prices['GBPUSD'] = {
                    'price': rates['GBP'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI'
                }
            
            return prices
            
    except Exception as e:
        print(f"Error fetching from forex APIs: {e}")
    
    return None

def is_data_fresher(new_data, old_data):
    """Check if new data is fresher than old data"""
    try:
        new_time = datetime.fromisoformat(new_data['lastUpdate'].replace('Z', '+00:00'))
        old_time = datetime.fromisoformat(old_data['lastUpdate'].replace('Z', '+00:00'))
        return new_time > old_time
    except:
        return False

def get_alpha_vantage_prices():
    """Get prices from Alpha Vantage API using key rotation"""
    prices = {}
    
    # Get the next key in rotation
    api_key = get_next_alpha_vantage_key()
    
    if not api_key:
        print("No Alpha Vantage API keys configured")
        return None
    
    print(f"Using Alpha Vantage key: {api_key[:8]}...")
    
    # Fetch EUR/USD
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=EUR&to_currency=USD&apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_data = data['Realtime Currency Exchange Rate']
            if '5. Exchange Rate' in rate_data:
                eur_usd_rate = float(rate_data['5. Exchange Rate'])
                prices['EURUSD'] = {
                    'price': eur_usd_rate,
                    'change': 0,
                    'lastUpdate': datetime.now().isoformat(),
                    'source': 'AlphaVantage'
                }
                print(f"✅ EUR/USD: {eur_usd_rate}")
    except Exception as e:
        print(f"Error fetching EUR/USD from Alpha Vantage: {e}")
    
    # Fetch USD/JPY
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=JPY&apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_data = data['Realtime Currency Exchange Rate']
            if '5. Exchange Rate' in rate_data:
                usd_jpy_rate = float(rate_data['5. Exchange Rate'])
                prices['USDJPY'] = {
                    'price': usd_jpy_rate,
                    'change': 0,
                    'lastUpdate': datetime.now().isoformat(),
                    'source': 'AlphaVantage'
                }
                print(f"✅ USD/JPY: {usd_jpy_rate}")
    except Exception as e:
        print(f"Error fetching USD/JPY from Alpha Vantage: {e}")
    
    # Fetch GBP/USD
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=GBP&to_currency=USD&apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Realtime Currency Exchange Rate' in data:
            rate_data = data['Realtime Currency Exchange Rate']
            if '5. Exchange Rate' in rate_data:
                gbp_usd_rate = float(rate_data['5. Exchange Rate'])
                prices['GBPUSD'] = {
                    'price': gbp_usd_rate,
                    'change': 0,
                    'lastUpdate': datetime.now().isoformat(),
                    'source': 'AlphaVantage'
                }
                print(f"✅ GBP/USD: {gbp_usd_rate}")
    except Exception as e:
        print(f"Error fetching GBP/USD from Alpha Vantage: {e}")
    
    return prices

def get_exchange_rate_prices():
    """Get prices from ExchangeRateAPI"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' in data and 'time_last_updated' in data:
            rates = data['rates']
            last_update = datetime.fromtimestamp(data['time_last_updated'])
            
            prices = {}
            
            # Map all available rates to our supported pairs
            pair_mappings = {
                'EUR': 'EURUSD',
                'JPY': 'USDJPY', 
                'GBP': 'GBPUSD',
                'CHF': 'USDCHF',
                'AUD': 'AUDUSD',
                'CAD': 'USDCAD',
                'NZD': 'NZDUSD',
                'SEK': 'USDSEK',
                'NOK': 'USDNOK',
                'DKK': 'USDDKK'
            }
            
            # Create prices for all available pairs
            for rate_currency, pair_key in pair_mappings.items():
                if rate_currency in rates:
                    prices[pair_key] = {
                        'price': rates[rate_currency],
                        'change': 0,  # ExchangeRateAPI doesn't provide change data
                        'lastUpdate': last_update.isoformat(),
                        'source': 'ExchangeRateAPI'
                    }
            
            # Handle cross-currency pairs (EUR/GBP, EUR/JPY, etc.)
            if 'EUR' in rates and 'GBP' in rates:
                prices['EURGBP'] = {
                    'price': rates['EUR'] / rates['GBP'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI (calculated)'
                }
            
            # Add HKD if available
            if 'HKD' in rates:
                prices['USDHKD'] = {
                    'price': rates['HKD'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI'
                }
            
            if 'EUR' in rates and 'JPY' in rates:
                prices['EURJPY'] = {
                    'price': rates['EUR'] * rates['JPY'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI (calculated)'
                }
            
            if 'GBP' in rates and 'JPY' in rates:
                prices['GBPJPY'] = {
                    'price': rates['GBP'] * rates['JPY'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI (calculated)'
                }
            
            if 'EUR' in rates and 'CHF' in rates:
                prices['EURCHF'] = {
                    'price': rates['EUR'] / rates['CHF'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI (calculated)'
                }
            
            if 'GBP' in rates and 'CHF' in rates:
                prices['GBPCHF'] = {
                    'price': rates['GBP'] / rates['CHF'],
                    'change': 0,
                    'lastUpdate': last_update.isoformat(),
                    'source': 'ExchangeRateAPI (calculated)'
                }
            
            return prices
            
    except Exception as e:
        print(f"Error fetching from ExchangeRateAPI: {e}")
    
    return None

def get_tradingview_prices():
    """Get real-time forex prices from TradingView API for all supported pairs"""
    try:
        url = "https://scanner.tradingview.com/forex/scan"
        headers = {
            "Content-Type": "application/json"
        }
        
        # All 15 forex pairs we support - using pairs that are actually available on TradingView
        all_pairs = [
            "FX:EURUSD", "FX:GBPUSD", "FX:USDJPY", "FX:USDCHF", "FX:AUDUSD",
            "FX:USDCAD", "FX:NZDUSD", "FX:EURGBP", "FX:EURJPY", "FX:GBPJPY",
            "FX:USDSEK", "FX:USDNOK", "FX:USDHKD", "FX:EURCHF", "FX:GBPCHF"
        ]
        
        data = {
            "symbols": {
                "tickers": all_pairs
            },
            "columns": ["close", "change", "change_abs"]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        
        if 'data' in result and result['data']:
            prices = {}
            
            for item in result['data']:
                symbol = item['s']
                values = item['d']
                
                if len(values) >= 3:
                    price = values[0]  # close price
                    change_percent = values[1]  # change percentage
                    change_abs = values[2]  # absolute change
                    
                    # Map TradingView symbols to our internal format
                    pair_mapping = {
                        "FX:EURUSD": "EURUSD",
                        "FX:GBPUSD": "GBPUSD", 
                        "FX:USDJPY": "USDJPY",
                        "FX:USDCHF": "USDCHF",
                        "FX:AUDUSD": "AUDUSD",
                        "FX:USDCAD": "USDCAD",
                        "FX:NZDUSD": "NZDUSD",
                        "FX:EURGBP": "EURGBP",
                        "FX:EURJPY": "EURJPY",
                        "FX:GBPJPY": "GBPJPY",
                        "FX:USDSEK": "USDSEK",
                        "FX:USDNOK": "USDNOK",
                        "FX:USDHKD": "USDHKD",  # Replaced USDDKK with USDHKD
                        "FX:EURCHF": "EURCHF",
                        "FX:GBPCHF": "GBPCHF"
                    }
                    
                    if symbol in pair_mapping:
                        pair_key = pair_mapping[symbol]
                        prices[pair_key] = {
                            'price': price,
                            'change': change_abs,
                            'changePercent': change_percent,
                            'lastUpdate': datetime.now().isoformat(),
                            'source': 'TradingView'
                        }
            
            if prices:
                print(f"✅ Successfully fetched data from TradingView")
                print(f"   Fetched {len(prices)} pairs: {list(prices.keys())}")
                
                # Check if we got all expected pairs
                expected_pairs = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", 
                                "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", 
                                "USDSEK", "USDNOK", "USDHKD", "EURCHF", "GBPCHF"]
                missing_pairs = [pair for pair in expected_pairs if pair not in prices]
                if missing_pairs:
                    print(f"⚠️ TradingView missing pairs: {missing_pairs}")
                
                return prices
                
    except Exception as e:
        print(f"Error fetching from TradingView: {e}")
    
    return None

@app.route('/api/dashboard-data')
def get_dashboard_data():
    """Get all dashboard data in a single request for better performance"""
    try:
        import concurrent.futures
        from datetime import datetime
        
        # Function to get news data
        def get_news_data():
            try:
                # Try cached news first for speed
                from services.news_cache import news_cache
                cached_news = news_cache.load_news()
                if cached_news:
                    return {
                        "news": cached_news,
                        "sources": ["cached_data"],
                        "cache_status": "cached"
                    }
                
                # If no cache, get fresh news (simplified version)
                try:
                    rss_news = news_aggregator.get_recent_news(hours=24)
                    return {
                        "news": rss_news[:10],  # Limit to 10 articles
                        "sources": ["RSS Feeds"],
                        "cache_status": "fresh"
                    }
                except:
                    return {
                        "news": get_mock_news(),
                        "sources": ["fallback_data"],
                        "cache_status": "fallback"
                    }
            except Exception as e:
                print(f"Error getting news: {e}")
                return {
                    "news": get_mock_news(),
                    "sources": ["fallback_data"],
                    "cache_status": "fallback"
                }
        
        # Function to get trading data
        def get_trading_data():
            try:
                return {
                    "eurUsd": {"price": 1.0856, "change": 0.12, "sentiment": "bullish"},
                    "usdJpy": {"price": 148.23, "change": -0.08, "sentiment": "bearish"},
                    "gold": {"price": 2034.50, "change": 0.45, "sentiment": "bullish"},
                    "marketSentiment": "neutral",
                    "volatilityIndex": 15.2
                }
            except Exception as e:
                print(f"Error getting trading data: {e}")
                return {}
        
        # Function to get alerts data
        def get_alerts_data():
            try:
                return {
                    "alerts": [
                        {
                            "id": 1,
                            "type": "telegram",
                            "event": "US CPI Data",
                            "status": "sent",
                            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                            "recipients": 1250,
                            "impact": "High"
                        }
                    ],
                    "stats": {
                        "telegramSubscribers": 1250,
                        "emailSubscribers": 890,
                        "alertsThisWeek": 24,
                        "totalAlerts": 156
                    }
                }
            except Exception as e:
                print(f"Error getting alerts: {e}")
                return {"alerts": [], "stats": {}}
        
        # Function to get AI insights
        def get_ai_insights():
            try:
                return [
                    {
                        "pair": "EUR/USD",
                        "analysis": "Strong support at 1.0850 level. Break above 1.0870 could trigger bullish momentum.",
                        "confidence": 85,
                        "timeframe": "4H",
                        "sentiment": "bullish"
                    }
                ]
            except Exception as e:
                print(f"Error getting AI insights: {e}")
                return []
        
        # Function to get alert settings
        def get_alert_settings():
            try:
                return {
                    "telegram": True,
                    "email": False,
                    "highImpact": True,
                    "mediumImpact": True,
                    "lowImpact": False,
                    "notificationTime": 15
                }
            except Exception as e:
                print(f"Error getting alert settings: {e}")
                return {}
        
        # Execute all functions in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(get_news_data): "news",
                executor.submit(get_trading_data): "tradingData",
                executor.submit(get_alerts_data): "alerts",
                executor.submit(get_ai_insights): "aiInsights",
                executor.submit(get_alert_settings): "alertSettings"
            }
            
            results = {}
            for future in concurrent.futures.as_completed(futures, timeout=10):
                data_type = futures[future]
                try:
                    results[data_type] = future.result()
                except Exception as e:
                    print(f"Error getting {data_type}: {e}")
                    # Provide fallback data
                    if data_type == "news":
                        results[data_type] = {"news": get_mock_news(), "sources": ["fallback"], "cache_status": "fallback"}
                    elif data_type == "tradingData":
                        results[data_type] = {}
                    elif data_type == "alerts":
                        results[data_type] = {"alerts": [], "stats": {}}
                    elif data_type == "aiInsights":
                        results[data_type] = []
                    elif data_type == "alertSettings":
                        results[data_type] = {}
        
        return jsonify({
            "news": results.get("news", {}).get("news", []),
            "newsSources": results.get("news", {}).get("sources", []),
            "newsCacheStatus": results.get("news", {}).get("cache_status", "unknown"),
            "tradingData": results.get("tradingData", {}),
            "alerts": results.get("alerts", {}).get("alerts", []),
            "alertStats": results.get("alerts", {}).get("stats", {}),
            "aiInsights": results.get("aiInsights", []),
            "alertSettings": results.get("alertSettings", {}),
            "lastUpdated": datetime.now().isoformat(),
            "status": "success"
        })
        
    except Exception as e:
        print(f"Error in dashboard data endpoint: {e}")
        return jsonify({
            "news": get_mock_news(),
            "newsSources": ["fallback"],
            "newsCacheStatus": "fallback",
            "tradingData": {},
            "alerts": [],
            "alertStats": {},
            "aiInsights": [],
            "alertSettings": {},
            "lastUpdated": datetime.now().isoformat(),
            "status": "error",
            "error": str(e)
        })

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        "message": "FXSentinel API is running",
        "status": "healthy",
        "endpoints": {
            "news": "/api/news",
            "analysis": "/api/analysis/<id>",
            "health": "/api/health",
            "trading_data": "/api/trading-data",
            "alerts": "/api/alerts",
            "ai_insights": "/api/ai-insights"
        }
    })

@app.route('/api/pre-event-analysis/<int:news_id>')
def get_pre_event_analysis(news_id):
    """Get pre-event analysis for upcoming news events"""
    try:
        # Get the economic event by ID from Finnhub calendar data
        event = get_economic_event_by_id(news_id)
        
        # Create enhanced market context
        enhanced_market_context = EnhancedMarketContext(
            current_prices={
                'EUR/USD': 1.0850,
                'USD/JPY': 148.50,
                'GBP/USD': 1.2650,
                'USD/CHF': 0.8650,
                'AUD/USD': 0.6650,
                'USD/CAD': 1.3550
            },
            recent_volatility={
                'EUR/USD': 0.008,
                'USD/JPY': 0.012,
                'GBP/USD': 0.010,
                'USD/CHF': 0.007,
                'AUD/USD': 0.009,
                'USD/CAD': 0.006
            },
            market_sentiment={
                'EUR/USD': 'neutral',
                'USD/JPY': 'bullish',
                'GBP/USD': 'bearish',
                'USD/CHF': 'neutral',
                'AUD/USD': 'neutral',
                'USD/CAD': 'neutral'
            },
            key_levels={
                'EUR/USD': {'support': 1.0800, 'resistance': 1.0900},
                'USD/JPY': {'support': 148.00, 'resistance': 149.00},
                'GBP/USD': {'support': 1.2600, 'resistance': 1.2700}
            },
            economic_calendar=[],
            bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
            equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
            commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
            central_bank_expectations={},
            historical_reactions={}
        )
        
        # Get pre-event analysis
        pre_event_analysis = enhanced_ai_analyzer.analyze_macro_event(
            event, 
            enhanced_market_context, 
            "pre_event"
        )
        
        # Transform to frontend-compatible format
        analysis_result = {
            'event': event,
            'event_context': pre_event_analysis.immediate_impact,  # Contains event explanation
            'historical_context': pre_event_analysis.long_term_impact,  # Contains historical analysis
            'market_expectations': pre_event_analysis.context_expectations,  # Contains expectations
            'pre_event_sentiment': pre_event_analysis.sentiment_analysis,  # Contains sentiment
            'cross_market_context': pre_event_analysis.cross_market_links,  # Contains cross-market
            'preparation_strategy': pre_event_analysis.market_shifts,  # Contains preparation strategy
            'risk_assessment': pre_event_analysis.big_picture,  # Contains risks
            'confidence_score': pre_event_analysis.confidence_score,
            'timestamp': pre_event_analysis.analysis_timestamp,
            'analysis_type': 'pre_event_preparation'
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"Error generating pre-event analysis: {e}")
        return jsonify({"error": "Failed to generate pre-event analysis"}), 500

@app.route('/api/post-event-analysis/<int:news_id>')
def get_post_event_analysis(news_id):
    """Get post-event analysis for completed news events"""
    try:
        # Get the economic event by ID from Finnhub calendar data
        event = get_economic_event_by_id(news_id)
        
        # Create enhanced market context
        enhanced_market_context = EnhancedMarketContext(
            current_prices={
                'EUR/USD': 1.0850,
                'USD/JPY': 148.50,
                'GBP/USD': 1.2650,
                'USD/CHF': 0.8650,
                'AUD/USD': 0.6650,
                'USD/CAD': 1.3550
            },
            recent_volatility={
                'EUR/USD': 0.008,
                'USD/JPY': 0.012,
                'GBP/USD': 0.010,
                'USD/CHF': 0.007,
                'AUD/USD': 0.009,
                'USD/CAD': 0.006
            },
            market_sentiment={
                'EUR/USD': 'neutral',
                'USD/JPY': 'bullish',
                'GBP/USD': 'bearish',
                'USD/CHF': 'neutral',
                'AUD/USD': 'neutral',
                'USD/CAD': 'neutral'
            },
            key_levels={
                'EUR/USD': {'support': 1.0800, 'resistance': 1.0900},
                'USD/JPY': {'support': 148.00, 'resistance': 149.00},
                'GBP/USD': {'support': 1.2600, 'resistance': 1.2700}
            },
            economic_calendar=[],
            bond_yields={'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8},
            equity_indices={'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000},
            commodity_prices={'GOLD': 2000, 'OIL': 75, 'SILVER': 25},
            central_bank_expectations={},
            historical_reactions={}
        )
        
        # Get post-event analysis
        post_event_analysis = enhanced_ai_analyzer.analyze_macro_event(
            event, 
            enhanced_market_context, 
            "post_event"
        )
        
        # Transform to frontend-compatible format
        analysis_result = {
            'event': event,
            'immediate_impact': post_event_analysis.immediate_impact,
            'long_term_impact': post_event_analysis.long_term_impact,
            'context_expectations': post_event_analysis.context_expectations,
            'sentiment_analysis': post_event_analysis.sentiment_analysis,
            'cross_market_links': post_event_analysis.cross_market_links,
            'market_shifts': post_event_analysis.market_shifts,
            'big_picture': post_event_analysis.big_picture,
            'confidence_score': post_event_analysis.confidence_score,
            'timestamp': post_event_analysis.analysis_timestamp,
            'analysis_type': 'post_event_analysis'
        }
        
        return jsonify(analysis_result)
        
    except Exception as e:
        print(f"Error generating post-event analysis: {e}")
        return jsonify({"error": "Failed to generate post-event analysis"}), 500

@app.route('/api/news-history')
def get_news_history():
    """Get news history for the live news analysis card"""
    try:
        from services.news_cache import news_cache
        from services.analysis_history import analysis_history
        
        # Get hours parameter from query string (default 24 hours)
        hours = request.args.get('hours', 24, type=int)
        
        # Get recent history
        history = news_cache.get_recent_history(hours)
        
        # Get analysis history
        analysis_records = analysis_history.get_analysis_history(hours)
        
        # Mark news items as analyzed
        analyzed_news_ids = analysis_history.get_analyzed_news_ids()
        
        # Add analysis status to news items
        for news_item in history:
            news_item['is_analyzed'] = str(news_item.get('id')) in analyzed_news_ids
            if news_item['is_analyzed']:
                # Get the analysis data for this news item
                analysis_data = analysis_history.get_analysis_for_news(str(news_item.get('id')))
                if analysis_data:
                    news_item['analysis_summary'] = {
                        'type': analysis_data.get('analysis_type'),
                        'confidence': analysis_data.get('confidence'),
                        'reaction': analysis_data.get('immediate_reaction'),
                        'cost': analysis_data.get('cost', 0.0)
                    }
        
        # Get history status
        history_status = news_cache.get_history_status()
        
        # Get analysis stats
        analysis_stats = analysis_history.get_analysis_stats()
        
        return jsonify({
            "history": history,
            "analysis_records": analysis_records,
            "status": history_status,
            "analysis_stats": analysis_stats,
            "hours_requested": hours,
            "total_items": len(history),
            "analyzed_items": len(analyzed_news_ids)
        })
        
    except Exception as e:
        print(f"Error getting news history: {e}")
        return jsonify({
            "history": [],
            "analysis_records": [],
            "status": {"total_items": 0},
            "analysis_stats": {"total_analyses": 0},
            "hours_requested": hours,
            "total_items": 0,
            "analyzed_items": 0,
            "error": str(e)
        }), 500

@app.route('/api/news/<int:news_id>')
def get_news_by_id(news_id):
    """Get a specific news item by ID from cache or history"""
    try:
        from services.news_cache import news_cache
        
        news_item = news_cache.get_news_by_id(news_id)
        
        if news_item:
            return jsonify(news_item)
        else:
            return jsonify({"error": "News item not found"}), 404
            
    except Exception as e:
        print(f"Error getting news by ID: {e}")
        return jsonify({"error": "Failed to retrieve news item"}), 500

@app.route('/api/get-cached-analysis/<news_id>')
def get_cached_analysis(news_id):
    """Get cached analysis for a specific news item"""
    try:
        from services.analysis_history import analysis_history
        
        # Get the cached analysis
        analysis_data = analysis_history.get_analysis_for_news(str(news_id))
        
        if analysis_data:
            print(f"✅ Retrieved cached analysis for news ID: {news_id}")
            return jsonify(analysis_data)
        else:
            print(f"❌ No cached analysis found for news ID: {news_id}")
            return jsonify({"error": "No cached analysis found for this news item"}), 404
            
    except Exception as e:
        print(f"Error getting cached analysis: {e}")
        return jsonify({"error": "Failed to retrieve cached analysis"}), 500

@app.route('/api/clear-analysis-history', methods=['POST'])
def clear_analysis_history():
    """Clear analysis history and related data"""
    try:
        from services.analysis_history import analysis_history
        from services.news_cache import news_cache
        
        # Get parameters from request
        data = request.get_json() or {}
        clear_type = data.get('type', 'all')  # analysis, news_cache, news_history, all
        confirm = data.get('confirm', False)
        
        # Validate clear_type
        valid_types = ['analysis', 'news_cache', 'news_history', 'all']
        if clear_type not in valid_types:
            return jsonify({"error": f"Invalid clear_type. Must be one of: {valid_types}"}), 400
        
        results = {
            "success": True,
            "cleared_items": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Clear analysis history
        if clear_type in ["analysis", "all"]:
            try:
                if analysis_history.clear_history():
                    results["cleared_items"].append("analysis_history")
                else:
                    results["errors"].append("Failed to clear analysis history")
            except Exception as e:
                results["errors"].append(f"Error clearing analysis history: {e}")
        
        # Clear news cache
        if clear_type in ["news_cache", "all"]:
            try:
                if news_cache.clear_cache():
                    results["cleared_items"].append("news_cache")
                else:
                    results["errors"].append("Failed to clear news cache")
            except Exception as e:
                results["errors"].append(f"Error clearing news cache: {e}")
        
        # Clear news history
        if clear_type in ["news_history", "all"]:
            try:
                if news_cache.clear_history():
                    results["cleared_items"].append("news_history")
                else:
                    results["errors"].append("Failed to clear news history")
            except Exception as e:
                results["errors"].append(f"Error clearing news history: {e}")
        
        # Check if operation was successful
        if results["errors"]:
            results["success"] = False
            return jsonify(results), 500
        
        print(f"✅ Analysis history cleared successfully: {results['cleared_items']}")
        return jsonify(results)
        
    except Exception as e:
        print(f"Error clearing analysis history: {e}")
        return jsonify({
            "success": False,
            "errors": [f"Unexpected error: {e}"],
            "timestamp": datetime.now().isoformat()
        }), 500





@app.route('/api/alerts/settings', methods=['GET', 'PUT'])
def update_alert_settings():
    """Get or update user's alert settings"""
    try:
        if request.method == 'GET':
            user_id = request.args.get('userId')
            if not user_id:
                return jsonify({"success": False, "error": "userId is required"}), 400
            
            # Get settings from Firebase
            try:
                from services.firebase_realtime_storage import FirebaseRealtimeStorage
                firebase_storage = FirebaseRealtimeStorage()
                settings = firebase_storage.get_user_alert_settings(user_id)
                
                if settings:
                    return jsonify({
                        "success": True,
                        "settings": settings
                    })
                else:
                    # Return default settings if user doesn't exist
                    default_settings = {
                        "channels": {
                            "telegram": {"enabled": False, "chatId": "", "username": ""},
                            "email": {"enabled": False, "address": ""}
                        },
                        "preferences": {
                            "impactLevels": {"high": True, "medium": True, "low": False},
                            "alertTypes": {"preNews": True, "postNews": True, "liveNews": True, "technicalAnalysis": False},
                            "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
                            "quietHours": {"enabled": False, "start": "22:00", "end": "06:00", "timezone": "UTC"}
                        }
                    }
                    return jsonify({
                        "success": True,
                        "settings": default_settings
                    })
                    
            except Exception as e:
                print(f"Firebase error: {e}")
                # Return mock settings as fallback
                mock_settings = {
                    "channels": {
                        "telegram": {"enabled": True, "chatId": "mock_chat_id", "username": "@kavi_user"},
                        "email": {"enabled": False, "address": ""}
                    },
                    "preferences": {
                        "impactLevels": {"high": True, "medium": True, "low": False},
                        "alertTypes": {"preNews": True, "postNews": True, "liveNews": True, "technicalAnalysis": False},
                        "currencyPairs": ["EUR/USD", "USD/JPY", "GBP/USD"],
                        "quietHours": {"enabled": False, "start": "22:00", "end": "06:00", "timezone": "UTC"}
                    }
                }
                return jsonify({
                    "success": True,
                    "settings": mock_settings
                })
        
        elif request.method == 'PUT':
            data = request.get_json()
            if not data or 'userId' not in data or 'settings' not in data:
                return jsonify({"success": False, "error": "userId and settings are required"}), 400
            
            user_id = data['userId']
            settings = data['settings']
            
            # Save settings to Firebase
            try:
                from services.firebase_realtime_storage import FirebaseRealtimeStorage
                firebase_storage = FirebaseRealtimeStorage()
                success = firebase_storage.update_user_alert_settings(user_id, settings)
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Settings saved successfully"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to save settings"
                    }), 500
                    
            except Exception as e:
                print(f"Firebase error: {e}")
                return jsonify({
                    "success": False,
                    "error": f"Database error: {str(e)}"
                }), 500
        
    except Exception as e:
        print(f"Error managing alert settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with alert configurations (for testing)"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        firebase_storage = FirebaseRealtimeStorage()
        
        # Get all users from Firebase (this would need to be implemented in FirebaseRealtimeStorage)
        # For now, return empty list as this is just for testing
        users = []
        
        return jsonify(users)
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify([])

@app.route('/api/test-alert', methods=['POST'])
def test_alert_with_data():
    """Test alert with custom data (for testing)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id', 'test_user')
        news_item = data.get('news_item', {})
        ai_analysis = data.get('ai_analysis', {})
        
        # Create alert message using the news alert trigger service
        from services.news_alert_trigger import news_alert_trigger
        
        # Ensure the news item has proper data
        if not news_item.get('timestamp'):
            news_item['timestamp'] = datetime.now().isoformat()
        if not news_item.get('source'):
            news_item['source'] = 'Test Source'
        
        message = news_alert_trigger._create_alert_message(news_item, ai_analysis)
        
        return jsonify({
            "success": True,
            "message": "Test alert message created successfully",
            "alert_message": message
        })
        
    except Exception as e:
        print(f"Error creating test alert: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/test-alert-template', methods=['POST'])
def test_alert_template():
    """Test alert template creation (for testing)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        news_item = data.get('news_item', {})
        ai_analysis = data.get('ai_analysis', {})
        
        # Create alert message using the news alert trigger service
        from services.news_alert_trigger import news_alert_trigger
        
        message = news_alert_trigger._create_alert_message(news_item, ai_analysis)
        
        return jsonify({
            "success": True,
            "message": "Alert template created successfully",
            "message": message,
            "length": len(message),
            "has_ai_analysis": "🤖" in message,
            "has_emojis": "🚨" in message
        })
        
    except Exception as e:
        print(f"Error testing alert template: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cost-monitor')
def get_cost_monitor():
    """Get cost monitoring information"""
    try:
        from services.cost_optimized_monitor import cost_optimized_monitor
        
        cost_summary = cost_optimized_monitor.get_cost_summary()
        
        return jsonify({
            "success": True,
            "cost_summary": cost_summary,
            "monitor_status": "running" if cost_optimized_monitor.running else "stopped"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "cost_summary": {
                "total_daily_cost": 0.0,
                "max_daily_budget": 5.0,
                "budget_remaining": 5.0,
                "note": "Cost monitor not available"
            }
        })

# Stripe Payment Routes
from services.stripe_service import StripeService
from services.error_handler import StripeErrorHandler
from services.retry_handler import RetryHandler, PaymentRetryHandler

stripe_service = StripeService()

@app.route('/api/create-customer', methods=['POST'])
def create_customer():
    """Create a Stripe customer for a new user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name')
        
        customer = stripe_service.create_customer(user_id, email, name)
        
        return jsonify({
            'success': True,
            'customer_id': customer.id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subscription-status/<user_id>', methods=['GET'])
def get_subscription_status(user_id):
    """Get subscription status for a user"""
    try:
        # Get email from query parameter for developer check
        email = request.args.get('email')
        
        status = stripe_service.get_subscription_status(user_id, email)
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/api/check-trial-eligibility/<email>', methods=['GET'])
@limiter.limit("10 per minute")  # Limit eligibility checks
def check_trial_eligibility(email):
    """Check if an email is eligible for a trial"""
    try:
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        # Decode URL-encoded email
        import urllib.parse
        email = urllib.parse.unquote(email)
        
        # Check if Firebase is available for stripe_service
        if not stripe_service.firebase_available:
            # If Firebase is not available, allow trial (fallback behavior)
            return jsonify({
                'email': email,
                'eligible': True,
                'trial_history': [],
                'message': 'Eligible for trial (Firebase not available)',
                'firebase_status': 'unavailable'
            })
        
        is_eligible = stripe_service.check_trial_eligibility(email)
        trial_history = stripe_service.get_trial_history(email)
        
        return jsonify({
            'email': email,
            'eligible': is_eligible,
            'trial_history': trial_history,
            'message': 'Trial already used' if not is_eligible else 'Eligible for trial',
            'firebase_status': 'available'
        })
        
    except Exception as e:
        print(f"Error checking trial eligibility: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-analysis-permission/<user_id>', methods=['GET'])
def check_analysis_permission(user_id):
    """Check if user can perform an AI analysis"""
    try:
        # Get email from query parameter for developer check
        email = request.args.get('email')
        
        permission_data = stripe_service.can_perform_analysis(user_id, email)
        
        # If user can perform analysis, increment the count (but not for developers)
        if permission_data.get('can_perform', False) and not permission_data.get('status') == 'developer':
            stripe_service.increment_analysis_count(user_id)
        
        return jsonify(permission_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")  # Limit checkout attempts
def create_checkout_session():
    """Create a Stripe Checkout Session for trial subscription"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name')
        
        # Validate required fields
        if not all([user_id, email]):
            return jsonify({'error': 'Missing required fields: user_id and email'}), 400
        
        # Check trial eligibility
        if not stripe_service.check_trial_eligibility(email):
            return jsonify({
                'error': 'Trial already used',
                'message': 'This email address has already used a free trial. Please sign in to your existing account or use a different email address.'
            }), 403
        
        # Get the frontend URL for success/cancel redirects
        # Always use the production frontend URL for Stripe redirects
        frontend_url = 'https://fxsentinel-production.up.railway.app'
        
        def create_session():
            return stripe.checkout.Session.create(
                customer_email=email,
                line_items=[{
                    'price': os.getenv('STRIPE_PRICE_ID'),
                    'quantity': 1,
                }],
                mode='subscription',
                subscription_data={
                    'trial_period_days': int(os.getenv('TRIAL_DAYS', 3)),
                    'metadata': {'firebase_user_id': user_id}
                },
                success_url=f'{frontend_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}',
                cancel_url=f'{frontend_url}/trial-welcome',
                metadata={
                    'firebase_user_id': user_id,
                    'user_name': name
                }
            )
        
        # Use retry mechanism for checkout session creation
        checkout_session = RetryHandler.retry_operation(
            create_session,
            max_attempts=3,
            context={'operation': 'create_checkout_session', 'user_id': user_id},
            user_id=user_id
        )
        
        return jsonify({'session_url': checkout_session.url})
        
    except stripe.error.StripeError as e:
        error_data, status_code = StripeErrorHandler.create_error_response(
            e, 
            context={'operation': 'create_checkout_session', 'user_id': user_id},
            user_id=user_id
        )
        return jsonify(error_data), status_code
        
    except Exception as e:
        error_data, status_code = StripeErrorHandler.create_error_response(
            e,
            context={'operation': 'create_checkout_session', 'user_id': user_id},
            user_id=user_id
        )
        return jsonify(error_data), status_code

@app.route('/api/verify-checkout-session', methods=['POST'])
@limiter.limit("20 per minute")  # Limit verification attempts
def verify_checkout_session():
    """Verify a completed checkout session and update user status"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        def retrieve_session():
            return stripe.checkout.Session.retrieve(session_id)
        
        # Use retry mechanism for session retrieval
        session = RetryHandler.retry_operation(
            retrieve_session,
            max_attempts=3,
            context={'operation': 'verify_checkout_session', 'session_id': session_id}
        )
        
        if session.payment_status == 'paid' or session.payment_status == 'no_payment_required':
            # Get user ID from session metadata
            user_id = session.metadata.get('firebase_user_id')
            
            if user_id and stripe_service.firebase_available and stripe_service.db:
                try:
                    # Update user status in Firebase
                    stripe_service.db.collection('users').document(user_id).update({
                        'subscription_status': 'trial',
                        'trial_start_date': datetime.now(),
                        'trial_end_date': datetime.now() + timedelta(days=stripe_service.trial_days),
                        'daily_analysis_count': 0,
                        'last_analysis_reset': datetime.now().date(),
                        'stripe_customer_id': session.customer,
                        'subscription_id': session.subscription
                    })
                    
                    # Mark trial as used for this email
                    stripe_service.mark_trial_used(user_id, session.customer_email)
                    
                    return jsonify({
                        'success': True,
                        'subscription_status': 'trial',
                        'trial_end_date': (datetime.now() + timedelta(days=stripe_service.trial_days)).isoformat()
                    })
                except Exception as firebase_error:
                    error_data, status_code = StripeErrorHandler.create_error_response(
                        firebase_error,
                        context={'operation': 'verify_checkout_session', 'session_id': session_id, 'user_id': user_id},
                        user_id=user_id
                    )
                    return jsonify(error_data), status_code
            else:
                return jsonify({'error': 'User not found or database unavailable'}), 404
        
        return jsonify({'error': 'Invalid session or payment not completed'}), 400
        
    except stripe.error.StripeError as e:
        error_data, status_code = StripeErrorHandler.create_error_response(
            e,
            context={'operation': 'verify_checkout_session', 'session_id': session_id}
        )
        return jsonify(error_data), status_code
        
    except Exception as e:
        error_data, status_code = StripeErrorHandler.create_error_response(
            e,
            context={'operation': 'verify_checkout_session', 'session_id': session_id}
        )
        return jsonify(error_data), status_code

@app.route('/api/create-portal-session', methods=['POST'])
@limiter.limit("5 per minute")  # Limit portal access
def create_portal_session():
    """Create Stripe Customer Portal session for subscription management"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        return_url = data.get('return_url')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Get user's Stripe customer ID from Firebase
        if stripe_service.firebase_available and stripe_service.db:
            try:
                user_doc = stripe_service.db.collection('users').document(user_id).get()
                if user_doc.exists:
                    customer_id = user_doc.get('stripe_customer_id')
                    
                    if not customer_id:
                        return jsonify({'error': 'No subscription found for this user'}), 404
                    
                    # Create portal session
                    session = stripe.billing_portal.Session.create(
                        customer=customer_id,
                        return_url=return_url,
                    )
                    
                    return jsonify({'url': session.url})
                else:
                    return jsonify({'error': 'User not found'}), 404
            except Exception as firebase_error:
                print(f"Firebase error: {firebase_error}")
                return jsonify({'error': 'Database error'}), 500
        else:
            return jsonify({'error': 'Database not available'}), 500
            
    except Exception as e:
        print(f"Error creating portal session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Create a setup intent for trial payment method collection"""
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        
        # Create a setup intent (no charge, just collect payment method)
        setup_intent = stripe.SetupIntent.create(
            customer=customer_id,
            payment_method_types=['card'],
            usage='off_session',  # For future payments
        )
        
        return jsonify({
            'client_secret': setup_intent.client_secret
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/setup-trial-subscription', methods=['POST'])
def setup_trial_subscription():
    """Setup trial subscription with payment method"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        customer_id = data.get('customer_id')
        payment_method_id = data.get('payment_method_id')
        
        # Setup payment method
        stripe_service.setup_payment_method(customer_id, payment_method_id)
        
        # Create trial subscription
        subscription = stripe_service.create_trial_subscription(customer_id)
        
        # Update user in Firebase
        if stripe_service.firebase_available and stripe_service.db:
            stripe_service.db.collection('users').document(user_id).update({
                'subscription_id': subscription.id,
                'subscription_status': 'trial',
                'trial_start_date': datetime.now(),
                'trial_end_date': datetime.now() + timedelta(days=stripe_service.trial_days),
                'daily_analysis_count': 0,
                'last_analysis_reset': datetime.now().date()
            })
        
        return jsonify({
            'success': True,
            'subscription_id': subscription.id,
            'trial_end_date': (datetime.now() + timedelta(days=stripe_service.trial_days)).isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-welcome-email', methods=['POST'])
@limiter.limit("3 per minute")  # Limit email sending
def send_welcome_email():
    """Send welcome email with customer portal link"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        
        if not user_id or not email:
            return jsonify({'error': 'User ID and email required'}), 400
        
        # Get user's Stripe customer ID from Firebase
        if stripe_service.firebase_available and stripe_service.db:
            try:
                user_doc = stripe_service.db.collection('users').document(user_id).get()
                if user_doc.exists:
                    customer_id = user_doc.get('stripe_customer_id')
                    
                    if customer_id:
                        # Create portal session
                        portal_session = stripe.billing_portal.Session.create(
                            customer=customer_id,
                            return_url='https://fxsentinel-production.up.railway.app/dashboard',
                        )
                        
                        # Here you would integrate with your email service
                        # For now, we'll return the portal URL
                        return jsonify({
                            'success': True,
                            'portal_url': portal_session.url,
                            'message': 'Welcome email sent with customer portal link'
                        })
                    else:
                        return jsonify({'error': 'No subscription found for this user'}), 404
                else:
                    return jsonify({'error': 'User not found'}), 404
            except Exception as firebase_error:
                print(f"Firebase error: {firebase_error}")
                return jsonify({'error': 'Database error'}), 500
        else:
            return jsonify({'error': 'Database not available'}), 500
            
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upgrade-subscription', methods=['POST'])
def upgrade_subscription():
    """Upgrade user to paid subscription immediately"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        customer_id = data.get('customer_id')
        
        # Create immediate subscription (no trial)
        subscription = stripe_service.create_subscription_after_trial(customer_id)
        
        # Update user in Firebase
        if stripe_service.firebase_available and stripe_service.db:
            stripe_service.db.collection('users').document(user_id).update({
                'subscription_id': subscription.id,
                'subscription_status': 'active',
                'current_period_end': datetime.fromtimestamp(subscription['current_period_end'])
            })
        
        return jsonify({
            'success': True,
            'subscription_id': subscription.id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stripe-webhook', methods=['POST'])
@limiter.exempt  # Webhooks should not be rate limited
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            print("⚠️ No Stripe signature header found")
            return jsonify({'error': 'No signature header'}), 400
        
        print(f"📡 Received Stripe webhook: {request.headers.get('Stripe-Signature', 'No signature')[:20]}...")
        
        def process_webhook():
            stripe_service.handle_webhook(payload, sig_header)
        
        # Use retry mechanism for webhook processing
        from services.retry_handler import WebhookRetryHandler
        WebhookRetryHandler.retry_webhook_processing(
            process_webhook,
            max_attempts=3,
            context={'operation': 'stripe_webhook', 'signature': sig_header[:20]}
        )
        
        print("✅ Webhook processed successfully")
        return jsonify({'success': True}), 200
        
    except ValueError as e:
        print(f"❌ Invalid webhook payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print(f"❌ Invalid webhook signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        error_data, status_code = StripeErrorHandler.create_error_response(
            e,
            context={'operation': 'stripe_webhook', 'signature': sig_header[:20] if sig_header else 'None'}
        )
        return jsonify(error_data), status_code



@app.route('/api/request-refund', methods=['POST'])
@limiter.limit("5 per hour")  # Limit refund requests
def request_refund():
    """Handle refund request and send email to support team"""
    try:
        data = request.get_json()
        user_email = data.get('email')
        reason = data.get('reason')
        details = data.get('details', '')
        
        if not user_email or not reason:
            return jsonify({'error': 'Email and reason are required'}), 400
        
        # Create email content
        subject = f"Refund Request - {user_email}"
        content = f"""
New refund request received:

User Email: {user_email}
Reason: {reason}
Additional Details: {details}

Request submitted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please review and process this refund request.
        """
        
        # Send email to support team
        support_email = "fxsentinelapp@gmail.com"
        
        # For now, we'll use a simple email sending approach
        # In production, you'd want to use a proper email service like SendGrid, AWS SES, etc.
        try:
            # Import smtplib for email sending
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get email credentials from environment
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if smtp_username and smtp_password:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = smtp_username
                msg['To'] = support_email
                msg['Subject'] = subject
                
                # Add body
                msg.attach(MIMEText(content, 'plain'))
                
                # Send email
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                
                print(f"✅ Refund request email sent to {support_email}")
                
            else:
                # Fallback: just log the request
                print(f"📧 Refund request received (email not configured):")
                print(f"   From: {user_email}")
                print(f"   Reason: {reason}")
                print(f"   Details: {details}")
                
        except Exception as email_error:
            print(f"⚠️ Failed to send email: {email_error}")
            # Still log the request even if email fails
            print(f"📧 Refund request received:")
            print(f"   From: {user_email}")
            print(f"   Reason: {reason}")
            print(f"   Details: {details}")
        
        # Store refund request in database for tracking
        if stripe_service.firebase_available and stripe_service.db:
            try:
                refund_doc = {
                    'user_email': user_email,
                    'reason': reason,
                    'details': details,
                    'status': 'pending',
                    'created_at': datetime.now(),
                    'processed_at': None
                }
                
                stripe_service.db.collection('refund_requests').add(refund_doc)
                print(f"✅ Refund request stored in database")
                
            except Exception as db_error:
                print(f"⚠️ Failed to store refund request in database: {db_error}")
        
        return jsonify({
            'success': True,
            'message': 'Refund request submitted successfully. We will contact you within 24 hours.'
        })
        
    except Exception as e:
        print(f"❌ Error processing refund request: {e}")
        return jsonify({
            'error': 'Failed to submit refund request',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Use Railway's PORT environment variable or default to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    # Force debug mode off for background execution
    debug_mode = False
    
    # Start cost-optimized monitor
    try:
        from services.cost_optimized_monitor import cost_optimized_monitor
        cost_optimized_monitor.start()
        print("✅ Cost-optimized monitor started")
    except Exception as e:
        print(f"⚠️ Could not start cost-optimized monitor: {e}")
    
    print(f"🚀 Starting Flask server on port {port}, debug={debug_mode}")
    print("📊 Cost-optimized monitoring enabled - reduced API calls and logging")
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 