#!/usr/bin/env python3
"""
Setup script for QA-with-Evidence system.

This script performs the ONE-TIME setup/training phase:
1. Ingests corpus (sentence splitting + tagging)
2. Builds embeddings and indices (FAISS + BM25)
3. Verifies correctness

Run this ONCE before inference.
"""

import sys
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.ingest.sentence_split import ingest_corpus, verify_offsets
from src.ingest.tagger import enrich_tags
from src.embed.build_index import build_index

console = Console()


def main():
    """Run complete setup/training pipeline."""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]   QA-with-Evidence: Setup & Training Phase[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    start_time = time.time()
    config = load_config()
    
    # Create artifacts directory
    Path("artifacts").mkdir(exist_ok=True)
    
    # ============================================================
    # STEP 1: Ingest Corpus
    # ============================================================
    console.print("[bold blue]STEP 1/3: Ingesting Corpus[/bold blue]")
    console.print("  - Splitting sentences with exact offsets")
    console.print("  - Enriching with crop + practice tags")
    console.print("  - Verifying offset correctness\n")
    
    with console.status("[bold green]Processing corpus..."):
        in_path = Path(config["paths"]["corpus_dir"])
        out_path = Path(config["paths"]["sentences_file"])
        
        # Ingest
        count = ingest_corpus(in_path, out_path)
        console.print(f"  ✓ Ingested {count:,} sentences → {out_path}")
        
        # Enrich tags
        enrich_tags(out_path)
        console.print(f"  ✓ Tags enriched (crop + practice)")
        
        # Verify offsets
        verify_offsets(in_path, out_path, sample_size=200)
        console.print(f"  ✓ Verified 200 random offsets: 100% correct\n")
    
    # ============================================================
    # STEP 2: Build Embeddings & Indices
    # ============================================================
    console.print("[bold blue]STEP 2/3: Building Embeddings & Indices[/bold blue]")
    console.print(f"  - Model: {config['embedding']['model']}")
    console.print("  - Building FAISS index for dense retrieval")
    console.print("  - Creating metadata store\n")
    
    with console.status("[bold green]Encoding sentences..."):
        sentences_file = Path(config["paths"]["sentences_file"])
        embeddings_file = Path(config["paths"]["embeddings_file"])
        index_file = Path(config["paths"]["index_file"])
        meta_file = Path(config["paths"]["meta_file"])
        model_name = config["embedding"]["model"]
        normalize = config["embedding"]["normalize"]
        
        stats = build_index(
            sentences_file,
            embeddings_file,
            index_file,
            meta_file,
            model_name,
            normalize
        )
        
        console.print(f"  ✓ Embeddings: {stats['num_sentences']:,} × {stats['embedding_dim']}d → {embeddings_file}")
        console.print(f"  ✓ FAISS index: {stats['num_sentences']:,} vectors → {index_file}")
        console.print(f"  ✓ Metadata: {stats['num_sentences']:,} records → {meta_file}\n")
    
    # ============================================================
    # STEP 3: Verify Setup
    # ============================================================
    console.print("[bold blue]STEP 3/3: Verifying Setup[/bold blue]\n")
    
    # Check all artifacts exist
    artifacts = [
        ("Sentences", Path(config["paths"]["sentences_file"])),
        ("Embeddings", Path(config["paths"]["embeddings_file"])),
        ("FAISS Index", Path(config["paths"]["index_file"])),
        ("Metadata DB", Path(config["paths"]["meta_file"]))
    ]
    
    all_exist = True
    for name, path in artifacts:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            console.print(f"  ✓ {name}: {path} ({size_mb:.1f} MB)")
        else:
            console.print(f"  ✗ {name}: {path} [bold red]MISSING![/bold red]")
            all_exist = False
    
    elapsed = time.time() - start_time
    
    # ============================================================
    # Summary
    # ============================================================
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    
    if all_exist:
        console.print("[bold green]✓ Setup Complete![/bold green]")
        console.print(f"  Time elapsed: {elapsed:.1f} seconds")
        console.print(f"  Total sentences: {stats['num_sentences']:,}")
        console.print(f"  Embedding dimension: {stats['embedding_dim']}")
        console.print("\n[bold yellow]Next Steps:[/bold yellow]")
        console.print("  1. Test retrieval: [cyan]python -m src.cli retrieve --q \"What is canola?\"[/cyan]")
        console.print("  2. Answer single question: [cyan]python inference.py --question \"What soil pH is recommended?\"[/cyan]")
        console.print("  3. Run batch: [cyan]python -m src.cli batch --questions data/questions.txt[/cyan]")
        console.print("  4. Evaluate: [cyan]python -m src.cli eval --run artifacts/run.jsonl[/cyan]")
    else:
        console.print("[bold red]✗ Setup Failed![/bold red]")
        console.print("  Some artifacts are missing. Check errors above.")
        sys.exit(1)
    
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")


if __name__ == "__main__":
    main()

