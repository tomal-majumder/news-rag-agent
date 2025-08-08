import feedparser
import requests
from datetime import datetime
import hashlib
import logging
from typing import List, Optional
from app.databases.models import NewsArticle

# Description: Service to fetch and parse news articles from RSS feeds
# Handles multiple sources and formats
# Cleans HTML content to extract readable text
class NewsScraperService:
    def __init__(self):
        # RSS feeds from various sources
        self.rss_feeds = [
            #{"url": "https://feeds.nbcnews.com/nbcnews/public/news", "source": "NBC News"},
            #{"url": "https://www.cnbc.com/id/100727362/device/rss/rss.html", "source": "CNBC World"},
            {"url": "https://feeds.bbci.co.uk/news/rss.xml", "source": "BBC News"},
            # {"url": "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/world/rss.xml", "source": "NY Times"},
        ]
    
    def fetch_articles_from_rss(self, max_articles: int = 200) -> List[dict]:
        """Fetch articles from RSS feeds"""
        articles = []
        
        for feed_info in self.rss_feeds:
            
            try:
                feed = feedparser.parse(feed_info["url"])                
                for entry in feed.entries[:100]:  # Limit per source
                    #rint("Printing entry:")  # Debugging line  
                    #print(entry)  # Debugging line to see the entry structure
                    article_data = {
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "source": feed_info["source"],
                        "body": entry.get("summary", entry.get("description", "")),
                        "published_at": self._parse_date(entry.get("published")),
                    }
                    
                    # Skip if essential data is missing
                    if article_data["title"] and article_data["url"]:
                        articles.append(article_data)
                
                if len(articles) >= max_articles:
                    break
                    
            except Exception as e:
                logging.error(f"Error fetching from {feed_info['url']}: {e}")
        
        return articles[:max_articles]
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parse various date formats"""
        if not date_string:
            return datetime.now()
            
        try:
            # Try different date formats
            for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%SZ"]:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If all fail, use current time
            return datetime.now()
            
        except Exception:
            return datetime.now()
