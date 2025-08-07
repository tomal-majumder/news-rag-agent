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

# 🚀 Flutter Frontend – Local Development Setup

This guide explains how to run the Flutter frontend locally, including web support via `localhost:3000`.

---

## 📦 Prerequisites

Make sure the following tools are installed on your system:

- ✅ [Flutter SDK](https://flutter.dev/docs/get-started/install)  
   **macOS** users can install via Homebrew:
  ```bash
  brew install flutter
  ✅ Dart SDK (comes bundled with Flutter)
  ```

✅ Android Studio or VS Code

✅ Mobile emulator or real device (Android/iOS)

To verify that everything is set up correctly:

```bash
flutter doctor
```

## 🛠️ Installation Steps

1. Clone the repository

```bash
cd your-project/flutter-frontend  # Adjust this path if needed
```

2. Get Flutter packages

```bash
flutter pub get
```

3. (Optional) Enable Web Support: To run the app in a web browser:

```bash
flutter config --enable-web
```

4. Run the App

On Android/iOS emulator or physical device:

```bash
flutter run
```

On Web (Chrome, localhost:3000):

```bash
flutter run -d chrome --web-port=3000
```

Then visit http://localhost:3000 in your browser.

## ⚙️ Common Issues

1. Permission denied:
   If you see permission errors, run:

```bash
chmod +x flutter/bin/*
```

2. No devices found:
   Ensure an emulator is running or a device is connected via USB.

3. Missing dependencies

```bash
flutter pub get
```

### 🧪 Hot Reload & Restart

While the app is running:

- Press r for hot reload
- Press R for hot restart
