from typing import List, Dict
import numpy as np
from src.core.models.story_bible import StoryBible
from src.worker.config import settings

class VectorStoreService:
    def __init__(self):
        self.embeddings = {}  # In-memory for now, can switch to Pinecone/etc
        
    async def store_bible(self, bible: StoryBible, embedding: np.ndarray):
        """Store bible with its embedding"""
        self.embeddings[bible.title] = {
            "bible": bible,
            "embedding": embedding
        }
    
    async def find_similar(self, query_embedding: np.ndarray, top_k: int = 3) -> List[StoryBible]:
        """Find most similar bibles by embedding similarity"""
        similarities = []
        for title, data in self.embeddings.items():
            similarity = np.dot(query_embedding, data["embedding"])
            similarities.append((similarity, data["bible"]))
        
        similarities.sort(reverse=True)
        return [bible for _, bible in similarities[:top_k]] 