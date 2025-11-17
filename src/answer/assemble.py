"""Answer assembly with numeric safeguard."""
import re
from typing import List, Dict, Any, Tuple, Optional


def extract_numbers_and_units(text: str) -> List[str]:
    """
    Extract numeric values with their units from text.
    
    Returns:
        List of numeric strings (e.g., ["2.5 inches", "150 kg", "6.5"])
    """
    # Pattern matches: number (int/float) optionally followed by unit
    # Handles: "2.5", "150", "6.5 inches", "2-4", "150 kg/ha"
    pattern = r'\b\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?(?:\s*[a-zA-Z/%]+(?:/[a-zA-Z]+)?)?\b'
    
    matches = re.findall(pattern, text)
    return matches


def check_numeric_safeguard(final_answer: str, source_sentences: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Verify that any numbers in final answer appear in at least one source sentence.
    
    Args:
        final_answer: The assembled answer text
        source_sentences: List of sentence dictionaries used to build answer
        
    Returns:
        Tuple of (is_valid, reason)
    """
    # Extract numbers from final answer
    answer_numbers = extract_numbers_and_units(final_answer)
    
    if not answer_numbers:
        # No numbers in answer, safeguard passes
        return True, None
    
    # Extract numbers from all source sentences
    source_numbers = set()
    for sent in source_sentences:
        sent_numbers = extract_numbers_and_units(sent["text"])
        source_numbers.update(sent_numbers)
    
    # Check if each answer number appears in sources
    missing_numbers = []
    for num in answer_numbers:
        # Check for exact match or if the core number appears
        core_num = re.match(r'[\d\.]+', num).group() if re.match(r'[\d\.]+', num) else num
        
        found = False
        for src_num in source_numbers:
            if num in src_num or core_num in src_num:
                found = True
                break
        
        if not found:
            missing_numbers.append(num)
    
    if missing_numbers:
        reason = f"Numeric safeguard failed: numbers {missing_numbers} not found in source sentences"
        return False, reason
    
    return True, None


def assemble_answer(selected_sentences: List[Dict[str, Any]], check_numeric: bool = True) -> Tuple[str, bool, Optional[str]]:
    """
    Assemble final answer from selected sentences.
    
    Args:
        selected_sentences: List of sentence dictionaries
        check_numeric: Whether to apply numeric safeguard
        
    Returns:
        Tuple of (final_answer, is_valid, reason)
    """
    if not selected_sentences:
        return "", False, "No sentences selected"
    
    # Join sentences with newline
    # Each sentence is verbatim text from the source
    final_answer = "\n".join(sent["text"] for sent in selected_sentences)
    
    # Apply numeric safeguard
    if check_numeric:
        is_valid, reason = check_numeric_safeguard(final_answer, selected_sentences)
        return final_answer, is_valid, reason
    
    return final_answer, True, None


def format_answer_with_citations(selected_sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format answer with full citation information.
    
    Args:
        selected_sentences: List of sentence dictionaries
        
    Returns:
        Dictionary with answer and citations
    """
    final_answer, is_valid, reason = assemble_answer(selected_sentences)
    
    # Format citations
    citations = []
    for sent in selected_sentences:
        citation = {
            "text": sent["text"],
            "doc_id": sent["doc_id"],
            "start": sent["start"],
            "end": sent["end"],
            "tags": sent["tags"]
        }
        citations.append(citation)
    
    return {
        "final_answer": final_answer,
        "answer_sentences": citations,
        "is_valid": is_valid,
        "validation_reason": reason
    }


