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

## Local Setup with Virtual Environment

1. **Clone the repo**
   ```bash
   git clone https://github.com/tomal-majumder/news-rag-agent.git
   cd news-rag-agent
   ```
2. **Create and activate a virtual environment**

   macOS/Linux:

   ```bash
   python3 -m venv news-rag-venv
   source news-rag-venv/bin/activate
   ```

   Windows:

   ```cmd
   python -m venv news-rag-venv
   news-rag-venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up environment variables**

   Create a .env file in the root directory and add:

   ```bash
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   ```

5. **Run a chunking job (example)**

   ```bash
   python scripts/chunking/run_chunking.py --sample_type tiny --splitter semantic
   ```

6. **Run the backend API**
   ```bash
   uvicorn app.main:app --reload
   ```
7. **Deactivate when finished**
   ```bash
   deactivate
   ```

**Note:** Do not forget to commit your .env.example and add venv/ to .gitignore.
