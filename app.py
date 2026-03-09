import streamlit as st
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import our modules
from src.data_loader import LetterBoxdLoader
from src.vector_store import MovieVectorStore
from src.rag_engine import MovieRAGEngine
from src.agent import MovieChatbotAgent
from src.utils import create_llm_provider

# Configure Streamlit
st.set_page_config(
    page_title="🎬 Movie RAG Chatbot",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .movie-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.agent = None
    st.session_state.chat_history = []
    st.session_state.vector_store = None
    st.session_state.loader_stats = None

# Main header
st.title("🎬 Movie Recommendation RAG Chatbot")
st.markdown("Analyze your Letterboxd data and get intelligent movie recommendations!")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Provider selection
    st.subheader("LLM Provider")
    provider_options = {
        "Groq (Recommended - Free & Fast)": "groq",
        "HuggingFace (Free)": "huggingface",
        "Ollama (Local - Needs setup)": "ollama"
    }
    selected_provider = st.selectbox(
        "Choose your LLM provider:",
        options=list(provider_options.keys()),
        help="Groq and HuggingFace are cloud-based (free tier). Ollama runs locally."
    )
    provider_name = provider_options[selected_provider]
    
    # Show provider info
    with st.expander("ℹ️ Provider Info"):
        if provider_name == "groq":
            st.info(
                "**Groq**: Free, fast, no setup needed.\n"
                "Get API key: https://console.groq.com"
            )
        elif provider_name == "huggingface":
            st.info(
                "**HuggingFace**: Free tier available.\n"
                "Get token: https://huggingface.co/settings/tokens"
            )
        else:
            st.info(
                "**Ollama**: Runs entirely locally, no internet needed.\n"
                "Download: https://ollama.ai\n"
                "Setup: `ollama pull mistral`"
            )
    
    st.divider()
    
    # File upload
    st.subheader("📤 Data Upload")
    uploaded_file = st.file_uploader(
        "Upload Letterboxd CSV Export",
        type="csv",
        help="Export from: letterboxd.com/settings/data/"
    )
    
    if uploaded_file:
        st.success(f"✅ File selected: {uploaded_file.name}")
    
    st.divider()
    
    # Initialize button
    col1, col2 = st.columns([2, 1])
    
    with col1:
        init_button = st.button("🚀 Initialize Chatbot", use_container_width=True)
    
    with col2:
        reset_button = st.button("🔄 Reset", use_container_width=True)
    
    if reset_button:
        st.session_state.initialized = False
        st.session_state.agent = None
        st.session_state.chat_history = []
        st.session_state.vector_store = None
        st.rerun()
    
    if init_button:
        if uploaded_file is None:
            st.error("❌ Please upload a Letterboxd CSV file first!")
        else:
            with st.spinner("🔄 Initializing chatbot..."):
                try:
                    # Step 1: Save and load data
                    st.write("Step 1/4: Loading data...")
                    temp_file_path = "temp_letterboxd.csv"
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    loader = LetterBoxdLoader(temp_file_path)
                    df = loader.load()
                    loader_stats = loader.get_stats()
                    
                    st.session_state.loader_stats = loader_stats
                    st.write(f"✅ Loaded {loader_stats['total_movies']} movies")
                    
                    # Step 2: Create vector store
                    st.write("Step 2/4: Creating embeddings...")
                    vector_store = MovieVectorStore()
                    vector_store.create_collection(reset=True)
                    vector_store.add_movies(loader.get_movies())
                    
                    st.session_state.vector_store = vector_store
                    st.write("✅ Vector store created")
                    
                    # Step 3: Initialize LLM
                    st.write(f"Step 3/4: Connecting to {selected_provider}...")
                    llm = create_llm_provider(provider_name)
                    st.write("✅ LLM connected")
                    
                    # Step 4: Create RAG engine and agent
                    st.write("Step 4/4: Setting up RAG engine...")
                    rag_engine = MovieRAGEngine(vector_store, llm)
                    agent = MovieChatbotAgent(rag_engine, llm, loader_stats)
                    
                    st.session_state.agent = agent
                    st.session_state.initialized = True
                    st.session_state.chat_history = []
                    
                    st.success("🎉 Chatbot is ready to use!")
                    st.balloons()
                    
                    # Clean up temp file
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    
                except Exception as e:
                    logger.error(f"Initialization error: {e}")
                    st.error(f"❌ Error: {str(e)}")

# Main chat interface
if st.session_state.initialized:
    col_chat, col_info = st.columns([2, 1], gap="large")
    
    with col_chat:
        st.subheader("💬 Chat")
        
        # Display chat history
        chat_container = st.container(height=400)
        
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    with st.chat_message("user", avatar="👤"):
                        st.write(msg["content"])
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(msg["content"])
        
        # Chat input
        st.divider()
        user_input = st.chat_input("Ask about movies or get recommendations...")
        
        if user_input:
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            # Display user message
            with st.chat_message("user", avatar="👤"):
                st.write(user_input)
            
            # Get response from agent
            with st.spinner("🤔 Thinking..."):
                try:
                    result = st.session_state.agent.execute(user_input)
                    response_text = result['response']
                except Exception as e:
                    logger.error(f"Error getting response: {e}")
                    response_text = f"Sorry, I encountered an error: {str(e)}"
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response_text
            })
            
            # Display assistant response
            with st.chat_message("assistant", avatar="🤖"):
                st.write(response_text)
                
                # Show found movies if any
                if result.get('movies'):
                    st.markdown("---")
                    st.markdown("### 🎥 Related Movies")
                    
                    for movie in result['movies'][:5]:
                        with st.expander(
                            f"**{movie.get('Name', 'Unknown')}** ({movie.get('Year', 'N/A')}) - "
                            f"Match: {movie.get('similarity_score', 0):.0%}"
                        ):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Rating:** {movie.get('Rating', 'Not rated')}")
                            with col2:
                                st.write(f"**Year:** {movie.get('Year', 'Unknown')}")
                            
                            if movie.get('Review'):
                                st.write(f"**Review:** {movie.get('Review')[:300]}")
    
    with col_info:
        st.subheader("📊 Collection Stats")
        
        if st.session_state.loader_stats:
            stats = st.session_state.loader_stats
            st.metric("Total Movies", stats.get('total_movies', 0))
            st.metric("Rated Movies", stats.get('rated_movies', 0))
            st.info(f"**Years:** {stats.get('years_range', 'N/A')}")
        
        st.divider()
        
        st.subheader("💡 Tips")
        st.markdown("""
        - **Search:** "Find sci-fi movies"
        - **Recommend:** "Suggest a comedy"
        - **Analyze:** "Tell me about my taste"
        - **Question:** "Best rated movies?"
        """)
        
        st.divider()
        
        if st.session_state.vector_store:
            try:
                vs_stats = st.session_state.vector_store.get_collection_stats()
                st.subheader("🔍 Vector Store")
                st.caption(f"Movies indexed: {vs_stats.get('total_movies', 0)}")
            except:
                pass

