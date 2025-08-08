from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from scripts.Main.answer import answer_question
from app.databases.database import get_db, create_tables
from app.databases.crud import NewsService
from app.services.background_tasks import BackgroundTaskService
from app.schemas import QuestionRequest
from datetime import datetime, date

# Pydantic models
class ArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    source: str
    ai_summary: str
    topic: str
    published_at: datetime
    
    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    articles: List[ArticleResponse]
    total_count: int
    page: int
    has_more: bool

# Initialize FastAPI app
app = FastAPI(title="News AI Platform", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize background tasks
background_service = BackgroundTaskService()

@app.on_event("startup")
async def startup_event():
    create_tables()
    background_service.start()
    await background_service.fetch_and_process_news()
    await background_service.process_pending_articles()

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/api/news", response_model=NewsListResponse)
async def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    topic: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for filtering (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get paginated news articles with filtering"""
    
    skip = (page - 1) * limit
     # Convert dates to datetime for database filtering
    start_datetime = None
    end_datetime = None
    
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
    
    if end_date:
        # Set to end of day to include all articles from that day
        end_datetime = datetime.combine(end_date, datetime.max.time())
    
    articles = NewsService.get_articles(
        db=db,
        skip=skip,
        limit=limit + 1,  # Get one extra to check if more exist
        topic=topic,
        search=search,
        start_date=start_datetime,
        end_date=end_datetime,
        source=source, 
    )
    
    has_more = len(articles) > limit
    if has_more:
        articles = articles[:-1]  # Remove the extra article
    
    return NewsListResponse(
        articles=articles,
        total_count=len(articles),
        page=page,
        has_more=has_more
    )

@app.get("/api/topics")
async def get_topics(db: Session = Depends(get_db)):
    """Get available topics for filtering"""
    topics = NewsService.get_available_topics(db)
    return {"topics": ["All"] + topics}


@app.post("/ask")
async def ask_question(req: QuestionRequest):
    result = answer_question(req.question)
    return result

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)