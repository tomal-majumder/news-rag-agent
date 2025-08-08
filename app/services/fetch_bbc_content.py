import requests
from bs4 import BeautifulSoup

# this function can be used in the test file or integrated into the service as needed
# it fetches and cleans the article content from a given URL
# it removes scripts, styles, and hyperlinks while preserving the text
async def fetch_clean_article_content(url: str) -> str:
    """Fetch and clean full article content from URL"""
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, "html.parser")

    # Remove all script and style tags
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Find all paragraph tags inside the main article container
    content_selectors = [
        'article',
        '.article-body',
        '.story-content',
        '[data-testid="article-content"]',
        '.entry-content'
    ]

    article_text = []
    for selector in content_selectors:
        container = soup.select_one(selector)
        if container:
            for p in container.find_all("p"):
                for a in p.find_all("a"):
                    a.unwrap()
                text = p.get_text(strip=True)
                if text:
                    article_text.append(text)
            break 

    clean_text = "\n".join(article_text)
    return clean_text if clean_text else "Content not found"