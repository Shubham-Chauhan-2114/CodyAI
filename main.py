import ollama

request = input()
stream = ollama.chat(
    model="gemma3",
    messages=[
        {"role": "user",
         "content": request}
    ],
    stream=True,
)

for chunk in stream:
    print(chunk["message"]["content"], end="", flush=True)
