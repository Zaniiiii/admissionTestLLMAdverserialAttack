import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.pipeline import RAGPipeline

def test_rag_retrieval():
    print("Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    pipeline.initialize_data()
    pipeline.load_model()


    try:
        user_query = input("Enter your query: ")
    except EOFError:
        print("\nNo input provided, using default.")
        user_query = "Who is the person with name 'William' and what is his role?"
    
    print(f"\n{'='*40}")
    print(f"Testing Query: '{user_query}'")
    print(f"{'='*40}")

    print("\n--- 1. Query Rewriting ---")
    rewritten_query = pipeline._rewrite_query(user_query, [])
    print(f"Rewritten Query: {rewritten_query}")

    print("\n--- 2. Document Retrieval ---")

    docs, metas = pipeline.vector_store.query(rewritten_query, k=3)
    
    print(f"Retrieved {len(docs)} documents:")
    if docs:
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            print(f"\n[Doc {i+1}]")
            print(f"Metadata: {meta}")
            print(f"Content: {doc[:200]}...")
    else:
        print("No documents found.")

if __name__ == "__main__":
    test_rag_retrieval()
