"""
Test script for chroma_ingest.py ingestion pipeline.
Verifies that LDUs are correctly inserted into ChromaDB.
"""
import chromadb

def test_chroma_ingest(collection_name="ldu_collection"):
    client = chromadb.Client()
    collection = client.get_or_create_collection(collection_name)
    count = collection.count()
    print(f"ChromaDB collection '{collection_name}' contains {count} records.")
    assert count > 0, "No records found in ChromaDB collection!"

if __name__ == "__main__":
    test_chroma_ingest()
