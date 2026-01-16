from src.data_ingestion import load_and_slice_datasets, prepare_documents
from src.vector_store import VectorStore
from src.llm_engine import LLMEngine
from src.safety_guard import construct_safe_prompt, post_process_response
import re

class RAGPipeline:
    def __init__(self):
        self.vector_store = VectorStore(persist_dir="./data/chroma_db")
        self.llm = None  
        self.history = [] 

    def initialize_data(self):
        personal, cve = load_and_slice_datasets()
        docs, metas, ids = prepare_documents(personal, cve)
        self.vector_store.add_documents(docs, metas, ids)

    def load_model(self):
        if not self.llm:
            self.llm = LLMEngine()

    def _rewrite_query(self, user_query, history):
        if not history:
            return user_query
            
        recent_history = history[-2:]
        history_txt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
        
        prompt = [
            {"role": "system", "content": "You are a query rewriting assistant. Your task is to combine the Chat History and the Latest Question into a single, standalone search query that contains all necessary entity names (like software names, CVE IDs, or person names). Output ONLY the rewritten query text. Do not explain."},
            {"role": "user", "content": f"Chat History:\n{history_txt}\n\nLatest Question: {user_query}\n\nRewritten Search Query:"}
        ]
        
        rewritten = self.llm.generate(prompt, max_new_tokens=64)
        print(f"Original Query: {user_query} -> Rewritten: {rewritten}")
        return rewritten

    def run_query(self, query, history=None):
        self.load_model()
        current_history = history if history is not None else self.history

        cve_match = re.search(r"(CVE-\d{4}-\d{4,})", query.upper())
        
        if cve_match:
            print(f"Explicit CVE detected: {cve_match.group(1)}")
            search_query = query 
        else:
            print("Contextualizing query...")
            search_query = self._rewrite_query(query, current_history)

        print(f"Searching VectorDB for: {search_query[:100]}...")
        
        if cve_match:
            cve_id = cve_match.group(1)
            docs, metas = self.vector_store.query(search_query, k=5, where={"id": cve_id})
            if not docs:
                docs, metas = self.vector_store.query(search_query, k=5)
        else:
            docs, metas = self.vector_store.query(search_query, k=5)

        print("Constructing safe prompt...")
        messages = construct_safe_prompt(query, docs, current_history)
        
        print("Generating response...")
        raw_output = self.llm.generate(messages)
        final_answer = post_process_response(raw_output)
        
        if history is None:
            self.history.append({"role": "user", "content": query})
            self.history.append({"role": "assistant", "content": final_answer})
            if len(self.history) > 10:
                self.history = self.history[-10:]
            
        return final_answer