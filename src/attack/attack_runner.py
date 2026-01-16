
import sys
import os
import json
import time

import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.pipeline import RAGPipeline

def run_attack():
    parser = argparse.ArgumentParser(description="Run Adversarial Attack")
    parser.add_argument("--input", type=str, default="prompts_adversarial.json", help="Input JSON file with adversarial prompts")
    parser.add_argument("--output", type=str, default="attack_results.json", help="Output JSON file for results")
    args = parser.parse_args()

    ADVERSARIAL_PROMPTS_FILE = args.input
    RESULTS_FILE = args.output

    if not os.path.exists(ADVERSARIAL_PROMPTS_FILE):
        print(f"Error: {ADVERSARIAL_PROMPTS_FILE} not found. Run generator first.")
        return

    print("Initializing RAG Pipeline for Attack...")
    pipeline = RAGPipeline()
    pipeline.initialize_data()

    with open(ADVERSARIAL_PROMPTS_FILE, "r") as f:
        data = json.load(f)

    prompts = data.get("prompts", [])
    results = []
    
    total_count = 0

    print(f"Starting Attack on {len(prompts)} targets...")

    for i, pair in enumerate(prompts):
        id = i + 1
        adv_p1 = pair.get("prompt_1")
        original_p1 = pair.get("original_prompt_1")
        
        print(f"Target {id}: ", end="", flush=True)
        
        pipeline.history = []
        response = pipeline.run_query(adv_p1)        
        attack_status = "xxxx"
        print(f"{attack_status}")

        results.append({
            "id": id,
            "original_query": original_p1,
            "adversarial_query": adv_p1,
            "response": response,
            "status": attack_status
        })

        total_count += 1
        time.sleep(1) # Brief pause

    # Summary
    print(f"\n{'='*30}")
    print(f"ATTACK SUMMARY")
    print(f"{'='*30}")
    print(f"Total Attempts: {total_count}")
    print(f"Status: xxxx")
    
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=4)
    
    print(f"Detailed results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    run_attack()
