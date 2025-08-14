import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from app.scripts.retrieval.chromadb_retriever import retrieve_chunks
from app.scripts.prompts.build_prompt import build_local_prompt
from app.scripts.prompts.build_prompt import build_web_prompt
from app.scripts.agents.web_search_agent import run_web_search
from app.scripts.agents.llm_client import generate_llm_answer
from app.scripts.utils.should_fallback_to_web import should_fallback_to_web
import time
import asyncio
import re

# Global singleton cache
# vector_store = chromadb_retriever()

def estimate_tokens(text):
    """Rough token estimation: ~3.5 characters per token for English"""
    return len(text) / 3.5

def build_optimized_context(chunks, max_tokens=6000, min_chunk_tokens=25):
    """
    Build context optimally using available token budget
    Prioritizes chunks by retrieval order (assuming they're ranked by relevance)
    """
    context_parts = []
    total_tokens = 0
    
    for i, chunk in enumerate(chunks):
        content = chunk.page_content.strip()
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        
        chunk_tokens = estimate_tokens(content)
        
        # Skip very short chunks
        if chunk_tokens < min_chunk_tokens:
            continue
            
        # Check if we can fit this chunk
        if total_tokens + chunk_tokens > max_tokens:
            # Try to fit a truncated version if we have significant space left
            remaining_tokens = max_tokens - total_tokens
            if remaining_tokens > 100:  # Only if we have meaningful space
                remaining_chars = int(remaining_tokens * 3.5)
                # Truncate at sentence/word boundary
                truncated = content[:remaining_chars]
                if '. ' in truncated:
                    truncated = truncated.rsplit('. ', 1)[0] + '.'
                else:
                    truncated = truncated.rsplit(' ', 1)[0]
                
                context_parts.append(f"[Source {i+1}] {truncated}...")
                total_tokens += estimate_tokens(truncated)
            break
        else:
            context_parts.append(f"[Source {i+1}] {content}")
            total_tokens += chunk_tokens
    
    final_context = "\n\n".join(context_parts)
    print(f"Built context: {len(final_context)} characters (~{total_tokens:.0f} tokens) from {len(context_parts)} sources")
    return final_context

def build_optimized_web_context(web_snippets, max_tokens=6000):
    """Build optimized context from web search results"""
    if isinstance(web_snippets, str):
        # If it's already a string, split it back to individual snippets
        snippets = web_snippets.split('\n\n')
    else:
        snippets = web_snippets
    
    context_parts = []
    total_tokens = 0
    
    for i, snippet in enumerate(snippets):
        content = snippet.strip()
        content = re.sub(r'\s+', ' ', content)
        
        snippet_tokens = estimate_tokens(content)
        
        if total_tokens + snippet_tokens > max_tokens:
            remaining_tokens = max_tokens - total_tokens
            if remaining_tokens > 100:
                remaining_chars = int(remaining_tokens * 3.5)
                truncated = content[:remaining_chars].rsplit(' ', 1)[0]
                context_parts.append(f"[Web Source {i+1}] {truncated}...")
            break
        else:
            context_parts.append(f"[Web Source {i+1}] {content}")
            total_tokens += snippet_tokens
    
    final_context = "\n\n".join(context_parts)
    print(f"Built web context: {len(final_context)} characters (~{total_tokens:.0f} tokens) from {len(context_parts)} sources")
    return final_context

def calculate_optimal_max_tokens(prompt):
    """Calculate optimal max_tokens based on prompt length"""
    prompt_tokens = estimate_tokens(prompt)
    
    # Total capacity: 8192 tokens
    # Reserve some safety margin
    total_capacity = 8192
    safety_margin = 200
    
    available_for_response = total_capacity - prompt_tokens - safety_margin
    
    # Ensure reasonable bounds (minimum 500, maximum 4000)
    max_tokens = max(min(available_for_response, 4000), 500)
    
    print(f"Prompt tokens: ~{prompt_tokens:.0f}, Allocated for response: {max_tokens}")
    return int(max_tokens)

def answer_question(question, vector_store):
    start_time = time.time()

    if not question:
        print("Please provide a question using --question argument.")
        return
    
    # first retrieve relevant chunks
    if not vector_store:
        print("Failed to initialize vector store.")
        return
    
    chunks, scores = retrieve_chunks(vector_store, question)
    sources = []
    if not chunks:
        print("No relevant chunks found.")
        return
    print(f"Retrieved {len(chunks)} chunks with scores: {scores}")
    # for chunk in chunks:
    #     print(chunk)

    # then build optimized prompt
    if should_fallback_to_web(scores):
        print("Not enough relevant context found in local archive. Using web fallback...")
        web_snippets, urls = run_web_search(question) # 3 snippets
        sources = urls if urls else ["Web Search"]
        
        # Build optimized web context
        optimized_context = build_optimized_web_context(web_snippets, max_tokens=6000)
        prompt = build_web_prompt(question, optimized_context)
    else:
        sources = [chunk.metadata.get("url") if chunk.metadata.get("url") 
                            else chunk.metadata.get("title", "Unknown") for chunk in chunks[:5]]
        
        # Build optimized local context
        optimized_context = build_optimized_context(chunks[:5], max_tokens=6000)
        prompt = build_local_prompt(question, optimized_context)
    
    # Calculate optimal response token allocation
    optimal_max_tokens = calculate_optimal_max_tokens(prompt)

    # then use LLM to answer the question with optimized parameters
    answer = generate_llm_answer(prompt, max_tokens=optimal_max_tokens)
    elapsed_time = time.time() - start_time
    return {
        "answer": answer,
        "sources": sources,
        "time_taken_seconds": elapsed_time
    }

async def answer_question_stream(question, vector_store):
    """Stream the answer generation process with selective live updates"""
    start_time = time.time()
    
    if not question:
        yield {
            'type': 'error',
            'message': 'Please provide a question.'
        }
        return

    try:
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

        # Step 2: Determine search strategy and build optimized context
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
                
                # Build optimized web context
                optimized_context = build_optimized_web_context(web_snippets, max_tokens=6000)
                prompt = build_web_prompt(question, optimized_context)
                search_method = 'web_search'
                
            except Exception as e:
                yield {
                    'type': 'error',
                    'message': f'Web search failed: {str(e)}'
                }
                return
        else:
            # Use local context (fast, no need for detailed feedback)
            yield {
                'type': 'status',
                'message': 'Building optimized context...',
                'step': 'build_context'
            }
            
            sources = [chunk.metadata.get("url") if chunk.metadata.get("url") 
                      else chunk.metadata.get("title", "Unknown") for chunk in chunks]
            print(sources)
            # Build optimized local context
            optimized_context = build_optimized_context(chunks, max_tokens=6000)
            prompt = build_local_prompt(question, optimized_context)
            search_method = 'local_knowledge'

        # Step 3: Generate answer with optimal token allocation
        yield {
            'type': 'status',
            'message': 'Generating AI response...',
            'step': 'generate_answer'
        }

        try:
            # Calculate optimal response token allocation
            optimal_max_tokens = calculate_optimal_max_tokens(prompt)
            answer = generate_llm_answer(prompt, max_tokens=optimal_max_tokens)
                
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