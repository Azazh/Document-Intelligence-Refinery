"""
Query Agent for the Document Intelligence Refinery
Implements Phase 4: Query Agent & Provenance Layer

- pageindex_navigate: Traverse PageIndex tree to locate relevant sections
- semantic_search: Retrieve LDUs from ChromaDB vector store
- structured_query: Query FactTable (SQLite) for precise answers
- Every answer includes ProvenanceChain (document_name, page_number, bbox, content_hash)
- Audit Mode: claim verification with source citation or 'unverifiable' flag
"""
import chromadb
import sqlite3
import json
from typing import List, Dict, Any

# Placeholder: Load PageIndex tree from .refinery/pageindex_{doc_id}.json
# Placeholder: Load LDUs from ChromaDB
# Placeholder: Query FactTable (SQLite)

class ProvenanceChainEntry:
    def __init__(self, document_name, page_number, bbox, content_hash):
        self.document_name = document_name
        self.page_number = page_number
        self.bbox = bbox
        self.content_hash = content_hash

    def as_dict(self):
        return {
            "document_name": self.document_name,
            "page_number": self.page_number,
            "bbox": self.bbox,
            "content_hash": self.content_hash
        }

class QueryAgent:
    def __init__(self, chroma_collection="ldu_collection", facttable_path="facttable.db"):
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(chroma_collection)
        self.facttable_path = facttable_path

    def pageindex_navigate(self, doc_id: str, topic: str) -> List[Dict[str, Any]]:
        """
        Traverse the PageIndex tree for the given document and return sections relevant to the topic.
        Uses simple keyword matching in section titles and summaries.
        """
        import os
        pageindex_path = f".refinery/pageindex_{doc_id}.json"
        if not os.path.exists(pageindex_path):
            print(f"PageIndex file not found: {pageindex_path}")
            return []
        with open(pageindex_path, "r", encoding="utf-8") as f:
            pageindex = json.load(f)

        matches = []

        def search_section(section):
            # Check if topic keyword is in title or summary (case-insensitive)
            title = section.get("title", "").lower()
            summary = section.get("summary", "").lower()
            if topic.lower() in title or topic.lower() in summary:
                matches.append(section)
            # Recursively search child sections
            for child in section.get("child_sections", []):
                search_section(child)

        # Start from root (assume pageindex is a dict with 'root' key or is the root section itself)
        root = pageindex.get("root", pageindex)
        search_section(root)
        return matches

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant LDUs from ChromaDB using embedding similarity.
        Returns top_k LDUs with provenance info.
        """
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        query_embedding = model.encode(query)
        # ChromaDB expects a list of queries
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        # Each result contains ids, documents, metadatas
        hits = []
        for i in range(len(results["ids"][0])):
            hit = {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            }
            # Add provenance info if available
            meta = hit["metadata"]
            hit["provenance"] = {
                "document_name": meta.get("document_name"),
                "page_number": meta.get("page_refs"),
                "bbox": meta.get("bounding_box"),
                "content_hash": meta.get("content_hash")
            }
            hits.append(hit)
        return hits

    def structured_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Query FactTable (SQLite) for answers.
        Returns a list of result rows as dicts.
        """
        conn = sqlite3.connect(self.facttable_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            results = [dict(row) for row in rows]
        except Exception as e:
            print(f"SQL query error: {e}")
            results = []
        finally:
            conn.close()
        return results

    def answer_with_provenance(self, query: str) -> Dict[str, Any]:
        """
        Return the top semantic search result as the answer, with its ProvenanceChain.
        """
        hits = self.semantic_search(query, top_k=1)
        if not hits:
            return {"answer": None, "provenance_chain": []}
        hit = hits[0]
        provenance = hit.get("provenance", {})
        return {
            "answer": hit["content"],
            "provenance_chain": [provenance]
        }

    def audit_mode(self, claim: str) -> Dict[str, Any]:
        """
        Verify claim with source citation or flag as unverifiable.
        Uses semantic search to find supporting evidence.
        """
        hits = self.semantic_search(claim, top_k=1)
        if not hits:
            return {"claim": claim, "verdict": "not found / unverifiable", "provenance_chain": []}
        hit = hits[0]
        provenance = hit.get("provenance", {})
        # Simple check: if the top hit's content contains the claim (case-insensitive)
        if claim.lower() in hit["content"].lower():
            verdict = "verified"
        else:
            verdict = "not found / unverifiable"
        return {
            "claim": claim,
            "verdict": verdict,
            "provenance_chain": [provenance]
        }
