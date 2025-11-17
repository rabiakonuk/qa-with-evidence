"""Test determinism of the pipeline."""
import pytest
from src.ingest.sentence_split import split_into_sentences


def test_sentence_split_determinism():
    """Test that sentence splitting is deterministic."""
    text = "First sentence. Second sentence! Third sentence?"
    
    # Run multiple times
    results = []
    for _ in range(5):
        sentences = split_into_sentences(text)
        results.append(sentences)
    
    # All results should be identical
    for i in range(1, len(results)):
        assert results[i] == results[0], "Sentence splitting is not deterministic"


def test_tagging_determinism():
    """Test that tagging is deterministic."""
    from src.ingest.tagger import detect_crop, detect_practice
    
    text = "Canola requires nitrogen fertilizer for optimal growth."
    
    # Run multiple times
    crops = []
    practices = []
    for _ in range(5):
        crops.append(detect_crop(text, "canola/guide.md"))
        practices.append(detect_practice(text))
    
    # All results should be identical
    assert len(set(crops)) == 1, "Crop detection is not deterministic"
    assert len(set(practices)) == 1, "Practice detection is not deterministic"


def test_offset_determinism():
    """Test that offsets are deterministic."""
    text = """---
crop_type: test
---
# Header

This is a test sentence. Another test sentence!"""
    
    # Run multiple times
    results = []
    for _ in range(5):
        sentences = split_into_sentences(text)
        # Extract just the offsets
        offsets = [(s, e) for s, e, _ in sentences]
        results.append(offsets)
    
    # All results should be identical
    for i in range(1, len(results)):
        assert results[i] == results[0], "Offset computation is not deterministic"


