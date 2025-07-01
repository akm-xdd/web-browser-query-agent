import google.generativeai as genai
import numpy as np
from app.core.config import settings
from app.services.cache_manager import query_cache

class SimilarityChecker:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using Gemini"""
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query"
            )
            return np.array(result['embedding'])
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return random embedding as fallback (for development)
            return np.random.rand(768)
    
    async def check_similarity(self, query: str) -> tuple[bool, str, float, str]:
        """
        Check if query is similar to cached queries
        Returns: (found_similar, similar_query, similarity_score, cached_result)
        """
        try:
            # Get embedding for the new query
            query_embedding = self.get_embedding(query)
            
            # Check against cached queries (excluding the current query)
            found, similar_query, similarity_score, cached_result = query_cache.find_similar_query(query_embedding, query)
            
            return found, similar_query or "", similarity_score or 0.0, cached_result or ""
            
        except Exception as e:
            print(f"Error in similarity check: {e}")
            return False, "", 0.0, ""
    
    def cache_query_result(self, query: str, result: str):
        """Cache a new query and its result"""
        try:
            query_embedding = self.get_embedding(query)
            query_cache.add_query(query, query_embedding, result)
            print(f"Cached query: {query}")
        except Exception as e:
            print(f"Error caching query: {e}")