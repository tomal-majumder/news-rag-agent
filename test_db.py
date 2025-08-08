from app.databases.database import SessionLocal
from app.databases.crud import NewsService
from app.databases.models import NewsArticle
# Create a new database session
db = SessionLocal()

# Example: Check if it works by fetching articles
total_count = db.query(NewsArticle).count()
print(f"Total articles in DB: {total_count}")

articles = NewsService.get_articles(db, skip=0, limit=5)
# for article in articles:
#     print(f"Title: {article.title}, URL: {article.url}, Source: {article.source}, Published At: {article.published_at}")
#     print(f"AI Summary: {article.ai_summary}, Topic: {article.topic}")
# Close when done
db.close()