"""
Script: clear_chromadb_collection.py
Purpose: Delete all LDUs from the specified ChromaDB collection (persistent store).
Usage:
    python scripts/clear_chromadb_collection.py
"""
import chromadb

COLLECTION_NAME = "ldu_collection"
PERSIST_PATH = "chroma_store"

client = chromadb.PersistentClient(path=PERSIST_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

all_ids = collection.get()["ids"]
if all_ids:
    collection.delete(ids=all_ids)
    print(f"Deleted {len(all_ids)} LDUs from collection '{COLLECTION_NAME}' at '{PERSIST_PATH}'.")
else:
    print("No LDUs to delete.")
