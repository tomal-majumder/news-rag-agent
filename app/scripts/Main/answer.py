import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from app.scripts.retrieval.chromadb_retriever import chromadb_retriever, retrieve_chunks
from app.scripts.prompts.build_prompt import build_local_prompt
from app.scripts.prompts.build_prompt import build_web_prompt
from app.scripts.agents.web_search_agent import run_web_search
from app.scripts.agents.llm_client import generate_llm_answer
from app.scripts.utils.should_fallback_to_web import should_fallback_to_web
import time
import asyncio

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

async def answer_question_stream(question):
    """Stream the answer generation process with selective live updates"""
    start_time = time.time()
    
    if not question:
        yield {
            'type': 'error',
            'message': 'Please provide a question.'
        }
        return

    try:
        global vector_store
        if not vector_store:
            yield {
                'type': 'error',
                'message': 'Failed to initialize vector store.'
            }
            return

        # Step 1: Search local knowledge base (show feedback - takes time)
        yield {
            'type': 'status',
            'message': 'Searching knowledge base...',
            'step': 'local_search'
        }
        
        chunks, scores = retrieve_chunks(vector_store, question)
        
        if not chunks:
            yield {
                'type': 'error',
                'message': 'No relevant information found.'
            }
            return

        # Step 2: Determine search strategy
        sources = []
        
        if should_fallback_to_web(scores):
            # Web search fallback (show feedback - takes significant time)
            yield {
                'type': 'status',
                'message': 'Searching the web for latest information...',
                'step': 'web_search'
            }
            
            try:
                web_snippets, urls = run_web_search(question)
                sources = urls if urls else ["Web Search"]
                prompt = build_web_prompt(question, web_snippets)
                search_method = 'web_search'
                
            except Exception as e:
                yield {
                    'type': 'error',
                    'message': f'Web search failed: {str(e)}'
                }
                return
        else:
            # Use local context (fast, no need for detailed feedback)
            sources = [chunk.metadata.get("url") if chunk.metadata.get("url") 
                      else chunk.metadata.get("title", "Unknown") for chunk in chunks]
            context = "\n\n".join([chunk.page_content for chunk in chunks])
            prompt = build_local_prompt(question, context)
            search_method = 'local_knowledge'

        # Step 3: Generate answer (show feedback - takes time)
        yield {
            'type': 'status',
            'message': 'Generating AI response...',
            'step': 'generate_answer'
        }

        try:
            answer = generate_llm_answer(prompt)
                
        except Exception as e:
            yield {
                'type': 'error',
                'message': f'Failed to generate answer: {str(e)}'
            }
            return

        # Final response - send complete answer
        elapsed_time = time.time() - start_time
        yield {
            'type': 'complete',
            'message': 'Answer generated successfully!',
            'data': {
                'answer': answer,
                'sources': sources,
                'time_taken_seconds': elapsed_time,
                'method': search_method
            }
        }

    except Exception as e:
        yield {
            'type': 'error',
            'message': f'Unexpected error: {str(e)}'
        }

# Legacy function for backward compatibility
def answer_question_stream_legacy(question):
    """Legacy streaming function - kept for compatibility"""
    answer = answer_question(question)
    if not answer:
        yield "No answer generated."
        return

    for word in answer.split():
        yield word + " "
        time.sleep(0.1)  # simulate typing delay