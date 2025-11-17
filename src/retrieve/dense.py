"""Dense retrieval using FAISS."""
import numpy as np
import faiss
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer


class DenseRetriever:
    """Dense retrieval using FAISS index."""
    
    def __init__(self, index_file: Path, model_name: str, normalize: bool = True):
        """
        Initialize dense retriever.
        
        Args:
            index_file: Path to FAISS index file
            model_name: Sentence transformer model name
            normalize: Whether to normalize embeddings
        """
        print(f"Loading FAISS index from {index_file}")
        self.index = faiss.read_index(str(index_file))
        
        print(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.normalize = normalize
        
        print(f"Dense retriever ready ({self.index.ntotal} vectors)")
    
    def retrieve(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Retrieve top-k sentences using dense search.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of (sentence_id, score) tuples, sorted by score descending
        """
        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=self.normalize
        )
        
        # Search FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Convert to list of tuples
        results = [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0])]
        
        return results

