from typing import Dict, List, Tuple, Optional
import numpy as np
import json
import os
from sklearn.metrics.pairwise import cosine_similarity

class QueryCache:
    def __init__(self):
        self.cache_file = "query_cache.json"
        self.queries: List[str] = []
        self.embeddings: List[np.ndarray] = []
        self.results: List[str] = []
        self.similarity_threshold = 0.75
        
        # Load existing cache on startup
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from JSON file if it exists"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.queries = data.get('queries', [])
                self.results = data.get('results', [])
                
                # Convert embeddings back to numpy arrays
                embeddings_list = data.get('embeddings', [])
                self.embeddings = [np.array(emb) for emb in embeddings_list]
                
                print(f"Loaded {len(self.queries)} cached queries from {self.cache_file}")
            else:
                print("No existing cache file found. Starting with empty cache.")
                
        except Exception as e:
            print(f"Error loading cache: {e}. Starting with empty cache.")
            self.queries = []
            self.embeddings = []
            self.results = []
    
    def _save_cache(self):
        """Save cache to JSON file"""
        try:
            data = {
                'queries': self.queries,
                'results': self.results,
                # Convert numpy arrays to lists for JSON serialization
                'embeddings': [emb.tolist() for emb in self.embeddings]
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Cache saved to {self.cache_file}")
            
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def add_query(self, query: str, embedding: np.ndarray, result: str):
        """Add a new query, embedding, and result to cache"""
        self.queries.append(query)
        self.embeddings.append(embedding)
        self.results.append(result)
        
        # Auto-cleanup if cache gets too large
        self.cleanup_old_entries(max_entries=50)
        
        # Save to file immediately
        self._save_cache()
    
    def find_similar_query(self, query_embedding: np.ndarray, current_query: str = "") -> Tuple[bool, Optional[str], Optional[float], Optional[str]]:
        """
        Find similar query in cache
        Returns: (found, similar_query, similarity_score, cached_result)
        """
        if len(self.embeddings) == 0:
            return False, None, None, None
        
        # Calculate cosine similarity with all cached embeddings
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Find the most similar query above threshold
        for idx in np.argsort(similarities)[::-1]:  # Sort by highest similarity
            similarity = similarities[idx]
            
            if similarity >= self.similarity_threshold:
                return (
                    True,
                    self.queries[idx],
                    float(similarity),
                    self.results[idx]
                )
        
        return False, None, None, None
    
    
    
    def cleanup_old_entries(self, max_entries: int = 50):
        """Remove oldest entries if cache exceeds max_entries"""
        try:
            if len(self.queries) > max_entries:
                entries_to_remove = len(self.queries) - max_entries
                
                # Remove oldest entries (first in, first out)
                self.queries = self.queries[entries_to_remove:]
                self.embeddings = self.embeddings[entries_to_remove:]
                self.results = self.results[entries_to_remove:]
                
                self._save_cache()
                print(f"Cleaned up {entries_to_remove} old cache entries")
        except Exception as e:
            print(f"Error during cache cleanup: {e}")
    
    def clear_cache(self):
        """Clear all cache data and delete the file"""
        self.queries = []
        self.embeddings = []
        self.results = []
        
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
            print(f"Cache file {self.cache_file} deleted")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        file_size = 0
        if os.path.exists(self.cache_file):
            file_size = os.path.getsize(self.cache_file)
        
        return {
            "total_queries": len(self.queries),
            "similarity_threshold": self.similarity_threshold,
            "cache_file": self.cache_file,
            "file_exists": os.path.exists(self.cache_file),
            "file_size_mb": round(file_size / (1024 * 1024), 2)
        }

# Global cache instance
query_cache = QueryCache()