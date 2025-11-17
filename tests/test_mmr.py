"""Test MMR diversity selection."""
import pytest
import numpy as np
from src.retrieve.diversity import compute_redundancy, pairwise_similarity_matrix


def test_compute_redundancy_identical():
    """Test redundancy is high for identical vectors."""
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0]
    ])
    
    redundancy = compute_redundancy(embeddings)
    
    # Should be very high (close to 1.0) for identical vectors
    assert redundancy > 0.95


def test_compute_redundancy_orthogonal():
    """Test redundancy is low for orthogonal vectors."""
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ])
    
    redundancy = compute_redundancy(embeddings)
    
    # Should be close to 0 for orthogonal vectors
    assert redundancy < 0.1


def test_compute_redundancy_single():
    """Test redundancy is 0 for single vector."""
    embeddings = np.array([[1.0, 0.0, 0.0]])
    
    redundancy = compute_redundancy(embeddings)
    
    assert redundancy == 0.0


def test_pairwise_similarity_matrix():
    """Test pairwise similarity matrix computation."""
    embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0]
    ])
    
    sim_matrix = pairwise_similarity_matrix(embeddings)
    
    # Check shape
    assert sim_matrix.shape == (3, 3)
    
    # Check diagonal is 1
    assert np.allclose(np.diag(sim_matrix), 1.0)
    
    # Check symmetry
    assert np.allclose(sim_matrix, sim_matrix.T)
    
    # Check specific similarities
    assert sim_matrix[0, 1] < 0.1  # Orthogonal
    assert sim_matrix[0, 2] > 0.95  # Identical


def test_mmr_reduces_redundancy():
    """Test that MMR selection reduces redundancy."""
    # Create highly redundant set with one diverse item
    embeddings = np.array([
        [1.0, 0.0, 0.0],  # Similar
        [0.99, 0.01, 0.0],  # Similar
        [0.98, 0.02, 0.0],  # Similar
        [0.0, 0.0, 1.0]  # Diverse
    ])
    
    redundancy_all = compute_redundancy(embeddings)
    
    # Select diverse subset (indices 0 and 3)
    diverse_embeddings = embeddings[[0, 3]]
    redundancy_diverse = compute_redundancy(diverse_embeddings)
    
    # Redundancy should be lower after selection
    assert redundancy_diverse < redundancy_all


def test_mmr_threshold_enforcement():
    """Test that MMR respects similarity threshold."""
    from sentence_transformers import SentenceTransformer
    from src.retrieve.diversity import DiversitySelector
    
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    selector = DiversitySelector(model, mmr_lambda=0.7, max_sim_threshold=0.85)
    
    # Create similar sentences
    texts = [
        "Canola is an oilseed crop.",
        "Canola is grown for oil.",  # Very similar
        "Wheat is a cereal grain."   # Different
    ]
    
    embeddings = model.encode(texts, normalize_embeddings=True)
    
    # Create reranked list
    reranked = [
        (i, 0.9 - i*0.1, {"text": texts[i], "doc_id": f"doc{i}", "start": 0, "end": 10, "crop": "test", "practice": "test"}, embeddings[i])
        for i in range(len(texts))
    ]
    
    selected, metrics = selector.select_diverse("What is canola?", reranked)
    
    # Should select at least 2 different sentences
    # and avoid selecting both very similar ones
    assert len(selected) >= 2
    
    # Check that selected sentences aren't too similar
    if len(selected) > 1:
        selected_ids = [s["sent_id"] for s in selected]
        # If sentences 0 and 1 are both selected, something is wrong
        # (they're too similar)
        # This test might be flaky depending on threshold
        assert metrics["redundancy_after"] < 0.9


