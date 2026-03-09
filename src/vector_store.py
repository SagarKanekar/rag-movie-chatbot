import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)

class MovieVectorStore:
    """Manage vector embeddings for movie data using ChromaDB"""
    
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        
        # Create directory if it doesn't exist
        os.makedirs(persist_dir, exist_ok=True)
        
        # Initialize embedding model (free, lightweight)
        logger.info("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize Chroma client
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        )
        self.client = chromadb.Client(settings)
        self.collection = None
        logger.info("Vector store initialized")
    
    def create_collection(self, name: str = "movies", reset: bool = False):
        """Create or get existing collection"""
        try:
            if reset:
                self.client.delete_collection(name=name)
                logger.info(f"Reset collection: {name}")
            
            self.collection = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{name}' created/retrieved")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def add_movies(self, movies: List[Dict]):
        """Add movies with their embeddings to the vector store"""
        if self.collection is None:
            raise ValueError("Collection not created. Call create_collection() first.")
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for idx, movie in enumerate(movies):
                # Create document text from movie data
                doc_text = movie.get('combined_text', str(movie))
                documents.append(doc_text)
                
                # Store metadata
                metadata = {k: str(v)[:500] for k, v in movie.items()}  # Limit to 500 chars
                metadatas.append(metadata)
                
                ids.append(f"movie_{idx}")
            
            logger.info(f"Generating embeddings for {len(documents)} movies...")
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                documents,
                show_progress_bar=True,
                batch_size=32
            ).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(documents)} movies to vector store")
            
        except Exception as e:
            logger.error(f"Error adding movies: {e}")
            raise
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar movies based on query"""
        if self.collection is None:
            raise ValueError("Collection not created. Call create_collection() first.")
        
        try:
            logger.info(f"Searching for: {query}")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].tolist()
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 10),
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            movies = []
            if results['metadatas'] and len(results['metadatas']) > 0:
                for i in range(len(results['ids'][0])):
                    movie = results['metadatas'][0][i].copy()
                    movie['similarity_score'] = float(1 - results['distances'][0][i])
                    movie['document'] = results['documents'][0][i]
                    movies.append(movie)
            
            logger.info(f"Found {len(movies)} matching movies")
            return movies
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        if self.collection is None:
            return {"error": "Collection not initialized"}
        
        try:
            count = self.collection.count()
            return {
                "total_movies": count,
                "collection_name": self.collection.name,
                "embedding_dimension": 384  # all-MiniLM-L6-v2 uses 384 dimensions
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def persist(self):
        """Explicitly persist the vector store"""
        try:
            self.client.persist()
            logger.info("Vector store persisted")
        except Exception as e:
            logger.error(f"Error persisting: {e}")