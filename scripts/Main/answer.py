import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from scripts.retrieval.chromadb_retriever import chromadb_retriever, retrieve_chunks
from scripts.prompts.build_prompt import build_local_prompt
from scripts.prompts.build_prompt import build_web_prompt
from scripts.agents.web_search_agent import run_web_search
from scripts.agents.llm_client import generate_llm_answer
from scripts.utils.should_fallback_to_web import should_fallback_to_web
import time
# Global singleton cache
vector_store = chromadb_retriever()

def answer_question(question):
    start_time = time.time()

    if not question:
        print("Please provide a question using --question argument.")
        return
    
    # first retrieve relevant chunks
    # vector_store = chromadb_retriever()
    if not vector_store:
        print("Failed to initialize vector store.")
        return
    
    chunks, scores = retrieve_chunks(vector_store, question)
    sources = []
    if not chunks:
        print("No relevant chunks found.")
        return
    print(f"Retrieved {len(chunks)} chunks with scores: {scores}")

    # then build prompt
    if should_fallback_to_web(scores):
        print("Not enough relevant context found in local archive. Using web fallback...")
        web_snippets, urls = run_web_search(question)
        sources = urls if urls else ["Web Search"]
        prompt = build_web_prompt(question, web_snippets)
    else:
        sources = [chunk.metadata.get("url") if chunk.metadata.get("url") 
                            else chunk.metadata.get("title", "Unknown") for chunk in chunks]
        context = "\n\n".join([chunk.page_content for chunk in chunks])
        prompt = build_local_prompt(question, context)
    

    # then use LLM to answer the question
    answer = generate_llm_answer(prompt)
    elapsed_time = time.time() - start_time
    return {
        "answer": answer,
        "sources": sources,
        "time_taken_seconds": elapsed_time
    }

import time

def answer_question_stream(question):
    answer = answer_question(question)
    if not answer:
        yield "No answer generated."
        return

    for word in answer.split():
        yield word + " "
        time.sleep(0.1)  # simulate typing delay

