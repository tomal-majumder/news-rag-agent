# test Vector service
from app.services.vector_service import VectorService
from app.databases.database import get_db
from app.databases.models import NewsArticle
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
from app.scripts.utils.get_embedding_model import get_embedding_model
from langchain_community.vectorstores import PGVector
import pgvector

connection_string = os.getenv("DATABASE_URL", "sqlite:///./news.db")
embeddings = get_embedding_model()
collection_name = "news_articles"

vector_store = PGVector(
            connection_string=connection_string,
            embedding_function=embeddings,
            collection_name=collection_name
        )

question = "Any news on AI?"
results = vector_store.similarity_search_with_score(question, k=5)  # Mocking the vector store's search method
chunks, scores = zip(*results) if results else ([], [])
for chunk in chunks:
    print("Chunk:", chunk.page_content)
    print("Metadata:", chunk.metadata)
    print(len(chunk.page_content), "characters long")
print("Scores:", scores)
