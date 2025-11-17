"""Evaluation scripts for QA system."""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List


def validate_offsets(run_file: Path, corpus_dir: Path) -> Dict[str, Any]:
    """
    Validate that all answer sentence offsets are correct.
    
    Args:
        run_file: Path to run JSONL file
        corpus_dir: Path to corpus directory
        
    Returns:
        Dictionary with validation statistics
    """
    total_sentences = 0
    valid_sentences = 0
    errors = []
    
    # Load run
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            
            if result["abstained"]:
                continue
            
            for sent in result["answer_sentences"]:
                total_sentences += 1
                
                doc_path = corpus_dir / sent["doc_id"]
                
                try:
                    # Read original file
                    with open(doc_path, 'r', encoding='utf-8') as df:
                        raw_text = df.read()
                    
                    # Extract slice
                    extracted = raw_text[sent["start"]:sent["end"]]
                    
                    # Compare (after stripping)
                    if extracted.strip() == sent["text"]:
                        valid_sentences += 1
                    else:
                        errors.append({
                            "question_id": result["question_id"],
                            "doc_id": sent["doc_id"],
                            "start": sent["start"],
                            "end": sent["end"],
                            "expected": sent["text"][:50],
                            "got": extracted[:50]
                        })
                except Exception as e:
                    errors.append({
                        "question_id": result["question_id"],
                        "doc_id": sent["doc_id"],
                        "error": str(e)
                    })
    
    pass_rate = (valid_sentences / total_sentences * 100) if total_sentences > 0 else 0
    
    return {
        "total_sentences": total_sentences,
        "valid_sentences": valid_sentences,
        "pass_rate": pass_rate,
        "errors": errors
    }


def compute_answer_rate(run_file: Path) -> Dict[str, Any]:
    """Compute answer rate statistics."""
    total = 0
    answered = 0
    abstained = 0
    
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            total += 1
            if result["abstained"]:
                abstained += 1
            else:
                answered += 1
    
    answer_rate = (answered / total * 100) if total > 0 else 0
    
    return {
        "total_questions": total,
        "answered": answered,
        "abstained": abstained,
        "answer_rate": answer_rate
    }


def compute_redundancy_stats(run_file: Path) -> Dict[str, Any]:
    """Compute redundancy reduction statistics."""
    before_values = []
    after_values = []
    
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            
            if result["abstained"]:
                continue
            
            scores = result["run_notes"]["scores"]
            before_values.append(scores.get("redundancy_before", 0.0))
            after_values.append(scores.get("redundancy_after", 0.0))
    
    if not before_values:
        return {
            "mean_redundancy_before": 0.0,
            "mean_redundancy_after": 0.0,
            "redundancy_reduction": 0.0
        }
    
    mean_before = sum(before_values) / len(before_values)
    mean_after = sum(after_values) / len(after_values)
    reduction = ((mean_before - mean_after) / mean_before * 100) if mean_before > 0 else 0
    
    return {
        "mean_redundancy_before": mean_before,
        "mean_redundancy_after": mean_after,
        "redundancy_reduction": reduction
    }


def compute_coverage_stats(run_file: Path) -> Dict[str, Any]:
    """Compute coverage diversity statistics."""
    crop_practice_pairs = []
    
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            
            if result["abstained"]:
                continue
            
            pairs = set()
            for sent in result["answer_sentences"]:
                crop = sent["tags"]["crop"]
                practice = sent["tags"]["practice"]
                pairs.add((crop, practice))
            
            crop_practice_pairs.append(len(pairs))
    
    if not crop_practice_pairs:
        return {
            "mean_unique_pairs": 0.0,
            "max_unique_pairs": 0,
            "min_unique_pairs": 0
        }
    
    return {
        "mean_unique_pairs": sum(crop_practice_pairs) / len(crop_practice_pairs),
        "max_unique_pairs": max(crop_practice_pairs),
        "min_unique_pairs": min(crop_practice_pairs)
    }


def evaluate_run(run_file: Path, corpus_dir: Path) -> Dict[str, Any]:
    """
    Complete evaluation of a run.
    
    Args:
        run_file: Path to run JSONL file
        corpus_dir: Path to corpus directory
        
    Returns:
        Dictionary with all statistics
    """
    print("Computing answer rate...")
    answer_stats = compute_answer_rate(run_file)
    
    print("Computing redundancy statistics...")
    redundancy_stats = compute_redundancy_stats(run_file)
    
    print("Computing coverage statistics...")
    coverage_stats = compute_coverage_stats(run_file)
    
    print("Validating offsets...")
    offset_stats = validate_offsets(run_file, corpus_dir)
    
    # Combine all stats
    all_stats = {
        **answer_stats,
        **redundancy_stats,
        **coverage_stats,
        "offset_pass_rate": offset_stats["pass_rate"],
        "offset_errors": len(offset_stats["errors"])
    }
    
    # Save detailed reports
    artifacts_dir = run_file.parent
    
    # Redundancy CSV
    redundancy_data = []
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            if not result["abstained"]:
                scores = result["run_notes"]["scores"]
                redundancy_data.append({
                    "question_id": result["question_id"],
                    "redundancy_before": scores.get("redundancy_before", 0.0),
                    "redundancy_after": scores.get("redundancy_after", 0.0),
                    "reduction": (scores.get("redundancy_before", 0.0) - scores.get("redundancy_after", 0.0))
                })
    
    if redundancy_data:
        pd.DataFrame(redundancy_data).to_csv(artifacts_dir / "redundancy.csv", index=False)
        print(f"Saved redundancy.csv")
    
    # Coverage CSV
    coverage_data = []
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            if not result["abstained"]:
                pairs = set()
                for sent in result["answer_sentences"]:
                    pairs.add((sent["tags"]["crop"], sent["tags"]["practice"]))
                coverage_data.append({
                    "question_id": result["question_id"],
                    "unique_crop_practice_pairs": len(pairs),
                    "num_sentences": len(result["answer_sentences"])
                })
    
    if coverage_data:
        pd.DataFrame(coverage_data).to_csv(artifacts_dir / "coverage.csv", index=False)
        print(f"Saved coverage.csv")
    
    # Decisions CSV
    decision_data = []
    with open(run_file, 'r', encoding='utf-8') as f:
        for line in f:
            result = json.loads(line)
            decision_data.append({
                "question_id": result["question_id"],
                "abstained": result["abstained"],
                "decision": "; ".join(result["run_notes"]["decision"]),
                "max_retrieval": result["run_notes"]["scores"]["max_retrieval"],
                "support_count": result["run_notes"]["scores"]["support_count"]
            })
    
    pd.DataFrame(decision_data).to_csv(artifacts_dir / "decisions.csv", index=False)
    print(f"Saved decisions.csv")
    
    # Save offset errors if any
    if offset_stats["errors"]:
        pd.DataFrame(offset_stats["errors"]).to_csv(artifacts_dir / "offset_errors.csv", index=False)
        print(f"Saved offset_errors.csv ({len(offset_stats['errors'])} errors)")
    
    return all_stats


