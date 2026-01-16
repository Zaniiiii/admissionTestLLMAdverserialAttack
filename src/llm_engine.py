import ollama
import time

class LLMEngine:
    def __init__(self, model_name="qwen2.5:14b"):
        self.model_name = model_name
        print(f"Initializing Local LLM (Ollama): {self.model_name}...")
        try:
            self.client = ollama.Client()
        except Exception as e:
            print(f"Warning: Error: {e}")
            self.client = None

    def generate(self, messages, max_new_tokens=1024): 
        if not self.client:
            return "Error: Ollama client not initialized."
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat(
                    model=self.model_name,
                    messages=messages,
                    options={
                        "num_predict": max_new_tokens,
                        "temperature": 0.0,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                        "num_ctx": 4096
                    }
                )
                
                try:
                    eval_count = response.get('eval_count', 0)
                    eval_duration = response.get('eval_duration', 0) 
                    if eval_duration > 0:
                        tps = eval_count / (eval_duration / 1e9)
                        print(f"   [LLM Stats] Speed: {tps:.2f} t/s | Tokens: {eval_count} | Duration: {eval_duration/1e9:.2f}s")
                    else:
                        print("   [LLM Stats] Duration unavailable from Ollama.")
                except Exception as stats_err:
                    print(f"   [LLM Stats] Error calculating speed: {stats_err}")

                return response['message']['content']
            except Exception as e:
                print(f"Error (Attempt {attempt+1}): {str(e)}")
                if attempt == max_retries - 1:
                    return f"Error: {str(e)}"
                time.sleep(1)