# Makefile for Document Intelligence Pipeline

.PHONY: run test clean

run:
	PYTHONPATH=. python3 src/main.py

test:
	PYTHONPATH=. pytest -v --maxfail=1 --disable-warnings

clean:
	rm -rf .refinery/profiles/*.json
