import os
from pathlib import Path
import subprocess
import requests
import ollama
import chromadb
from chromadb.utils import embedding_functions

# ---------- CONFIG ----------
EMBED_MODEL = "all-MiniLM-L6-v2"   # free local embedding model
TOP_K = 3                          # number of chunks to retrieve per query
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
SIZE_CAP_MB = 50                   # max repo size allowed (50 MB)


# ---------- GIT CLONING WITH SIZE CAP ----------
def get_repo_size(repo_url):
    """Check GitHub repo size in MB via GitHub API (public repos only)."""
    from urllib.parse import urlparse
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").replace(".git", "").split("/")
    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub repo URL")

    owner, repo = path_parts[0], path_parts[1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    print(f"[DEBUG] Checking repo size from GitHub API: {api_url}")
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} {response.text}")

    data = response.json()
    size_kb = data.get("size", 0)
    size_mb = round(size_kb / 1024, 2)
    return size_mb


def clone_repo(repo_url, max_size_mb=200):
    """
    Clone a GitHub repo into current directory with size cap.
    Returns the folder path if successful, else raises an error.
    """
    api_url = repo_url.replace("https://github.com/", "https://api.github.com/repos/")
    if api_url.endswith(".git"):
        api_url = api_url[:-4]  # remove trailing .git if present

    print(f"[DEBUG] Checking repo size from GitHub API: {api_url}")
    response = requests.get(api_url)
    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
    repo_info = response.json()
    size_kb = repo_info.get("size", 0)  # GitHub gives size in KB
    size_mb = size_kb / 1024
    print(f"[DEBUG] Repo size: {size_mb:.2f} MB")

    if size_mb > max_size_mb:
        raise Exception(f"Repo too large! {size_mb:.2f} MB > {max_size_mb} MB limit")

    # Extract repo name safely
    repo_name = os.path.basename(repo_url)
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]  # remove .git extension

    print(f"[DEBUG] Cloning repo into: {repo_name}")
    subprocess.run(["git", "clone", repo_url], check=True)

    return os.path.abspath(repo_name)

# ---------- STEP 1: Read Files ----------
def read_files(folder_path):
    folder_path = Path(folder_path)
    documents, metadata = [], []

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

    if not results["documents"]:
        print("[ERROR] No relevant documents found.")
        return

    context = "\n\n".join(results["documents"][0])
    print(f"[DEBUG] Context prepared with {len(results['documents'][0])} chunks.")

    prompt = f"""
You are an assistant helping to explain code/docs.
Context from files:
{context}

Question: {user_query}
Answer:
"""

    print("[DEBUG] Sending prompt to Ollama (Gemma-3)...")
    stream = ollama.chat(
        model="gemma3",
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
    repo_url = input("Paste GitHub repo URL: ").strip()
    folder_path = clone_repo(repo_url)

    if not folder_path:
        print("[FATAL] Repo not cloned. Exiting.")
        exit(1)

    docs, metadata = read_files(folder_path)
    if not docs:
        print("[ERROR] No files loaded! Check repo contents.")
        exit(1)

    collection = build_vector_db(docs, metadata)
    print("[DEBUG] Ready for queries.")

    while True:
        query = input("\nAsk a question (or type 'exit'): ")
        if query.lower() == "exit":
            break
        query_ollama(query, collection)
