# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A **starter scaffold for a student RAG (Retrieval-Augmented Generation) assignment** — "The Unofficial Guide, Project 1" for an AI course (AI201). The pipeline code does **not exist yet**; the student writes it. This repo currently contains only planning/submission docs, dependencies, and an empty `documents/` folder.

The deliverable is a RAG system over a domain of the student's choosing (e.g. unofficial student knowledge — professor reviews, forum posts) that answers questions **grounded strictly in retrieved documents**, with source attribution.

## Repository layout

- `planning.md` — Written *before* coding. The spec: domain, sources, chunking strategy, embedding model, top-k, 5 evaluation questions, architecture diagram, and per-milestone AI-tool plan. **Read this first** — it defines the intended design and is the source of truth for chunk sizes, embedding model choice, and test questions.
- `README.md` — The *submission report* template, filled in *after* each part is built (evaluation results, failure-case analysis, reflections). Not a how-to-run doc.
- `documents/` — Corpus goes here (`.gitkeep` only for now). May hold `.txt`, `.md`, or `.pdf`.
- `requirements.txt` — Pinned deps.
- `.env` / `.env.example` — Holds `GROQ_API_KEY`. `.env` is gitignored; never commit it.

## Intended pipeline (five stages)

Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation

The chosen stack (from `requirements.txt`):
- **Embedding + chunking**: `sentence-transformers` (local embedding model, e.g. all-MiniLM-L6-v2).
- **Vector store**: `chromadb` — persists locally to `chroma_db/` (gitignored).
- **Generation**: `groq` SDK — LLM inference via Groq, keyed by `GROQ_API_KEY`. Free tier, no card required (console.groq.com).
- **Query interface (Milestone 5)**: `gradio` or `streamlit` — commented out in `requirements.txt`; uncomment and `pip install` whichever is used.
- **PDF ingestion**: `pdfplumber` — also commented out; enable only if `documents/` contains PDFs.

**Grounding is the core requirement**: the system prompt must constrain the LLM to answer only from retrieved chunks (refuse/say-unknown otherwise), and responses must surface which source each answer came from. This is graded — don't generate a pipeline that lets the model answer from general knowledge.

## Environment & commands

Python **3.11**, with a `.venv/` already created and deps installed (chromadb 1.5.9, groq 0.15.0, sentence-transformers 3.4.1).

```bash
source .venv/bin/activate          # activate the venv first, every session
pip install -r requirements.txt    # if deps drift / after uncommenting optional ones

cp .env.example .env               # then paste a real GROQ_API_KEY
```

No build, test, or lint config exists yet. If you add a pipeline, prefer a small runnable entrypoint (e.g. `python ingest.py` to build the Chroma index, `python query.py` or a `gradio`/`streamlit` app to query).

## When implementing

- Align implementation to `planning.md` — match the chunk size, overlap, embedding model, and top-k the student specified there. If you diverge, note it (the README has a "Spec Reflection" / divergence section).
- Embedding runs locally (no API); only generation calls Groq.
- Keep the Chroma persist directory under `chroma_db/` so it stays gitignored.
