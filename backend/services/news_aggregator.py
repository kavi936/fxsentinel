import requests
import feedparser
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsAggregator:
    def __init__(self):
        self.rss_feeds = {
            'reuters': {
                'url': 'https://feeds.reuters.com/reuters/businessNews',
                'name': 'Reuters',
                'forex_keywords': ['forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe']
            },
            'bloomberg': {
                'url': 'https://feeds.bloomberg.com/markets/news.rss',
                'name': 'Bloomberg',
                'forex_keywords': ['forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe']
            },
            'cnbc': {
                'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'name': 'CNBC',
                'forex_keywords': ['forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe']
            },
            'marketwatch': {
                'url': 'https://feeds.marketwatch.com/marketwatch/marketpulse/',
                'name': 'MarketWatch',
                'forex_keywords': ['forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe']
            }
        }
        
        # Forex-specific keywords for filtering
        self.forex_keywords = [
            'forex', 'currency', 'dollar', 'euro', 'yen', 'pound', 'franc', 'australian dollar', 'canadian dollar',
            'cpi', 'inflation', 'interest rate', 'fed', 'ecb', 'boj', 'boe', 'rba', 'boc', 'snb',
            'eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd',
            'non-farm payrolls', 'gdp', 'retail sales', 'manufacturing', 'services pmi',
            'unemployment', 'employment', 'wages', 'trade balance', 'current account'
        ]
        
        # Impact keywords for categorizing news
        self.high_impact_keywords = ['cpi', 'inflation', 'fed', 'ecb', 'boj', 'boe', 'interest rate', 'non-farm payrolls', 'gdp']
        self.medium_impact_keywords = ['retail sales', 'manufacturing', 'services pmi', 'unemployment', 'employment', 'trade balance']
        
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
            
            for entry in feed.entries[:10]:  # Limit to 10 most recent articles
                # Check if article is forex-related
                if self.is_forex_related(entry.title, entry.summary):
                    article = self.parse_article(entry, source_name)
                    if article:
                        articles.append(article)
            
            logger.info(f"Fetched {len(articles)} forex-related articles from {source_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed from {source_name}: {str(e)}")
            return []
    
    def is_forex_related(self, title: str, summary: str) -> bool:
        """Check if article is forex-related based on keywords"""
        text = f"{title} {summary}".lower()
        
        # Check for forex-specific keywords
        for keyword in self.forex_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def determine_impact_level(self, title: str, summary: str) -> str:
        """Determine the impact level of the news"""
        text = f"{title} {summary}".lower()
        
        # Check for high impact keywords
        for keyword in self.high_impact_keywords:
            if keyword.lower() in text:
                return 'high'
        
        # Check for medium impact keywords
        for keyword in self.medium_impact_keywords:
            if keyword.lower() in text:
                return 'medium'
        
        return 'low'
    
    def extract_currency_pairs(self, title: str, summary: str) -> List[str]:
        """Extract mentioned currency pairs from the article"""
        text = f"{title} {summary}".lower()
        currency_pairs = []
        
        # Common currency pair patterns
        pairs = ['eur/usd', 'usd/jpy', 'gbp/usd', 'usd/chf', 'aud/usd', 'usd/cad', 'nzd/usd', 'eur/gbp', 'eur/jpy', 'gbp/jpy']
        
        for pair in pairs:
            if pair in text:
                currency_pairs.append(pair.upper())
        
        return currency_pairs
    
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
                'id': abs(article_id),  # Ensure positive ID
                'title': title,
                'summary': summary[:200] + '...' if len(summary) > 200 else summary,
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
    
    def aggregate_news(self) -> List[Dict[str, Any]]:
        """Aggregate news from all RSS feeds"""
        all_articles = []
        
        for feed_key, feed_config in self.rss_feeds.items():
            try:
                articles = self.fetch_rss_feed(feed_config['url'], feed_config['name'])
                all_articles.extend(articles)
            except Exception as e:
                logger.error(f"Error aggregating from {feed_key}: {str(e)}")
                continue
        
        # Sort by publication date (newest first)
        all_articles.sort(key=lambda x: x['published_at'], reverse=True)
        
        # Remove duplicates based on title similarity
        unique_articles = self.remove_duplicates(all_articles)
        
        logger.info(f"Aggregated {len(unique_articles)} unique forex articles")
        return unique_articles
    
    def remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Create a simplified title for comparison
            simple_title = re.sub(r'[^\w\s]', '', article['title'].lower())
            words = simple_title.split()[:5]  # First 5 words
            title_key = ' '.join(words)
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles
    
    def get_recent_news(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get news from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        all_articles = self.aggregate_news()
        recent_articles = []
        
        for article in all_articles:
            try:
                pub_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                if pub_date >= cutoff_time:
                    recent_articles.append(article)
            except:
                # If date parsing fails, include the article
                recent_articles.append(article)
        
        return recent_articles[:20]  # Limit to 20 most recent articles

# Global instance
news_aggregator = NewsAggregator()
