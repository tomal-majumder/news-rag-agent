def build_local_prompt(question, context):

    return f"""You are a helpful news assistant.
        Answer the following question based on the context below.
        Question: {question}

        Context:   
        {context}

        Answer:"""

def build_web_prompt(question, web_snippets):
    return f"""You are a helpful news assistant.
        Answer the following question based on the context below.
        Question: {question}

        Context:   
        {web_snippets}

        Answer:"""
