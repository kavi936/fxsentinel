from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import openai
import os
import json
import time

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
CORS(app)

# Configure OpenAI (you'll need to set OPENAI_API_KEY environment variable)
openai.api_key = os.getenv('OPENAI_API_KEY')

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

@app.route('/api/news')
def get_news():
    """Get real economic events data"""
    try:
        events = scrape_forexfactory_events()
        return jsonify({
            "news": events,
            "last_updated": datetime.now().isoformat(),
            "source": "ForexFactory"
        })
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({
            "news": get_mock_news(),
            "last_updated": datetime.now().isoformat(),
            "source": "mock_data"
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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React app for all non-API routes"""
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True) 