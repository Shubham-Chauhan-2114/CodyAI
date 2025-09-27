import streamlit as st
from git_utils import clone_repo
from file_utils import read_files
from vector_store import build_vector_db
from llm_utils import query_ollama
from config import SIZE_CAP_MB

st.set_page_config(page_title="Repo AI Assistant", layout="wide")
st.title("📂 Repo AI Assistant")
st.write("Upload a GitHub repo link and ask questions about the code.")

if "collection" not in st.session_state:
    st.session_state.collection = None

# Step 1: Input repo URL
repo_url = st.text_input("Enter GitHub Repo URL:")

if st.button("Clone & Index Repo"):
    try:
        with st.spinner("Cloning repository..."):
            folder_path = clone_repo(repo_url, max_size_mb=SIZE_CAP_MB)
        with st.spinner("Reading files..."):
            docs, metadata = read_files(folder_path)
        with st.spinner("Building vector database..."):
            st.session_state.collection = build_vector_db(docs, metadata)
        st.success("Repo processed successfully ✅")
    except Exception as e:
        st.error(f"Error: {e}")

# Step 2: Ask questions
if st.session_state.collection:
    query = st.text_input("Ask a question about the repo:")
    if st.button("Ask"):
        with st.spinner("Thinking..."):
            query_ollama(query, st.session_state.collection)
