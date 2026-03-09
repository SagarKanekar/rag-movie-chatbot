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
git clone https://github.com/Varun-666/rag-movie-chatbot.git
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

## 🚢 Deployment

### Railway
1. Push to GitHub
2. Connect to Railway
3. Add `GROQ_API_KEY` environment variable
4. Auto-deploy

### Render
1. Create `render.yaml` with deployment config
2. Connect GitHub repo
3. Add secrets
4. Deploy

### HuggingFace Spaces
1. Create new Streamlit space
2. Connect repo
3. Add `GROQ_API_KEY` as secret
4. Deploy

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