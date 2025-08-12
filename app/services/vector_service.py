import os
import logging
from typing import List, Dict, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from sqlalchemy.orm import Session
from app.databases.models import NewsArticle
from app.databases.database import get_db
from datetime import datetime, timedelta
from app.scripts.utils.get_embedding_model import get_embedding_model

import asyncio
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

class VectorService:
    """Service for handling document embeddings and vector storage"""
    
    def __init__(self):
        self.embeddings = get_embedding_model()  # Load your embedding model
        
        # Database connection for PGVector
        self.connection_string = os.getenv("DATABASE_URL")
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        self.collection_name = "news_articles"
        self.vector_store = PGVector(
            connection_string=self.connection_string,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        
    def _get_vector_store(self) -> PGVector:
        """Get PGVector instance"""
        return self.vector_store
    
    async def process_article_for_vectors(self, article: NewsArticle) -> bool:
        """Process a single article: split text and create embeddings"""
        try:
            # Combine title and body for comprehensive content
            full_text = f"{article.body}"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(full_text)
            
            if not chunks:
                logging.warning(f"No chunks created for article {article.id}")
                return False
            
            # Create metadata for each chunk
            metadatas = []
            texts = []
            
            for i, chunk in enumerate(chunks):
                metadata = {
                    "article_id": article.id,
                    "title": article.title[:200],  # Truncate long titles
                    "topic": article.topic or "General",
                    "url": article.url,
                    "published_at": article.published_at.isoformat(),
                    "chunk_index": i,
                }
                metadatas.append(metadata)
                texts.append(chunk)
            
            # Add to vector store
            vector_store = self._get_vector_store()
            await asyncio.get_event_loop().run_in_executor(
                None, 
                vector_store.add_texts,
                texts,
                metadatas
            )
            
            logging.info(f"Successfully created {len(chunks)} embeddings for article {article.id}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing article {article.id} for vectors: {e}")
            return False
    
    async def batch_process_articles(self, articles: List[NewsArticle]) -> List[int]:
        """Process multiple articles for vector storage"""
        successful_ids = []
        
        for article in articles:
            success = await self.process_article_for_vectors(article)
            if success:
                successful_ids.append(article.id)
            
            # Add small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)
        
        return successful_ids
    
    async def cleanup_old_vectors(self, days_old: int = 90) -> int:
        """Remove vectors for articles older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            vector_store = self._get_vector_store()
            
            # Get all vectors with metadata
            # Note: This approach depends on your PGVector setup
            # You might need to adjust based on your specific implementation
            
            # Query old vectors using SQL directly if needed
            from sqlalchemy import create_engine, text
            engine = create_engine(self.connection_string)
            
            delete_query = text("""
                DELETE FROM langchain_pg_embedding 
                WHERE cmetadata->>'published_at' < :cutoff_date
            """)
            
            with engine.begin() as conn:
                result = conn.execute(delete_query, {"cutoff_date": cutoff_date.isoformat()})
                deleted_count = result.rowcount
            
            logging.info(f"Cleaned up {deleted_count} old vector embeddings")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error during vector cleanup: {e}")
            return 0
    
    async def cleanup_vectors_by_article_ids(self, article_ids: List[int]) -> int:
        """Remove vectors for specific articles"""
        try:
            if not article_ids:
                return 0
                
            vector_store = self._get_vector_store()
            
            # Delete vectors for specific article IDs
            from sqlalchemy import create_engine, text
            engine = create_engine(self.connection_string)
            
            # Convert article IDs to string for JSON query
            id_list = [str(id) for id in article_ids]
            
            delete_query = text("""
                DELETE FROM langchain_pg_embedding 
                WHERE cmetadata->>'article_id' = ANY(:article_ids)
            """)
            
            with engine.begin() as conn:
                result = conn.execute(delete_query, {"article_ids": id_list})
                deleted_count = result.rowcount
            
            logging.info(f"Deleted {deleted_count} vectors for {len(article_ids)} articles")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error deleting vectors by article IDs: {e}")
            return 0
    
    async def search_similar_articles(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar articles using vector similarity"""
        try:
            vector_store = self._get_vector_store()
            
            # Perform similarity search
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                vector_store.similarity_search_with_score,
                query,
                k,
                filter_dict
            )
            
            formatted_results = []
            for doc, score in results:
                result = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                }
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error during vector search: {e}")
            return []
    
    def get_vector_stats(self) -> Dict:
        """Get statistics about stored vectors"""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.connection_string)
            
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_vectors,
                    COUNT(DISTINCT cmetadata->>'article_id') as unique_articles,
                    MIN(cmetadata->>'published_at') as oldest_article,
                    MAX(cmetadata->>'published_at') as newest_article
                FROM langchain_pg_embedding
                WHERE collection_id = (
                    SELECT uuid FROM langchain_pg_collection 
                    WHERE name = :collection_name
                )
            """)
            
            with engine.connect() as conn:
                result = conn.execute(stats_query, {"collection_name": self.collection_name})
                row = result.fetchone()
                
                if row:
                    return {
                        "total_vectors": row[0] or 0,
                        "unique_articles": row[1] or 0,
                        "oldest_article": row[2],
                        "newest_article": row[3]
                    }
            
            return {
                "total_vectors": 0,
                "unique_articles": 0,
                "oldest_article": None,
                "newest_article": None
            }
            
        except Exception as e:
            logging.error(f"Error getting vector stats: {e}")
            return {
                "total_vectors": 0,
                "unique_articles": 0,
                "oldest_article": None,
                "newest_article": None,
                "error": str(e)
            }