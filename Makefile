# Makefile for Document Intelligence Pipeline


.PHONY: install run test clean

install:
	pip install .

run:
	PYTHONPATH=. python3 src/main.py

test:
	PYTHONPATH=. pytest -v --maxfail=1 --disable-warnings


clean:
	rm -rf .refinery/profiles/*.json

# Run rubric directory listing
rubric:
	ls rubric/

# Inspect ChromaDB collection
inspect-chroma:
	PYTHONPATH=. python3 scripts/inspect_chroma.py

# Clear ChromaDB collection
clear-chromadb:
	PYTHONPATH=. python3 scripts/clear_chromadb_collection.py
