"""Test offset correctness and sentence splitting."""
import pytest
from pathlib import Path
from src.ingest.sentence_split import split_into_sentences, parse_frontmatter


def test_offset_exactness_simple():
    """Test that offsets correctly map to original text."""
    text = "This is sentence one. This is sentence two! And sentence three?"
    
    sentences = split_into_sentences(text)
    
    # Verify each sentence
    for start, end, sent_text in sentences:
        extracted = text[start:end].strip()
        assert extracted == sent_text, f"Mismatch: expected '{sent_text}', got '{extracted}'"


def test_offset_with_frontmatter():
    """Test offsets work correctly with YAML frontmatter."""
    text = """---
crop_type: canola
language: en
---
# Title

This is the first sentence. This is the second sentence."""
    
    sentences = split_into_sentences(text)
    
    # Verify each sentence against original text
    for start, end, sent_text in sentences:
        extracted = text[start:end].strip()
        assert extracted == sent_text


def test_offset_with_special_chars():
    """Test offsets with special characters and punctuation."""
    text = "Dr. Smith said pH is 6.5-7.0. Use 150 kg/ha N-P-K fertilizer!"
    
    sentences = split_into_sentences(text)
    
    for start, end, sent_text in sentences:
        extracted = text[start:end].strip()
        assert extracted == sent_text


def test_offset_no_overlap():
    """Test that sentence offsets don't overlap."""
    text = "First sentence. Second sentence. Third sentence."
    
    sentences = split_into_sentences(text)
    
    # Check no overlaps
    for i in range(len(sentences) - 1):
        _, end1, _ = sentences[i]
        start2, _, _ = sentences[i + 1]
        assert end1 <= start2, f"Sentences {i} and {i+1} overlap"


def test_frontmatter_parsing():
    """Test YAML frontmatter parsing."""
    text = """---
crop_type: canola
language: en
source: test.pdf
---
Content here."""
    
    metadata, raw = parse_frontmatter(text)
    
    assert metadata["crop_type"] == "canola"
    assert metadata["language"] == "en"
    assert metadata["source"] == "test.pdf"
    assert raw == text  # Original text unchanged


def test_empty_text():
    """Test handling of empty text."""
    text = ""
    sentences = split_into_sentences(text)
    assert len(sentences) == 0


def test_multiline_text():
    """Test sentences spanning multiple lines."""
    text = """This is a sentence
that spans multiple
lines in the source.

This is a new paragraph."""
    
    sentences = split_into_sentences(text)
    
    # Verify offsets
    for start, end, sent_text in sentences:
        extracted = text[start:end].strip()
        assert extracted == sent_text


