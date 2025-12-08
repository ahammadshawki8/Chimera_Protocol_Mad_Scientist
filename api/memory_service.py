"""
Memory service for text-based search
Optimized for low memory usage - uses simple keyword matching instead of TF-IDF
"""
import re
from typing import List, Dict
from .models import Memory


class MemoryService:
    """
    Lightweight memory search service using keyword matching
    No heavy dependencies (scikit-learn, numpy removed)
    """
    
    def search(self, query: str, top_k: int = 5, workspace_id: str = None) -> List[Dict]:
        """
        Search for similar memories using keyword matching
        
        Args:
            query: Search query text
            top_k: Number of top results to return
            workspace_id: Optional filter by workspace
            
        Returns:
            List of dicts with memory data and relevance scores
        """
        try:
            # Get memories from database
            memories_qs = Memory.objects.all()
            
            if workspace_id:
                memories_qs = memories_qs.filter(workspace_id=workspace_id)
            
            memories = list(memories_qs[:100])  # Limit to 100 for performance
            
            if not memories:
                return []
            
            # Tokenize query
            query_tokens = self._tokenize(query.lower())
            
            if not query_tokens:
                return []
            
            # Score each memory
            scored_memories = []
            for memory in memories:
                score = self._calculate_score(query_tokens, memory)
                if score > 0:
                    scored_memories.append((memory, score))
            
            # Sort by score descending
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k results
            results = []
            for memory, score in scored_memories[:top_k]:
                results.append({
                    'id': memory.id,
                    'title': memory.title,
                    'content': memory.content[:500],  # Truncate for memory efficiency
                    'snippet': memory.snippet,
                    'score': score,
                    'tags': memory.tags,
                    'workspace_id': memory.workspace_id,
                    'created_at': memory.created_at.isoformat()
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching memories: {e}")
            return []
    
    def _tokenize(self, text: str) -> set:
        """Simple tokenization - split on non-alphanumeric chars"""
        # Remove special chars and split
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter short words and common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                      'can', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by',
                      'from', 'as', 'into', 'through', 'during', 'before', 'after',
                      'above', 'below', 'between', 'under', 'again', 'further',
                      'then', 'once', 'here', 'there', 'when', 'where', 'why',
                      'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                      'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                      'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
                      'because', 'until', 'while', 'this', 'that', 'these', 'those',
                      'it', 'its', 'i', 'me', 'my', 'we', 'our', 'you', 'your',
                      'he', 'him', 'his', 'she', 'her', 'they', 'them', 'their'}
        return {w for w in words if len(w) > 2 and w not in stop_words}
    
    def _calculate_score(self, query_tokens: set, memory) -> float:
        """Calculate relevance score based on keyword overlap"""
        # Combine title and content
        memory_text = f"{memory.title} {memory.content}".lower()
        memory_tokens = self._tokenize(memory_text)
        
        if not memory_tokens:
            return 0.0
        
        # Calculate Jaccard-like similarity
        intersection = query_tokens & memory_tokens
        if not intersection:
            return 0.0
        
        # Score based on matches, weighted by title matches
        title_tokens = self._tokenize(memory.title.lower())
        title_matches = len(query_tokens & title_tokens)
        content_matches = len(intersection) - title_matches
        
        # Title matches worth more
        score = (title_matches * 2.0 + content_matches) / len(query_tokens)
        
        return min(score, 1.0)  # Cap at 1.0


# Global instance
memory_service = MemoryService()
