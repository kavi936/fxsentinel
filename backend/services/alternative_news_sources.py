#!/usr/bin/env python3
"""
Alternative news sources for forex news
These sources don't require authentication and are more reliable
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class AlternativeNewsSources:
    def __init__(self):
        # Forex-specific RSS feeds and news sources
        self.news_sources = {
            'forexlive': {
                'url': 'https://www.forexlive.com/feed/',
                'name': 'ForexLive',
                'type': 'rss'
            },
            'fxstreet': {
                'url': 'https://www.fxstreet.com/rss',
                'name': 'FXStreet',
                'type': 'rss'
            },
            'investing_forex': {
                'url': 'https://www.investing.com/rss/news_forex.rss',
                'name': 'Investing.com Forex',
                'type': 'rss'
            },
            'marketwatch_forex': {
                'url': 'https://feeds.marketwatch.com/marketwatch/marketpulse/',
                'name': 'MarketWatch',
                'type': 'rss'
            }
        }
        
        # Forex keywords for filtering
        self.forex_keywords = [
            'forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'franc',
            'cpi', 'inflation', 'interest rate', 'fed', 'ecb', 'boj', 'boe',
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad',
            'non-farm payrolls', 'gdp', 'retail sales', 'manufacturing',
            'unemployment', 'employment', 'wages', 'trade balance', 'trump',
            'tariffs', 'trade war', 'economic policy'
        ]
        
        # Impact keywords
        self.high_impact_keywords = ['cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp', 'trump', 'tariffs']
        self.medium_impact_keywords = ['retail sales', 'manufacturing', 'unemployment', 'employment', 'trade balance']
        
    def is_forex_related(self, title: str, summary: str, source: str = "") -> bool:
        """Check if article is forex-related using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        return enhanced_forex_filter.is_forex_related(title, summary, source)
    
    def determine_impact_level(self, title: str, summary: str) -> str:
        """Determine impact level using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        score = enhanced_forex_filter.get_forex_score(title, summary)
        return score['impact_level']
    
    def extract_currency_pairs(self, title: str, summary: str) -> List[str]:
        """Extract currency pairs using enhanced filtering"""
        from .enhanced_forex_filter import enhanced_forex_filter
        return enhanced_forex_filter.extract_currency_pairs(title, summary)
    
    def fetch_rss_feed(self, feed_url: str, source_name: str) -> List[Dict[str, Any]]:
        """Fetch and parse RSS feed"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            articles = []
            
            for entry in feed.entries[:15]:  # Limit to 15 most recent articles
                # Check if article is forex-related using improved filtering
                if self.is_forex_related(entry.title, entry.summary, source_name):
                    article = self.parse_article(entry, source_name)
                    if article:
                        articles.append(article)
            
            logger.info(f"Fetched {len(articles)} forex-related articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed from {source_name}: {str(e)}")
            return []
    
    def parse_article(self, entry, source_name: str) -> Dict[str, Any]:
        """Parse RSS entry into standardized format"""
        try:
            # Parse publication date
            pub_date = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            
            # Clean title and summary
            title = entry.title.strip() if hasattr(entry, 'title') else ''
            summary = entry.summary.strip() if hasattr(entry, 'summary') else ''
            
            # Remove HTML tags from summary
            summary = re.sub(r'<[^>]+>', '', summary)
            
            # Determine impact level
            impact = self.determine_impact_level(title, summary)
            
            # Extract currency pairs
            currency_pairs = self.extract_currency_pairs(title, summary)
            
            # Generate unique ID
            article_id = hash(f"{source_name}_{title}_{pub_date.isoformat()}")
            
            return {
                'id': abs(article_id),
                'title': title,
                'summary': summary[:800] + '...' if len(summary) > 800 else summary,  # Increased from 200 to 800 characters for more detailed descriptions
                'source': source_name,
                'url': entry.link if hasattr(entry, 'link') else '',
                'published_at': pub_date.isoformat(),
                'impact': impact,
                'currency_pairs': currency_pairs,
                'type': 'RSS_FEED',
                'status': 'PUBLISHED'
            }
            
        except Exception as e:
            logger.error(f"Error parsing article from {source_name}: {str(e)}")
            return None
    
    def get_alternative_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get news from alternative sources"""
        all_articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for source_key, source_config in self.news_sources.items():
            try:
                if source_config['type'] == 'rss':
                    articles = self.fetch_rss_feed(source_config['url'], source_config['name'])
                    all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error fetching from {source_key}: {str(e)}")
                continue
        
        # Filter by time and remove duplicates
        recent_articles = []
        seen_titles = set()
        
        for article in all_articles:
            try:
                pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                if pub_date >= cutoff_time:
                    # Simple deduplication based on title
                    title_key = article['title'][:50].lower()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        recent_articles.append(article)
            except:
                # If date parsing fails, include the article
                recent_articles.append(article)
        
        # Sort by date (newest first)
        recent_articles.sort(key=lambda x: x['published_at'], reverse=True)
        
        logger.info(f"Retrieved {len(recent_articles)} alternative news articles")
        return recent_articles[:30]  # Increased from 20 to 30 most recent

# Global instance
alternative_news_sources = AlternativeNewsSources()
