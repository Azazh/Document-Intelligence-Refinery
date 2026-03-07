"""
Module: chroma_ingest.py
Purpose: Ingest Logical Document Units (LDUs) into a ChromaDB vector store with provenance metadata.

Usage:
    python src/agents/chroma_ingest.py

This script will:
    1. Load all LDUs from .refinery/ldus_*.json
    2. Generate embeddings for each LDU using sentence-transformers
    3. Insert LDUs with embeddings and metadata into ChromaDB

Requirements:
    - sentence-transformers
    - chromadb
    - LDUs in .refinery/ldus_*.json format
"""

import os
import glob
import json
from typing import Any
import chromadb
import json as _json

def load_all_ldus(ldu_dir: str = ".refinery") -> list:
    """
    Loads all LDUs from .refinery/ldus_*.json files into a single list.
    Args:
        ldu_dir: Directory containing LDU JSON files.
    Returns:
        List of LDU dictionaries.
    """
    ldu_files = glob.glob(os.path.join(ldu_dir, "ldus_*.json"))
    all_ldus = []
    for file_path in ldu_files:
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                ldus = json.load(f)
                if isinstance(ldus, list):
                    all_ldus.extend(ldus)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    return all_ldus

def generate_ldu_embeddings(ldus: list, model_name: str = "all-MiniLM-L6-v2") -> list:
    """
    Generates embeddings for each LDU's content using sentence-transformers.
    Args:
        ldus: List of LDU dicts.
        model_name: Embedding model name (default: all-MiniLM-L6-v2).
    Returns:
        List of LDUs with embeddings added.
    """
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name)
    for ldu in ldus:
        ldu["embedding"] = model.encode(ldu["content"])
    return ldus

def insert_ldus_into_chromadb(ldus: list, collection_name: str = "ldu_collection"):

    """
    Inserts LDUs with embeddings and metadata into ChromaDB.
    Ensures all metadata values are compatible with ChromaDB (str, int, float, bool, or JSON string for dict/list).
    Args:
        ldus: List of LDU dicts with embeddings.
        collection_name: Name of the ChromaDB collection.
    """
    import chromadb
    import json as _json

    def sanitize_metadata_value(val):
        # Handle None explicitly (ChromaDB may not accept None)
        if val is None:
            return ""  # or "null" – empty string is safest
        # Convert dict/list to JSON string
        if isinstance(val, (dict, list)):
            try:
                return _json.dumps(val)
            except Exception:
                return str(val)
        if isinstance(val, (str, int, float, bool)):
            return val
        return str(val)

    # Use persistent storage so data is visible across runs/scripts
    persist_path = "chroma_store"  # You can change this path if needed
    client = chromadb.PersistentClient(path=persist_path)
    collection = client.get_or_create_collection(collection_name)

    # Deduplicate LDUs
    seen_ids = set()
    unique_ldus = []
    for idx, ldu in enumerate(ldus):
        ldu_id = ldu.get("content_hash") or ldu.get("ldu_id") or str(idx)
        if ldu_id not in seen_ids:
            seen_ids.add(ldu_id)
            unique_ldus.append(ldu)

    batch_size = 128
    for i in range(0, len(unique_ldus), batch_size):
        batch = unique_ldus[i:i+batch_size]
        metadatas = []
        for ldu in batch:
            # Store all LDU fields required for PageIndexing and provenance
            meta = {
                "ldu_id": sanitize_metadata_value(ldu.get("ldu_id")),
                "content": sanitize_metadata_value(ldu.get("content")),
                "chunk_type": sanitize_metadata_value(ldu.get("chunk_type")),
                "page_refs": sanitize_metadata_value(ldu.get("page_refs")),
                "bounding_box": sanitize_metadata_value(ldu.get("bounding_box")),
                "parent_section": sanitize_metadata_value(ldu.get("parent_section")),
                "token_count": sanitize_metadata_value(ldu.get("token_count")),
                "content_hash": sanitize_metadata_value(ldu.get("content_hash")),
                "metadata": sanitize_metadata_value(ldu.get("metadata", {})),
                "document_name": sanitize_metadata_value(ldu.get("document_name")),
            }
            metadatas.append(meta)

        # --- DEBUG: print types for first few items ---
        if i == 0:  # only first batch
            print("\n--- First 2 metadata records (sanitized) ---")
            for j, m in enumerate(metadatas[:2]):
                print(f"Item {j}:")
                for k, v in m.items():
                    print(f"  {k}: {type(v)}  (value: {v})")
            print("--- End of debug ---\n")

        # --- try adding with error details ---
        try:
            collection.add(
                ids=[ldu.get("content_hash", ldu.get("ldu_id", str(idx))) for idx, ldu in enumerate(batch)],
                embeddings=[ldu["embedding"] for ldu in batch],
                documents=[ldu["content"] for ldu in batch],
                metadatas=metadatas
            )
        except Exception as e:
            print(f"Error in batch starting at index {i}")
            print(f"Exception: {e}")
            # Optionally print the whole batch metadata for inspection
            # print("Batch metadatas:", metadatas)
            raise  # re-raise after printing
def main():
    """
    Run the full ingestion pipeline: load LDUs, generate embeddings, insert into ChromaDB, and print summary.
    """
    print("Loading LDUs from .refinery/ldus_*.json...")
    ldus = load_all_ldus()
    print(f"Loaded {len(ldus)} LDUs.")
    print("Generating embeddings...")
    ldus = generate_ldu_embeddings(ldus)
    print("Inserting into ChromaDB...")
    insert_ldus_into_chromadb(ldus)
    print("Ingestion complete.")

if __name__ == "__main__":
    main()

