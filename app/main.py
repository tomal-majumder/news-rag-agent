from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import asyncio
from app.scripts.Main.answer import answer_question, answer_question_stream
from app.databases.database import get_db, create_tables
from app.databases.crud import NewsService
from app.services.background_tasks import BackgroundTaskService
from app.schemas import QuestionRequest
from datetime import datetime, date
from app.services.vector_service import VectorService
from app.databases.models import NewsArticle

# Initialize vector service
vector_service = VectorService()

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

class SimilarArticleResponse(BaseModel):
    article: ArticleResponse
    similarity_score: float

class ArticleDetailResponse(BaseModel):
    article: ArticleResponse
    similar_articles: List[SimilarArticleResponse] = []

class SystemStatsResponse(BaseModel):
    articles: dict
    vectors: dict
    system: dict
    timestamp: str

class TrendingTopicsResponse(BaseModel):
    trending_topics: List[dict]
    period_days: int

class SemanticSearchResponse(BaseModel):
    query: str
    results: List[dict]
    total_found: int


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
background_service = BackgroundTaskService(vector_service=vector_service)

@app.on_event("startup")
async def startup_event():
    create_tables()
    background_service.start()
    await background_service.fetch_and_process_news()
    await background_service.process_pending_articles()
    await background_service.process_vectors_for_articles()
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
    result = answer_question(req.question, vector_store=vector_service._get_vector_store())
    return result

# New streaming endpoint
@app.post("/ask/stream")
async def ask_question_stream(req: QuestionRequest):
    """Stream the answer generation process with live updates"""
    
    async def generate():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your question...', 'step': 'init'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Stream the answer generation process
            async for update in answer_question_stream(req.question, vector_store=vector_service._get_vector_store()):
                yield f"data: {json.dumps(update)}\n\n"
                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': f'Error: {str(e)}'
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        finally:
            # Send completion signal
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get comprehensive system statistics"""
    try:
        # Get article stats from database
        article_stats = NewsService.get_article_stats(db)
        
        # Get vector stats
        vector_stats = vector_service.get_vector_stats()
        
        # Get background task status
        system_status = await background_service.get_system_status()
        
        return {
            "articles": article_stats,
            "vectors": vector_stats,
            "system": system_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/api/trending")
async def get_trending_topics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get trending topics in recent articles"""
    trending = NewsService.get_trending_topics(db, days_back=days)
    return {"trending_topics": trending, "period_days": days}

@app.get("/api/sources")
async def get_available_sources(db: Session = Depends(get_db)):
    """Get available news sources"""
    sources = NewsService.get_available_sources(db)
    return {"sources": sources}

@app.post("/api/search/semantic")
async def semantic_search(
    query: str = Query(..., description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of results"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    source: Optional[str] = Query(None, description="Filter by source")
):
    """Search articles using vector similarity"""
    try:
        # Build filter dictionary
        filter_dict = {}
        if topic and topic != "All":
            filter_dict["topic"] = topic
        if source:
            filter_dict["source"] = source
        
        # Perform semantic search
        results = await vector_service.search_similar_articles(
            query=query,
            k=k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/api/admin/process-vectors")
async def trigger_vector_processing():
    """Manually trigger vector processing for unembedded articles"""
    try:
        await background_service.process_vectors_for_articles()
        return {"message": "Vector processing triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/admin/cleanup")
async def trigger_cleanup(
    days_old: int = Query(30, ge=7, le=90, description="Delete content older than X days")
):
    """Manually trigger cleanup of old content"""
    try:
        db = SessionLocal()
        
        # Count what will be deleted
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_articles_count = db.query(NewsArticle).filter(
            NewsArticle.published_at < cutoff_date
        ).count()
        
        db.close()
        
        # Perform cleanup
        await background_service.cleanup_old_content()
        
        return {
            "message": f"Cleanup completed",
            "cutoff_date": cutoff_date.isoformat(),
            "articles_affected": old_articles_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup error: {str(e)}")

@app.get("/api/article/{article_id}")
async def get_article_detail(
    article_id: int,
    include_similar: bool = Query(False, description="Include similar articles"),
    db: Session = Depends(get_db)
):
    """Get detailed article information"""
    article = NewsService.get_article_by_id(db, article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    response = {
        "article": ArticleResponse.from_orm(article),
        "similar_articles": []
    }
    
    # Optionally find similar articles using vector search
    if include_similar and article.is_embedded:
        try:
            # Use article title and summary for similarity search
            search_query = f"{article.title} {article.ai_summary or ''}"
            similar_results = await vector_service.search_similar_articles(
                query=search_query,
                k=6  # Get 6 to exclude the original article
            )
            
            # Filter out the original article and convert to response format
            similar_articles = []
            for result in similar_results:
                if result["metadata"].get("article_id") != article_id:
                    similar_article = NewsService.get_article_by_id(
                        db, int(result["metadata"]["article_id"])
                    )
                    if similar_article:
                        similar_articles.append({
                            "article": ArticleResponse.from_orm(similar_article),
                            "similarity_score": result["similarity_score"]
                        })
            
            response["similar_articles"] = similar_articles[:5]  # Return top 5
            
        except Exception as e:
            logging.error(f"Error finding similar articles: {e}")
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)