from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
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
        # what is pagination?
        # answer: Pagination is the process of dividing a large dataset into smaller, manageable chunks or pages. This allows users to view a subset of data at a time, improving performance and usability. In this context, pagination is implemented by skipping a certain number of records (based on the page number and limit) and limiting the number of records returned in each query.
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
    def get_available_topics(db: Session) -> List[str]:
        """Get all unique topics"""
        topics = db.query(NewsArticle.topic).filter(
            NewsArticle.topic.isnot(None)
        ).distinct().all()
        return [topic[0] for topic in topics]
    
    @staticmethod
    def create_article(db: Session, article_data: dict) -> NewsArticle:
        """Create new article"""
        article = NewsArticle(**article_data)
        db.add(article)
        db.commit()
        db.refresh(article)
        return article