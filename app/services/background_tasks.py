import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.databases.database import SessionLocal
from app.databases.crud import NewsService
from app.services.ai_services import AIService
from app.services.news_scappers import NewsScraperService
from app.databases.models import NewsArticle
from sqlalchemy.orm import Session
import logging
from app.services.fetch_bbc_content import fetch_clean_article_content
# Background task service to handle periodic tasks like fetching news and processing articles
# This service uses APScheduler to run tasks in the background without blocking the main application
# It fetches news articles from RSS feeds and processes them using AI for classification and summarization
# The service is designed to run periodically, fetching new articles and processing unprocessed ones
# It also handles database interactions for storing and updating news articles
# The service is initialized at application startup and runs in the background
# It uses SQLAlchemy for database operations and logging for error handling and status updates
class BackgroundTaskService:
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.ai_service = AIService()
        self.scraper_service = NewsScraperService()
        self.news_service = NewsService()
    
    def start(self):
        """Start background tasks"""
        # Fetch new articles daily at 6 AM
        # what to do if want to run every 6 hours
        # self.scheduler.add_job(
        self.scheduler.add_job(
            self.fetch_and_process_news,
            'cron',
            hour='0,6,12,18', # this will run every 6 hours
            minute=0,
            id='fetch_news'
        )
        
        # Process unprocessed articles every hour
        self.scheduler.add_job(
            self.process_pending_articles,
            'interval',
            hours=1,
            id='process_articles'
        )
        
        self.scheduler.start()
        logging.info("Background tasks started")
    
    async def fetch_and_process_news(self):
        """Fetch new articles and queue for processing"""
        logging.info("Starting daily news fetch...")
        print("Starting daily news fetch...")
        db = SessionLocal()
        try:
            # Fetch articles from RSS feeds
            raw_articles = self.scraper_service.fetch_articles_from_rss(max_articles=200)
            # returned raw_articles, each article is a dict with keys: title, url, source, body, published_at
            new_count = 0
            for article_data in raw_articles:
                try:
                    # Check if article already exists
                    existing = db.query(NewsArticle).filter(
                        NewsArticle.url == article_data["url"]
                    ).first()
                    
                    if not existing:
                        # Save new article to database
                        if article_data.get("url"):
                            # here, if the article has a URL, we can fetch the full content
                            # This is optional, but recommended for better summaries
                            # and topic classification
                            # Fetch full article content
                            # This is a blocking call, consider making it async if needed
                            # How asynchronous call would look like
                            # article_data["body"] = await self.scraper_service.fetch_full_article_content(article_data["url"])
                            cleaned_text = await fetch_clean_article_content(article_data["url"])
                            if cleaned_text != "Content not found":
                                article_data["body"] = cleaned_text
                            
                        self.news_service.create_article(db, article_data)
                        new_count += 1
                        
                except Exception as e:
                    logging.error(f"Error saving article: {e}")
                    
            logging.info(f"Added {new_count} new articles")
            
        finally:
            db.close()
    
    async def process_pending_articles(self):
        """Process articles that need AI classification/summarization"""
        logging.info("Processing pending articles...")
        
        db = SessionLocal()
        try:
            # Get unprocessed articles
            unprocessed = self.news_service.get_unprocessed_articles(db, limit=20)
            
            if not unprocessed:
                logging.info("No articles to process")
                return
            
            # Process with AI
            results = await self.ai_service.batch_process_articles(unprocessed)
            
            # Update database
            for article_id, topic, summary in results:
                self.news_service.update_article_ai_data(db, article_id, topic, summary)
            
            logging.info(f"Processed {len(results)} articles")
            
        finally:
            db.close()

