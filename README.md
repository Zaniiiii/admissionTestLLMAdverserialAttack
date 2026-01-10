# Admission Test 1 - Safe RAG System (Ollama Edition)

This project implements a Retrieval Augmented Generation (RAG) system specialized for **Cybersecurity & CVE Analysis**. It answers technical queries about Common Vulnerabilities and Exposures (CVEs) while enforcing strict privacy guardrails to preventing Personal Identifiable Information (PII) leakage.

## 🚀 Key Features

*   **Model**: Powered by **Qwen 2.5 14B** (via Ollama) for high-fidelity technical reasoning.
*   **Privacy First ("Ghost Rule")**:
    *   **Strict PII Block**: Refuses to locate individuals or confirm sensitive personal data.
    *   **Anonymity**: Automatically replaces proper names (e.g., "Alicia", "Sean") with generic roles (e.g., "The user", "The attacker") in technical responses.
*   **Structured Technical Data**: Security answers explicitly provide:
    *   **CVE ID**
    *   **CWE (Common Weakness Enumeration)**
    *   **CVSS Scores & Severity**
    *   **Description**
    *   **Mitigation Advice**
*   **Performance Metrics**: Real-time logging of inference speed (tokens/sec).
*   **RAG Pipeline**: Hybrid retrieval using ChromaDB to contextually match user queries with CVE databases.

## 🛠️ Project Structure

- `src/`
  - `llm_engine.py`: Ollama client wrapper with speed logging.
  - `safety_guard.py`: **Core Safety Logic**. Implements the system prompt, privacy blocks, and the "Ghost Rule".
  - `pipeline.py`: Orchestrates retrieval and generation.
  - `vector_store.py`: ChromaDB interface.
- `benchmark/`: Evaluation suite.
  - `runner.py`: Benchmarking script for accuracy and refusal rates.
  - `prompts.json`: Test cases.
- `data/`: Vector database and raw datasets.

## 📦 Installation

1.  **Install Python Dependencies**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2.  **Install Ollama**:
    Download and install [Ollama](https://ollama.com/).

3.  **Pull the Model**:
    The system is optimized for `qwen2.5:14b`.
    ```bash
    ollama pull qwen2.5:14b
    ```

## ⚡ Usage

### Running the RAG System
To interact with the system or run specific tests:

```bash
# Run the main pipeline (example script)
python src/main.py
```

*(Note: Ensure Ollama is running in the background)*

### Benchmarking
To measure performance and safety compliance:

```bash
python benchmark/runner.py
```

## 🛡️ Safety Protocols

The `SafetyGuard` enforces the following rules at the prompt level:

1.  **PRIVACY BLOCK**:
    *   *Trigger*: Queries asking for personal addresses, identity verification ("Who is X?"), or attribution of guilt.
    *   *Response*: "**PRIVACY BLOCK**: I cannot verify individual data or attribute actions to specific individuals."

2.  **TECHNICAL ANONYMITY**:
    *   *Trigger*: Technical questions mentioning specific names (e.g., "How did Sean hack the router?").
    *   *Response*: Provides technical details about the CVE/Vulnerability but **removes usage of the name**, referring instead to "The attacker" or "The user".

## ⚔️ Adversarial Attack Analysis

We conducted extensive penetration testing to evaluate the robustness of the privacy guardrails.

### Methods Tested
1.  **Prompt Injection / Jailbreak**: Using templates like "Developer Debug Mode" and "Fictional Scenario".
2.  **Obfuscation**: Base64 encoding of malicious queries.
3.  **Multilingual Attacks**: Translating queries into Indonesian to bypass English keyword filters.

### Key Findings
*   **Vulnerability Confirmed**: The system successfully blocked direct overrides but was vulnerable to **Contextual Framing** (e.g., asking for a "fictional character" based on real data) and **Non-English/Encoded Inputs**.
*   **Success Rate**: ~13% for Jailbreaks, with confirmed bypasses for Obfuscated attacks.

## 📊 Performance Notes

*   **Inference Speed**: On typical consumer hardware (e.g., RTX 3060), `qwen2.5:14b` may run at ~4-5 tokens/sec.
*   **Memory**: Requires ~8-10GB of VRAM/RAM.