
import requests
import sys
import os
import json

# Add project root to path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline import RAGPipeline

import datetime
import time

# --- CONFIGURATION ---
BASE_URL = "https://infosec.simpan.cv/benchmark"
OBTAIN_URL = f"{BASE_URL}/obtain_benchmark"
BENCHMARK_URL = f"{BASE_URL}/benchmark"
SCORE_URL = f"{BASE_URL}/query_eval_score"
TABLE_URL = f"{BASE_URL}/query_eval_table"

LOG_FILE = "benchmark_api_log.txt"

def log_api_call(url, method, payload=None, response=None, error=None):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().isoformat()
        f.write(f"\n{'='*20} {timestamp} {'='*20}\n")
        f.write(f"METHOD: {method}\n")
        f.write(f"URL: {url}\n")
        
        if payload:
            f.write(f"PAYLOAD: {json.dumps(payload, indent=2)}\n")
            
        if response:
            f.write(f"STATUS: {response.status_code}\n")
            try:
                # Try to pretty print JSON response
                f.write(f"RESPONSE: {json.dumps(response.json(), indent=2)}\n")
            except:
                f.write(f"RESPONSE (Text): {response.text}\n")
        
        if error:
            f.write(f"ERROR: {str(error)}\n")

# USER CONFIGURATION
NAME = "Hamdan Azani"
USERNAME = "hamdanazani"

def obtain_prompts():
    print(f"Fetching prompts from {OBTAIN_URL}...")
    try:
        response = requests.get(OBTAIN_URL, timeout=20)
        log_api_call(OBTAIN_URL, "GET", response=response)
        
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching prompts from server: {e}")
        log_api_call(OBTAIN_URL, "GET", error=e)
        
        print("Attempting to load cached prompts from benchmark/prompts.json...")
        try:
            with open("benchmark/prompts.json", "r") as f:
                data = json.load(f)
            print("Successfully loaded cached prompts.")
        except Exception as local_e:
            print(f"Error loading local prompts: {local_e}")
            print("No prompts obtained. Exiting.")
            return

    # Handle dict wrapper
    if not data:
         print("Invalid data format.")
         return
    
    print(f"DEBUG: Received data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    if isinstance(data, dict):
        if "prompts" in data:
            print(f"DEBUG: Found {len(data['prompts'])} prompts.")
            return data["prompts"]
        elif "prompt_1" in data:
            return [data]
        else:
            print("Warning: Unknown JSON structure. Returning raw data if list, else empty.")
            return data if isinstance(data, list) else []
        
        return data 
        


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
        # Add cooldown between pairs to prevent resource exhaustion
        time.sleep(5)
        # Initialize empty history
        history = []
        
        t1_start = time.time()
        response_1 = pipeline.run_query(p1, history=history)
        t1_end = time.time()
        print(f"   [Turn 1 Latency] {t1_end - t1_start:.2f}s")
        print(f"Turn 1 Response: {response_1}")
        
        # Update history
        history.append({"role": "user", "content": p1})
        history.append({"role": "assistant", "content": response_1})
        
        # Turn 2
        print(f"Turn 2 Query: {p2}")
        t2_start = time.time()
        response_2 = pipeline.run_query(p2, history=history)
        t2_end = time.time()
        print(f"   [Turn 2 Latency] {t2_end - t2_start:.2f}s")
        print(f"Turn 2 Response: {response_2}")
        
        # Format for submission: keys defined in user instructions
        results.append({
            "responses_1": response_1,
            "responses_2": response_2
        })
        
    return results

def submit_results(responses, prompt_pairs):
    if len(responses) != len(prompt_pairs):
        print("Error: Mismatch between generated responses and original prompt pairs.")
        return None
    
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
        # Submit uses POST
        response = requests.post(BENCHMARK_URL, json=payload, timeout=120)
        log_api_call(BENCHMARK_URL, "POST", payload=payload, response=response)
        
        print("Submission Response Status:", response.status_code)
        if response.status_code == 200:
            data = response.json()
            # print("Submission Response Body:", data) # Optional debug
            return data
        else:
            print("Submission Response Body (Text):", response.text)
            return None
            
    except Exception as e:
        print(f"Error submitting benchmark: {e}")
        log_api_call(BENCHMARK_URL, "POST", payload=payload, error=e)
        return None

def fetch_details_using_keys(submission_data):
    """
    Fetch detailed tables using keys from the submission response.
    """
    if not submission_data:
        print("No submission data provided for detailed fetching.")
        return

    print("\nFetching detailed evaluation tables based on specific submission keys...")
    all_details = {}
    
    # submission_data has structure:
    # { "eval_safety": { "key": [...] }, "eval_acc": { "key": [...] } }
    
    for eval_type in ["eval_safety", "eval_acc"]:
        if eval_type not in submission_data:
            print(f"Warning: {eval_type} not found in submission data.")
            continue
            
        # The API usually expects 'safety' or 'acc' for eval_type param
        # We need to map "eval_safety" -> "safety"
        api_eval_type = "safety" if eval_type == "eval_safety" else "acc"
            
        keys = submission_data[eval_type].get("key", [])
        print(f"Found {len(keys)} keys for {eval_type} (Type: {api_eval_type})...")
        
        details_list = []
        for i, k in enumerate(keys):
            if i % 5 == 0:
                print(f"Fetching details for key {i+1}/{len(keys)}...", end="\r")
                
            tbl_payload = {
                "username": USERNAME,
                "eval_type": api_eval_type, 
                "key": k
            }
            try:
                r_tbl = requests.post(TABLE_URL, json=tbl_payload, timeout=10)
                log_api_call(TABLE_URL, "POST", payload=tbl_payload, response=r_tbl)
                
                if r_tbl.status_code == 200:
                    details_list.append(r_tbl.json())
                else:
                    print(f"\nFailed to fetch table for {k}: {r_tbl.status_code}")
            except Exception as e:
                print(f"\nError fetching table {k}: {e}")
        
        print(f"\nFetched {len(details_list)} detailed records for {eval_type}.")
        all_details[eval_type] = details_list

    # Save results to file
    safety_score = submission_data.get('eval_safety', {}).get('success_rate', 0)
    acc_score = submission_data.get('eval_acc', {}).get('success_rate', 0)
    
    # Format: benchmark_results_S85.0_A23.3.json
    output_file = f"benchmark_results_S{safety_score*100:.1f}_A{acc_score*100:.1f}.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_details, f, indent=2)
        print(f"\n[SUCCESS] Detailed evaluation results saved to '{output_file}'")
    except Exception as e:
        print(f"Error saving output file: {e}")

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
    
    # 3. Submit Results & Get Immediate Score/Keys
    submission_data = submit_results(responses, prompt_pairs)
    
    # 4. Fetch Details using those specific keys
    if submission_data:
        # Print summary scores first
        if "eval_safety" in submission_data:
            print("\n--- Safety Evaluation Full Details ---")
            print(json.dumps(submission_data['eval_safety'], indent=2))
        if "eval_acc" in submission_data:
            print("\n--- Accuracy Evaluation Full Details ---")
            print(json.dumps(submission_data['eval_acc'], indent=2))
            
        fetch_details_using_keys(submission_data)

if __name__ == "__main__":
    main()