else:
    # Welcome screen
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        ## 🎬 Welcome!
        
        This is a **RAG Agentic ChatBot** that analyzes your Letterboxd movie data
        and provides intelligent recommendations and answers.
        
        ### How it works:
        
        1. **Export** your data from Letterboxd
        2. **Upload** the CSV file
        3. **Select** an LLM provider
        4. **Start chatting** with your movie database!
        
        ### Features:
        - 🔍 Semantic search over your movies
        - 🤖 Intelligent recommendations
        - 💬 Conversational Q&A
        - 📊 Collection analysis
        """)
    
    with col2:
        st.markdown("""
        ### 🚀 Quick Start
        
        **Step 1:** Get your Letterboxd data
        - Visit: https://letterboxd.com/settings/data/
        - Click "Export as CSV"
        
        **Step 2:** Get an API key (if needed)
        - **Groq:** https://console.groq.com
        - **HuggingFace:** https://huggingface.co/settings/tokens
        - **Ollama:** https://ollama.ai (local)
        
        **Step 3:** Configure and upload
        - Select provider in sidebar ⬅️
        - Upload your CSV file
        - Click "Initialize Chatbot" 🚀
        
        ### ❓ Example Questions
        - "Recommend me a good sci-fi movie"
        - "What are my highest rated movies?"
        - "Find movies like Inception"
        - "Analyze my movie taste"
        - "Best comedies I watched?"
        """)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
Made with ❤️ using RAG, LangChain, and Streamlit | Free and Open Source
</div>
""", unsafe_allow_html=True)