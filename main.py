# main.py
from git_utils import clone_repo
from file_utils import read_files
from vector_store import build_vector_db
from llm_utils import query_ollama
from config import SIZE_CAP_MB

if __name__ == "__main__":
    print("[DEBUG] Starting AI Repo Assistant...")
    repo_url = input("Paste GitHub repo URL: ").strip()
    folder_path = clone_repo(repo_url, max_size_mb=SIZE_CAP_MB)

    docs, metadata = read_files(folder_path)
    if not docs:
        print("[ERROR] No files loaded. Exiting.")
        exit(1)

    collection = build_vector_db(docs, metadata)
    print("[DEBUG] Ready for queries.")

    while True:
        query = input("\nAsk a question (or type 'exit'): ")
        if query.lower() == "exit":
            break
        query_ollama(query, collection)
