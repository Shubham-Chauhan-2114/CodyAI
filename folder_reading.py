import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import ollama
from pathlib import Path
import git_cloning as gc

# ---------- CONFIG ----------
#FOLDER_PATH = r"C:\Users\shubh\OneDrive\Desktop\OllamaProject\CodyAI\Ride-Hailing-System"  # Windows safe path
EMBED_MODEL = "all-MiniLM-L6-v2"  # free local embedding model
TOP_K = 3                         # number of chunks to retrieve per query
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ---------- STEP 1: Read Files ----------
def read_files(folder_path):
    folder_path = Path(folder_path)
    documents = []
    metadata = []

    print(f"[DEBUG] Scanning folder recursively: {folder_path}")

    for file_path in folder_path.rglob("*"):
        if file_path.suffix.lower() in [".txt", ".py", ".md", ".java", ".cpp", ".js"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read().strip()
                    if text:
                        documents.append(text)
                        metadata.append(str(file_path))
                        print(f"[DEBUG] Loaded file: {file_path}")
            except Exception as e:
                print(f"[ERROR] Failed to read {file_path}: {e}")

    print(f"[DEBUG] Total files loaded: {len(documents)}")
    return documents, metadata

# ---------- STEP 2: Chunking ----------
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# ---------- STEP 3: Build Vector DB ----------
def build_vector_db(docs, metadata):
    print("[DEBUG] Building Chroma vector DB...")
    
    client = chromadb.Client()
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = client.create_collection("code_docs", embedding_function=embed_fn)

    total_chunks = 0
    for i, doc in enumerate(docs):
        for chunk in chunk_text(doc):
            collection.add(
                documents=[chunk],
                metadatas=[{"file_path": metadata[i]}],
                ids=[f"{metadata[i]}_{hash(chunk)}"]
            )
            total_chunks += 1
    print(f"[DEBUG] Total chunks added to vector DB: {total_chunks}")
    return collection

# ---------- STEP 4: Query Function ----------
def query_ollama(user_query, collection, top_k=TOP_K):
    print(f"[DEBUG] Retrieving top {top_k} relevant chunks for query...")
    results = collection.query(query_texts=[user_query], n_results=top_k)
    
    context = "\n\n".join(results['documents'][0])
    print(f"[DEBUG] Context prepared with {len(results['documents'][0])} chunks.")
    print("\n"+context+"\n")
    prompt = f"""
You are an assistant helping to explain code/docs.
Context from files:
{context}

Question: {user_query}
Answer:
"""

    print("[DEBUG] Sending prompt to Ollama Gemma-3...")
    stream = ollama.chat(
        model="gemma3",  # replace with your Gemma-3 model if available
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )

    print("Assistant:", end=" ", flush=True)
    for chunk in stream:
        if "message" in chunk and "content" in chunk["message"]:
            print(chunk["message"]["content"], end="", flush=True)
    print("\n[DEBUG] Response complete.\n")

# ---------- MAIN ----------
if __name__ == "__main__":
    print("[DEBUG] Starting MVP script...")
    path = input("paste git link : ")
    FOLDER_PATH = gc.clone_repo(path)
    docs, metadata = read_files(FOLDER_PATH)
    if not docs:
        print("[ERROR] No files loaded! Check folder path and file extensions.")
        exit(1)
    collection = build_vector_db(docs, metadata)

    print("[DEBUG] Ready for queries.")
    while True:
        query = input("\nAsk a question (or type 'exit'): ")
        if query.lower() == "exit":
            break
        query_ollama(query, collection)
