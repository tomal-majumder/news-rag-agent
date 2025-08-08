
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

# This is the model for storing news articles in the database
# Details:
# - id: Unique identifier for each article
# - title: Title of the article
# - url: URL of the article, must be unique
# - source: Source of the article (e.g., CNN, BBC)
# - body: Full text of the article
# - published_at: Date and time when the article was published
# - created_at: Timestamp when the record was created
# - updated_at: Timestamp when the record was last updated
# - topic: AI classified topic of the article
# - ai_summary: AI generated summary of the article
# - is_processed: Flag to indicate if the article has been processed by AI
# - Performance indexes for faster querying based on topic, processed status, and source
class NewsArticle(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), unique=True, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    body = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # AI-generated fields
    topic = Column(String(50), index=True)  # AI classified
    ai_summary = Column(Text)  # AI generated summary
    is_processed = Column(Boolean, default=False, index=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_topic_date', 'topic', 'published_at'),
        Index('idx_processed_date', 'is_processed', 'published_at'),
        Index('idx_source_date', 'source', 'published_at'),
    )