"""Abstention policy for low-confidence or invalid answers."""
from typing import List, Dict, Any, Tuple, Optional


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


