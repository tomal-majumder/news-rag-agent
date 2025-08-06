import argparse
from scripts.retrieval.chromadb_retriever import chromadb_retriever, retrieve_chunks
from scripts.utils.create_chromadb_collection import create_chromadb_collection
from scripts.utils.get_embedding_function import get_embedding_function
from scripts.utils.build_context_from_chunks import build_context_from_chunks
from scripts.prompts.build_prompt import build_local_prompt
from scripts.prompts.build_prompt import build_web_prompt
from scripts.agents.web_search_agent import run_web_search
from scripts.agents.llm_client import generate_llm_answer
from scripts.utils.should_fallback_to_web import should_fallback_to_web

def main():
    parser = argparse.ArgumentParser(description="Answer questions using RAG pipeline")
    parser.add_argument('--question', type=str, help="Question to answer")
    args = parser.parse_args()
    
    question = args.question
    if not question:
        print("Please provide a question using --question argument.")
        return
    
    # first retrieve relevant chunks
    vector_store = chromadb_retriever()
    if not vector_store:
        print("Failed to initialize vector store.")
        return
    chunks, scores = retrieve_chunks(vector_store, question)
    if not chunks:
        print("No relevant chunks found.")
        return
    print(f"Retrieved {len(chunks)} chunks with scores: {scores}")

    # then build prompt
    if should_fallback_to_web(scores):
        print("Not enough relevant context found in local archive. Using web fallback...")
        web_snippets = run_web_search(question)
        prompt = build_web_prompt(question, web_snippets)
    else:
        context = "\n\n".join([chunk.page_content for chunk in chunks])
        prompt = build_local_prompt(question, context)
    

    # then use LLM to answer the question
    print("Generating answer using LLM...")
    answer = generate_llm_answer(prompt)
    print("Answer generated:")
    print(answer)
    
if __name__ == "__main__":
    main()
