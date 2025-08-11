from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import openai
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure CORS to allow requests from Vercel
CORS(app, origins=[
    "http://localhost:5173",  # Local development
    "http://localhost:3000",  # Alternative local port
    "https://fxsentinel.io",  # Your custom domain
    "https://www.fxsentinel.io",  # Your custom domain with www
    "https://*.vercel.app",  # Any Vercel subdomain (for preview deployments)
    "https://*.railway.app"  # Any Railway subdomain
], methods=["GET", "POST", "OPTIONS"], supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and (origin.startswith('https://fxsentinel.io') or 
                   origin.startswith('https://www.fxsentinel.io') or
                   origin.endswith('.vercel.app') or
                   origin.endswith('.railway.app') or
                   origin.startswith('http://localhost')):
        response.headers.add('Access-Control-Allow-Origin', origin)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
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

def scrape_forexfactory_events():
    """Scrape upcoming economic events from ForexFactory"""
    try:
        # ForexFactory economic calendar URL
        url = "https://www.forexfactory.com/calendar"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find economic calendar events
        calendar_rows = soup.find_all('tr', class_='calendar__row')
        
        for row in calendar_rows[:10]:  # Limit to 10 events for MVP
            try:
                # Extract event details
                event_cell = row.find('td', class_='calendar__event')
                if not event_cell:
                    continue
                    
                event_name = event_cell.get_text(strip=True)
                
                # Extract currency
                currency_cell = row.find('td', class_='calendar__currency')
                currency = currency_cell.get_text(strip=True) if currency_cell else "USD"
                
                # Extract impact
                impact_cell = row.find('td', class_='calendar__impact')
                impact = "Medium"
                if impact_cell:
                    impact_icons = impact_cell.find_all('span', class_='icon--ff-impact-red')
                    if len(impact_icons) >= 3:
                        impact = "High"
                    elif len(impact_icons) >= 1:
                        impact = "Medium"
                    else:
                        impact = "Low"
                
                # Extract time
                time_cell = row.find('td', class_='calendar__time')
                event_time = time_cell.get_text(strip=True) if time_cell else "00:00"
                
                # Generate event ID
                event_id = len(events) + 1
                
                events.append({
                    "id": event_id,
                    "title": event_name,
                    "description": f"{event_name} - {currency} Economic Event",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": event_time,
                    "impact": impact,
                    "currency": currency,
                    "pairs": get_currency_pairs(currency),
                    "expected": "TBD",
                    "previous": "TBD"
                })
                
            except Exception as e:
                print(f"Error parsing event: {e}")
                continue
                
        return events
        
    except Exception as e:
        print(f"Error scraping ForexFactory: {e}")
        # Fallback to mock data if scraping fails
        return get_mock_news()

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

def generate_ai_analysis(event_title, currency, impact):
    """Generate AI analysis using OpenAI GPT-3.5-turbo"""
    try:
        if not openai.api_key:
            return get_mock_analysis(event_title)
        
        prompt = f"""
        Analyze the potential market impact of this economic event:
        Event: {event_title}
        Currency: {currency}
        Impact Level: {impact}
        
        Provide a concise analysis including:
        1. Brief summary of what this event means
        2. Potential impact on EUR/USD
        3. Potential impact on USD/JPY  
        4. Potential impact on Gold
        5. Confidence level (as a percentage)
        
        Format as JSON with keys: summary, eur_usd_impact, usd_jpy_impact, gold_impact, confidence
        Keep each response under 100 words.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a forex market analyst. Provide concise, actionable analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        analysis_text = response.choices[0].message.content
        
        # Try to parse JSON response
        try:
            analysis = json.loads(analysis_text)
            return analysis
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured text
            return {
                "summary": analysis_text[:200] + "...",
                "eur_usd_impact": "Analysis available",
                "usd_jpy_impact": "Analysis available", 
                "gold_impact": "Analysis available",
                "confidence": "75%"
            }
            
    except Exception as e:
        print(f"Error generating AI analysis: {e}")
        return get_mock_analysis(event_title)

def get_mock_analysis(event_title):
    """Fallback mock analysis if AI fails"""
    return {
        "summary": f"Analysis for {event_title} - This economic event could impact currency markets based on the data release and market expectations.",
        "eur_usd_impact": "Monitor for volatility around release time",
        "usd_jpy_impact": "Potential movement based on data outcome",
        "gold_impact": "Safe haven flows may be affected",
        "confidence": "70%"
    }

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from FXSentinel backend!'})

# Import the news aggregator
from services.news_aggregator import news_aggregator
# Import the telegram monitor
from services.telegram_monitor_user import telegram_user_monitor

@app.route('/api/news')
def get_news():
    """Get aggregated news from multiple sources with optimized performance"""
    try:
        # Import cache system
        from services.news_cache import news_cache
        
        # First, try to get cached data immediately
        cached_news = news_cache.load_news()
        if cached_news:
            print(f"✅ Returning cached news ({len(cached_news)} articles)")
            return jsonify({
                "news": cached_news,
                "last_updated": datetime.now().isoformat(),
                "sources": ["cached_data"],
                "total_articles": len(cached_news),
                "cache_status": "cached"
            })
        
        # If no cache, fetch fresh data with optimized parallel processing
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
        
        # Function to fetch ForexFactory events with timeout
        def fetch_forex_events():
            try:
                forex_events = scrape_forexfactory_events()
                print(f"✅ Fetched {len(forex_events)} ForexFactory events")
                return forex_events
            except Exception as e:
                print(f"❌ Error fetching ForexFactory events: {e}")
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks with 10-second timeout each
            rss_future = executor.submit(fetch_rss_news)
            forex_future = executor.submit(fetch_forex_events)
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
                forex_events = forex_future.result(timeout=10)
                fresh_news.extend(forex_events)
                sources_used.append("ForexFactory")
            except concurrent.futures.TimeoutError:
                print("⚠️ ForexFactory fetch timed out")
                forex_events = []
            except Exception as e:
                print(f"❌ ForexFactory fetch failed: {e}")
                forex_events = []
            
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
            
            # Save to cache for future use
            news_cache.save_news(all_news)
            
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

@app.route('/api/analysis/<int:news_id>')
def get_analysis(news_id):
    """Generate AI analysis for specific news event"""
    try:
        # Get the news event
        events = scrape_forexfactory_events()
        event = next((e for e in events if e['id'] == news_id), None)
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        # Generate AI analysis
        analysis = generate_ai_analysis(
            event['title'], 
            event['currency'], 
            event['impact']
        )
        
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return jsonify(get_mock_analysis("Economic Event"))

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

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

@app.route('/api/alert-settings', methods=['GET', 'POST'])
def alert_settings():
    """Get or update alert settings"""
    if request.method == 'GET':
        # Return default settings
        return jsonify({
            "telegram": True,
            "email": False,
            "highImpact": True,
            "mediumImpact": True,
            "lowImpact": False,
            "notificationTime": 15  # minutes before event
        })
    
    elif request.method == 'POST':
        # Update settings (mock implementation)
        settings = request.json
        # In production, save to database
        return jsonify({
            "message": "Settings updated successfully",
            "settings": settings
        })

@app.route('/api/forex-prices', methods=['GET', 'OPTIONS'])
def get_forex_prices():
    """Get real-time forex prices from multiple sources for better accuracy"""
    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        # Try to get data from multiple sources for better accuracy
        prices = {}
        data_sources_used = []
        unirate_rate_limited = False
        
        # Check UniRateAPI rate limits first
        can_make_unirate_call, reason = check_unirate_rate_limits()
        if not can_make_unirate_call:
            print(f"⚠️ UniRateAPI rate limit exceeded: {reason}")
            unirate_rate_limited = True
        
        # Try to get data from multiple sources for better accuracy
        prices = {}
        data_sources_used = []
        
        # Source 1: TradingView API (real-time forex market data)
        try:
            tradingview_prices = get_tradingview_prices()
            if tradingview_prices:
                prices.update(tradingview_prices)
                data_sources_used.append('TradingView')
                print(f"✅ Successfully fetched data from TradingView: {len(tradingview_prices)} pairs")
                print(f"   TradingView pairs: {list(tradingview_prices.keys())}")
        except Exception as e:
            print(f"❌ TradingView failed: {e}")
        
        # Source 2: Alpha Vantage (if keys are configured)
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
        
        # Source 3: UniRateAPI (exchange rates) - only if not rate limited
        if not unirate_rate_limited:
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
        else:
            print("⏭️ Skipping UniRateAPI due to rate limits")
        
        # Source 4: ExchangeRateAPI as fallback
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
        
        # If we still don't have all pairs, use fallback
        required_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD',
            'USDCAD', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY',
            'USDSEK', 'USDNOK', 'USDHKD', 'EURCHF', 'GBPCHF'
        ]
        
        # Ensure we have all required pairs by using fallback for missing ones
        for pair in required_pairs:
            if pair not in prices:
                print(f"⚠️ Missing pair {pair}, using fallback data")
                prices[pair] = get_fallback_price(pair)
                if 'fallback' not in data_sources_used:
                    data_sources_used.append('fallback')
        
        print(f"✅ Final result: {len(prices)} pairs available: {list(prices.keys())}")
        
        # Add data freshness information
        for pair in prices:
            if 'lastUpdate' in prices[pair]:
                try:
                    last_update = datetime.fromisoformat(prices[pair]['lastUpdate'].replace('Z', '+00:00'))
                    age_minutes = (datetime.now(last_update.tzinfo) - last_update).total_seconds() / 60
                    prices[pair]['dataAgeMinutes'] = round(age_minutes, 1)
                    
                    # Check if market is likely closed (weekend or outside trading hours)
                    current_time = datetime.now(last_update.tzinfo)
                    is_weekend = current_time.weekday() >= 5  # Saturday = 5, Sunday = 6
                    is_market_hours = 0 <= current_time.hour <= 23  # Simplified market hours check
                    
                    # During market hours: data is stale after 60 minutes (more lenient)
                    # During market closure: data is stale after 4 hours (more lenient)
                    stale_threshold = 240 if (is_weekend or not is_market_hours) else 60
                    moderate_threshold = 60 if (is_weekend or not is_market_hours) else 15
                    
                    prices[pair]['isStale'] = age_minutes > stale_threshold
                    prices[pair]['isModeratelyOld'] = moderate_threshold < age_minutes <= stale_threshold
                    prices[pair]['isMarketClosed'] = is_weekend or not is_market_hours
                except:
                    prices[pair]['dataAgeMinutes'] = None
                    prices[pair]['isStale'] = True
                    prices[pair]['isModeratelyOld'] = False
                    prices[pair]['isMarketClosed'] = False
        
        return jsonify({
            'prices': prices,
            'dataSource': ' + '.join(data_sources_used) if data_sources_used else 'fallback',
            'timestamp': datetime.now().isoformat(),
            'dataQuality': {
                'hasStaleData': any(p.get('isStale', False) for p in prices.values()),
                'hasModeratelyOldData': any(p.get('isModeratelyOld', False) for p in prices.values()),
                'isMarketClosed': any(p.get('isMarketClosed', False) for p in prices.values()),
                'averageAgeMinutes': sum(p.get('dataAgeMinutes', 0) for p in prices.values()) / len(prices) if prices else 0
            }
        })
        
    except Exception as e:
        print(f"Error in forex prices endpoint: {e}")
        # Return fallback data
        fallback_prices = {
            'EURUSD': {'price': 1.0923, 'change': 0.0012, 'lastUpdate': datetime.now().isoformat()},
            'USDJPY': {'price': 147.85, 'change': -0.08, 'lastUpdate': datetime.now().isoformat()},
            'GBPUSD': {'price': 1.2712, 'change': -0.0020, 'lastUpdate': datetime.now().isoformat()}
        }
        
        # Add data quality info for fallback data
        for pair in fallback_prices:
            try:
                last_update = datetime.fromisoformat(fallback_prices[pair]['lastUpdate'].replace('Z', '+00:00'))
                current_time = datetime.now(last_update.tzinfo)
                is_weekend = current_time.weekday() >= 5
                is_market_hours = 0 <= current_time.hour <= 23
                fallback_prices[pair]['isMarketClosed'] = is_weekend or not is_market_hours
            except:
                fallback_prices[pair]['isMarketClosed'] = False
        
        return jsonify({
            'prices': fallback_prices,
            'dataSource': 'fallback',
            'timestamp': datetime.now().isoformat(),
            'dataQuality': {
                'hasStaleData': False,
                'hasModeratelyOldData': False,
                'isMarketClosed': any(p.get('isMarketClosed', False) for p in fallback_prices.values()),
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
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
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

if __name__ == '__main__':
    app.run(debug=True, port=8000) 