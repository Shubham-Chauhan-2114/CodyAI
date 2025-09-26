import ollama

stream = ollama.chat(
    model="gemma3",
    messages=[
        {"role": "user", "content": "Explain system design of a URL shortener in 5 bullet points"}
    ],
    stream=True,
)

for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)
