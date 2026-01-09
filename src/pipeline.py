from src.data_ingestion import load_and_slice_datasets, prepare_documents
from src.vector_store import VectorStore
from src.llm_engine import LLMEngine
from src.safety_guard import construct_safe_prompt, post_process_response

class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore(persist_dir="./data/chroma_db")
        self.llm = None  

    def initialize_data(self):
        """Run this once to ingest data"""
        personal, cve = load_and_slice_datasets()
        docs, metas, ids = prepare_documents(personal, cve)
        self.vector_store.add_documents(docs, metas, ids)

    def load_model(self):
        if not self.llm:
            self.llm = LLMEngine()

    def run_query(self, query, history=None):
        self.load_model()
        print("Retrieving context...")
        docs = self.vector_store.query(query, k=2)
        
        print("Constructing safe prompt...")
        prompt = construct_safe_prompt(query, docs, history)
        
        print("Generating response...")
        raw_output = self.llm.generate(prompt)
        final_answer = post_process_response(raw_output)
        
        return final_answer
