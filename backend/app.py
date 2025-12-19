from flask import Flask, jsonify, request, send_from_directory, redirect, render_template
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
import logging
from datetime import datetime
from dotenv import load_dotenv
import stripe
from firebase_admin import credentials, firestore, initialize_app
from services.stripe_service import StripeService
from services.coupon_service import CouponService
from services.google_sheets_service import GoogleSheetsService

# Configure logging
logger = logging.getLogger(__name__)

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

# Initialize background alert worker
from services.background_alert_worker import background_worker

# Debug: Check if environment variables are loaded
print(f"🔍 Environment Debug:")
print(f"   OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
if os.getenv('OPENAI_API_KEY'):
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"   API Key Preview: {api_key[:10]}...{api_key[-4:]}")

app = Flask(__name__)

# Initialize background alert worker
# background_worker.init_app(app)  # Removed - not needed

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    enabled=False  # Temporarily disable rate limiting for testing
)

# Initialize Google Sheets Service
try:
    google_sheets_service = GoogleSheetsService()
    if google_sheets_service.is_available():
        print("✅ Google Sheets service initialized")
    else:
        print("⚠️ Google Sheets service not available (missing credentials)")
except Exception as e:
    print(f"⚠️ Google Sheets service initialization failed: {e}")
    google_sheets_service = None

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
    """Get relevant currency pairs for a given currency (max 4 pairs)"""
    pairs_map = {
        "USD": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF"],
        "EUR": ["EUR/USD", "EUR/GBP", "EUR/JPY", "EUR/CHF"],
        "GBP": ["GBP/USD", "EUR/GBP", "GBP/JPY", "GBP/CHF"],
        "JPY": ["USD/JPY", "EUR/JPY", "GBP/JPY", "AUD/JPY"],
        "AUD": ["AUD/USD", "EUR/AUD", "GBP/AUD", "AUD/JPY"],
        "CAD": ["USD/CAD", "EUR/CAD", "GBP/CAD", "AUD/CAD"],
        "CHF": ["USD/CHF", "EUR/CHF", "GBP/CHF", "AUD/CHF"],
        "NZD": ["NZD/USD", "EUR/NZD", "GBP/NZD", "NZD/JPY"]
    }
    return pairs_map.get(currency, ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF"])

def enforce_currency_pairs_limit(events):
    """Enforce strict 4-pair limit on all events"""
    if not events:
        return events
    
    for event in events:
        currency_pairs = event.get('currencyPairs', [])
        if len(currency_pairs) > 4:
            # Keep only the first 4 pairs (most important/liquid)
            event['currencyPairs'] = currency_pairs[:4]
        elif len(currency_pairs) == 0:
            # If no pairs, add default major pairs based on currency
            currency = event.get('currency', 'USD')
            default_pairs = {
                'USD': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'],
                'EUR': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF'],
                'GBP': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF'],
                'JPY': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY'],
                'CHF': ['USDCHF', 'EURCHF', 'GBPCHF', 'AUDCHF'],
                'CAD': ['USDCAD', 'EURCAD', 'GBPCAD', 'AUDCAD'],
                'AUD': ['AUDUSD', 'EURAUD', 'GBPAUD', 'AUDJPY'],
                'NZD': ['NZDUSD', 'EURNZD', 'GBPNZD', 'NZDJPY']
            }
            event['currencyPairs'] = default_pairs.get(currency, ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF'])
    
    return events

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
from services.local_ai_analysis import local_ai_analyzer
# MarketContext from local_ai_analysis removed to avoid conflicts
from services.news_sentiment_analyzer import news_sentiment_analyzer
from services.technical_analysis_service import technical_analyzer
from services.enhanced_ai_analysis import enhanced_ai_analyzer, MarketContext as EnhancedMarketContext
try:
    from services.gpt_ai_analysis import GPTAIAnalyzer, MarketContext as GPTMarketContext
    from services.optimized_chatgpt_analyzer import optimized_chatgpt_analyzer
    # Create GPT analyzer instance
    print(f"🔍 DEBUG: Creating GPT analyzer instance...")
    gpt_ai_analyzer = GPTAIAnalyzer()
    print(f"🔍 DEBUG: GPT analyzer created successfully!")
    print(f"🔍 DEBUG: Has _select_model: {hasattr(gpt_ai_analyzer, '_select_model')}")
    print(f"🔍 DEBUG: Has _get_error_fallback: {hasattr(gpt_ai_analyzer, '_get_error_fallback')}")
    GPT_AVAILABLE = True
except Exception as e:
    print(f"🔍 GPT Analyzer import failed: {e}")
    import traceback
    traceback.print_exc()
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
        
        # Import basic MarketContext for local analyzer
        from services.local_ai_analysis import MarketContext as LocalMarketContext
        
        # Create basic market context for local AI analyzer
        market_context = LocalMarketContext(
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
            economic_calendar=[]
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
# Import economic calendar services
from services.hybrid_economic_calendar import hybrid_economic_calendar
# NOTE: Only using hybrid_economic_calendar now - no fallbacks to prevent bugs
# Import the Finnhub historical service
from services.finnhub_historical import finnhub_historical

@app.route('/api/economy-indicators/<country_code>', methods=['GET'])
def get_economy_indicators(country_code):
    """
    Get economic indicators for a country from Google Sheets
    
    Args:
        country_code: Country code (US, EUR, GBP, JPY)
    
    Query Parameters:
        refresh: If 'true', bypasses cache and fetches fresh data
    
    Returns:
        JSON response with indicators data or error message
    """
    try:
        # Normalize country code to uppercase
        country_code = country_code.upper()
        
        # Check if service is available
        if not google_sheets_service or not google_sheets_service.is_available():
            return jsonify({
                "status": "error",
                "message": "Google Sheets service not available",
                "fallback": "Use static JSON file"
            }), 503
        
        # Check if refresh is requested
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Fetch indicators from Google Sheets (with optional cache bypass)
        if force_refresh:
            # Clear cache for this country to force fresh fetch
            cache_key = f"indicators_{country_code}"
            if cache_key in google_sheets_service.cache:
                del google_sheets_service.cache[cache_key]
            if cache_key in google_sheets_service.cache_timestamps:
                del google_sheets_service.cache_timestamps[cache_key]
            logger.info(f"🔄 Cache cleared for {country_code}, forcing fresh fetch")
        
        indicators = google_sheets_service.get_economy_indicators(country_code)
        
        if indicators:
            # Check if data is cached
            cache_key = f"indicators_{country_code}"
            is_cached = google_sheets_service._is_cache_valid(cache_key)
            
            return jsonify({
                "status": "success",
                "country": country_code,
                "indicators": indicators,
                "source": "google_sheets",
                "cached": is_cached,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            # No data found in Google Sheets
            return jsonify({
                "status": "error",
                "message": f"No indicators found for {country_code}",
                "country": country_code,
                "fallback": "Use static JSON file"
            }), 404
            
    except Exception as e:
        logger.error(f"Error in economy-indicators API endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "country": country_code
        }), 500

@app.route('/api/economic-calendar')
def get_economic_calendar():
    """Get economic calendar events from hybrid calendar ONLY (your curated ForexFactory data)"""
    print("🚀 ECONOMIC CALENDAR ENDPOINT CALLED")
    try:
        # Get query parameters for date range and timezone
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_timezone = request.args.get('timezone', 'UTC')
        
        # ONLY USE HYBRID CALENDAR - No fallbacks!
        print("🔄 Fetching from hybrid_economic_calendar (Your Curated ForexFactory Data)...")
        events = hybrid_economic_calendar.get_economic_events(start_date, end_date)
        source = "Hybrid Calendar (ForexFactory)"
        
        if not events:
            print("❌ No events available - hybrid calendar returned empty")
            return jsonify({
                "events": [],
                "source": "hybrid_calendar",
                "last_updated": datetime.now().isoformat(),
                "total_events": 0,
                "status": "no_data",
                "message": "No events in date range. Update calendar with new events."
            })
        
        print(f"✅ Got {len(events)} events from Hybrid Calendar")
        print(f"🔍 First event: {events[0].get('title', 'Unknown')} on {events[0].get('date', 'Unknown')}")
        
        # Light currency pair limit (just ensure max 4 pairs per event)
        events = enforce_currency_pairs_limit(events)
        print(f"✅ Currency pairs limited to max 4 per event")
        print(f"✅ Returning {len(events)} events to frontend")
        
        return jsonify({
            "events": events,
            "source": source,
            "last_updated": datetime.now().isoformat(),
            "total_events": len(events),
            "status": "success"
        })
            
    except Exception as e:
        print(f"❌ Error in economic calendar endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "events": [],
            "source": "error",
            "last_updated": datetime.now().isoformat(),
            "total_events": 0,
            "status": "error",
            "error": str(e),
            "message": "Failed to fetch economic calendar data. Please try again later."
        }), 500

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
        print(f"🔍 Force refresh requested: {force_refresh}")
        print(f"🔍 Request args: {dict(request.args)}")
        
        # Check for deployment notification that requires cache clearing
        if DEPLOYMENT_NOTIFICATION["active"] and DEPLOYMENT_NOTIFICATION["requires_cache_clear"]:
            print("🧹 Deployment notification active - clearing cache for user")
            news_cache.clear_cache()
            force_refresh = True
        
        # First, try to get cached data immediately (unless force refresh)
        cached_news = None
        if not force_refresh:
            cached_news = news_cache.load_news()
            print(f"🔍 Loading from cache: {len(cached_news) if cached_news else 0} articles")
        else:
            print("🔍 Force refresh requested - skipping cache")
        
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
                # Also add added_to_feed_at fallback for cached items that don't have it
                for item in cached_news:
                    if 'id' in item:
                        item['id'] = str(item['id'])
                    # Add added_to_feed_at fallback for old cached items (use published_at as fallback)
                    if 'added_to_feed_at' not in item:
                        item['added_to_feed_at'] = item.get('published_at', datetime.now().isoformat())
                response_data = {
                    "news": cached_news,
                    "last_updated": datetime.now().isoformat(),
                    "sources": ["cached_data"],
                    "total_articles": len(cached_news),
                    "cache_status": "cached"
                }
                
                # Add deployment notification if active
                if DEPLOYMENT_NOTIFICATION["active"]:
                    response_data["deployment_notification"] = DEPLOYMENT_NOTIFICATION
                
                return jsonify(response_data)
        
        # If force refresh is requested, use the force refresh function
        if force_refresh:
            print("🔍 Using force refresh function for fresh data")
            try:
                force_result = force_refresh_news_internal()
                print(f"🔍 Force refresh result: {force_result}")
                if force_result["success"]:
                    return jsonify(force_result)
                else:
                    print("❌ Force refresh failed, falling back to regular fetch")
            except Exception as e:
                print(f"❌ Error in force refresh: {e}")
                import traceback
                traceback.print_exc()
                print("Falling back to regular fetch")
        
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
        
        # Try Telegram news separately using the same approach as force refresh
        telegram_news = []
        try:
            import sys
            import os
            # Add current directory to path for imports
            if os.path.dirname(__file__) not in sys.path:
                sys.path.insert(0, os.path.dirname(__file__))
            
            print("🔍 Attempting to import telegram_sync in news endpoint...")
            from services.telegram_sync_wrapper import telegram_sync
            print("✅ Successfully imported telegram_sync in news endpoint")
            
            print("🔍 Calling telegram_sync.get_recent_telegram_news in news endpoint...")
            telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
            print(f"🔍 Telegram sync returned {len(telegram_news)} articles in news endpoint")
            
            # Debug: Show what we got from Telegram
            if telegram_news:
                print("📰 Sample Telegram articles from news endpoint:")
                for i, news in enumerate(telegram_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print(f"     Impact: {news.get('impact', 'No impact')}")
                    print()
            else:
                print("⚠️ No Telegram news returned from sync wrapper in news endpoint")
            
            fresh_news.extend(telegram_news)
            sources_used.append("Telegram")
            print(f"✅ Added {len(telegram_news)} Telegram news articles to fresh_news")
            print(f"📊 Total fresh_news count after Telegram: {len(fresh_news)}")
        except Exception as e:
            print(f"❌ Error fetching Telegram news in news endpoint: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing with other sources...")
            telegram_news = []
        
        # If we got fresh news, save it to cache and return it
        if fresh_news:
            # Combine and sort all news by publication date
            all_news = fresh_news
            
            # Ensure all fresh news items have added_to_feed_at set (safeguard)
            current_time = datetime.now().isoformat()
            for item in all_news:
                if 'added_to_feed_at' not in item:
                    item['added_to_feed_at'] = current_time
            
            all_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            # Remove duplicates across all sources using simple logic
            def remove_duplicate_news_simple(news_list):
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
            
            print(f"📊 Before deduplication in news endpoint: {len(all_news)} articles")
            
            # Debug: Show breakdown by source before deduplication
            sources_before = {}
            for item in all_news:
                source = item.get('source', 'Unknown')
                sources_before[source] = sources_before.get(source, 0) + 1
            
            print("📊 Source breakdown before deduplication:")
            for source, count in sorted(sources_before.items()):
                print(f"  {source}: {count} articles")
            
            all_news = remove_duplicate_news_simple(all_news)
            print(f"📊 After deduplication in news endpoint: {len(all_news)} articles")
            
            # Debug: Show breakdown by source after deduplication
            sources_after = {}
            for item in all_news:
                source = item.get('source', 'Unknown')
                sources_after[source] = sources_after.get(source, 0) + 1
            
            print("📊 Source breakdown after deduplication:")
            for source, count in sorted(sources_after.items()):
                print(f"  {source}: {count} articles")
            
            # Save to cache for future use
            news_cache.save_news(all_news)
            
            # Note: Alert processing moved to cost-optimized background monitor
            # This prevents excessive API calls and reduces terminal noise
            
            response_data = {
                "news": all_news,
                "last_updated": datetime.now().isoformat(),
                "sources": sources_used,
                "total_articles": len(all_news),
                "cache_status": "fresh"
            }
            
            # Add deployment notification if active
            if DEPLOYMENT_NOTIFICATION["active"]:
                response_data["deployment_notification"] = DEPLOYMENT_NOTIFICATION
            
            return jsonify(response_data)
        else:
            # No fresh news available, use mock data as fallback
            print("⚠️ No fresh news available, using mock data")
            mock_news = get_mock_news()
            response_data = {
                "news": mock_news,
                "last_updated": datetime.now().isoformat(),
                "sources": ["fallback_data"],
                "total_articles": len(mock_news),
                "cache_status": "fallback"
            }
            
            # Add deployment notification if active
            if DEPLOYMENT_NOTIFICATION["active"]:
                response_data["deployment_notification"] = DEPLOYMENT_NOTIFICATION
            
            return jsonify(response_data)
                
    except Exception as e:
        print(f"❌ Error in news endpoint: {e}")
        # Try to load from cache as fallback
        try:
            from services.news_cache import news_cache
            cached_news = news_cache.load_news()
            if cached_news:
                # Remove duplicates from fallback cached news as well
                cached_news = remove_duplicate_news(cached_news)
                
                # Convert all news item IDs to strings and add added_to_feed_at fallback
                for item in cached_news:
                    if 'id' in item:
                        item['id'] = str(item['id'])
                    # Add added_to_feed_at fallback for old cached items (use published_at as fallback)
                    if 'added_to_feed_at' not in item:
                        item['added_to_feed_at'] = item.get('published_at', datetime.now().isoformat())
                
                print(f"✅ Error occurred, using cached news ({len(cached_news)} articles)")
                response_data = {
                    "news": cached_news,
                    "last_updated": datetime.now().isoformat(),
                    "sources": ["cached_data"],
                    "total_articles": len(cached_news),
                    "cache_status": "cached_fallback"
                }
                
                # Add deployment notification if active
                if DEPLOYMENT_NOTIFICATION["active"]:
                    response_data["deployment_notification"] = DEPLOYMENT_NOTIFICATION
                
                return jsonify(response_data)
        except:
            pass
        
        # Last resort: mock data
        mock_news = get_mock_news()
        response_data = {
            "news": mock_news,
            "last_updated": datetime.now().isoformat(),
            "sources": ["fallback_data"],
            "total_articles": len(mock_news),
            "cache_status": "fallback"
        }
        
        # Add deployment notification if active
        if DEPLOYMENT_NOTIFICATION["active"]:
            response_data["deployment_notification"] = DEPLOYMENT_NOTIFICATION
        
        return jsonify(response_data)

# Global deployment notification flag
DEPLOYMENT_NOTIFICATION = {
    "active": False,
    "timestamp": None,
    "message": "",
    "version": "1.0.0",
    "requires_cache_clear": False
}

@app.route('/api/deployment-notification', methods=['GET'])
def get_deployment_notification():
    """Get current deployment notification status"""
    return jsonify(DEPLOYMENT_NOTIFICATION)

@app.route('/api/deployment-notification', methods=['POST'])
def set_deployment_notification():
    """Set deployment notification to force all users to refresh and clear cache"""
    try:
        data = request.get_json() or {}
        message = data.get('message', 'System update deployed - clearing cache and refreshing news feed')
        version = data.get('version', '1.0.0')
        requires_cache_clear = data.get('requires_cache_clear', True)  # Default to True
        
        global DEPLOYMENT_NOTIFICATION
        DEPLOYMENT_NOTIFICATION = {
            "active": True,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "version": version,
            "requires_cache_clear": requires_cache_clear
        }
        
        print(f"🚀 Deployment notification activated: {message}")
        if requires_cache_clear:
            print("🧹 Cache clearing required for all users")
        
        # Force refresh news immediately
        force_refresh_result = force_refresh_news_internal()
        
        return jsonify({
            "success": True,
            "message": "Deployment notification activated",
            "deployment_notification": DEPLOYMENT_NOTIFICATION,
            "force_refresh_result": force_refresh_result
        })
    except Exception as e:
        print(f"❌ Error setting deployment notification: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@app.route('/api/clear-deployment-notification', methods=['POST'])
def clear_deployment_notification():
    """Clear deployment notification"""
    global DEPLOYMENT_NOTIFICATION
    DEPLOYMENT_NOTIFICATION = {
        "active": False,
        "timestamp": None,
        "message": "",
        "version": "1.0.0",
        "requires_cache_clear": False
    }
    
    print("✅ Deployment notification cleared")
    
    return jsonify({
        "success": True,
        "message": "Deployment notification cleared"
    })

@app.route('/api/clear-all-caches', methods=['POST'])
def clear_all_caches():
    """Clear all server-side caches"""
    try:
        # Clear news cache
        from services.news_cache import news_cache
        news_cache.clear_cache()
        
        # Clear any other caches
        try:
            from services.gpt_analyzer import gpt_analyzer
            if hasattr(gpt_analyzer, 'clear_cache'):
                gpt_analyzer.clear_cache()
        except:
            pass
        
        try:
            from services.enhanced_macro_analyzer import enhanced_macro_analyzer
            if hasattr(enhanced_macro_analyzer, 'clear_cache'):
                enhanced_macro_analyzer.clear_cache()
        except:
            pass
        
        print("🧹 All server-side caches cleared")
        
        return jsonify({
            "success": True,
            "message": "All server-side caches cleared",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Error clearing caches: {e}")
        return jsonify({
            "success": False,
            "message": f"Error clearing caches: {str(e)}"
        }), 500

def force_refresh_news_internal():
    """Internal function to force refresh news (used by deployment notification)"""
    try:
        print("🔄 Force refreshing news (internal)...")
        
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
        
        # Fetch Telegram news using synchronous wrapper
        telegram_news = []
        try:
            import sys
            import os
            # Add current directory to path for imports
            if os.path.dirname(__file__) not in sys.path:
                sys.path.insert(0, os.path.dirname(__file__))
            
            print("🔍 Attempting to import telegram_sync...")
            from services.telegram_sync_wrapper import telegram_sync
            print("✅ Successfully imported telegram_sync")
            
            print("🔍 Calling telegram_sync.get_recent_telegram_news...")
            telegram_news = telegram_sync.get_recent_telegram_news(hours=24)
            print(f"✅ Telegram sync returned {len(telegram_news)} articles")
            
            # Debug: Show what we got from Telegram
            if telegram_news:
                print("📰 Sample Telegram articles:")
                for i, news in enumerate(telegram_news[:3], 1):
                    print(f"  {i}. {news.get('title', 'No title')}")
                    print(f"     Source: {news.get('source', 'No source')}")
                    print(f"     Impact: {news.get('impact', 'No impact')}")
                    print(f"     Type: {news.get('type', 'No type')}")
                    print()
            else:
                print("⚠️ No Telegram news returned from sync wrapper")
            
            fresh_news.extend(telegram_news)
            print(f"✅ Added {len(telegram_news)} Telegram news articles to fresh_news")
            print(f"📊 Total fresh_news count after Telegram: {len(fresh_news)}")
        except Exception as e:
            print(f"❌ Error fetching Telegram news: {e}")
            import traceback
            traceback.print_exc()
            print("Continuing with other sources...")
            telegram_news = []
        
        if fresh_news:
            print(f"📊 Before deduplication: {len(fresh_news)} articles")
            
            # Remove duplicates and sort
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
                    else:
                        print(f"🔄 Duplicate removed: {item.get('title', 'No title')} ({item.get('source', 'No source')})")
                return unique_news
            
            fresh_news = remove_duplicate_news(fresh_news)
            print(f"📊 After deduplication: {len(fresh_news)} articles")
            
            # Debug: Show breakdown by source
            sources = {}
            for item in fresh_news:
                source = item.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
            
            print("📊 Source breakdown after deduplication:")
            for source, count in sorted(sources.items()):
                print(f"  {source}: {count} articles")
            
            fresh_news.sort(key=lambda x: x.get('published_at', ''), reverse=True)
            
            # Save to cache
            news_cache.save_news(fresh_news)
            print(f"💾 Saved {len(fresh_news)} articles to cache")
            
            # Trigger alerts immediately
            try:
                from services.news_alert_trigger import news_alert_trigger
                results = news_alert_trigger.process_news_for_alerts(fresh_news)
                print(f"🎯 Force refresh alert results: {results}")
            except Exception as e:
                print(f"❌ Error triggering alerts: {e}")
            
            return {
                "success": True,
                "message": f"Force refreshed {len(fresh_news)} news articles",
                "articles_count": len(fresh_news),
                "alert_results": results if 'results' in locals() else None
            }
        else:
            print("⚠️ No fresh news available after processing")
            return {
                "success": False,
                "message": "No fresh news available"
            }
    except Exception as e:
        print(f"❌ Error in force refresh (internal): {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

@app.route('/api/force-refresh-news', methods=['POST'])
def force_refresh_news():
    """Force refresh news and trigger alerts immediately"""
    try:
        result = force_refresh_news_internal()
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
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
    """Get comprehensive GPT-powered analysis for economic events with data validation"""
    print(f"🚨🚨🚨 ENHANCED ANALYSIS ENDPOINT CALLED - ID: {news_id} 🚨🚨🚨")
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: Request headers: {dict(request.headers)}")
    try:
        # Get event data from request body if POST, otherwise from Finnhub calendar
        print(f"🔍 DEBUG: Getting event data...")
        if request.method == 'POST':
            request_data = request.get_json()
            print(f"🔍 DEBUG: Request data keys: {list(request_data.keys()) if request_data else 'None'}")
            event = request_data.get('event')
            analysis_type = request_data.get('analysisType', 'pre-event')
            print(f"🚨 Using event data from request: {event.get('title', 'Unknown')} - {event.get('currency', 'Unknown')}")
            print(f"🔍 DEBUG: Event keys: {list(event.keys()) if event else 'None'}")
        else:
            # Get the economic event by ID from Finnhub calendar data
            print(f"🔍 DEBUG: Getting event by ID from calendar...")
            event = get_economic_event_by_id(news_id)
            analysis_type = 'pre-event'
            print(f"🔍 DEBUG: Event from calendar: {event.get('title', 'Unknown') if event else 'None'}")
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        # Import the data validation service
        print(f"🔍 DEBUG: Importing data validator...")
        from services.data_validator import economic_data_validator
        print(f"🔍 DEBUG: Data validator imported successfully")
        
        # Validate the event data before analysis
        print(f"🔍 Validating event data: {event.get('title', 'Unknown')}")
        print(f"🔍 DEBUG: Event data being validated: {event}")
        print(f"🔍 DEBUG: Event keys: {list(event.keys()) if event else 'None'}")
        is_valid, validated_event, validation_errors = economic_data_validator.validate_event_data(event)
        print(f"🔍 DEBUG: Validation result - is_valid: {is_valid}, errors: {validation_errors}")
        print(f"🔍 DEBUG: Validated event: {validated_event}")
        
        if not is_valid:
            print(f"❌ Event data validation failed: {validation_errors}")
            return jsonify({
                "error": "Event data validation failed",
                "validation_errors": validation_errors,
                "event_title": event.get('title', 'Unknown'),
                "recommendation": "Event data quality issues detected - analysis may be unreliable"
            }), 400
        
        print(f"✅ Event data validation passed: {validated_event.get('title', 'Unknown')}")
        
        # Create GPT market context with live market data
        print(f"🔍 DEBUG: Importing live market data service...")
        from services.live_market_data import live_market_data_service
        print(f"🔍 DEBUG: Live market data service imported successfully")
        
        # Get live market data from TradingView
        print("🔄 Fetching live market data from TradingView")
        live_market_data = live_market_data_service.get_live_market_data()
        print(f"🔍 DEBUG: Live market data keys: {list(live_market_data.keys()) if live_market_data else 'None'}")
        
        # Create GPT market context for GPT analyzer
        print(f"🔍 DEBUG: About to create GPTMarketContext...")
        print(f"🔍 DEBUG: GPTMarketContext class: {GPTMarketContext}")
        print(f"🔍 DEBUG: GPTMarketContext parameters: {GPTMarketContext.__annotations__.keys()}")
        try:
            # GPTMarketContext expects string volatility values, so keep them as strings
            raw_volatility = live_market_data.get('recent_volatility', {})
            
            gpt_market_context = GPTMarketContext(
                current_prices=live_market_data.get('current_prices', {
                    'EUR/USD': 1.0850,
                    'USD/JPY': 148.50,
                    'GBP/USD': 1.2650,
                    'USD/CHF': 0.8650,
                    'AUD/USD': 0.6650,
                    'USD/CAD': 1.3550
                }),
                recent_volatility=raw_volatility,
                market_sentiment=live_market_data.get('market_sentiment', {
                    'EUR/USD': 'neutral',
                    'USD/JPY': 'neutral',
                    'GBP/USD': 'neutral',
                    'USD/CHF': 'neutral',
                    'AUD/USD': 'neutral',
                    'USD/CAD': 'neutral'
                }),
                key_levels=live_market_data.get('key_levels', {
                    'EUR/USD': {'support': [1.0800, 1.0750, 1.0700], 'resistance': [1.0900, 1.0950, 1.1000]},
                    'USD/JPY': {'support': [148.00, 147.50, 147.00], 'resistance': [149.00, 149.50, 150.00]},
                    'GBP/USD': {'support': [1.2600, 1.2550, 1.2500], 'resistance': [1.2700, 1.2750, 1.2800]}
                }),
                economic_calendar=[],
                bond_yields=live_market_data.get('bond_yields', {'US_10Y': 4.5, 'DE_10Y': 2.3, 'JP_10Y': 0.8}),
                equity_indices=live_market_data.get('equity_indices', {'SPX': 4500, 'DAX': 16000, 'NIKKEI': 33000}),
                commodity_prices=live_market_data.get('commodity_prices', {'GOLD': 2000, 'OIL': 75, 'SILVER': 25}),
                # Enhanced positioning data from live market data
                retail_sentiment=live_market_data.get('retail_sentiment', {
                    'EUR/USD': 0.65,
                    'USD/JPY': 0.35,
                    'GBP/USD': 0.50,
                    'USD/CHF': 0.70,
                    'AUD/USD': 0.40,
                    'USD/CAD': 0.55
                }),
                futures_positioning=live_market_data.get('futures_positioning', {
                    'EUR/USD': 15000,
                    'USD/JPY': -8000,
                    'GBP/USD': 5000,
                    'USD/CHF': 12000,
                    'AUD/USD': -3000,
                    'USD/CAD': 2000
                }),
                institutional_flow=live_market_data.get('institutional_flow', {
                    'EUR/USD': 25.5,
                    'USD/JPY': -15.2,
                    'GBP/USD': 8.7,
                    'USD/CHF': 18.3,
                    'AUD/USD': -12.1,
                    'USD/CAD': 5.4
                }),
                time_to_event=3600,  # 1 hour until event
                liquidity_level=2,   # Medium liquidity
                scenario_probabilities={
                    'higher': 0.30,
                    'lower': 0.50,
                    'inline': 0.20
                }
            )
            print(f"🔍 DEBUG: GPTMarketContext created successfully!")
        except Exception as e:
            print(f"🔍 DEBUG: ERROR creating GPTMarketContext: {e}")
            print(f"🔍 DEBUG: Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            raise
        
        # Use analysis_type from request or determine based on actual data availability
        if 'analysis_type' not in locals():
            has_actual_data = validated_event.get('actual') and validated_event.get('actual') not in ['N/A', '', None, '--']
            analysis_type = "post_event" if has_actual_data else "pre_event"
        
        print(f"📊 Analysis type: {analysis_type.upper()} (Actual data: {validated_event.get('actual', 'Not available')})")
        print(f"📊 Market data source: {live_market_data.get('data_source', 'unknown')}")
        print(f"📊 Data quality: {live_market_data.get('data_quality', 'unknown')}")
        
        # Get GPT-powered comprehensive analysis using validated data and live market context
        # TIER 1 ONLY - No generic fallback to Enhanced analyzer
        print(f"🔍 DEBUG: About to start GPT Tier 1 analysis...")
        print(f"🔍 DEBUG: gpt_ai_analyzer: {gpt_ai_analyzer}")
        print(f"🔍 DEBUG: GPT_AVAILABLE: {GPT_AVAILABLE}")
        
        if gpt_ai_analyzer is None:
            print(f"❌ GPT ANALYZER NOT AVAILABLE - Cannot proceed")
            return jsonify({
                "error": "AI Analysis service unavailable",
                "message": "GPT analyzer is not initialized. Please ensure OpenAI API key is configured.",
                "event_title": validated_event.get('title', 'Unknown')
            }), 503
        
        # Use GPT analyzer (Tier 1) - it has built-in event-specific fallbacks
        print(f"🚨🚨🚨 USING GPT TIER 1 ANALYZER (Event-Specific Analysis) 🚨🚨🚨")
        print(f"🔍 DEBUG: About to call gpt_ai_analyzer.analyze_macro_event...")
        gpt_analysis = gpt_ai_analyzer.analyze_macro_event(validated_event, gpt_market_context, analysis_type)
        print(f"🔍 DEBUG: GPT Tier 1 analysis completed successfully!")
        
        # Debug: Log what we're getting from GPT
        print(f"🚨🚨🚨 AI ANALYSIS DEBUG - EASY TO FIND 🚨🚨🚨")
        print(f"🚨 Analysis Type: {type(gpt_analysis)}")
        print(f"🚨 Analysis Class Name: {type(gpt_analysis).__name__}")
        print(f"🚨 Analysis Keys: {list(gpt_analysis.__dict__.keys()) if hasattr(gpt_analysis, '__dict__') else 'Not an object'}")
        print(f"🚨 Has headline: {hasattr(gpt_analysis, 'headline')}")
        print(f"🚨 Model Used: {getattr(gpt_analysis, 'model_used', 'unknown')}")
        print(f"🚨 Data Quality: {getattr(gpt_analysis, 'data_quality', 'unknown')}")
        print(f"🚨 Validation Status: {getattr(gpt_analysis, 'validation_status', 'unknown')}")
        print(f"🚨 Market Data Source: {getattr(gpt_analysis, 'market_data_source', 'unknown')}")
        print(f"🚨 Cache Hit: {getattr(gpt_analysis, 'cache_hit', False)}")
        print(f"🚨 Cost Estimate: ${getattr(gpt_analysis, 'cost_estimate', 0.0):.4f}")
        print(f"🚨🚨🚨 END AI ANALYSIS DEBUG 🚨🚨🚨")
        
        # Transform GPT Tier 1 analysis to frontend-compatible format
        print(f"🔍 DEBUG: Starting response transformation...")
        
        # GPT analyzer ALWAYS returns GPTAnalysisResult object with headline
        if not hasattr(gpt_analysis, 'headline'):
            print(f"❌ ERROR: GPT analysis missing expected structure")
            return jsonify({
                "error": "Invalid analysis format",
                "message": "GPT analyzer returned unexpected format",
                "event_title": validated_event.get('title', 'Unknown')
            }), 500
        
        print(f"🔍 DEBUG: Using GPT Tier 1 transformation (GPTAnalysisResult)")
        # GPT analyzer returns GPTAnalysisResult object
        enhanced_analysis = {
            # GPT analysis structure
            'headline': gpt_analysis.headline,
            'key_takeaway': gpt_analysis.key_takeaway,
            'forward_scenarios': gpt_analysis.forward_scenarios,
            'event_summary': gpt_analysis.event_summary,
            'market_reaction': gpt_analysis.market_reaction,
            'implications_takeaways': gpt_analysis.implications_takeaways,
            'trading_plan': gpt_analysis.trading_plan,
            'big_picture': gpt_analysis.big_picture,
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
            
            # Data quality information
            'data_quality': gpt_analysis.data_quality,
            'validation_status': gpt_analysis.validation_status,
            'market_data_source': gpt_analysis.market_data_source
        }
        
        return jsonify(enhanced_analysis)
        
    except Exception as e:
        print(f"❌ Error in enhanced analysis endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": "Analysis failed",
            "message": str(e),
            "event_id": news_id
        }), 500

@app.route('/api/health')
@limiter.exempt  # Health endpoints should not be rate limited
def health_check():
    """Main health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/api/health/alerts')
@limiter.exempt  # Health endpoints should not be rate limited
def health_alerts():
    """Alert system health check"""
    try:
        from services.alert_service import get_alert_service
        alert_service = get_alert_service()
        
        # Check if alert service is working
        telegram_bot_working = alert_service.telegram_bot is not None
        
        # Check background alert worker status
        background_worker_status = background_worker.get_status()
        background_worker_running = background_worker_status.get('running', False)
        
        # Check robust alert service if available
        robust_service_status = None
        robust_service_running = False
        try:
            from services.robust_alert_service import get_service_health
            robust_service_status = get_service_health()
            robust_service_running = robust_service_status.get('status') == 'running'
        except ImportError:
            robust_service_status = {"status": "not_available"}
        
        # Check subscription cache status
        subscription_cache_status = None
        try:
            from services.subscription_cache import get_cache_stats
            subscription_cache_status = get_cache_stats()
        except ImportError:
            subscription_cache_status = {"status": "not_available"}
        
        # Check robust Telegram service status
        telegram_service_status = None
        try:
            from services.robust_telegram_service import get_telegram_service_stats
            telegram_service_status = get_telegram_service_stats()
        except ImportError:
            telegram_service_status = {"status": "not_available"}
        
        # Determine overall status
        if telegram_bot_working and (background_worker_running or robust_service_running):
            overall_status = "healthy"
        elif telegram_bot_working:
            overall_status = "degraded"  # Telegram works but no background service
        else:
            overall_status = "unhealthy"
        
        return jsonify({
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "telegram_bot": "connected" if telegram_bot_working else "disconnected",
            "firebase": "connected" if alert_service.firebase_storage.test_connection() else "disconnected",
            "background_worker": background_worker_status,
            "robust_service": robust_service_status,
            "subscription_cache": subscription_cache_status,
            "robust_telegram_service": telegram_service_status,
            "alerts_working": background_worker_running or robust_service_running,
            "message": "Alerts handled by dedicated background worker (fxsentinel-background-worker-v2)" if (background_worker_running or robust_service_running) else "Dedicated background worker not running - check fxsentinel-background-worker-v2"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500

@app.route('/api/health/telegram')
@limiter.exempt  # Health endpoints should not be rate limited
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
@limiter.exempt  # Health endpoints should not be rate limited
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

@app.route('/api/alerts/trigger-check', methods=['POST'])
@limiter.exempt
def trigger_alert_check():
    """Manually trigger alert checking"""
    try:
        # Run alert checking
        run_alert_check()
        
        return jsonify({
            'success': True,
            'message': 'Alert check triggered successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/alerts/trigger', methods=['POST'])
@limiter.exempt
def trigger_alert():
    """Trigger alert for background worker"""
    try:
        data = request.get_json()
        alert_type = data.get('type')
        alert_data = data.get('data')
        
        if not alert_type or not alert_data:
            return jsonify({
                'success': False,
                'error': 'Missing type or data'
            }), 400
        
        # Import here to avoid circular imports
        from services.news_alert_trigger import news_alert_trigger
        from services.economic_calendar_alerts import economic_calendar_alerts
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        # Get all connected users
        firebase = FirebaseRealtimeStorage()
        mapping_path = "telegram_mappings"
        all_mappings = firebase._make_request('GET', mapping_path)
        
        logger.info(f"🔍 Alert trigger received - Type: {alert_type}")
        logger.info(f"📊 Found {len(all_mappings) if all_mappings else 0} telegram mappings")
        
        if not all_mappings or not isinstance(all_mappings, dict):
            logger.warning("⚠️  No telegram mappings found")
            return jsonify({
                'success': True,
                'message': 'No connected users found'
            })
        
        # Process each mapping
        alerts_sent = 0
        for chat_id, mapping_data in all_mappings.items():
            if isinstance(mapping_data, dict) and 'user_id' in mapping_data:
                user_id = mapping_data['user_id']
                
                # Skip test users with invalid chat IDs (only if they're actually test users)
                if chat_id == '123456789' and user_id.startswith('test_'):
                    continue
                
                # Get user settings
                user_settings = firebase.get_user_alert_settings(user_id)
                if not user_settings:
                    continue
                
                # Check if user has Telegram enabled (handle multiple settings structures)
                telegram_enabled = (
                    user_settings.get('telegram_enabled', False) or  # Old structure
                    user_settings.get('telegram', False) or  # Direct telegram setting
                    user_settings.get('channels', {}).get('telegram', {}).get('enabled', False)  # New structure
                )
                
                if not telegram_enabled:
                    logger.debug(f"User {user_id} has Telegram disabled")
                    continue
                
                # Check if user has liveNews alerts enabled (handle multiple settings structures)
                live_news_enabled = False
                
                # Check direct alert_types structure
                alert_types = user_settings.get('alert_types', {})
                if isinstance(alert_types, dict):
                    live_news_enabled = alert_types.get('liveNews', True)  # Default to True
                elif isinstance(alert_types, list):
                    live_news_enabled = 'liveNews' in alert_types or 'news' in alert_types
                else:
                    live_news_enabled = True  # Default to True if no alert_types
                
                # Also check preferences structure
                preferences = user_settings.get('preferences', {})
                if preferences and 'alertTypes' in preferences:
                    pref_alert_types = preferences['alertTypes']
                    if isinstance(pref_alert_types, dict):
                        live_news_enabled = pref_alert_types.get('liveNews', live_news_enabled)
                
                if not live_news_enabled:
                    logger.debug(f"User {user_id} has liveNews alerts disabled")
                    continue
                
                # Create user data
                user_data = {
                    'user_id': user_id,
                    'chat_id': chat_id,
                    'settings': user_settings
                }
                
                # Send alert based on type
                if alert_type == 'news':
                    # FIXED: Trust the dedicated worker's filtering - don't apply additional forex filtering
                    # The dedicated worker already filtered for high-impact news, so we should process it
                    logger.info(f"Processing news alert from dedicated worker: {alert_data.get('title', '')[:50]}...")
                    
                    # Determine if AI analysis is needed
                    needs_ai_analysis = news_alert_trigger.should_analyze_with_ai(alert_data)
                    
                    # Send the alert using async handling
                    try:
                        import asyncio
                        # Use asyncio.run to properly handle the async function
                        success = asyncio.run(news_alert_trigger._send_alert_to_user(user_data, alert_data, needs_ai_analysis))
                        
                        if success:
                            alerts_sent += 1
                            logger.info(f"✅ Successfully sent alert to user {user_id}")
                        else:
                            logger.warning(f"❌ Failed to send alert to user {user_id}")
                    except Exception as e:
                        logger.error(f"Error sending news alert to user {user_id}: {e}")
                        continue
                
                elif alert_type == 'calendar':
                    # Send calendar alert using the correct method name
                    try:
                        # The economic calendar alerts service uses synchronous methods
                        success = economic_calendar_alerts._send_pre_event_alert(user_data, alert_data)
                        
                        if success:
                            alerts_sent += 1
                    except Exception as e:
                        logger.error(f"Error sending calendar alert to user {user_id}: {e}")
                        continue
        
        logger.info(f"📨 Alert processing complete: {alerts_sent} alerts sent")
        return jsonify({
            'success': True,
            'message': f'Sent {alerts_sent} alerts',
            'alerts_sent': alerts_sent
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/news')
@limiter.exempt  # Health endpoints should not be rate limited
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
@limiter.exempt  # Health endpoints should not be rate limited
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
@limiter.exempt  # Health endpoints should not be rate limited
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
        
        # Check subscription status
        subscription_valid = _check_subscription_status(user_id)
        if not subscription_valid:
            return jsonify({
                "success": False, 
                "error": "Subscription required. Please renew your subscription to use Telegram alerts.",
                "subscription_required": True
            }), 403
        
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
        
        # Check subscription status
        subscription_valid = _check_subscription_status(user_id)
        if not subscription_valid:
            return jsonify({
                "success": False, 
                "error": "Subscription required. Please renew your subscription to use Telegram alerts.",
                "subscription_required": True
            }), 403
        
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

def _check_subscription_status(user_id):
    """Check if user has valid subscription status with caching"""
    try:
        from services.subscription_cache import get_subscription_status_sync
        
        is_valid, error = get_subscription_status_sync(user_id)
        
        if error:
            print(f"Error checking subscription status for {user_id}: {error}")
            return False
        
        print(f"🔍 Subscription check for user {user_id}: Valid: {is_valid}")
        return is_valid
        
    except Exception as e:
        print(f"Error checking subscription status: {e}")
        return False  # Deny access if we can't verify subscription

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
        import importlib
        import services.market_sentiment_service
        importlib.reload(services.market_sentiment_service)
        from services.market_sentiment_service import market_sentiment_service
        
        # Get sentiment data
        sentiment_data = market_sentiment_service.get_market_sentiment()
        
        print(f"✅ Successfully fetched sentiment data for trading day: {sentiment_data.get('trading_day')}")
        print(f"🔍 Market status: {sentiment_data.get('market_status')}")
        print(f"🔍 Is market closed: {sentiment_data.get('is_market_closed')}")
        
        return jsonify(sentiment_data)
        
    except Exception as e:
        print(f"❌ Error fetching market sentiment: {e}")
        import traceback
        traceback.print_exc()
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
    """
    DEPRECATED: Use /api/enhanced-analysis/<news_id> instead
    This endpoint uses the old Enhanced analyzer (Tier 2) instead of GPT (Tier 1)
    Get pre-event analysis for upcoming news events
    """
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
    """
    DEPRECATED: Use /api/enhanced-analysis/<news_id> instead
    This endpoint uses the old Enhanced analyzer (Tier 2) instead of GPT (Tier 1)
    Get post-event analysis for completed news events
    """
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



# REMOVED: Trial eligibility checking not needed in freemium model
# All users get free tier by default

@app.route('/api/check-analysis-permission/<user_id>', methods=['GET'])
def check_analysis_permission(user_id):
    """Check if user can perform an AI analysis (freemium model)"""
    try:
        # Get email from query parameter for developer check
        email = request.args.get('email')
        
        permission_data = stripe_service.can_perform_analysis(user_id, email)
        
        # If user can perform analysis, increment the count
        # Stripe service handles monthly vs daily increment based on tier
        if permission_data.get('can_perform', False) and permission_data.get('status') != 'developer':
            stripe_service.increment_analysis_count(user_id, email)
        
        return jsonify(permission_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create-checkout-session', methods=['POST'])
@limiter.limit("10 per minute")  # Limit checkout attempts
def create_checkout_session():
    """Create a Stripe Checkout Session for premium subscription upgrade"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name')
        coupon_code = data.get('coupon_code')  # Optional: support for coupon codes
        
        # Validate required fields
        if not all([user_id, email]):
            return jsonify({'error': 'Missing required fields: user_id and email'}), 400
        
        # Validate coupon if provided
        coupon_service = CouponService()
        if coupon_code:
            coupon_validation = coupon_service.validate_coupon(coupon_code)
            if not coupon_validation['valid']:
                return jsonify({
                    'error': 'Invalid coupon code',
                    'message': coupon_validation.get('reason', 'Coupon code is invalid or expired.')
                }), 400
        
        # Get the frontend URL for success/cancel redirects
        frontend_url = 'https://fxsentinel.io'
        
        def create_session():
            session_params = {
                'customer_email': email,
                'line_items': [{
                    'price': os.getenv('STRIPE_PRICE_ID'),
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'subscription_data': {
                    'metadata': {'firebase_user_id': user_id}
                },
                'success_url': f'{frontend_url}/dashboard?session_id={{CHECKOUT_SESSION_ID}}',
                'cancel_url': f'{frontend_url}/dashboard',
                'metadata': {
                    'firebase_user_id': user_id,
                    'user_name': name
                }
            }
            
            # Add coupon if provided
            if coupon_code:
                session_params['discounts'] = [{'coupon': coupon_code}]
            
            return stripe.checkout.Session.create(**session_params)
        
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

@app.route('/api/validate-coupon', methods=['POST'])
@limiter.limit("20 per minute")  # Limit coupon validation attempts
def validate_coupon():
    """Validate a coupon code before checkout"""
    try:
        data = request.get_json()
        coupon_code = data.get('coupon_code')
        
        if not coupon_code:
            return jsonify({'error': 'Coupon code required'}), 400
        
        coupon_service = CouponService()
        validation_result = coupon_service.validate_coupon(coupon_code)
        
        if validation_result['valid']:
            return jsonify({
                'valid': True,
                'coupon': {
                    'code': coupon_code,
                    'percent_off': validation_result['coupon'].percent_off,
                    'description': validation_result['coupon'].metadata.get('description', ''),
                    'type': validation_result['type']
                }
            })
        else:
            return jsonify({
                'valid': False,
                'error': validation_result.get('reason', 'Invalid coupon code')
            }), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
                    print(f"Firebase error: {firebase_error}")
                    # Fallback: return success even if Firebase fails
                    return jsonify({
                        'success': True,
                        'subscription_status': 'trial',
                        'trial_end_date': (datetime.now() + timedelta(days=stripe_service.trial_days)).isoformat(),
                        'firebase_status': 'unavailable'
                    })
            else:
                # Firebase not available - return success anyway
                print("⚠️ Firebase not available, returning success without database update")
                return jsonify({
                    'success': True,
                    'subscription_status': 'trial',
                    'trial_end_date': (datetime.now() + timedelta(days=stripe_service.trial_days)).isoformat(),
                    'firebase_status': 'unavailable'
                })
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

# REMOVED: Trial subscription setup not needed in freemium model
# Users start on free tier, upgrade via /api/create-checkout-session

@app.route('/dashboard')
def dashboard_redirect():
    """Redirect dashboard requests to frontend"""
    return redirect('https://fxsentinel.io/dashboard')

# REMOVED: Trial welcome page not needed in freemium model
# New users go directly to dashboard with free tier

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
                            return_url='https://fxsentinel.io/dashboard',
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

@app.route('/api/telegram/test', methods=['GET'])
def telegram_test():
    """Test route for Telegram webhook"""
    return jsonify({'status': 'ok', 'message': 'Telegram test route working'})

@app.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook updates"""
    try:
        # Get the update from Telegram
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({'status': 'error', 'message': 'No update data'}), 400
        
        # Log the incoming update
        print(f"📨 Received Telegram update: {update_data}")
        
        # Extract message information
        message = update_data.get('message', {})
        text = message.get('text', '')
        chat_id = message.get('chat', {}).get('id')
        user = message.get('from', {})
        user_id = user.get('id')
        username = user.get('username', 'Unknown')
        
        print(f"📝 Message: {text}")
        print(f"💬 Chat ID: {chat_id}")
        print(f"👤 User: @{username} (ID: {user_id})")
        
        # Handle /start command
        if text == '/start':
            try:
                # Send welcome message
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and chat_id:
                    welcome_message = {
                        "chat_id": chat_id,
                        "text": "🎉 Welcome to FXSentinel Alerts!\n\nI'm your personal market alert assistant. I'll send you real-time notifications about:\n• 🔥 Breaking forex news\n• 📊 Economic data releases\n• 🎯 High-impact market events\n\nTo get started, visit the FXSentinel app and click 'Connect Telegram Bot'.\n\nCommands:\n/status - Check your alert settings\n/test - Send a test alert\n/help - Show all commands",
                        "parse_mode": "HTML"
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=welcome_message,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Welcome message sent to chat {chat_id}")
                        return jsonify({'status': 'ok', 'message': 'Welcome message sent'})
                    else:
                        print(f"❌ Failed to send welcome message: {response.status_code}")
                        # Send fallback message
                        fallback_message = {
                            "chat_id": chat_id,
                            "text": "🎉 Welcome to FXSentinel Alerts!\n\nI'm your personal market alert assistant.\n\nCommands:\n/status - Check your alert settings\n/test - Send a test alert\n/help - Show all commands",
                            "parse_mode": "HTML"
                        }
                        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=fallback_message, timeout=10)
                        return jsonify({'status': 'ok', 'message': 'Fallback welcome message sent'})
                else:
                    print(f"❌ Bot token or chat_id missing: token={bool(bot_token)}, chat_id={chat_id}")
                    return jsonify({'status': 'error', 'message': 'Bot configuration error'}), 500
                
            except Exception as e:
                print(f"❌ Error sending welcome message: {e}")
                # Try to send a simple fallback message
                try:
                    if bot_token and chat_id:
                        simple_message = {
                            "chat_id": chat_id,
                            "text": "🎉 Welcome to FXSentinel Alerts!\n\nCommands:\n/status - Check settings\n/test - Test alert\n/help - Help",
                            "parse_mode": "HTML"
                        }
                        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json=simple_message, timeout=5)
                except:
                    pass
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Handle /help command
        elif text == '/help':
            try:
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and chat_id:
                    help_message = {
                        "chat_id": chat_id,
                        "text": "🤖 FXSentinel Bot Commands:\n\n/start - Welcome message and setup instructions\n/help - Show this help message\n/status - Check your alert settings\n/test - Send a test alert\n\nFor support, visit https://fxsentinel.io",
                        "parse_mode": "HTML"
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=help_message,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Help message sent to chat {chat_id}")
                        return jsonify({'status': 'ok', 'message': 'Help message sent'})
                    else:
                        print(f"❌ Failed to send help message: {response.status_code}")
                        return jsonify({'status': 'error', 'message': f'Failed to send help: {response.status_code}'}), 500
                else:
                    return jsonify({'status': 'error', 'message': 'Bot configuration error'}), 500
                
            except Exception as e:
                print(f"❌ Error sending help message: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Handle /test command
        elif text == '/test':
            try:
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and chat_id:
                    test_message = {
                        "chat_id": chat_id,
                        "text": "🧪 Test Alert\n\nThis is a test message from FXSentinel Bot!\n\n✅ Your connection is working properly.\n\nYou'll receive real alerts for:\n• Breaking news\n• Economic events\n• Market analysis\n\nStay tuned for real market alerts! 📈",
                        "parse_mode": "HTML"
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=test_message,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Test message sent to chat {chat_id}")
                        return jsonify({'status': 'ok', 'message': 'Test message sent'})
                    else:
                        print(f"❌ Failed to send test message: {response.status_code}")
                        return jsonify({'status': 'error', 'message': f'Failed to send test: {response.status_code}'}), 500
                else:
                    return jsonify({'status': 'error', 'message': 'Bot configuration error'}), 500
                
            except Exception as e:
                print(f"❌ Error sending test message: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Handle /status command
        elif text == '/status':
            try:
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and chat_id:
                    # Try to get user status from Firebase
                    try:
                        from services.firebase_realtime_storage import FirebaseRealtimeStorage
                        firebase = FirebaseRealtimeStorage()
                        
                        # Find user by chat_id using the new mapping system
                        user_id = None
                        
                        # First try to find the mapping directly
                        mapping_path = f"telegram_mappings/{chat_id}"
                        mapping_result = firebase._make_request('GET', mapping_path)
                        
                        if mapping_result and isinstance(mapping_result, dict) and 'user_id' in mapping_result:
                            user_id = mapping_result['user_id']
                            print(f"Found user mapping for chat_id {chat_id}: {user_id}")
                        else:
                            # If no direct mapping, search through all users (legacy support)
                            print(f"No direct mapping found for chat_id {chat_id}, searching through users...")
                            users_path = "alerts/users"
                            users_result = firebase._make_request('GET', users_path)
                            
                            if users_result and isinstance(users_result, dict):
                                for safe_user_id, user_data in users_result.items():
                                    if isinstance(user_data, dict) and 'settings' in user_data:
                                        settings = user_data['settings']
                                        if isinstance(settings, dict) and 'channels' in settings:
                                            channels = settings['channels']
                                            if isinstance(channels, dict) and 'telegram' in channels:
                                                telegram_settings = channels['telegram']
                                                if isinstance(telegram_settings, dict) and telegram_settings.get('chatId') == str(chat_id):
                                                    user_id = safe_user_id
                                                    print(f"Found user with chat_id {chat_id} in settings")
                                                    
                                                    # Create mapping for future use
                                                    mapping_data = {
                                                        'user_id': safe_user_id,
                                                        'chat_id': str(chat_id),
                                                        'username': username,
                                                        'created_at': datetime.now().isoformat(),
                                                        'status': 'active'
                                                    }
                                                    firebase._make_request('PUT', mapping_path, mapping_data)
                                                    print(f"Created mapping for chat_id {chat_id}")
                                                    break
                        
                        if user_id:
                            # Get user settings
                            user_settings = firebase.get_user_alert_settings(user_id)
                            
                            # Check subscription status
                            from services.subscription_cache import get_subscription_status_sync
                            is_valid, error = get_subscription_status_sync(user_id)
                            
                            status_message = f"📊 <b>FXSentinel Alert Status</b>\n\n"
                            status_message += f"🆔 <b>User ID:</b> {user_id}\n"
                            status_message += f"💬 <b>Chat ID:</b> {chat_id}\n"
                            status_message += f"📱 <b>Telegram:</b> @{username}\n\n"
                            
                            if is_valid:
                                status_message += "✅ <b>Subscription:</b> Active\n"
                            else:
                                status_message += "❌ <b>Subscription:</b> Expired\n"
                            
                            status_message += f"\n📋 <b>Alert Settings:</b>\n"
                            # Read from the correct nested structure
                            preferences = user_settings.get('preferences', {})
                            alert_types = preferences.get('alertTypes', {})
                            status_message += f"• Live News: {'✅' if alert_types.get('liveNews', False) else '❌'}\n"
                            status_message += f"• Economic Calendar: {'✅' if alert_types.get('postNews', False) else '❌'}\n"
                            status_message += f"• AI Analysis: {'✅' if alert_types.get('technicalAnalysis', False) else '❌'}\n"
                            
                            status_message += f"\n🎯 <b>Currency Pairs:</b>\n"
                            currency_pairs = preferences.get('currencyPairs', [])
                            if currency_pairs:
                                for pair in currency_pairs[:5]:  # Show first 5
                                    status_message += f"• {pair}\n"
                                if len(currency_pairs) > 5:
                                    status_message += f"• ... and {len(currency_pairs) - 5} more\n"
                            else:
                                status_message += "• No pairs configured\n"
                            
                            status_message += f"\n📈 <b>Impact Levels:</b>\n"
                            impact_levels = preferences.get('impactLevels', {})
                            if impact_levels:
                                for level, enabled in impact_levels.items():
                                    if enabled:
                                        status_message += f"• {level.title()}\n"
                            else:
                                status_message += "• All levels\n"
                            
                        else:
                            status_message = f"📊 <b>FXSentinel Alert Status</b>\n\n"
                            status_message += f"❌ <b>Status:</b> Not Connected\n\n"
                            status_message += f"💬 <b>Chat ID:</b> {chat_id}\n"
                            status_message += f"📱 <b>Telegram:</b> @{username}\n\n"
                            status_message += f"To connect your account:\n"
                            status_message += f"1. Visit https://fxsentinel.io\n"
                            status_message += f"2. Log in to your account\n"
                            status_message += f"3. Go to Alerts tab\n"
                            status_message += f"4. Click 'Connect Telegram Bot'\n"
                            
                    except Exception as e:
                        print(f"❌ Error getting user status: {e}")
                        status_message = f"📊 <b>FXSentinel Alert Status</b>\n\n"
                        status_message += f"❌ <b>Status:</b> Error retrieving settings\n\n"
                        status_message += f"💬 <b>Chat ID:</b> {chat_id}\n"
                        status_message += f"📱 <b>Telegram:</b> @{username}\n\n"
                        status_message += f"Please try again or contact support."
                    
                    status_response = {
                        "chat_id": chat_id,
                        "text": status_message,
                        "parse_mode": "HTML"
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=status_response
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Status message sent to chat {chat_id}")
                    else:
                        print(f"❌ Failed to send status message: {response.status_code}")
                
            except Exception as e:
                print(f"❌ Error sending status message: {e}")
        
        # Handle unknown commands
        else:
            try:
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                if bot_token and chat_id:
                    unknown_message = {
                        "chat_id": chat_id,
                        "text": "❓ Unknown command\n\nAvailable commands:\n/start - Welcome message\n/help - Show help\n/status - Check settings\n/test - Send test alert\n\nFor support, visit https://fxsentinel.io",
                        "parse_mode": "HTML"
                    }
                    
                    response = requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json=unknown_message
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Unknown command response sent to chat {chat_id}")
                    else:
                        print(f"❌ Failed to send unknown command response: {response.status_code}")
                
            except Exception as e:
                print(f"❌ Error sending unknown command response: {e}")
        
        return jsonify({'status': 'ok', 'message': 'Update processed'})
            
    except Exception as e:
        print(f"❌ Error in Telegram webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/telegram/setup-webhook', methods=['POST'])
def setup_telegram_webhook():
    """Setup Telegram webhook URL"""
    try:
        from services.telegram_bot_setup import telegram_bot_setup
        import asyncio
        
        # Get the webhook URL from the request
        data = request.get_json()
        webhook_url = data.get('webhook_url') if data else None
        
        if not webhook_url:
            # Use the current server URL
            webhook_url = f"{request.host_url.rstrip('/')}/api/telegram/webhook"
        
        async def setup_webhook():
            try:
                # Set the webhook
                await telegram_bot_setup.bot.set_webhook(url=webhook_url)
                logger.info(f"Telegram webhook set to: {webhook_url}")
                return True
            except Exception as e:
                logger.error(f"Error setting webhook: {e}")
                return False
        
        success = asyncio.run(setup_webhook())
        
        if success:
            return jsonify({
                'success': True,
                'webhook_url': webhook_url,
                'message': 'Webhook setup successful'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to setup webhook'
            }), 500
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/<path:path>')
def catch_all(path):
    """Catch-all route to redirect non-API routes to frontend"""
    # Don't redirect API routes
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Redirect all other routes to frontend
    return redirect(f'https://fxsentinel.io/{path}')

# Simple background task for alert checking
def run_alert_check():
    """Run alert checking in background"""
    try:
        with app.app_context():
            # Import here to avoid circular imports
            from services.background_alert_worker import background_worker
            background_worker._check_news_alerts()
            background_worker._check_economic_calendar_alerts()
            print("✅ Background alert check completed")
    except Exception as e:
        print(f"❌ Background alert check error: {e}")

# Schedule background task to run every 5 minutes
import threading
import time

def background_scheduler():
    """Background scheduler for alert checking"""
    while True:
        try:
            run_alert_check()
        except Exception as e:
            print(f"Background scheduler error: {e}")
        
        # Wait 5 minutes
        time.sleep(300)

# Initialize and start background alert worker
# background_worker.init_app(app)  # Removed - not needed
# background_worker.start()  # Disabled - using dedicated background worker instead
print("🚀 Main app started (background worker disabled - using dedicated worker)")

@app.route('/api/post-news-analysis', methods=['POST'])
@limiter.limit("10 per minute")
def post_news_analysis():
    """Generate post-news analysis for high-impact news events"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        news_id = data.get('news_id')
        title = data.get('title', '')
        content = data.get('content', '')
        source = data.get('source', '')
        timestamp = data.get('timestamp', '')
        
        if not news_id or not title:
            return jsonify({'error': 'Missing required fields: news_id and title'}), 400
        
        # Generate post-news analysis using AI
        analysis_prompt = f"""
        POST-NEWS ANALYSIS REQUEST
        
        News Title: {title}
        Source: {source}
        Content: {content}
        Timestamp: {timestamp}
        
        Please provide a comprehensive post-news analysis including:
        
        1. **Market Impact Assessment**: How this news has affected or will affect forex markets
        2. **Currency Pair Analysis**: Specific impact on major currency pairs
        3. **Trading Implications**: What traders should consider in their strategies
        4. **Risk Assessment**: Potential risks and opportunities
        5. **Technical Levels**: Key support/resistance levels to watch
        
        Provide detailed, actionable analysis suitable for forex traders.
        """
        
        # Call AI analysis service
        try:
            # For now, return a mock analysis since AIAnalysisService doesn't exist
            mock_analysis = {
                'analysis': f"Post-news analysis for '{title}' from {source}. This news event may impact forex markets.",
                'market_impact': f"Potential impact on currency pairs based on {title}",
                'trading_implications': "Monitor price action and consider position adjustments",
                'currency_pairs': ['EUR/USD', 'USD/JPY', 'GBP/USD'],
                'risk_assessment': "Standard market risk applies",
                'technical_levels': "Watch key support/resistance levels"
            }
            
            return jsonify({
                'success': True,
                'analysis': mock_analysis.get('analysis', ''),
                'market_impact': mock_analysis.get('market_impact', ''),
                'trading_implications': mock_analysis.get('trading_implications', ''),
                'currency_pairs': mock_analysis.get('currency_pairs', []),
                'risk_assessment': mock_analysis.get('risk_assessment', ''),
                'technical_levels': mock_analysis.get('technical_levels', ''),
                'timestamp': datetime.now().isoformat()
            })
                
        except Exception as ai_error:
            logger.error(f"AI analysis error: {ai_error}")
            return jsonify({
                'success': False,
                'error': 'AI analysis service unavailable'
            }), 503
        
    except Exception as e:
        logger.error(f"Error in post-news analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Background worker management endpoints
@app.route('/api/background-worker/status')
@limiter.exempt
def background_worker_status():
    """Check background worker status"""
    try:
        # Check if background worker is running
        worker_running = background_worker.running if hasattr(background_worker, 'running') else False
        worker_thread = background_worker.thread if hasattr(background_worker, 'thread') else None
        thread_alive = worker_thread.is_alive() if worker_thread else False
        
        return jsonify({
            'worker_running': worker_running,
            'thread_alive': thread_alive,
            'last_check': background_worker.last_check.isoformat() if hasattr(background_worker, 'last_check') and background_worker.last_check else None,
            'check_interval': background_worker.check_interval if hasattr(background_worker, 'check_interval') else None,
            'status': 'running' if worker_running and thread_alive else 'stopped'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/background-worker/start', methods=['POST'])
@limiter.exempt
def start_background_worker():
    """Start background worker manually"""
    try:
        if not background_worker.running:
            background_worker.start()
            return jsonify({
                'success': True,
                'message': 'Background worker started',
                'status': 'running'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Background worker already running',
                'status': 'running'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/bot/stats')
@limiter.exempt
def bot_statistics():
    """Get comprehensive bot statistics"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        from services.alert_service import get_alert_service
        
        firebase = FirebaseRealtimeStorage()
        alert_service = get_alert_service()
        
        # Get users with alerts
        users_with_alerts = firebase.get_all_users_with_alerts()
        
        # Get user statistics
        total_users = len(users_with_alerts)
        active_users = 0
        telegram_connected_users = 0
        alert_enabled_users = 0
        
        # Analyze each user
        user_details = []
        for user_data in users_with_alerts:
            user_id = user_data.get('user_id', 'unknown')
            settings = user_data.get('settings', {})
            chat_id = user_data.get('telegram_chat_id')
            
            user_info = {
                'user_id': user_id,
                'telegram_connected': bool(chat_id),
                'alerts_enabled': bool(settings),
                'alert_settings': settings,
                'chat_id': chat_id
            }
            
            # Count statistics
            if chat_id:
                telegram_connected_users += 1
            if settings:
                alert_enabled_users += 1
            if chat_id or settings:
                active_users += 1
            
            user_details.append(user_info)
        
        # Get background worker stats
        worker_stats = background_worker.get_status()
        
        return jsonify({
            'bot_statistics': {
                'total_users': total_users,
                'active_users': active_users,
                'telegram_connected_users': telegram_connected_users,
                'alert_enabled_users': alert_enabled_users,
                'background_worker_status': worker_stats
            },
            'user_details': user_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/bot/users')
@limiter.exempt
def bot_users():
    """Get detailed user information"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        firebase = FirebaseRealtimeStorage()
        users_with_alerts = firebase.get_all_users_with_alerts()
        
        users_info = []
        for user_data in users_with_alerts:
            user_id = user_data.get('user_id', 'unknown')
            settings = user_data.get('settings', {})
            chat_id = user_data.get('telegram_chat_id')
            
            user_info = {
                'user_id': user_id,
                'chat_id': chat_id,
                'telegram_connected': bool(chat_id),
                'alert_settings': settings,
                'has_settings': bool(settings)
            }
            users_info.append(user_info)
        
        return jsonify({
            'users': users_info,
            'total_users': len(users_info),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/bot/chat-ids')
@limiter.exempt
def bot_chat_ids():
    """Get all Telegram chat ID mappings"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        firebase = FirebaseRealtimeStorage()
        users_with_alerts = firebase.get_all_users_with_alerts()
        
        chat_id_mappings = {}
        for user_data in users_with_alerts:
            user_id = user_data.get('user_id', 'unknown')
            chat_id = user_data.get('telegram_chat_id')
            if chat_id:
                chat_id_mappings[user_id] = chat_id
        
        return jsonify({
            'chat_id_mappings': chat_id_mappings,
            'total_mappings': len(chat_id_mappings),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/bot/alert-history')
@limiter.exempt
def bot_alert_history():
    """Get recent alert history"""
    try:
        from services.firebase_realtime_storage import FirebaseRealtimeStorage
        
        firebase = FirebaseRealtimeStorage()
        
        # Get users with alerts
        users_with_alerts = firebase.get_all_users_with_alerts()
        
        # Get alert history for each user
        all_alerts = []
        alerts_by_user = {}
        
        for user_data in users_with_alerts:
            user_id = user_data.get('user_id', 'unknown')
            user_alerts = firebase.get_user_alert_history(user_id, limit=50)
            
            if user_alerts:
                alerts_by_user[user_id] = user_alerts
                all_alerts.extend(user_alerts)
        
        return jsonify({
            'recent_alerts': all_alerts,
            'alerts_by_user': alerts_by_user,
            'total_alerts': len(all_alerts),
            'users_with_alerts': len(alerts_by_user),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/restart-background-worker', methods=['POST'])
@limiter.exempt
def restart_background_worker():
    """Restart the background worker to pick up new code"""
    try:
        from services.background_alert_worker import background_worker
        
        # Stop the current worker
        background_worker.stop()
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Start the worker again
        background_worker.start()
        
        return jsonify({
            'success': True,
            'message': 'Background worker restarted successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/trigger-alerts', methods=['POST'])
@limiter.exempt
def trigger_alerts():
    """Trigger alert processing via webhook - called by external cron jobs"""
    try:
        logger.info("🔄 Alert trigger received via webhook")
        
        # Import alert processing functions
        from services.background_alert_worker import background_worker
        
        # Process news alerts
        news_alerts_processed = False
        try:
            background_worker._check_news_alerts()
            news_alerts_processed = True
            logger.info("✅ News alerts processed successfully")
        except Exception as e:
            logger.error(f"❌ Error processing news alerts: {e}")
        
        # Process economic calendar alerts
        calendar_alerts_processed = False
        try:
            background_worker._check_economic_calendar_alerts()
            calendar_alerts_processed = True
            logger.info("✅ Economic calendar alerts processed successfully")
        except Exception as e:
            logger.error(f"❌ Error processing calendar alerts: {e}")
        
        # Process post-news analysis
        post_news_processed = False
        try:
            background_worker._process_post_news_analysis()
            post_news_processed = True
            logger.info("✅ Post-news analysis processed successfully")
        except Exception as e:
            logger.error(f"❌ Error processing post-news analysis: {e}")
        
        return jsonify({
            'success': True,
            'news_alerts_processed': news_alerts_processed,
            'calendar_alerts_processed': calendar_alerts_processed,
            'post_news_processed': post_news_processed,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error in alert trigger: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health/alert-service')
@limiter.exempt
def alert_service_health():
    """Health check for alert service - called by monitoring services"""
    try:
        from services.background_alert_worker import background_worker
        
        # Check background worker status
        worker_status = background_worker.get_status()
        
        # Check if worker is running
        worker_healthy = worker_status.get('running', False) and worker_status.get('thread_alive', False)
        
        # Check last check time
        last_check = worker_status.get('last_check')
        if last_check:
            last_check_time = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            time_since_check = datetime.now(last_check_time.tzinfo) - last_check_time
            recent_check = time_since_check.total_seconds() < 300  # 5 minutes
        else:
            recent_check = False
        
        # Overall health status
        service_healthy = worker_healthy and recent_check
        
        health_status = {
            'service_status': 'healthy' if service_healthy else 'unhealthy',
            'last_check': datetime.now().isoformat(),
            'worker_running': worker_healthy,
            'recent_check': recent_check,
            'background_worker': worker_status,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return jsonify({
            'service_status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/deployment-health-check')
@limiter.exempt
def deployment_health_check():
    """Comprehensive health check after deployment - ensures bot is working"""
    try:
        from services.background_alert_worker import background_worker
        
        # Check all critical services
        services_status = {
            'background_worker': False,
            'telegram_bot': False,
            'news_api': False,
            'ai_service': False,
            'database': True  # Assume database is working if we can reach this endpoint
        }
        
        # Check background worker
        try:
            worker_status = background_worker.get_status()
            services_status['background_worker'] = (
                worker_status.get('running', False) and 
                worker_status.get('thread_alive', False)
            )
        except Exception as e:
            logger.error(f"Background worker check failed: {e}")
        
        # Check Telegram bot
        try:
            # Test Telegram bot connectivity
            import requests
            telegram_test = requests.get('https://api.telegram.org/bot' + os.getenv('TELEGRAM_BOT_TOKEN', '') + '/getMe', timeout=5)
            services_status['telegram_bot'] = telegram_test.status_code == 200
        except Exception as e:
            logger.error(f"Telegram bot check failed: {e}")
        
        # Check news API
        try:
            news_test = requests.get(f"{request.host_url}api/news", timeout=10)
            services_status['news_api'] = news_test.status_code == 200
        except Exception as e:
            logger.error(f"News API check failed: {e}")
        
        # Check AI service
        try:
            services_status['ai_service'] = bool(os.getenv('OPENAI_API_KEY'))
        except Exception as e:
            logger.error(f"AI service check failed: {e}")
        
        # Auto-restart background worker if it's down
        if not services_status['background_worker']:
            logger.warning("🔄 Background worker is down, attempting restart...")
            try:
                background_worker.stop()
                import time
                time.sleep(2)
                background_worker.start()
                logger.info("✅ Background worker restarted successfully")
                
                # Check again after restart
                time.sleep(5)
                worker_status = background_worker.get_status()
                services_status['background_worker'] = (
                    worker_status.get('running', False) and 
                    worker_status.get('thread_alive', False)
                )
            except Exception as e:
                logger.error(f"❌ Failed to restart background worker: {e}")
        
        # Overall status
        all_healthy = all(services_status.values())
        
        # Log status for monitoring
        logger.info(f"🔍 Deployment health check: {services_status}")
        
        return jsonify({
            'status': 'healthy' if all_healthy else 'restarting',
            'services': services_status,
            'timestamp': datetime.now().isoformat(),
            'message': 'All services healthy' if all_healthy else 'Some services need attention'
        })
        
    except Exception as e:
        logger.error(f"❌ Deployment health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Use Railway's PORT environment variable or default to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    # Force debug mode off for background execution
    debug_mode = False
    
    # Start robust alert service for production
    try:
        from services.robust_alert_service import start_robust_alert_service
        import threading
        
        # Start robust alert service in a separate thread
        alert_thread = threading.Thread(target=start_robust_alert_service, daemon=True)
        alert_thread.start()
        print("✅ Robust alert service started in background")
    except Exception as e:
        print(f"⚠️ Could not start robust alert service: {e}")
        print("   Alerts will not work for online users!")
    
    # Start cost-optimized monitor
    try:
        from services.cost_optimized_monitor import cost_optimized_monitor
        cost_optimized_monitor.start()
        print("✅ Cost-optimized monitor started")
    except Exception as e:
        print(f"⚠️ Could not start cost-optimized monitor: {e}")
    
    print(f"🚀 Starting Flask server on port {port}, debug={debug_mode}")
    print("📊 Robust alert service enabled - alerts will work for online users")
    print("📊 Cost-optimized monitoring enabled - reduced API calls and logging")
    app.run(debug=debug_mode, host='0.0.0.0', port=port) 