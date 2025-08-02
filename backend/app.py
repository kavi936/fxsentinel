from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from Flask backend!'})

@app.route('/api/news')
def get_news():
    """Mock news data for MVP - will be replaced with real API calls"""
    today = datetime.now()
    
    mock_news = [
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
        },
        {
            "id": 3,
            "title": "UK GDP Preliminary",
            "description": "UK Gross Domestic Product Q4 2024",
            "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "time": "09:30 UTC",
            "impact": "Medium",
            "currency": "GBP",
            "pairs": ["GBP/USD", "EUR/GBP"],
            "expected": "0.2%",
            "previous": "0.1%"
        },
        {
            "id": 4,
            "title": "BoJ Policy Rate Decision",
            "description": "Bank of Japan monetary policy meeting",
            "date": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
            "time": "03:00 UTC",
            "impact": "High",
            "currency": "JPY",
            "pairs": ["USD/JPY", "EUR/JPY"],
            "expected": "-0.10%",
            "previous": "-0.10%"
        }
    ]
    
    return jsonify({
        "news": mock_news,
        "last_updated": datetime.now().isoformat()
    })

@app.route('/api/analysis/<int:news_id>')
def get_analysis(news_id):
    """Mock AI analysis for news events"""
    analyses = {
        1: {
            "summary": "US CPI expected to show continued disinflation trend. Lower than expected reading could weaken USD as Fed may consider earlier rate cuts.",
            "eur_usd_impact": "Bullish EUR/USD if CPI comes in below 3.1%",
            "usd_jpy_impact": "Bearish USD/JPY on lower CPI reading",
            "gold_impact": "Gold likely to gain on USD weakness",
            "confidence": "75%"
        },
        2: {
            "summary": "ECB likely to maintain current rates but may signal future dovish stance. Focus on forward guidance and inflation projections.",
            "eur_usd_impact": "Potential EUR weakness if ECB signals dovish outlook",
            "usd_jpy_impact": "Indirect impact through EUR/USD correlation",
            "gold_impact": "Limited direct impact on gold",
            "confidence": "80%"
        },
        3: {
            "summary": "UK GDP growth expected to show modest improvement. Stronger than expected reading could support GBP.",
            "eur_usd_impact": "Indirect impact through GBP/USD correlation",
            "usd_jpy_impact": "Limited direct impact",
            "gold_impact": "Minimal impact on gold prices",
            "confidence": "65%"
        },
        4: {
            "summary": "BoJ likely to maintain ultra-loose policy. Any hints of future tightening could significantly strengthen JPY.",
            "eur_usd_impact": "Indirect impact through USD/JPY correlation",
            "usd_jpy_impact": "Highly sensitive to BoJ forward guidance",
            "gold_impact": "JPY strength could pressure gold in USD terms",
            "confidence": "70%"
        }
    }
    
    return jsonify(analyses.get(news_id, {"error": "Analysis not found"}))

if __name__ == '__main__':
    app.run(debug=True) 