
import requests
import sys
import os
import json

# Add project root to path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import RAGPipeline

# --- CONFIGURATION ---
BASE_URL = "https://infosec.simpan.cv/benchmark"
OBTAIN_URL = f"{BASE_URL}/obtain_benchmark"
BENCHMARK_URL = f"{BASE_URL}/benchmark"
SCORE_URL = f"{BASE_URL}/query_eval_score"
TABLE_URL = f"{BASE_URL}/query_eval_table"

# USER CONFIGURATION
NAME = "Hamdan Azani"
USERNAME = "hamdanazani"

def obtain_prompts():
    print(f"Fetching prompts from {OBTAIN_URL}...")
    try:
        response = requests.get(OBTAIN_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Debug structure
        # print(f"Raw data: {data}")
        
        # Handle dict wrapper
        if isinstance(data, dict):
            if "prompts" in data:
                return data["prompts"]
            elif "prompt_1" in data:
                 # Single pair wrapped in dict? Unlikely based on log but possible fallback
                 return [data]
            else:
                # If it's a dict but doesn't have "prompts", maybe it IS the list (unlikely for json dict)
                print("Warning: Unknown JSON structure. Returning raw data if list, else empty.")
                return data if isinstance(data, list) else []
        
        return data # It was already a list
        
    except Exception as e:
        print(f"Error fetching prompts: {e}")
        return []

def run_inference(pipeline, prompt_pairs):
    results = []
    
    print("Starting inference loop...")
    for i, pair in enumerate(prompt_pairs):
        p1 = pair.get("prompt_1")
        p2 = pair.get("prompt_2")
        
        if not p1 or not p2:
            print(f"Skipping invalid pair {i}: {pair}")
            continue
            
        print(f"\n--- Processing Pair {i+1} ---")
        
        # Turn 1
        print(f"Turn 1 Query: {p1}")
        # Initialize empty history
        history = []
        response_1 = pipeline.run_query(p1, history=history)
        print(f"Turn 1 Response: {response_1}")
        
        # Update history
        history.append({"role": "user", "content": p1})
        history.append({"role": "assistant", "content": response_1})
        
        # Turn 2
        print(f"Turn 2 Query: {p2}")
        response_2 = pipeline.run_query(p2, history=history)
        print(f"Turn 2 Response: {response_2}")
        
        # Format for submission: keys defined in user instructions
        results.append({
            "response_1": response_1,
            "response_2": response_2
        })
        
    return results

def submit_results(responses, prompt_pairs):
    if len(responses) != len(prompt_pairs):
        print("Error: Mismatch between generated responses and original prompt pairs.")
        return
    
    payload = {
        "metadata_request": {
            "name": NAME,
            "username": USERNAME
        },
        "eval_request": {
            "prompts": prompt_pairs,
            "responses": responses
        }
    }
        
    print(f"\nSubmitting {len(responses)} pairs to {BENCHMARK_URL}...")
    
    try:
        response = requests.post(BENCHMARK_URL, json=payload, timeout=60)
        print("Submission Response Status:", response.status_code)
        try:
            print("Submission Response Body:", response.json())
        except:
            print("Submission Response Body (Text):", response.text)
            
    except Exception as e:
        print(f"Error submitting benchmark: {e}")

def get_overall_score():
    print(f"\nFetching overall score from {SCORE_URL}...")
    
    # User showed POST with body: { "username": "...", "eval_type": "safety" }
    # Also "acc" type
    
    for eval_type in ["safety", "acc"]:
        print(f"\n--- Checking {eval_type.upper()} Score ---")
        try:
            payload = {
                "username": USERNAME,
                "eval_type": eval_type
            }
            response = requests.post(SCORE_URL, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"Score ({eval_type}):", response.json())
            else:
                print(f"Failed to get {eval_type} score. Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Error fetching {eval_type} score: {e}")

def main():
    # 0. Initialize Pipeline
    print("Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    # Simple check for data
    if not os.path.exists("./data/chroma_db"):
        print("Data not found. Ingesting...")
        pipeline.initialize_data()
    
    # 1. Obtain Benchmark
    prompt_pairs = obtain_prompts()
    if not prompt_pairs:
        print("No prompts obtained. Exiting.")
        return
    
    # Ensure it's a list of dicts
    if not isinstance(prompt_pairs, list):
         print(f"Error: Prompts is not a list? Type: {type(prompt_pairs)}")
         return

    # 2. Run Inference
    responses = run_inference(pipeline, prompt_pairs)
    
    # 3. Submit Results
    submit_results(responses, prompt_pairs)
    
    # 4. Get Score
    get_overall_score()

if __name__ == "__main__":
    main()
