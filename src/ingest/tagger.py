"""Light tagging for crop type and agricultural practice."""
import json
import re
from pathlib import Path
from typing import Dict, List, Any


# Crop keyword maps (case-insensitive)
CROP_KEYWORDS = {
    "canola": ["canola", "rapeseed", "brassica napus"],
    "corn": ["corn", "maize", "zea mays"],
    "wheat": ["wheat", "triticum"],
    "tomato": ["tomato", "tomatoes", "solanum lycopersicum"],
    "soy": ["soy", "soybean", "glycine max"],
    "rice": ["rice", "oryza"],
}

# Practice keyword maps
PRACTICE_KEYWORDS = {
    "irrigation": ["irrigation", "water management", "drip", "sprinkler", "watering"],
    "soil": ["soil", "tillage", "residue", "erosion", "compaction"],
    "fertility": ["fertility", "fertilizer", "nitrogen", "phosphorus", "potassium", "nutrient", "n-p-k"],
    "weeds": ["weed", "herbicide", "weed control"],
    "disease": ["disease", "pathogen", "fungicide", "infection", "blight", "rot", "mildew"],
    "pests": ["pest", "insect", "insecticide", "aphid", "beetle", "moth", "mite"],
    "harvest": ["harvest", "harvesting", "combine", "threshing", "yield"],
    "planting": ["planting", "seeding", "sowing", "germination", "emergence", "planting date"],
    "storage": ["storage", "post-harvest", "drying", "grain storage"],
}


def detect_crop(text: str, doc_id: str = "", existing_tag: str = None) -> str:
    """
    Detect crop type from text or document ID.
    
    Args:
        text: Text to search for crop mentions
        doc_id: Document ID (may contain crop name)
        existing_tag: Existing crop tag from metadata
        
    Returns:
        Crop type string (canola, corn, wheat, tomato, soy, rice, or other)
    """
    # Use existing tag if valid
    if existing_tag and existing_tag != "unknown":
        return existing_tag
    
    text_lower = text.lower()
    doc_id_lower = doc_id.lower()
    
    # Check doc_id first (more reliable)
    for crop, keywords in CROP_KEYWORDS.items():
        for keyword in keywords:
            if keyword in doc_id_lower:
                return crop
    
    # Then check text content
    for crop, keywords in CROP_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return crop
    
    return "other"


def detect_practice(text: str) -> str:
    """
    Detect agricultural practice from text.
    
    Args:
        text: Text to search for practice mentions
        
    Returns:
        Practice type string (irrigation, soil, fertility, weeds, disease, 
        pests, harvest, planting, storage, or other)
    """
    text_lower = text.lower()
    
    # Score each practice based on keyword matches
    scores = {}
    for practice, keywords in PRACTICE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text_lower:
                score += 1
        scores[practice] = score
    
    # Return practice with highest score, or "other" if no matches
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    
    return "other"


def enrich_tags(sentences_file: Path, output_file: Path = None) -> int:
    """
    Enrich sentence tags with crop and practice detection.
    
    Args:
        sentences_file: Input JSONL file with sentences
        output_file: Output JSONL file (defaults to overwriting input)
        
    Returns:
        Number of sentences processed
    """
    if output_file is None:
        output_file = sentences_file
    
    # Read all sentences
    sentences = []
    with open(sentences_file, 'r', encoding='utf-8') as f:
        for line in f:
            sentences.append(json.loads(line))
    
    print(f"Enriching tags for {len(sentences)} sentences...")
    
    # Enrich each sentence
    for sent in sentences:
        doc_id = sent["doc_id"]
        text = sent["text"]
        existing_crop = sent.get("tags", {}).get("crop", "unknown")
        
        # Detect crop and practice
        crop = detect_crop(text, doc_id, existing_crop)
        practice = detect_practice(text)
        
        # Update tags
        sent["tags"] = {
            "crop": crop,
            "practice": practice
        }
    
    # Write enriched sentences
    with open(output_file, 'w', encoding='utf-8') as f:
        for sent in sentences:
            f.write(json.dumps(sent, ensure_ascii=False) + '\n')
    
    print(f"Wrote {len(sentences)} enriched sentences to {output_file}")
    
    # Print statistics
    crop_counts = {}
    practice_counts = {}
    for sent in sentences:
        crop = sent["tags"]["crop"]
        practice = sent["tags"]["practice"]
        crop_counts[crop] = crop_counts.get(crop, 0) + 1
        practice_counts[practice] = practice_counts.get(practice, 0) + 1
    
    print("\nCrop distribution:")
    for crop, count in sorted(crop_counts.items(), key=lambda x: -x[1]):
        print(f"  {crop}: {count}")
    
    print("\nPractice distribution:")
    for practice, count in sorted(practice_counts.items(), key=lambda x: -x[1]):
        print(f"  {practice}: {count}")
    
    return len(sentences)
