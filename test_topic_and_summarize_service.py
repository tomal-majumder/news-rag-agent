# Test functions for topic and summarization service
from app.services.ai_services import AIService
from app.databases.models import NewsArticle
from app.services.fetch_bbc_content import fetch_clean_article_content
import asyncio

ai_service = AIService()
url = "https://www.bbc.com/news/articles/ce35v0zyzvlo?at_medium=RSS&at_campaign=rss"
content = fetch_clean_article_content(url)
print(content)

async def main():
	topic, summary = await ai_service.classify_and_summarize(content)
	print(f"{topic}")
	print(f"{summary}")

asyncio.run(main())