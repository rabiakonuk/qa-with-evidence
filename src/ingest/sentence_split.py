"""Sentence segmentation with exact offsets preserved."""
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import yaml


def parse_frontmatter(raw_text: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML front-matter if present.
    
    Returns:
        (metadata_dict, original_raw_text_unchanged)
    """
    metadata = {}
    
    # Check for YAML front-matter
    if raw_text.startswith('---\n') or raw_text.startswith('---\r\n'):
        # Find the closing ---
        pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(pattern, raw_text, re.DOTALL)
        
        if match:
            yaml_content = match.group(1)
            try:
                metadata = yaml.safe_load(yaml_content)
                if metadata is None:
                    metadata = {}
            except yaml.YAMLError:
                metadata = {}
    
    return metadata, raw_text


def split_into_sentences(raw_text: str) -> List[Tuple[int, int, str]]:
    """
    Split text into sentences with exact (start, end) offsets.
    
    Uses a simple but effective regex pattern that:
    - Splits on . ! ? followed by whitespace
    - Handles end of string
    - Preserves exact character positions in original text
    
    Returns:
        List of (start_pos, end_pos, sentence_text) tuples
    """
    sentences = []
    
    # Pattern matches sentences ending with . ! or ?
    # Followed by one or more whitespace characters or end of string
    # This is simple but deterministic and preserves all characters
    pattern = r'[^.!?\n]+[.!?]+(?:\s+|$)|[^.!?\n]+$'
    
    for match in re.finditer(pattern, raw_text, re.MULTILINE):
        start = match.start()
        end = match.end()
        text = match.group().strip()
        
        # Only keep substantial sentences (not just punctuation or whitespace)
        if text and len(text) > 2:
            # Get the actual slice positions (not stripped)
            sentences.append((start, end, text))
    
    return sentences


def process_document(doc_path: Path, doc_id: str = None) -> List[Dict[str, Any]]:
    """
    Process a single markdown document into sentence records.
    
    Args:
        doc_path: Path to markdown file
        doc_id: Optional document ID (defaults to relative path)
        
    Returns:
        List of sentence dictionaries with schema:
        {
            "doc_id": str,
            "start": int,
            "end": int,
            "text": str,
            "tags": {"crop": str, "practice": str}
        }
    """
    # Read raw text (preserve everything exactly)
    with open(doc_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # Parse metadata
    metadata, _ = parse_frontmatter(raw_text)
    
    # Generate doc_id if not provided
    if doc_id is None:
        doc_id = str(doc_path)
    
    # Split into sentences
    sentences = split_into_sentences(raw_text)
    
    # Create records
    records = []
    for start, end, text in sentences:
        record = {
            "doc_id": doc_id,
            "start": start,
            "end": end,
            "text": text,
            "tags": {
                "crop": metadata.get("crop_type", "unknown"),
                "practice": "other"  # Will be enriched by tagger
            }
        }
        records.append(record)
    
    return records


def ingest_corpus(corpus_dir: Path, output_file: Path) -> int:
    """
    Ingest all markdown files in corpus directory.
    
    Args:
        corpus_dir: Directory containing markdown files (recursive)
        output_file: Path to write JSONL output
        
    Returns:
        Number of sentences processed
    """
    all_records = []
    
    # Find all markdown files
    md_files = list(corpus_dir.glob("**/*.md"))
    
    print(f"Found {len(md_files)} markdown files")
    
    for md_file in md_files:
        # Use relative path as doc_id
        rel_path = md_file.relative_to(corpus_dir)
        doc_id = str(rel_path)
        
        try:
            records = process_document(md_file, doc_id)
            all_records.extend(records)
            print(f"  {doc_id}: {len(records)} sentences")
        except Exception as e:
            print(f"  ERROR processing {doc_id}: {e}")
    
    # Write JSONL
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    print(f"\nWrote {len(all_records)} sentences to {output_file}")
    return len(all_records)


def verify_offsets(corpus_dir: Path, sentences_file: Path, sample_size: int = 200) -> bool:
    """
    Verify that offsets are correct by checking samples.
    
    Args:
        corpus_dir: Directory with original markdown files
        sentences_file: JSONL file with sentences
        sample_size: Number of random samples to verify
        
    Returns:
        True if all samples pass, False otherwise
    """
    import random
    
    # Load all sentences
    sentences = []
    with open(sentences_file, 'r', encoding='utf-8') as f:
        for line in f:
            sentences.append(json.loads(line))
    
    # Sample random sentences
    sample_size = min(sample_size, len(sentences))
    samples = random.sample(sentences, sample_size)
    
    print(f"Verifying {sample_size} random sentence offsets...")
    
    errors = 0
    for sent in samples:
        doc_path = corpus_dir / sent["doc_id"]
        
        # Read original file
        with open(doc_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        
        # Extract slice
        extracted = raw_text[sent["start"]:sent["end"]]
        
        # Check if extracted text matches (after stripping)
        if extracted.strip() != sent["text"]:
            print(f"  MISMATCH in {sent['doc_id']} at {sent['start']}:{sent['end']}")
            print(f"    Expected: {sent['text'][:50]}...")
            print(f"    Got: {extracted[:50]}...")
            errors += 1
    
    if errors == 0:
        print(f"✓ All {sample_size} samples passed offset verification")
        return True
    else:
        print(f"✗ {errors}/{sample_size} samples failed verification")
        return False
