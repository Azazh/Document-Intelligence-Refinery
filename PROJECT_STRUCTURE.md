# src/
#   Core library code for the document intelligence pipeline (modular, reusable, no CLI logic)
# scripts/
#   Standalone scripts and entry points (e.g., pdf_type_classifier.py, data loaders, demo runners)
# data/
#   Raw input data (PDFs, source files, not tracked in VCS if large)
# sample/
#   Small sample files for demonstration/testing (e.g., 1 per PDF type)
# tests/
#   Unit and integration tests for src/ and scripts/
# .refinery/
#   Internal configs, pipeline state, or cache (not for code)
# rubric/
#   Challenge rubric, grading, or requirements docs
# .github/
#   Copilot instructions, workflows, and project automation
# README.md
#   Project overview and usage
# pyproject.toml, uv.lock
#   Dependency and environment management (uv-based)
# requirements.txt
#   (Optional) For compatibility, but pyproject.toml is canonical
# main.py
#   (Optional) Entrypoint for running the pipeline as a script
# TRP1 Challenge Week 3_ The Document Intelligence Refinery.md
#   Challenge instructions and context
