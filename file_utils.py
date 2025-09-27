# file_utils.py
from pathlib import Path
from config import CHUNK_SIZE, CHUNK_OVERLAP

def read_files(folder_path):
    """Read code/docs recursively from repo."""
    folder_path = Path(folder_path)
    documents, metadata = [], []

    for file_path in folder_path.rglob("*"):
        if file_path.suffix.lower() in [".txt", ".py", ".md", ".java", ".cpp", ".js"]:
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore").strip()
                if text:
                    documents.append(text)
                    metadata.append(str(file_path))
            except Exception as e:
                print(f"[ERROR] Failed to read {file_path}: {e}")

    return documents, metadata


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return chunks
