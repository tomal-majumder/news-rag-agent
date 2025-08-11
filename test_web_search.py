import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
import time

load_dotenv()  # This loads the .env file from project root
api_key = os.getenv("TAVILY_API_KEY")
search_tool = TavilySearchResults()

def run_web_search(query, num_snippets=3):
    try:
        start_time = time.time()
        results = search_tool.run(query)
        elapsed_time = time.time() - start_time
        print(f"Web search executed in lets say {elapsed_time:.2f} seconds")
       # print(f"Web search results: {results}")
        if isinstance(results, list):
            snippets = [doc['content'] for doc in results[:num_snippets]]
            return "\n\n".join(snippets), [doc['url'] for doc in results[:num_snippets]]
        else:
            #print("Unexpected result format:", results)
            return results.strip(), ["Web Search"]

    except Exception as e:
        return f"Web search error: {e}"

# Example usage
# track execution time
snippets, source =run_web_search("What are news on Donald Trump?", num_snippets=5)
