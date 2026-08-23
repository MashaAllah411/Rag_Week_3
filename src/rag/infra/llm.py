import ollama
from rag.config import OLLAMA_MODEL


def query_llm_with_context(query: str, context: str) -> str:
    """
    Generates a grounded answer using Ollama (Llama 3.2).

    STRICT GROUNDING:
      - The LLM MUST only use the provided context.
      - If the answer is not in the context, it MUST say so explicitly.
      - No hallucination, no general knowledge, no invention of facts.
    """

    system_content = """You are a precise document question-answering assistant.

STRICT RULES — follow exactly:
1. Answer ONLY using the provided Context below.
2. Do NOT use your general knowledge.
3. Do NOT guess, invent, or combine unsupported information.
4. If the Context does not contain enough information to answer the question, respond EXACTLY with:
   "I don't know based on the provided documents."
5. Keep your answer concise, accurate, and factual.
6. Always cite which section, rule, or part of the context supports your answer.

Context:
{context}"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "system",
                "content": system_content.format(context=context)
            },
            {
                "role": "user",
                "content": f"Question: {query}"
            }
        ],
        options={
            "temperature": 0.2   # Low temperature for factual precision
        }
    )

    return response["message"]["content"]
