"""Test numeric safeguard functionality."""
import pytest
from src.answer.assemble import check_numeric_safeguard, extract_numbers_and_units


def test_extract_numbers():
    """Test number extraction from text."""
    text = "Use 150 kg/ha fertilizer at pH 6.5-7.0 and temperature 20°C."
    
    numbers = extract_numbers_and_units(text)
    
    assert "150" in numbers or any("150" in n for n in numbers)
    assert any("6.5" in n or "7.0" in n for n in numbers)
    assert "20" in numbers or any("20" in n for n in numbers)


def test_numeric_safeguard_pass():
    """Test safeguard passes when numbers are in source."""
    final_answer = "Plant at 2 inch depth with 150 kg/ha fertilizer."
    
    source_sentences = [
        {"text": "Recommended planting depth is 2 inches."},
        {"text": "Apply 150 kg/ha of nitrogen fertilizer."}
    ]
    
    is_valid, reason = check_numeric_safeguard(final_answer, source_sentences)
    
    assert is_valid
    assert reason is None


def test_numeric_safeguard_fail():
    """Test safeguard fails when numbers not in source."""
    final_answer = "Plant at 3 inch depth with 200 kg/ha fertilizer."
    
    source_sentences = [
        {"text": "Recommended planting depth is 2 inches."},
        {"text": "Apply 150 kg/ha of nitrogen fertilizer."}
    ]
    
    is_valid, reason = check_numeric_safeguard(final_answer, source_sentences)
    
    assert not is_valid
    assert reason is not None
    assert "200" in reason or "3" in reason


def test_numeric_safeguard_no_numbers():
    """Test safeguard passes when no numbers present."""
    final_answer = "Canola is a type of oilseed crop."
    
    source_sentences = [
        {"text": "Canola is grown for oil production."},
        {"text": "It is a cool season crop."}
    ]
    
    is_valid, reason = check_numeric_safeguard(final_answer, source_sentences)
    
    assert is_valid
    assert reason is None


def test_numeric_safeguard_ranges():
    """Test safeguard with numeric ranges."""
    final_answer = "Soil pH should be 6.0-7.0."
    
    source_sentences = [
        {"text": "Optimal pH range is 6.0-7.0 for canola."}
    ]
    
    is_valid, reason = check_numeric_safeguard(final_answer, source_sentences)
    
    assert is_valid


def test_numeric_safeguard_units():
    """Test safeguard with various units."""
    final_answer = "Apply 100 kg/ha N and 50 kg/ha P."
    
    source_sentences = [
        {"text": "Nitrogen rate: 100 kg/ha."},
        {"text": "Phosphorus: 50 kg/ha recommended."}
    ]
    
    is_valid, reason = check_numeric_safeguard(final_answer, source_sentences)
    
    assert is_valid


