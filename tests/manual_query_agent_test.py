"""
Manual test script for QueryAgent (Phase 4)
Usage:
    python tests/manual_query_agent_test.py
"""
from src.agents.query_agent import QueryAgent

# Instantiate the agent
agent = QueryAgent()

# ---- Test PageIndex Navigation ----
doc_id = "d0c35365-b660-4063-90be-77220ca09e2f"  # Use just the UUID part for doc_id
print("\n--- PageIndex Navigation ---")
sections = agent.pageindex_navigate(doc_id, "ATM")
for s in sections:
    print(s)

# ---- Test Semantic Search ----
print("\n--- Semantic Search ---")
results = agent.semantic_search("Key figures in millions of Birr?", top_k=3)
for r in results:
    print(r)

# ---- Test Structured Query ----
print("\n--- Structured Query ---")
sql = "SELECT * FROM fact_table WHERE key='Subsidiaries' AND year=2018"  # Adjust table/fields as needed
rows = agent.structured_query(sql)
for row in rows:
    print(row)

# ---- Test Answer with Provenance ----
print("\n--- Answer with Provenance ---")
answer = agent.answer_with_provenance("What is the net income for Q3?")
print(answer)

# ---- Test Audit Mode ----
print("\n--- Audit Mode ---")
claim = "The report states revenue was $4.2B in Q3"
audit = agent.audit_mode(claim)
print(audit)
