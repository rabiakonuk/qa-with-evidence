"""BM25 lexical retrieval."""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
import sqlite_utils


class BM25Retriever:
    """BM25 retrieval over sentence corpus."""
    
    def __init__(self, sentences_file: Path):
        """
        Initialize BM25 index.
        
        Args:
            sentences_file: Path to JSONL file with sentences
        """
        print("Loading sentences for BM25...")
        self.sentences = []
        with open(sentences_file, 'r', encoding='utf-8') as f:
            for line in f:
                self.sentences.append(json.loads(line))
        
        print(f"Building BM25 index over {len(self.sentences)} sentences...")
        # Tokenize texts (simple whitespace + lowercase)
        texts = [s["text"] for s in self.sentences]
        tokenized_corpus = [text.lower().split() for text in texts]
        
        self.bm25 = BM25Okapi(tokenized_corpus)
        print("BM25 index built")
    
    def retrieve(self, query: str, top_k: int = 50) -> List[Tuple[int, float]]:
        """
        Retrieve top-k sentences using BM25.
        
        Args:
            query: Query string
            top_k: Number of results to return
            
        Returns:
            List of (sentence_id, score) tuples, sorted by score descending
        """
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = [(int(idx), float(scores[idx])) for idx in top_indices]
        
        return results
    
    def get_sentence(self, sent_id: int) -> Dict[str, Any]:
        """Get sentence by ID."""
        return self.sentences[sent_id]

