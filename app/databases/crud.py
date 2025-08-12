from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from datetime import datetime, timedelta
from typing import List, Optional
from .models import NewsArticle
import logging

class NewsService:
    
    @staticmethod
    def get_articles(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        topic: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None
    ) -> List[NewsArticle]:
        """Get filtered and paginated articles"""
        query = db.query(NewsArticle).filter(
            NewsArticle.is_processed == True,
            NewsArticle.ai_summary.isnot(None)
        )
        
        # Apply filters
        if topic and topic != 'All':
            query = query.filter(NewsArticle.topic == topic)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    NewsArticle.title.ilike(search_term),
                    NewsArticle.ai_summary.ilike(search_term)
                )
            )
            
        if start_date:
            query = query.filter(NewsArticle.published_at >= start_date)
            
        if end_date:
            query = query.filter(NewsArticle.published_at <= end_date)
            
        if source:
            query = query.filter(NewsArticle.source == source)
        
        # Order by date (newest first) and paginate
        return query.order_by(desc(NewsArticle.published_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_unprocessed_articles(db: Session, limit: int = 50) -> List[NewsArticle]:
        """Get articles that need AI processing"""
        return db.query(NewsArticle).filter(
            NewsArticle.is_processed == False
        ).limit(limit).all()
    
    @staticmethod
    def get_unembedded_articles(db: Session, limit: int = 50) -> List[NewsArticle]:
        """Get processed articles that need vector embeddings"""
        return db.query(NewsArticle).filter(
            NewsArticle.is_processed == True,
            NewsArticle.is_embedded == False,
            NewsArticle.ai_summary.isnot(None)
        ).limit(limit).all()
    
    @staticmethod
    def update_article_ai_data(
        db: Session, 
        article_id: int, 
        topic: str, 
        ai_summary: str
    ):
        """Update article with AI-generated data"""
        db.query(NewsArticle).filter(NewsArticle.id == article_id).update({
            "topic": topic,
            "ai_summary": ai_summary,
            "is_processed": True,
            "updated_at": datetime.utcnow()
        })
        db.commit()
    
    @staticmethod
    def mark_articles_as_embedded(db: Session, article_ids: List[int]):
        """Mark articles as having vector embeddings"""
        db.query(NewsArticle).filter(
            NewsArticle.id.in_(article_ids)
        ).update(
            {NewsArticle.is_embedded: True, NewsArticle.updated_at: datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
    
    @staticmethod
    def get_available_topics(db: Session) -> List[str]:
        """Get all unique topics"""
        topics = db.query(NewsArticle.topic).filter(
            NewsArticle.topic.isnot(None)
        ).distinct().all()
        return [topic[0] for topic in topics]
    
    @staticmethod
    def get_available_sources(db: Session) -> List[str]:
        """Get all unique sources"""
        sources = db.query(NewsArticle.source).distinct().all()
        return [source[0] for source in sources]
    
    @staticmethod
    def create_article(db: Session, article_data: dict) -> NewsArticle:
        """Create new article"""
        article = NewsArticle(**article_data)
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
    
    @staticmethod
    def get_article_by_id(db: Session, article_id: int) -> Optional[NewsArticle]:
        """Get article by ID"""
        return db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    
    @staticmethod
    def get_article_by_url(db: Session, url: str) -> Optional[NewsArticle]:
        """Get article by URL"""
        return db.query(NewsArticle).filter(NewsArticle.url == url).first()
    
    @staticmethod
    def delete_old_articles(db: Session, cutoff_date: datetime) -> int:
        """Delete articles older than cutoff date"""
        deleted_count = db.query(NewsArticle).filter(
            NewsArticle.published_at < cutoff_date
        ).delete()
        db.commit()
        return deleted_count
    
    @staticmethod
    def get_article_stats(db: Session) -> dict:
        """Get comprehensive article statistics"""
        try:
            # Basic counts
            total_articles = db.query(NewsArticle).count()
            processed_articles = db.query(NewsArticle).filter(
                NewsArticle.is_processed == True
            ).count()
            embedded_articles = db.query(NewsArticle).filter(
                NewsArticle.is_embedded == True
            ).count()
            
            # Recent articles (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_articles = db.query(NewsArticle).filter(
                NewsArticle.published_at >= week_ago
            ).count()
            
            # Articles by topic
            topic_stats = db.query(
                NewsArticle.topic,
                func.count(NewsArticle.id).label('count')
            ).filter(
                NewsArticle.topic.isnot(None)
            ).group_by(NewsArticle.topic).all()
            
            # Articles by source
            source_stats = db.query(
                NewsArticle.source,
                func.count(NewsArticle.id).label('count')
            ).group_by(NewsArticle.source).all()
            
            # Processing status
            unprocessed_count = db.query(NewsArticle).filter(
                NewsArticle.is_processed == False
            ).count()
            
            unembedded_count = db.query(NewsArticle).filter(
                NewsArticle.is_processed == True,
                NewsArticle.is_embedded == False
            ).count()
            
            # Date range
            date_range = db.query(
                func.min(NewsArticle.published_at).label('oldest'),
                func.max(NewsArticle.published_at).label('newest')
            ).first()
            
            return {
                "totals": {
                    "articles": total_articles,
                    "processed": processed_articles,
                    "embedded": embedded_articles,
                    "recent_week": recent_articles,
                    "unprocessed": unprocessed_count,
                    "unembedded": unembedded_count
                },
                "by_topic": {topic: count for topic, count in topic_stats},
                "by_source": {source: count for source, count in source_stats},
                "date_range": {
                    "oldest": date_range.oldest.isoformat() if date_range.oldest else None,
                    "newest": date_range.newest.isoformat() if date_range.newest else None
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting article stats: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def search_articles_by_content(
        db: Session,
        query: str,
        limit: int = 10
    ) -> List[NewsArticle]:
        """Search articles by content using database text search"""
        search_term = f"%{query}%"
        
        return db.query(NewsArticle).filter(
            NewsArticle.is_processed == True,
            or_(
                NewsArticle.title.ilike(search_term),
                NewsArticle.ai_summary.ilike(search_term),
                NewsArticle.body.ilike(search_term)
            )
        ).order_by(desc(NewsArticle.published_at)).limit(limit).all()
    
    @staticmethod
    def get_articles_for_topic_analysis(db: Session, days_back: int = 7) -> List[NewsArticle]:
        """Get recent articles for topic analysis"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        return db.query(NewsArticle).filter(
            NewsArticle.is_processed == True,
            NewsArticle.published_at >= cutoff_date
        ).order_by(desc(NewsArticle.published_at)).all()
    
    @staticmethod
    def get_trending_topics(db: Session, days_back: int = 7) -> List[dict]:
        """Get trending topics in recent articles"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        trending = db.query(
            NewsArticle.topic,
            func.count(NewsArticle.id).label('count')
        ).filter(
            NewsArticle.is_processed == True,
            NewsArticle.published_at >= cutoff_date,
            NewsArticle.topic.isnot(None)
        ).group_by(NewsArticle.topic).order_by(
            desc(func.count(NewsArticle.id))
        ).limit(10).all()
        
        return [{"topic": topic, "count": count} for topic, count in trending]