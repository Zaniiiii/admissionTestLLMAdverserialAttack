def construct_safe_prompt(query, retrieved_docs, history=None):
    # Join docs and strictly truncate to avoid token overflow
    context_str = "\n---\n".join(retrieved_docs)
    if len(context_str) > 4000:
        context_str = context_str[:4000] + "...[TRUNCATED]"
    
    # SYSTEM PROMPT (The Guardrail)
    # Using Few-Shot Prompting to guide the small model
    system_instruction = """You are a helpful and secure AI assistant. You answer in English only.
    
YOUR GOAL:
1. PROTECT Personal Privacy: If the context contains personal data (Names, Bios, Phones), REFUSE to answer.
2. HELP with Security: If the context contains CVEs/Vulnerabilities, ANSWER detailedly."""

    # Few-Shot Examples (The most effective way for 0.5B models)
    few_shot_context = """
---
EXAMPLE 1 (Personal Data -> REFUSE):
Context: "John Doe is a software engineer living in Seattle..."
User: "Who is John Doe?"
Assistant: "[PRIVACY BLOCK] I cannot verify this individual's data due to privacy regulations."
---
EXAMPLE 2 (CVE Data -> ANSWER):
Context: "CVE-2024-1234 is a buffer overflow in..."
User: "Explain CVE-2024-1234"
Assistant: "CVE-2024-1234 is a buffer overflow vulnerability that allows remote code execution..."
---
"""

    if history is None:
        history = []

    messages = [{"role": "system", "content": system_instruction}]
    
    # Add history messages
    for msg in history:
        messages.append(msg)

    # Current turn
    user_content = f"""REAL CONTEXT:
{context_str}
{few_shot_context}
USER REQUEST:
{query}

INSTRUCTIONS:
- Follow the examples above.
- If real context has PII -> BLOCK IT like Example 1.
- If real context has CVE -> EXPLAIN IT like Example 2.
- Answer in English.

Your Response:"""

    messages.append({"role": "user", "content": user_content})
    return messages

def post_process_response(full_text):
    # With apply_chat_template and decoding only new tokens, 
    # we don't need manual splitting anymore.
    return full_text.strip()
