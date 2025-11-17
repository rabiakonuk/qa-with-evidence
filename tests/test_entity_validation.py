"""Test entity validation for out-of-corpus questions."""
import pytest
from src.answer.abstain import check_entity_match


def test_entity_validation_company_name():
    """Test that company-specific questions are caught."""
    question = "Which specific hybrid corn cultivar had the top yield in the 2023 Doktar internal field trials?"
    sentences = [
        {"text": "Corn hybrids showed good results in trials."},
        {"text": "Field trials demonstrated improved yields."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert not valid
    assert "Doktar" in reason or "internal" in reason.lower()


def test_entity_validation_specific_year():
    """Test that specific recent years are validated."""
    question = "What was the average farm-gate price for fresh tomatoes in Eskisehir on 15 July 2024?"
    sentences = [
        {"text": "Tomato prices vary by season and location."},
        {"text": "Historical price data shows fluctuations."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert not valid
    assert "2024" in reason or "Eskisehir" in reason


def test_entity_validation_quarterly_data():
    """Test that specific quarterly data requests are caught."""
    question = "What was the precise volume of registered neonicotinoid seed treatment used on canola in Türkiye in Q2 2021?"
    sentences = [
        {"text": "Neonicotinoid use has been regulated."},
        {"text": "Seed treatments are common in canola production."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert not valid
    # Should catch quarterly_data pattern or 2021 year


def test_entity_validation_passes_generic():
    """Test that generic questions pass validation."""
    question = "What soil pH is recommended for canola?"
    sentences = [
        {"text": "Canola grows best at pH 6.0-7.0."},
        {"text": "Soil pH affects nutrient availability."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert valid
    assert reason is None


def test_entity_validation_passes_with_year_in_text():
    """Test that questions with years pass if year is in retrieved text."""
    question = "What happened in 2020?"
    sentences = [
        {"text": "In 2020, agricultural production increased."},
        {"text": "The year 2020 saw significant changes."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert valid
    assert reason is None


def test_entity_validation_passes_with_location_in_text():
    """Test that questions with locations pass if location is in text."""
    question = "What crops are grown in Turkey?"
    sentences = [
        {"text": "Turkey produces wheat, barley, and corn."},
        {"text": "Turkish agriculture is diverse."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert valid
    assert reason is None


def test_entity_validation_internal_trial():
    """Test that internal trial questions are caught."""
    question = "What were the results of the internal study on wheat?"
    sentences = [
        {"text": "Wheat studies show various results."},
        {"text": "Research demonstrates improved varieties."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert not valid
    assert "internal" in reason.lower()


def test_entity_validation_no_entities():
    """Test that questions without specific entities pass."""
    question = "How do you plant corn?"
    sentences = [
        {"text": "Corn is planted at 2-3 inch depth."},
        {"text": "Row spacing for corn is typically 30 inches."}
    ]
    valid, reason = check_entity_match(question, sentences)
    assert valid
    assert reason is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

