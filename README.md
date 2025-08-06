# News Q/A Agent using RAG + ChromaDB + Multi-Agent Prompting

This project builds an intelligent Q/A agent that answers questions from a 2018–2020 news dataset using Retrieval-Augmented Generation (RAG).

## Features

- 📚 Recursive + Semantic Chunking
- 🧠 Vector Storage with ChromaDB
- 🤖 Multi-agent retrieval with fallback prompts
- 🔌 FastAPI backend (in progress)
- 📱 Flutter frontend (in progress)

## Folder Structure

- `scripts/` – Data chunking, storage, and retrieval logic
- `backend/` – FastAPI service for Q/A
- `frontend/` – Flutter mobile frontend
- `data/` – Raw, processed, and sample datasets

## Setup

```bash
pip install -r requirements.txt
python scripts/chunking/recursive_chunker.py --config configs/chunking_config.yaml
```
