from scripts.retrieval.chromadb_retriever import chromadb_retriever
from scripts.utils.get_vector_store import get_vector_store
from scripts.utils.get_embedding_model import get_embedding_model
from scripts.Main.answer import answer_question

def main():
    print("Running vector store test...")
    result, time = answer_question("What is the news on USA election?")
    print("Test completed. Result:")
    print(result)
    print(f"Time taken: {time:.2f} seconds")



if __name__ == "__main__": 
    main()