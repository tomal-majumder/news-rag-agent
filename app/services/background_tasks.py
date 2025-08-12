import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.databases.database import SessionLocal
from app.databases.crud import NewsService
from app.services.ai_services import AIService
from app.services.vector_service import VectorService 
from app.services.news_scappers import NewsScraperService
from app.databases.models import NewsArticle
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from app.services.fetch_bbc_content import fetch_clean_article_content
from datetime import datetime, timedelta

class BackgroundTaskService:
    
    def __init__(self, vector_service: VectorService = None):
        self.scheduler = AsyncIOScheduler()
        self.ai_service = AIService()
        self.vector_service = vector_service or VectorService()
        self.scraper_service = NewsScraperService()
        self.news_service = NewsService()
    
    def start(self):
        """Start background tasks"""
        # Fetch new articles every 6 hours
        self.scheduler.add_job(
            self.fetch_and_process_news,
            'cron',
            hour='0,6,12,18',
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
        
        # Process articles for vector embeddings every 2 hours
        self.scheduler.add_job(
            self.process_vectors_for_articles,
            'interval',
            hours=2,
            id='process_vectors'
        )
        
        # Cleanup old content daily at 3 AM (free tier management)
        self.scheduler.add_job(
            self.cleanup_old_content,
            'cron',
            hour=3,
            minute=0,
            id='cleanup_old_content'
        )
        
        # Weekly comprehensive cleanup (Sundays at 4 AM)
        self.scheduler.add_job(
            self.weekly_maintenance,
            'cron',
            day_of_week=6,  # Sunday
            hour=4,
            minute=0,
            id='weekly_maintenance'
        )
        
        self.scheduler.start()
        logging.info("Background tasks started")
    
    async def fetch_and_process_news(self):
        """Fetch new articles and queue for processing"""
        logging.info("Starting news fetch...")
        print("Starting news fetch...")
        db = SessionLocal()
        try:
            # Fetch articles from RSS feeds
            raw_articles = self.scraper_service.fetch_articles_from_rss(max_articles=200)
            new_count = 0
            
            for article_data in raw_articles:
                try:
                    # Check if article already exists
                    existing = db.query(NewsArticle).filter(
                        NewsArticle.url == article_data["url"]
                    ).first()
                    
                    if not existing:
                        # Fetch full article content
                        if article_data.get("url"):
                            cleaned_text = await fetch_clean_article_content(article_data["url"])
                            if cleaned_text != "Content not found":
                                article_data["body"] = cleaned_text
                            
                        self.news_service.create_article(db, article_data)
                        new_count += 1
                        
                except Exception as e:
                    logging.error(f"Error saving article: {e}")
                    
            logging.info(f"Added {new_count} new articles")
            print(f"Added {new_count} new articles")
        finally:
            db.close()
    
    async def process_pending_articles(self):
        """Process articles that need AI classification/summarization"""
        logging.info("Processing pending articles...")
        print("Processing pending articles...")
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
            print(f"Processed {len(results)} articles")
        finally:
            db.close()
    
    async def process_vectors_for_articles(self):
        """Process articles that need vector embeddings"""
        logging.info("Processing articles for vector embeddings...")
        
        db = SessionLocal()
        try:
            # Get processed articles that don't have embeddings yet
            unembedded = db.query(NewsArticle).filter(
                NewsArticle.is_processed == True,
                NewsArticle.is_embedded == False,
                NewsArticle.ai_summary.isnot(None)
            ).limit(10).all()  # Process in smaller batches for free tier
            
            if not unembedded:
                logging.info("No articles need vector processing")
                return
            
            # Process articles for vector embeddings
            successful_ids = await self.vector_service.batch_process_articles(unembedded)
            
            # Update database to mark articles as embedded
            if successful_ids:
                db.query(NewsArticle).filter(
                    NewsArticle.id.in_(successful_ids)
                ).update(
                    {NewsArticle.is_embedded: True},
                    synchronize_session=False
                )
                db.commit()
                
                logging.info(f"Successfully embedded {len(successful_ids)} articles")
                print(f"Successfully embedded {len(successful_ids)} articles")
        except Exception as e:
            logging.error(f"Error processing vectors: {e}")
        finally:
            db.close()
    
    async def cleanup_old_content(self):
        """Clean up old articles and vectors (free tier management)"""
        logging.info("Starting daily cleanup...")
        
        db = SessionLocal()
        try:
            # Define retention periods
            ARTICLE_RETENTION_DAYS = 60  # Keep articles for 60 days
            VECTOR_RETENTION_DAYS = 45   # Keep vectors for 45 days
            
            cutoff_date = datetime.now() - timedelta(days=ARTICLE_RETENTION_DAYS)
            vector_cutoff_date = datetime.now() - timedelta(days=VECTOR_RETENTION_DAYS)
            
            # Get old articles to be deleted
            old_articles = db.query(NewsArticle).filter(
                NewsArticle.published_at < cutoff_date
            ).all()
            
            if old_articles:
                old_article_ids = [article.id for article in old_articles]
                
                # First, clean up vectors for these articles
                await self.vector_service.cleanup_vectors_by_article_ids(old_article_ids)
                
                # Then delete the articles
                deleted_count = db.query(NewsArticle).filter(
                    NewsArticle.id.in_(old_article_ids)
                ).delete(synchronize_session=False)
                
                db.commit()
                logging.info(f"Deleted {deleted_count} old articles and their vectors")
            
            # Also clean up orphaned vectors (vectors older than retention period)
            await self.vector_service.cleanup_old_vectors(days_old=VECTOR_RETENTION_DAYS)
            
            # Log current storage stats
            stats = self.vector_service.get_vector_stats()
            logging.info(f"Vector storage stats: {stats}")
            
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
        finally:
            db.close()
    
    async def weekly_maintenance(self):
        """Comprehensive weekly maintenance tasks"""
        logging.info("Starting weekly maintenance...")
        
        db = SessionLocal()
        try:
            # Get database stats
            total_articles = db.query(NewsArticle).count()
            processed_articles = db.query(NewsArticle).filter(
                NewsArticle.is_processed == True
            ).count()
            embedded_articles = db.query(NewsArticle).filter(
                NewsArticle.is_embedded == True
            ).count()
            
            # Get vector stats
            vector_stats = self.vector_service.get_vector_stats()
            
            # Log comprehensive stats
            maintenance_stats = {
                "total_articles": total_articles,
                "processed_articles": processed_articles,
                "embedded_articles": embedded_articles,
                "vector_stats": vector_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            logging.info(f"Weekly maintenance stats: {maintenance_stats}")
            
            # Perform more aggressive cleanup if needed (for free tier)
            if vector_stats.get("total_vectors", 0) > 5000:  # Adjust threshold as needed
                logging.warning("Vector count high, performing aggressive cleanup")
                await self.vector_service.cleanup_old_vectors(days_old=30)
            
            # Vacuum database if using PostgreSQL
            try:
                db.execute(text("VACUUM ANALYZE;"))
                db.commit()
                logging.info("Database vacuum completed")
            except Exception as e:
                logging.warning(f"Could not vacuum database: {e}")
            
        except Exception as e:
            logging.error(f"Error during weekly maintenance: {e}")
        finally:
            db.close()
    
    async def get_system_status(self):
        """Get current system status for monitoring"""
        db = SessionLocal()
        try:
            # Article stats
            total_articles = db.query(NewsArticle).count()
            recent_articles = db.query(NewsArticle).filter(
                NewsArticle.published_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            unprocessed_articles = db.query(NewsArticle).filter(
                NewsArticle.is_processed == False
            ).count()
            
            unembedded_articles = db.query(NewsArticle).filter(
                NewsArticle.is_processed == True,
                NewsArticle.is_embedded == False
            ).count()
            
            # Vector stats
            vector_stats = self.vector_service.get_vector_stats()
            
            return {
                "articles": {
                    "total": total_articles,
                    "recent_week": recent_articles,
                    "unprocessed": unprocessed_articles,
                    "unembedded": unembedded_articles
                },
                "vectors": vector_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return {"error": str(e)}
        finally:
            db.close()