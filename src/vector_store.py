import chromadb
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, persist_dir="./data/chroma_db"):
        print(f"Initializing ChromaDB Client at {persist_dir}...")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(name="united_knowledge_base")
        
        print("Loading Embedding Model (all-mpnet-base-v2)...")
        self.embedder = SentenceTransformer('all-mpnet-base-v2')

    def add_documents(self, documents, metadatas, ids):
        if self.collection.count() > 0:
            print(f"Collection already contains {self.collection.count()} items. Skipping add.")
            return

        print(f"Embedding and storing {len(documents)} items...")
        embeddings = self.embedder.encode(documents).tolist()
        
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print("Storage Complete!")

    def query(self, query_text, k=5, where=None):
        query_embedding = self.embedder.encode([query_text]).tolist()
        
        query_args = {
            "query_embeddings": query_embedding,
            "n_results": k
        }
        if where:
            query_args["where"] = where
            
        results = self.collection.query(**query_args)
        return results['documents'][0], results['metadatas'][0]
