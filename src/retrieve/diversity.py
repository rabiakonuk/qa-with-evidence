"""Reranking and MMR diversity selection."""
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def pairwise_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity matrix.
    
    Args:
        embeddings: numpy array of shape (n, dim)
        
    Returns:
        Similarity matrix of shape (n, n)
    """
    # Normalize embeddings
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    
    # Compute cosine similarity matrix
    return np.dot(normalized, normalized.T)


def compute_redundancy(embeddings: np.ndarray) -> float:
    """
    Compute mean pairwise cosine similarity as redundancy metric.
    
    Args:
        embeddings: numpy array of shape (n, dim)
        
    Returns:
        Mean pairwise similarity (excluding diagonal)
    """
    if len(embeddings) <= 1:
        return 0.0
    
    sim_matrix = pairwise_similarity_matrix(embeddings)
    
    # Get upper triangle (excluding diagonal)
    n = len(embeddings)
    upper_triangle = sim_matrix[np.triu_indices(n, k=1)]
    
    return float(np.mean(upper_triangle))


class DiversitySelector:
    """Reranking and MMR-based diversity selection."""
    
    def __init__(
        self,
        model: SentenceTransformer,
        mmr_lambda: float = 0.7,
        max_sim_threshold: float = 0.82,
        min_support: int = 3,
        max_support: int = 6
    ):
        """
        Initialize diversity selector.
        
        Args:
            model: Sentence transformer model for reranking
            mmr_lambda: Balance between relevance and diversity (higher = more relevance)
            max_sim_threshold: Skip candidates too similar to selected
            min_support: Minimum number of sentences to select
            max_support: Maximum number of sentences to select
        """
        self.model = model
        self.mmr_lambda = mmr_lambda
        self.max_sim_threshold = max_sim_threshold
        self.min_support = min_support
        self.max_support = max_support
    
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[int, float, Dict]],
        top_k: int = 20
    ) -> List[Tuple[int, float, Dict, np.ndarray]]:
        """
        Rerank candidates using query-sentence cosine similarity.
        
        Args:
            query: Query string
            candidates: List of (sent_id, fused_score, metadata) tuples
            top_k: Number to keep after reranking
            
        Returns:
            List of (sent_id, rerank_score, metadata, embedding) tuples
        """
        if not candidates:
            return []
        
        # Encode query
        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]
        
        # Encode all candidate texts
        texts = [meta["text"] for _, _, meta in candidates]
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Compute cosine similarities with query
        similarities = np.dot(embeddings, query_embedding)
        
        # Rerank by similarity
        reranked = []
        for i, (sent_id, fused_score, meta) in enumerate(candidates):
            reranked.append((sent_id, float(similarities[i]), meta, embeddings[i]))
        
        # Sort by rerank score and take top_k
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        return reranked[:top_k]
    
    def select_diverse(
        self,
        query: str,
        reranked: List[Tuple[int, float, Dict, np.ndarray]]
    ) -> Tuple[List[Dict], Dict[str, float]]:
        """
        Select diverse subset using MMR.
        
        Args:
            query: Query string
            reranked: List of (sent_id, rerank_score, metadata, embedding) tuples
            
        Returns:
            Tuple of (selected_sentences, metrics)
        """
        if not reranked:
            return [], {"redundancy_before": 0.0, "redundancy_after": 0.0}
        
        # Compute redundancy before selection
        all_embeddings = np.array([emb for _, _, _, emb in reranked])
        redundancy_before = compute_redundancy(all_embeddings)
        
        # MMR selection
        selected = []
        selected_embeddings = []
        remaining = list(reranked)
        
        # Start with highest-scoring candidate
        if remaining:
            best = remaining.pop(0)
            selected.append({
                "sent_id": best[0],
                "score": best[1],
                "text": best[2]["text"],
                "doc_id": best[2]["doc_id"],
                "start": best[2]["start"],
                "end": best[2]["end"],
                "tags": {
                    "crop": best[2]["crop"],
                    "practice": best[2]["practice"]
                }
            })
            selected_embeddings.append(best[3])
        
        # Greedily add diverse candidates
        while remaining and len(selected) < self.max_support:
            best_score = -float('inf')
            best_idx = -1
            
            for i, (sent_id, relevance, meta, emb) in enumerate(remaining):
                # Compute max similarity to already selected
                max_sim = 0.0
                if selected_embeddings:
                    sims = [cosine_similarity(emb, sel_emb) for sel_emb in selected_embeddings]
                    max_sim = max(sims)
                
                # Skip if too similar
                if max_sim > self.max_sim_threshold:
                    continue
                
                # MMR score: balance relevance and diversity
                mmr_score = self.mmr_lambda * relevance - (1 - self.mmr_lambda) * max_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            # Stop if no good candidate found
            if best_idx == -1:
                break
            
            # Add best candidate
            best = remaining.pop(best_idx)
            selected.append({
                "sent_id": best[0],
                "score": best[1],
                "text": best[2]["text"],
                "doc_id": best[2]["doc_id"],
                "start": best[2]["start"],
                "end": best[2]["end"],
                "tags": {
                    "crop": best[2]["crop"],
                    "practice": best[2]["practice"]
                }
            })
            selected_embeddings.append(best[3])
        
        # Compute redundancy after selection
        if len(selected_embeddings) > 1:
            selected_emb_array = np.array(selected_embeddings)
            redundancy_after = compute_redundancy(selected_emb_array)
        else:
            redundancy_after = 0.0
        
        metrics = {
            "redundancy_before": redundancy_before,
            "redundancy_after": redundancy_after,
            "num_candidates": len(reranked),
            "num_selected": len(selected)
        }
        
        return selected, metrics
    
    def select(
        self,
        query: str,
        candidates: List[Tuple[int, float, Dict]],
        rerank_topk: int = 20
    ) -> Tuple[List[Dict], Dict[str, float]]:
        """
        Complete pipeline: rerank + MMR selection.
        
        Args:
            query: Query string
            candidates: List of (sent_id, fused_score, metadata) tuples
            rerank_topk: Number to keep after reranking
            
        Returns:
            Tuple of (selected_sentences, metrics)
        """
        # Rerank
        reranked = self.rerank(query, candidates, rerank_topk)
        
        # Select diverse subset
        selected, metrics = self.select_diverse(query, reranked)
        
        return selected, metrics


