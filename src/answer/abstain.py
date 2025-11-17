"""Abstention policy for low-confidence or invalid answers."""
import re
from typing import List, Dict, Any, Tuple, Optional


def check_entity_match(question: str, selected_sentences: List[Dict]) -> Tuple[bool, Optional[str]]:
    """
    Check if specific entities in question appear in retrieved sentences.
    
    This prevents answering questions about specific entities not in the corpus:
    - Company names (Doktar, specific brands)
    - Specific years (2020+)
    - Specific locations (Türkiye, Eskisehir)
    - Internal trials/studies
    
    Args:
        question: The question text
        selected_sentences: List of retrieved sentence dictionaries
        
    Returns:
        Tuple of (is_valid, reason)
        - is_valid: True if entities match or no specific entities detected
        - reason: Error message if validation fails, None otherwise
    """
    entities = []
    
    # Check for company/brand names (case-insensitive)
    company_pattern = r'\b(Doktar|Company|Brand|Corporation|Inc\.?|Ltd\.?|LLC)\b'
    company_match = re.search(company_pattern, question, re.IGNORECASE)
    if company_match:
        entities.append(('company', company_match.group()))
    
    # Check for specific recent years (2020+)
    year_pattern = r'\b(202[0-9])\b'
    year_match = re.search(year_pattern, question)
    if year_match:
        entities.append(('year', year_match.group()))
    
    # Check for specific locations (Turkey/Türkiye and cities)
    location_pattern = r'\b(T[uü]rkiye|Turkey|Eskisehir|Eski[şs]ehir|Istanbul|Ankara)\b'
    location_match = re.search(location_pattern, question, re.IGNORECASE)
    if location_match:
        entities.append(('location', location_match.group()))
    
    # Check for specific trial/study/internal references
    trial_pattern = r'\b(internal|proprietary|confidential)\s+(trial|study|test|data|field\s+trial)\b'
    trial_match = re.search(trial_pattern, question, re.IGNORECASE)
    if trial_match:
        entities.append(('specific_study', 'internal_trial'))
    
    # Check for specific price/market data patterns
    price_pattern = r'\b(price|cost|rate)\s+(in|on|for|at)\s+\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
    price_match = re.search(price_pattern, question, re.IGNORECASE)
    if price_match:
        entities.append(('specific_price_date', 'dated_price'))
    
    # Check for specific volume/quantity with location+date
    volume_pattern = r'\b(volume|quantity|amount)\s+.*\b(in|at)\s+\w+\s+in\s+Q[1-4]\s+\d{4}\b'
    volume_match = re.search(volume_pattern, question, re.IGNORECASE)
    if volume_match:
        entities.append(('specific_volume_date', 'quarterly_data'))
    
    # If no specific entities detected, pass validation
    if not entities:
        return True, None
    
    # Collect all text from retrieved sentences
    all_text = ' '.join([s.get('text', '') for s in selected_sentences])
    all_text_lower = all_text.lower()
    
    # Check each entity appears in retrieved text
    missing_entities = []
    for entity_type, entity_value in entities:
        # For special entity types (internal trial, dated price), these are red flags
        if entity_type in ['specific_study', 'specific_price_date', 'specific_volume_date']:
            missing_entities.append(entity_value)
            continue
        
        # Check if entity appears in retrieved text (case-insensitive)
        if entity_value.lower() not in all_text_lower:
            missing_entities.append(entity_value)
    
    if missing_entities:
        reason = f"Entity validation failed: Specific entities not found in corpus [{', '.join(missing_entities)}]"
        return False, reason
    
    return True, None


def check_abstention(
    selected_sentences: List[Dict[str, Any]],
    max_retrieval_score: float,
    abstain_score_thresh: float = 0.35,
    min_support: int = 3,
    numeric_valid: bool = True,
    numeric_reason: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Determine whether to abstain from answering.
    
    Abstention criteria:
    1. Max retrieval score below threshold
    2. Insufficient supporting sentences
    3. Numeric safeguard failed
    
    Args:
        selected_sentences: List of selected sentence dictionaries
        max_retrieval_score: Best retrieval score from fusion
        abstain_score_thresh: Minimum acceptable retrieval score
        min_support: Minimum number of supporting sentences
        numeric_valid: Whether numeric safeguard passed
        numeric_reason: Reason for numeric validation failure
        
    Returns:
        Tuple of (should_abstain, reasons)
    """
    should_abstain = False
    reasons = []
    
    # Check 1: Low retrieval score
    if max_retrieval_score < abstain_score_thresh:
        should_abstain = True
        reasons.append(f"Low retrieval score: {max_retrieval_score:.3f} < {abstain_score_thresh}")
    
    # Check 2: Insufficient support
    support_count = len(selected_sentences)
    if support_count < min_support:
        should_abstain = True
        reasons.append(f"Insufficient support: {support_count} < {min_support}")
    
    # Check 3: Numeric safeguard failed
    if not numeric_valid:
        should_abstain = True
        reasons.append(f"Numeric validation failed: {numeric_reason}")
    
    return should_abstain, reasons


def make_decision(
    query: str,
    selected_sentences: List[Dict[str, Any]],
    max_retrieval_score: float,
    metrics: Dict[str, Any],
    config: Dict[str, Any],
    numeric_valid: bool = True,
    numeric_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make final decision on whether to answer or abstain.
    
    Args:
        query: The question
        selected_sentences: Selected sentences
        max_retrieval_score: Best retrieval score
        metrics: Diversity and retrieval metrics
        config: Configuration dictionary
        numeric_valid: Whether numeric safeguard passed
        numeric_reason: Reason for numeric failure
        
    Returns:
        Decision dictionary with abstention status and reasons
    """
    abstain_thresh = config.get("selection", {}).get("abstain_score_thresh", 0.35)
    min_support = config.get("selection", {}).get("min_support", 3)
    
    # First check entity validation (prevents out-of-corpus questions)
    entity_valid, entity_reason = check_entity_match(query, selected_sentences)
    if not entity_valid:
        return {
            "abstained": True,
            "reasons": [entity_reason],
            "scores": {
                "max_retrieval": max_retrieval_score,
                "support_count": len(selected_sentences),
                "redundancy_before": metrics.get("redundancy_before", 0.0),
                "redundancy_after": metrics.get("redundancy_after", 0.0)
            }
        }
    
    # Then check standard abstention criteria
    should_abstain, reasons = check_abstention(
        selected_sentences,
        max_retrieval_score,
        abstain_thresh,
        min_support,
        numeric_valid,
        numeric_reason
    )
    
    decision = {
        "abstained": should_abstain,
        "reasons": reasons,
        "scores": {
            "max_retrieval": max_retrieval_score,
            "support_count": len(selected_sentences),
            "redundancy_before": metrics.get("redundancy_before", 0.0),
            "redundancy_after": metrics.get("redundancy_after", 0.0)
        }
    }
    
    return decision


