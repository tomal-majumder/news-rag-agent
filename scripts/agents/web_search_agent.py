import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()  # This loads the .env file from project root
api_key = os.getenv("TAVILY_API_KEY")
search_tool = TavilySearchResults()

def run_web_search(query, num_snippets=3):
    try:
        results = search_tool.run(query)
        if isinstance(results, list):
            snippets = [doc['content'] for doc in results[:num_snippets]]
            return "\n\n".join(snippets)
        else:
            return results.strip()

    except Exception as e:
        return f"Web search error: {e}"
