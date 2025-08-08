# NewsRoom AI

Intelligent news aggregation platform with AI-powered chat assistant for instant news insights and analysis.

![Demo GIF](assets/news_room_demo.gif)

## ✨ Features

### 📱 Smart News Feed

- **Real-time News Aggregation** - Automatically fetches latest articles from multiple sources
- **AI-Generated Summaries** - Get key insights without reading full articles
- **Intelligent Topic Classification**- Auto-categorized by AI (Technology, Business, Health, etc.)
- **Advanced Filtering** - Filter by topic, source, date range, and search keywords
- **Infinite Scroll** - Seamless pagination with pull-to-refresh

### 🤖 AI Chat Assistant (RAG)

- **Context-Aware Conversations** - Ask questions about any news article
- **RAG (Retrieval Augmented Generation)** - AI searches your news database for accurate answers
- **Multi-Article Analysis** - Compare and analyze multiple articles
- **Natural Language Queries** - Ask in plain English: "What happened with tech stocks today?"

### 🎨 Modern UI/UX

- **Material Design 3** - Beautiful, responsive interface
- **Cross-Platform** - Works on iOS, Android, and Web

## Quick Start

### Preequisites:

- Flutter SDK (3.0+)
- Python (3.8+)
- PostGreSQL or SQLite
- Groq API Key
- Tavily API KEY

### Local Setup with Virtual Environment

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
   DATABASE_URL=sqlite:///./news.db or PostGreSQL url
   ```

5. **Run a chunking job (example)**

   ```bash
   python scripts/chunking/run_chunking.py --sample_type tiny --splitter semantic
   ```

   **Note:** Do not forget to commit your .env.example and add venv/ to .gitignore.

## Run the backend API

From the root folder, type the following command to start the backend.

```bash
uvicorn app.main:app --reload
```

This will start backend on http://localhost:3000.

## Run Flutter Frontend

This guide explains how to run the Flutter frontend locally, including web support via `localhost:3000`.

1. To verify that flutter is set up correctly:

```bash
flutter doctor
```

2. Cd to frontend folder

```bash
cd frontend  # Adjust this path if needed
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

## Coming Next:

- Folder Structure
- API docs
- Tests
- Docker Deployment
