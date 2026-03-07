import chromadb
import json
import os

def inspect_chroma_db(collection_name="ldu_collection"):
    """
    Inspect all ingested LDUs in ChromaDB collection (ephemeral or default location)
    """
    persist_path = "chroma_store"  # Must match the path used in ingestion
    client = chromadb.PersistentClient(path=persist_path)
    
    # List all collections
    print("=== Available Collections ===")
    collections = client.list_collections()
    if not collections:
        print("No collections found. If you used persistent storage, set the correct path or re-ingest your LDUs.")
    for col in collections:
        print(f"  - {col.name}")
    
    # Get specific collection
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"\nCollection '{collection_name}' not found!")
        print(f"Error: {e}")
        return
    
    # Count documents
    count = collection.count()
    print(f"\n=== Collection: {collection_name} ===")
    print(f"Total LDUs ingested: {count}")
    
    if count == 0:
        print("No data found in collection!")
        return
    
    # Peek at first 5 LDUs (quick view)
    print("\n=== Sample LDUs (first 5) ===")
    peek_data = collection.peek(limit=5)
    for i, doc_id in enumerate(peek_data['ids']):
        print(f"\n--- LDU {i+1} ---")
        print(f"ID: {doc_id}")
        print(f"Content: {peek_data['documents'][i][:200]}...")  # First 200 chars
        print(f"Metadata: {peek_data['metadatas'][i] if peek_data['metadatas'] else 'None'}")
    
    # Get ALL documents (use carefully for large datasets)
    print(f"\n=== Retrieving All {count} LDUs ===")
    all_data = collection.get(
        include=["metadatas", "documents", "embeddings"]
    )
    
    # Display summary
    print(f"\nRetrieved {len(all_data['ids'])} documents")
    print(f"Keys available: {list(all_data.keys())}")
    
    # Show full details for first 2 LDUs
    print("\n=== Full Details (First 2 LDUs) ===")
    for i in range(min(2, len(all_data['ids']))):
        print(f"\n{'='*50}")
        print(f"LDU ID: {all_data['ids'][i]}")
        print(f"Content:\n{all_data['documents'][i][:500]}...")
        print(f"Metadata: {json.dumps(all_data['metadatas'][i], indent=2) if all_data['metadatas'] else 'None'}")
        
        # FIXED: Check if embeddings key exists and is not None (not empty list)
        embeddings_list = all_data.get('embeddings')
        if embeddings_list is not None and i < len(embeddings_list) and embeddings_list[i] is not None:
            embedding = embeddings_list[i]
            # Handle both list and numpy array
            if hasattr(embedding, '__len__'):
                print(f"Embedding dim: {len(embedding)}")
            else:
                print(f"Embedding dim: 1 (scalar)")
        else:
            print("Embedding dim: N/A")
    
    return all_data

def query_ldus(query_text, collection_name="ldu_collection", n_results=3):
    """
    Query LDUs to see relevant results
    """
    persist_path = "chroma_store"
    client = chromadb.PersistentClient(path=persist_path)
    
    try:
        collection = client.get_collection(name=collection_name)
    except Exception as e:
        print(f"Collection '{collection_name}' not found!")
        print(f"Error: {e}")
        return
    
    print(f"\n=== Querying: '{query_text}' ===")
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        include=["metadatas", "documents", "distances"]
    )
    
    # Check if results found
    if not results['ids'][0]:
        print("No results found.")
        return
    
    for i, (doc_id, doc, meta, dist) in enumerate(zip(
        results['ids'][0], 
        results['documents'][0], 
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\n--- Result {i+1} (Distance: {dist:.4f}) ---")
        print(f"ID: {doc_id}")
        print(f"Content: {doc[:300]}...")
        print(f"Metadata: {json.dumps(meta, indent=2) if meta else 'None'}")

if __name__ == "__main__":
    COLLECTION_NAME = "ldu_collection"
    # Inspect all data
    inspect_chroma_db(COLLECTION_NAME)
    # Test query
    query_ldus("macroeconomic highlights", COLLECTION_NAME)