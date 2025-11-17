"""Hybrid retrieval with tag-based boosting."""
import numpy as np
import sqlite_utils
from pathlib import Path
from typing import List, Dict, Any, Tuple
from .bm25 import BM25Retriever
from .dense import DenseRetriever


class HybridRetriever:
    """Hybrid retrieval combining BM25 and dense retrieval with tag boosting."""
    
    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        dense_retriever: DenseRetriever,
        meta_file: Path,
        alpha_lexical: float = 0.4,
        tag_boost_crop: float = 0.08,
        tag_boost_practice: float = 0.05
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            bm25_retriever: BM25 retriever instance
            dense_retriever: Dense retriever instance
            meta_file: Path to metadata SQLite database
            alpha_lexical: Weight for BM25 scores (1-alpha for dense)
            tag_boost_crop: Boost factor for matching crop tags
            tag_boost_practice: Boost factor for matching practice tags
        """
        self.bm25 = bm25_retriever
        self.dense = dense_retriever
        self.db = sqlite_utils.Database(meta_file)
        self.alpha = alpha_lexical
        self.crop_boost = tag_boost_crop
        self.practice_boost = tag_boost_practice
        
        # Build tag keyword maps
        self.crop_keywords = {
            "canola": ["canola", "rapeseed"],
            "corn": ["corn", "maize"],
            "wheat": ["wheat"],
            "tomato": ["tomato", "tomatoes"],
            "soy": ["soy", "soybean"],
            "rice": ["rice"]
        }
        
        self.practice_keywords = {
            "irrigation": ["irrigation", "water", "drip"],
            "soil": ["soil", "tillage"],
            "fertility": ["fertility", "fertilizer", "nitrogen", "phosphorus", "nutrient"],
            "weeds": ["weed", "herbicide"],
            "disease": ["disease", "pathogen", "fungicide"],
            "pests": ["pest", "insect", "insecticide"],
            "harvest": ["harvest", "harvesting", "yield"],
            "planting": ["planting", "seeding", "sowing"],
            "storage": ["storage", "post-harvest"]
        }
    
    def detect_query_tags(self, query: str) -> Tuple[List[str], List[str]]:
        """Detect crop and practice tags from query."""
        query_lower = query.lower()
        
        detected_crops = []
        for crop, keywords in self.crop_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    detected_crops.append(crop)
                    break
        
        detected_practices = []
        for practice, keywords in self.practice_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    detected_practices.append(practice)
                    break
        
        return detected_crops, detected_practices
    
    def normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """Normalize scores to [0, 1] range."""
        if not scores:
            return {}
        
        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            return {k: 1.0 for k in scores}
        
        normalized = {}
        for k, v in scores.items():
            normalized[k] = (v - min_val) / (max_val - min_val)
        
        return normalized
    
    def retrieve(self, query: str, bm25_topk: int = 50, dense_topk: int = 50) -> List[Tuple[int, float, Dict]]:
        """
        Hybrid retrieval with fusion and tag boosting.
        
        Args:
            query: Query string
            bm25_topk: Number of BM25 results
            dense_topk: Number of dense results
            
        Returns:
            List of (sent_id, fused_score, metadata) tuples, sorted by score descending
        """
        # Retrieve from both
        bm25_results = self.bm25.retrieve(query, bm25_topk)
        dense_results = self.dense.retrieve(query, dense_topk)
        
        # Convert to dictionaries
        bm25_scores = {idx: score for idx, score in bm25_results}
        dense_scores = {idx: score for idx, score in dense_results}
        
        # Get union of candidates
        all_ids = set(bm25_scores.keys()) | set(dense_scores.keys())
        
        # Normalize within candidate set
        bm25_norm = self.normalize_scores(bm25_scores)
        dense_norm = self.normalize_scores(dense_scores)
        
        # Fuse scores
        fused_scores = {}
        for idx in all_ids:
            bm25_score = bm25_norm.get(idx, 0.0)
            dense_score = dense_norm.get(idx, 0.0)
            fused_scores[idx] = self.alpha * bm25_score + (1 - self.alpha) * dense_score
        
        # Detect query tags
        query_crops, query_practices = self.detect_query_tags(query)
        
        # Apply tag boosts
        if query_crops or query_practices:
            # Fetch metadata for all candidates
            meta_query = f"SELECT row_id, crop, practice FROM sentences WHERE row_id IN ({','.join(map(str, all_ids))})"
            rows = self.db.execute(meta_query).fetchall()
            metadata = {row[0]: {"crop": row[1], "practice": row[2]} for row in rows}
            
            for idx in all_ids:
                meta = metadata.get(idx, {})
                boost = 0.0
                
                if meta.get("crop") in query_crops:
                    boost += self.crop_boost
                if meta.get("practice") in query_practices:
                    boost += self.practice_boost
                
                fused_scores[idx] += boost
        
        # Get full metadata
        results = []
        for idx in sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True):
            meta_row = self.db["sentences"].get(idx)
            metadata = {
                "doc_id": meta_row["doc_id"],
                "start": meta_row["start"],
                "end": meta_row["end"],
                "text": meta_row["text"],
                "crop": meta_row["crop"],
                "practice": meta_row["practice"]
            }
            results.append((idx, fused_scores[idx], metadata))
        
        return results
