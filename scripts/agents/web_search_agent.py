import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()  # This loads the .env file from project root
api_key = os.getenv("TAVILY_API_KEY")
search_tool = TavilySearchResults()

def run_web_search(query, num_snippets=3):
    try:
        results = search_tool.run(query)
        print(f"Web search results: {results}")
        if isinstance(results, list):
            snippets = [doc['content'] for doc in results[:num_snippets]]
            return "\n\n".join(snippets), [doc['url'] for doc in results[:num_snippets]]
        else:
            print("Unexpected result format:", results)
            return results.strip(), ["Web Search"]

    except Exception as e:
        return f"Web search error: {e}"
