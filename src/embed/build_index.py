"""Build embeddings, FAISS index, and metadata store."""
import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import sqlite_utils
from tqdm import tqdm


def load_sentences(sentences_file: Path) -> List[Dict[str, Any]]:
    """Load sentences from JSONL file."""
    sentences = []
    with open(sentences_file, 'r', encoding='utf-8') as f:
        for line in f:
            sentences.append(json.loads(line))
    return sentences


def build_embeddings(sentences: List[Dict[str, Any]], model_name: str, normalize: bool = True) -> np.ndarray:
    """
    Build embeddings for all sentences.
    
    Args:
        sentences: List of sentence dictionaries
        model_name: Name of sentence-transformers model
        normalize: Whether to L2-normalize embeddings
        
    Returns:
        numpy array of shape (n_sentences, embedding_dim)
    """
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Extract texts
    texts = [s["text"] for s in sentences]
    
    print(f"Encoding {len(texts)} sentences...")
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=normalize
    )
    
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build FAISS index for dense retrieval.
    
    Args:
        embeddings: numpy array of embeddings (n_sentences, dim)
        
    Returns:
        FAISS index
    """
    dim = embeddings.shape[1]
    
    # Use IndexFlatIP for inner product (cosine similarity with normalized vectors)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype('float32'))
    
    print(f"Built FAISS index with {index.ntotal} vectors of dimension {dim}")
    
    return index


def build_metadata_store(sentences: List[Dict[str, Any]], db_path: Path):
    """
    Build SQLite metadata store.
    
    Args:
        sentences: List of sentence dictionaries
        db_path: Path to SQLite database
    """
    db = sqlite_utils.Database(db_path)
    
    # Create table with schema
    if "sentences" in db.table_names():
        db["sentences"].drop()
    
    records = []
    for idx, sent in enumerate(sentences):
        record = {
            "row_id": idx,
            "doc_id": sent["doc_id"],
            "start": sent["start"],
            "end": sent["end"],
            "text": sent["text"],
            "crop": sent["tags"]["crop"],
            "practice": sent["tags"]["practice"]
        }
        records.append(record)
    
    db["sentences"].insert_all(records, pk="row_id")
    db["sentences"].create_index(["doc_id"])
    db["sentences"].create_index(["crop"])
    db["sentences"].create_index(["practice"])
    
    print(f"Built metadata store with {len(records)} records at {db_path}")


def build_index(
    sentences_file: Path,
    embeddings_file: Path,
    index_file: Path,
    meta_file: Path,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    normalize: bool = True
) -> Dict[str, Any]:
    """
    Build complete index: embeddings + FAISS + metadata.
    
    Args:
        sentences_file: Path to input JSONL with sentences
        embeddings_file: Path to save embeddings (.npy)
        index_file: Path to save FAISS index (.bin)
        meta_file: Path to save metadata SQLite database
        model_name: Sentence transformer model name
        normalize: Whether to L2-normalize embeddings
        
    Returns:
        Dictionary with statistics
    """
    # Load sentences
    print(f"Loading sentences from {sentences_file}")
    sentences = load_sentences(sentences_file)
    print(f"Loaded {len(sentences)} sentences")
    
    # Build embeddings
    embeddings = build_embeddings(sentences, model_name, normalize)
    
    # Save embeddings
    embeddings_file.parent.mkdir(parents=True, exist_ok=True)
    np.save(embeddings_file, embeddings)
    print(f"Saved embeddings to {embeddings_file}")
    
    # Build FAISS index
    index = build_faiss_index(embeddings)
    
    # Save FAISS index
    faiss.write_index(index, str(index_file))
    print(f"Saved FAISS index to {index_file}")
    
    # Build metadata store
    build_metadata_store(sentences, meta_file)
    
    stats = {
        "num_sentences": len(sentences),
        "embedding_dim": embeddings.shape[1],
        "model": model_name,
        "normalized": normalize
    }
    
    return stats

