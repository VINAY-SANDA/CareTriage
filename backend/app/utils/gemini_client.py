"""
Gemini API Client
Wrapper for Google's Generative AI API with error handling and retry logic.
"""
import google.generativeai as genai
from typing import Optional, List, Dict, Any
import asyncio
import logging

from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google's Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini client with API key."""
        self._configure_api()
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.chat_sessions: Dict[str, Any] = {}
    
    def _configure_api(self):
        """Configure the Gemini API with credentials."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini API configured successfully")
    
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate text using Gemini.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction for context
            temperature: Creativity parameter (0.0-1.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        try:
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            if system_instruction:
                model = genai.GenerativeModel(
                    settings.GEMINI_MODEL,
                    system_instruction=system_instruction
                )
            else:
                model = self.model
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Gemini generation error: {str(e)}")
            raise
    
    async def generate_async(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Async version of generate."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate(prompt, system_instruction, temperature, max_tokens)
        )
    
    def start_chat(self, session_id: str, system_instruction: Optional[str] = None) -> None:
        """
        Start a new chat session.
        
        Args:
            session_id: Unique identifier for the chat session
            system_instruction: Optional system instruction
        """
        if system_instruction:
            model = genai.GenerativeModel(
                settings.GEMINI_MODEL,
                system_instruction=system_instruction
            )
        else:
            model = self.model
        
        self.chat_sessions[session_id] = model.start_chat(history=[])
        logger.info(f"Started chat session: {session_id}")
    
    def chat(self, session_id: str, message: str) -> str:
        """
        Send a message in an existing chat session.
        
        Args:
            session_id: The chat session ID
            message: User message
            
        Returns:
            Assistant response
        """
        if session_id not in self.chat_sessions:
            self.start_chat(session_id)
        
        chat = self.chat_sessions[session_id]
        response = chat.send_message(message)
        
        return response.text
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using Gemini.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            result = genai.embed_content(
                model=settings.EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            embeddings.append(result['embedding'])
        
        return embeddings
    
    def get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector
        """
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=query,
            task_type="retrieval_query"
        )
        return result['embedding']
    
    def end_chat(self, session_id: str) -> None:
        """End a chat session and clean up."""
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
            logger.info(f"Ended chat session: {session_id}")


# Singleton instance
gemini_client = GeminiClient()
