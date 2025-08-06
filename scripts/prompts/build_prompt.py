def build_local_prompt(question, context):
    return f"""You are a helpful news assistant.

Answer the following question in a detailed, well-structured, and grammatically correct manner using the information from the news articles below.

News Articles:
{context}

Question: {question}
Answer:"""

def build_web_prompt(question, web_snippets):
    return f"""You are a helpful news assistant.

The local news archive did not contain enough information, so the assistant retrieved relevant snippets from the web.

Web Search Results:
{web_snippets}

Question: {question}
Answer:"""
