# document_ingestion_service/utils/chroma_utils.py
import os
import json
import shutil

def ensure_ollama_chroma_collection(persist_dir: str, collection_name: str, expected_dim: int = 768):
    """
    Ensures the Chroma collection for Ollama has the correct embedding dimension.
    If not, deletes the collection so it can be recreated.
    """
    collection_path = os.path.join(persist_dir, collection_name)
    meta_path = os.path.join(collection_path, "collection_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        current_dim = meta.get("embedding_dimension")
        if current_dim != expected_dim:
            shutil.rmtree(collection_path, ignore_errors=True)
            print(f"Chroma collection dimension mismatch ({current_dim} vs {expected_dim}). Collection reset.")