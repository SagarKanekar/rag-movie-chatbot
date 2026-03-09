from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MovieRAGEngine:
    """RAG engine for movie recommendations and Q&A"""
    
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.conversation_history = []
    
    def search_movies(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for movies matching the query"""
        logger.info(f"RAG Search: {query}")
        movies = self.vector_store.search(query, n_results=n_results)
        return movies
    
    def format_movie_context(self, movies: List[Dict], detailed: bool = False) -> str:
        """Format search results as context for LLM"""
        if not movies:
            return "No movies found."
        
        context = "## Found Movies:\n\n"
        for i, movie in enumerate(movies, 1):
            name = movie.get('Name', 'Unknown')
            year = movie.get('Year', 'N/A')
            rating = movie.get('Rating', 'Not rated')
            similarity = movie.get('similarity_score', 0)
            
            context += f"{i}. **{name}** ({year})\n"
            context += f"   - Match Score: {similarity:.1%}\n"
            context += f"   - Rating: {rating}\n"
            
            if detailed and 'Review' in movie:
                review = movie.get('Review', '')[:150]
                if review:
                    context += f"   - Review: {review}...\n"
            
            context += "\n"
        
        return context
    
    def answer_question(self, question: str, context: str) -> str:
        """Answer user question using RAG context and LLM"""
        logger.info(f"Answering: {question}")
        
        system_prompt = """You are a helpful movie recommendation assistant with access to a user's personal movie database.

Your responsibilities:
1. Provide movie recommendations based on user preferences
2. Answer questions about movies in their collection
3. Give detailed information about specific films
4. Suggest similar movies based on preferences

Be concise, friendly, and always reference specific movies when possible.
When recommending, explain WHY you're recommending each movie."""
        
        user_prompt = f"""Movie Database Context:
{context}

User Question: {question}

Please provide a helpful response based on the movie database context above."""
        
        try:
            response = self.llm.generate_text(user_prompt, system_prompt)
            
            # Store in conversation history
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "response": response
            })
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def get_recommendations(self, preferences: str) -> Tuple[List[Dict], str]:
        """Get movie recommendations based on user preferences"""
        logger.info(f"Getting recommendations for: {preferences}")
        
        # Search for matching movies
        movies = self.search_movies(preferences, n_results=10)
        context = self.format_movie_context(movies[:5], detailed=True)
        
        prompt = f"""User Preference: {preferences}

{context}

Based on the movies above that match this preference, recommend the top 3 movies.
For each recommendation:
1. State the movie name and year
2. Explain why it matches their preference
3. Include the rating if available

Format your response as a numbered list."""
        
        try:
            recommendation_text = self.llm.generate_text(prompt)
            return movies[:3], recommendation_text
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return movies[:3], "Could not generate recommendations at this time."
    
    def analyze_collection(self, loader_stats: Dict) -> str:
        """Analyze the user's movie collection"""
        logger.info("Analyzing collection")
        
        prompt = f"""Analyze this movie collection:
- Total movies: {loader_stats.get('total_movies', 'Unknown')}
- Rated movies: {loader_stats.get('rated_movies', 'Unknown')}
- Time range: {loader_stats.get('years_range', 'Unknown')}

Provide a brief, friendly analysis of the collection. What might this person enjoy?"""
        
        try:
            analysis = self.llm.generate_text(prompt)
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing collection: {e}")
            return "Could not analyze collection."