import requests
from bs4 import BeautifulSoup

url = "https://www.bbc.com/news/articles/ce35v0zyzvlo?at_medium=RSS&at_campaign=rss"
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
            # Remove any hyperlinks but keep their text
            for a in p.find_all("a"):
                a.unwrap()
            text = p.get_text(strip=True)
            if text:
                article_text.append(text)
        break  # stop after first matching selector

clean_text = "\n".join(article_text)
print(clean_text)