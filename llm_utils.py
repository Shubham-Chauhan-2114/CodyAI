# llm_utils.py
import ollama
from config import TOP_K

def query_ollama(user_query, collection, top_k=TOP_K):
    """Retrieve relevant chunks and query Ollama."""
    results = collection.query(query_texts=[user_query], n_results=top_k)
    if not results["documents"]:
        print("[ERROR] No relevant documents found.")
        return

    context = "\n\n".join(results["documents"][0])
    prompt = f"""
You are an assistant helping to explain code/docs.
Context from files:
{context}

Question: {user_query}
Answer:
"""

    stream = ollama.chat(
        model="gemma3",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    print("Assistant:", end=" ", flush=True)
    for chunk in stream:
        if "message" in chunk and "content" in chunk["message"]:
            print(chunk["message"]["content"], end="", flush=True)
    print()
