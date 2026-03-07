"""
Manual test script for QueryAgent (Phase 4)
Usage:
    python tests/manual_query_agent_test.py
"""
from src.agents.query_agent import QueryAgent

# Instantiate the agent
agent = QueryAgent()

# ---- Test PageIndex Navigation ----
doc_id = "631bf3c1-aa0b-4ba6-b435-9db40e0a85a0"  # Use just the UUID part for doc_id
print("\n--- PageIndex Navigation ---")
sections = agent.pageindex_navigate(doc_id, "EXIM")
for s in sections:
    print(s)

# ---- Test Semantic Search ----
print("\n--- Semantic Search ---")
results = agent.semantic_search("total assets for 2024", top_k=3)
for r in results:
    print(r)

# ---- Test Structured Query ----
print("\n--- Structured Query ---")
sql = "SELECT * FROM fact_table WHERE key='revenue' AND year=2024"  # Adjust table/fields as needed
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
