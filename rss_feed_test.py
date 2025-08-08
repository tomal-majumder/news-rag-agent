# Test RSS feed article fetching and processing
from app.services.news_scappers import NewsScraperService
import requests
from bs4 import BeautifulSoup

def fetch_full_article_content(url: str) -> str:
    """Fetch full article content from URL"""

    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Common article content selectors (varies by site)
    content_selectors = [
        'article',
        '.article-body',
        '.story-content',
        '[data-testid="article-content"]',
        '.entry-content'
    ]
    
    for selector in content_selectors:
        content = soup.select_one(selector)
        if content:
            return content.get_text(strip=True)
    
    return "Content not found"
    
news_scrapper_service = NewsScraperService()

articles = news_scrapper_service.fetch_articles_from_rss(100)
print(len(articles), "articles fetched from RSS feeds.")
# print("Fetched Articles:")
# for article in articles:
#     print(f"Title: {article['title']}, Source: {article['source']}, URL: {article['url']}")
#     content = fetch_full_article_content(article['url'])  # Fetch full content for each article
#     print(f"Content: {len(content)}...")  # Print first 200 chars of content


import os

log_file = "fetched_articles.log"

with open(log_file, "w", encoding="utf-8") as f:
    f.write("=== Fetched Articles Log ===\n\n")
    for article in articles:  # make sure 'articles' is defined correctly
        title = article.get('title', 'N/A')
        source = article.get('source', 'N/A')
        url = article.get('url', 'N/A')

        content = fetch_full_article_content(url)  # Fetch the full content

        f.write(f"Title: {title}\n")
        f.write(f"Source: {source}\n")
        f.write(f"URL: {url}\n")
        f.write(f"Content:\n{content}\n")
        f.write("="*80 + "\n\n")  # Separator between articles

print(f"Articles logged to: {os.path.abspath(log_file)}")

