# vector_store.py
import chromadb
from chromadb.utils import embedding_functions
from config import EMBED_MODEL
from file_utils import chunk_text

def build_vector_db(docs, metadata):
    """Create Chroma collection with document chunks."""
    client = chromadb.Client()
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    collection = client.create_collection("code_docs", embedding_function=embed_fn)

    for i, doc in enumerate(docs):
        for chunk in chunk_text(doc):
            collection.add(
                documents=[chunk],
                metadatas=[{"file_path": metadata[i]}],
                ids=[f"{metadata[i]}_{hash(chunk)}"]
            )

    return collection
