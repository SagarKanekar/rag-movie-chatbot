from enum import Enum
from typing import Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class AgentAction(Enum):
    """Types of actions the agent can take"""
    SEARCH_MOVIES = "search"
    ANSWER_QUESTION = "answer"
    GET_RECOMMENDATIONS = "recommend"
    ANALYZE_COLLECTION = "analyze"
    CHAT = "chat"

class MovieChatbotAgent:
    """Intelligent agent for routing user inputs and generating responses"""
    
    def __init__(self, rag_engine, llm, loader_stats: Optional[Dict] = None):
        self.rag_engine = rag_engine
        self.llm = llm
        self.loader_stats = loader_stats or {}
        self.conversation_count = 0
    
    def classify_input(self, user_input: str) -> AgentAction:
        """Determine what type of action to take based on user input"""
        user_lower = user_input.lower().strip()
        
        # Define keyword patterns for each action
        keywords = {
            'recommend': [
                'recommend', 'suggestion', 'what should i watch',
                'any good', 'what would you recommend', 'suggest me',
                'find me a', 'i want to watch'
            ],
            'search': [
                'find', 'search for', 'looking for', 'show me',
                'list movies', 'movies like', 'similar to', 'movies with'
            ],
            'analyze': [
                'analyze my collection', 'tell me about my movies',
                'what do you think of my taste', 'analyze my taste',
                'what kind of movies'
            ],
            'question': [
                'how', 'why', 'when', 'where', 'what about',
                'tell me about', 'explain', 'who'
            ]
        }
        
        # Check for keywords
        for action, words in keywords.items():
            for word in words:
                if word in user_lower:
                    if action == 'recommend':
                        return AgentAction.GET_RECOMMENDATIONS
                    elif action == 'search':
                        return AgentAction.SEARCH_MOVIES
                    elif action == 'analyze':
                        return AgentAction.ANALYZE_COLLECTION
                    elif action == 'question':
                        return AgentAction.ANSWER_QUESTION
        
        # Default to chat
        return AgentAction.CHAT
    
    def execute(self, user_input: str) -> Dict:
        """Execute agent logic and return response"""
        self.conversation_count += 1
        logger.info(f"[Turn {self.conversation_count}] User input: {user_input}")
        
        action = self.classify_input(user_input)
        logger.info(f"Classified as action: {action.name}")
        
        result = {
            'action': action.name,
            'response': '',
            'movies': [],
            'conversation_turn': self.conversation_count
        }
        
        try:
            if action == AgentAction.SEARCH_MOVIES:
                result.update(self._handle_search(user_input))
            
            elif action == AgentAction.GET_RECOMMENDATIONS:
                result.update(self._handle_recommendations(user_input))
            
            elif action == AgentAction.ANALYZE_COLLECTION:
                result.update(self._handle_analysis(user_input))
            
            elif action == AgentAction.ANSWER_QUESTION:
                result.update(self._handle_question(user_input))
            
            else:  # CHAT
                result.update(self._handle_chat(user_input))
        
        except Exception as e:
            logger.error(f"Error in agent execution: {e}")
            result['response'] = "I encountered an error. Please try again."
        
        return result
    
    def _handle_search(self, query: str) -> Dict:
        """Handle movie search requests"""
        logger.info("Handling search action")
        
        movies = self.rag_engine.search_movies(query, n_results=5)
        
        if not movies:
            response = f"I couldn't find any movies matching '{query}'. Try different keywords!"
        else:
            response = self._format_search_results(movies)
        
        return {
            'response': response,
            'movies': movies
        }
    
    def _handle_recommendations(self, preferences: str) -> Dict:
        """Handle recommendation requests"""
        logger.info("Handling recommendation action")
        
        movies, recommendation_text = self.rag_engine.get_recommendations(preferences)
        
        return {
            'response': recommendation_text,
            'movies': movies
        }
    
    def _handle_analysis(self, query: str) -> Dict:
        """Handle collection analysis requests"""
        logger.info("Handling analysis action")
        
        analysis = self.rag_engine.analyze_collection(self.loader_stats)
        
        return {
            'response': analysis,
            'movies': []
        }
    
    def _handle_question(self, question: str) -> Dict:
        """Handle general movie questions"""
        logger.info("Handling question action")
        
        # Search for relevant movies
        movies = self.rag_engine.search_movies(question, n_results=5)
        context = self.rag_engine.format_movie_context(movies, detailed=True)
        
        # Get answer
        answer = self.rag_engine.answer_question(question, context)
        
        return {
            'response': answer,
            'movies': movies
        }
    
    def _handle_chat(self, user_input: str) -> Dict:
        """Handle general chat"""
        logger.info("Handling chat action")
        
        response = self.rag_engine.answer_question(
            user_input,
            "User is having a general conversation about movies."
        )
        
        return {
            'response': response,
            'movies': []
        }
    
    def _format_search_results(self, movies: List[Dict]) -> str:
        """Format search results for display"""
        if not movies:
            return "No movies found."
        
        response = f"🎬 **Found {len(movies)} matching movies:**\n\n"
        
        for i, movie in enumerate(movies, 1):
            name = movie.get('Name', 'Unknown')
            year = movie.get('Year', 'N/A')
            rating = movie.get('Rating', 'Not rated')
            similarity = movie.get('similarity_score', 0)
            
            response += f"{i}. **{name}** ({year})\n"
            response += f"   • Match Score: {similarity:.1%}\n"
            response += f"   • Rating: {rating}\n"
        
        return response
