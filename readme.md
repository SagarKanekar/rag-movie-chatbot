# 🎬 RAG Agentic Movie Recommendation ChatBot

A free, open-source movie recommendation chatbot that analyzes your Letterboxd data using RAG (Retrieval-Augmented Generation) and intelligent agent routing.

## ✨ Features

- 🔍 **Semantic Search** - Find movies similar to your preferences
- 🤖 **Intelligent Recommendations** - Get personalized suggestions
- 💬 **Conversational Q&A** - Ask questions about your movies
- 📊 **Collection Analysis** - Understand your movie taste
- 🆓 **100% Free** - Uses only free APIs and tools
- 🔐 **Private** - Your data stays with you

## 🛠️ Tech Stack

- **LLM**: Groq API (free & fast)
- **Vector DB**: ChromaDB + Sentence Transformers
- **RAG Framework**: LangChain
- **UI**: Streamlit
- **Data Processing**: Pandas

## 📋 Prerequisites

- Python 3.9+
- pip
- Letterboxd account (to export data)
- API key from [Groq](https://console.groq.com) (free)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/SagarKanekar/rag-movie-chatbot.git
cd rag-movie-chatbot
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Create .env file
echo "GROQ_API_KEY=your_api_key_here" > .env
```

Get your free API key from https://console.groq.com

### 5. Export Letterboxd Data
1. Go to https://letterboxd.com/settings/data/
2. Click "Export as CSV"
3. Download the file

### 6. Run Application
```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

### 7. Run Backend API Locally (optional)
```bash
gunicorn --chdir api chat:app --bind 127.0.0.1:8000
```

Then test:
```bash
curl http://127.0.0.1:8000/health
```

## 📚 Usage

1. Upload your Letterboxd CSV file
2. Select your LLM provider (Groq recommended)
3. Initialize the chatbot
4. Start asking questions!

### Example Queries
- "Recommend me a good sci-fi movie"
- "What are my highest rated movies?"
- "Find movies similar to Inception"
- "Analyze my movie taste"
- "Best comedies I've watched"

## 🏗️ Project Structure

```
rag-movie-chatbot/
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # Load Letterboxd data
│   ├── vector_store.py     # ChromaDB management
│   ├── rag_engine.py       # RAG pipeline
│   ├── agent.py            # Agent routing logic
│   └── utils.py            # LLM provider setup
├── data/                   # Your CSV exports
├── chroma_db/             # Vector store (auto-created)
├── app.py                 # Streamlit application
├── requirements.txt       # Dependencies
├── .env                   # API keys (don't commit!)
└── README.md
```

## 🔐 Security

- `.env` file is gitignored (never commit API keys)
- Data is processed locally
- Vector embeddings are stored locally
- No data is sent to third parties (except LLM provider)

## 🚢 Deployment (Production)

Recommended setup:
- **Backend API** on **Render** (long-running Python service)
- **Frontend** on **Vercel** (if you add a web frontend in this repo or a separate repo)

### 1) Backend on Render (Flask + Gunicorn)

This repository exposes a Flask API from `api/chat.py`.

- Health endpoint: `GET /health`
- Chat endpoints: `POST /chat` and `POST /api/chat` (both supported)

Render settings:
1. Create a **Web Service** from this repo (`main` branch).
2. Runtime: **Python**
3. Build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command (or rely on the included `Procfile`):
   ```bash
   gunicorn --chdir api chat:app --bind 0.0.0.0:$PORT
   ```
5. Set required environment variables:
   - `GROQ_API_KEY` (required for default `provider: "groq"`)
   - `HUGGINGFACE_API_KEY` (optional, only for `provider: "huggingface"`)
   - `VECTOR_STORE_DIR` (optional, defaults to `/tmp/chroma_db`)

Quick verification after deploy:
```bash
curl https://<your-render-service>.onrender.com/health
```

Expected response:
```json
{"status":"ok","endpoint":"/api/chat"}
```

Sample chat request:
```bash
curl -X POST https://<your-render-service>.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message":"Recommend me a sci-fi movie",
    "provider":"groq",
    "loader_stats":{"total_movies":1,"rated_movies":1,"years_range":"2010 - 2010"},
    "movies":[{"Name":"Inception","Year":"2010","Rating":"4.5","Review":"Mind-bending sci-fi."}]
  }'
```

### 2) Frontend on Vercel

This repository includes a static web frontend (`index.html`) designed for Vercel.

- `/` serves the chat UI
- UI requests are sent to `POST /chat`
- `/chat` is handled by `api/index.py`
- Frontend includes:
  - local chat history persistence via `localStorage`
  - progressive assistant rendering (typing-style fallback when backend is non-streaming)
  - assistant message actions (copy + regenerate) and retry on failed requests
  - optional prompt filter chips (genre, mood, decade, runtime, language)

### 3) Stateless hosting notes

- Runtime-critical chat data is sent in each request (`movies` payload), so the API does **not** require durable local disk.
- `VECTOR_STORE_DIR` defaults to `/tmp/chroma_db`; this is ephemeral and used as a cache/optimization only.
- Keep provider API keys in Render/Vercel environment variables. Do not commit secrets.

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Improve documentation
- Optimize code

## 📝 License

MIT License - Feel free to use and modify!

## 🆘 Troubleshooting

**Issue**: `GROQ_API_KEY not found`
- Solution: Check `.env` file exists and has correct key

**Issue**: Slow embeddings on first run
- Solution: This is normal. First run generates embeddings. Subsequent runs are fast.

**Issue**: App crashes on CSV upload
- Solution: Ensure CSV format matches Letterboxd export

## 📞 Support

- Open an issue on GitHub
- Check existing issues for solutions
- Review logs in the `logs/` folder

## 🎯 Roadmap

- [ ] Support for other movie databases
- [ ] Advanced filtering options
- [ ] Export recommendations as CSV
- [ ] Multi-user support
- [ ] Advanced analytics dashboard
- [ ] Custom genre classification

---

**Made with ❤️ using RAG, LangChain, and Streamlit**
