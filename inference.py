#!/usr/bin/env python3
"""
Inference script for QA-with-Evidence system.

This script performs FAST inference on pre-built indices.
Run setup.py FIRST to build indices.

Usage:
    # Single question
    python inference.py --question "What soil pH is recommended for canola?"
    
    # Batch processing
    python inference.py --batch data/questions.txt --output artifacts/run.jsonl
    
    # Interactive mode
    python inference.py --interactive
"""

import sys
import json
import argparse
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.retrieve.bm25 import BM25Retriever
from src.retrieve.dense import DenseRetriever
from src.retrieve.hybrid import HybridRetriever
from src.retrieve.diversity import DiversitySelector
from src.answer.assemble import format_answer_with_citations
from src.answer.abstain import make_decision
from sentence_transformers import SentenceTransformer

console = Console()


class QASystem:
    """
    Fast QA inference system with pre-loaded indices.
    
    This class loads all models and indices ONCE and keeps them in memory
    for fast repeated inference.
    """
    
    def __init__(self):
        """Initialize system by loading all components."""
        console.print("[bold blue]Loading QA System...[/bold blue]")
        
        self.config = load_config()
        
        # Check artifacts exist
        self._verify_artifacts()
        
        # Load retrievers
        with console.status("[cyan]Loading BM25 index..."):
            self.bm25 = BM25Retriever(Path(self.config["paths"]["sentences_file"]))
        console.print("  ✓ BM25 loaded")
        
        with console.status("[cyan]Loading dense index..."):
            self.dense = DenseRetriever(
                Path(self.config["paths"]["index_file"]),
                self.config["embedding"]["model"],
                self.config["embedding"]["normalize"]
            )
        console.print("  ✓ Dense retriever loaded")
        
        with console.status("[cyan]Initializing hybrid retriever..."):
            self.hybrid = HybridRetriever(
                self.bm25,
                self.dense,
                Path(self.config["paths"]["meta_file"]),
                self.config["retrieval"]["alpha_lexical"],
                self.config["retrieval"]["tag_boost_crop"],
                self.config["retrieval"]["tag_boost_practice"]
            )
        console.print("  ✓ Hybrid retriever ready")
        
        with console.status("[cyan]Loading embedding model for MMR..."):
            self.model = SentenceTransformer(self.config["embedding"]["model"])
            self.selector = DiversitySelector(
                self.model,
                self.config["selection"]["mmr_lambda"],
                self.config["selection"]["max_sim_threshold"],
                self.config["selection"]["min_support"],
                max_support=6
            )
        console.print("  ✓ Diversity selector ready")
        
        console.print("[bold green]✓ System loaded and ready for inference![/bold green]\n")
    
    def _verify_artifacts(self):
        """Verify all required artifacts exist."""
        artifacts = [
            Path(self.config["paths"]["sentences_file"]),
            Path(self.config["paths"]["embeddings_file"]),
            Path(self.config["paths"]["index_file"]),
            Path(self.config["paths"]["meta_file"])
        ]
        
        missing = [str(a) for a in artifacts if not a.exists()]
        
        if missing:
            console.print("[bold red]✗ Missing artifacts![/bold red]")
            console.print("  Please run setup.py first:")
            console.print("    [cyan]python setup.py[/cyan]\n")
            console.print("  Missing files:")
            for m in missing:
                console.print(f"    - {m}")
            sys.exit(1)
    
    def answer(self, question: str, verbose: bool = False) -> dict:
        """
        Answer a single question.
        
        Args:
            question: The question text
            verbose: If True, print detailed progress
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        if verbose:
            console.print(f"\n[bold blue]Question:[/bold blue] {question}\n")
        
        # Retrieve candidates
        if verbose:
            console.print("  [cyan]Retrieving candidates...[/cyan]")
        
        candidates = self.hybrid.retrieve(
            question,
            self.config["retrieval"]["bm25_topk"],
            self.config["retrieval"]["dense_topk"]
        )
        
        max_score = candidates[0][1] if candidates else 0.0
        
        if verbose:
            console.print(f"  [cyan]Found {len(candidates)} candidates (max score: {max_score:.3f})[/cyan]")
        
        # Select diverse sentences via MMR
        if verbose:
            console.print("  [cyan]Selecting diverse sentences (MMR)...[/cyan]")
        
        selected, metrics = self.selector.select(
            question,
            candidates,
            self.config["selection"]["rerank_topk"]
        )
        
        if verbose:
            console.print(f"  [cyan]Selected {len(selected)} sentences[/cyan]")
        
        # Assemble answer
        answer_data = format_answer_with_citations(selected)
        
        # Make abstention decision
        decision = make_decision(
            question,
            selected,
            max_score,
            metrics,
            self.config,
            answer_data["is_valid"],
            answer_data["validation_reason"]
        )
        
        # Build output
        output = {
            "question": question,
            "abstained": decision["abstained"],
            "answer_sentences": answer_data["answer_sentences"],
            "final_answer": answer_data["final_answer"] if not decision["abstained"] else "",
            "run_notes": {
                "retriever": "hybrid_bm25_dense",
                "k_initial": len(candidates),
                "rerank_topk": self.config["selection"]["rerank_topk"],
                "decision": decision["reasons"] if decision["abstained"] else ["answered"],
                "scores": decision["scores"]
            }
        }
        
        return output
    
    def answer_batch(self, questions_file: Path, output_file: Path):
        """
        Answer multiple questions from a file.
        
        Args:
            questions_file: Path to questions file (one per line)
            output_file: Path to output JSONL file
        """
        # Load questions
        questions = []
        with open(questions_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    questions.append((str(i), line))
        
        console.print(f"[bold blue]Processing {len(questions)} questions...[/bold blue]\n")
        
        results = []
        
        with console.status("[bold green]Answering questions...") as status:
            for qid, qtext in questions:
                status.update(f"[bold green]Q{qid}: {qtext[:60]}...")
                
                output = self.answer(qtext, verbose=False)
                output["question_id"] = qid
                results.append(output)
        
        # Write results
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        # Print summary
        answered = sum(1 for r in results if not r["abstained"])
        abstained = len(results) - answered
        
        console.print(f"\n[bold green]✓ Batch processing complete![/bold green]")
        console.print(f"  Total: {len(results)} questions")
        console.print(f"  Answered: {answered} ({answered/len(results)*100:.1f}%)")
        console.print(f"  Abstained: {abstained} ({abstained/len(results)*100:.1f}%)")
        console.print(f"  Output: {output_file}\n")
    
    def interactive(self):
        """Run interactive Q&A session."""
        console.print(Panel.fit(
            "[bold cyan]Interactive QA Mode[/bold cyan]\n"
            "Type your questions, or 'quit' to exit.",
            border_style="cyan"
        ))
        
        while True:
            try:
                question = Prompt.ask("\n[bold yellow]Question[/bold yellow]")
                
                if question.lower() in ['quit', 'exit', 'q']:
                    console.print("\n[cyan]Goodbye![/cyan]\n")
                    break
                
                if not question.strip():
                    continue
                
                # Answer
                result = self.answer(question, verbose=False)
                
                # Display result
                if result["abstained"]:
                    console.print(Panel(
                        f"[bold red]Abstained[/bold red]\n\n"
                        f"Reasons: {', '.join(result['run_notes']['decision'])}",
                        title="Answer",
                        border_style="red"
                    ))
                else:
                    # Build answer text with citations
                    answer_text = result["final_answer"]
                    
                    # Create citations table
                    table = Table(title="Evidence Citations", show_header=True, header_style="bold cyan")
                    table.add_column("#", style="cyan", width=3)
                    table.add_column("Document", style="yellow")
                    table.add_column("Crop", style="green", width=10)
                    table.add_column("Practice", style="magenta", width=12)
                    table.add_column("Text", style="white")
                    
                    for i, sent in enumerate(result["answer_sentences"], 1):
                        text_preview = sent["text"][:80] + "..." if len(sent["text"]) > 80 else sent["text"]
                        table.add_column(
                            str(i),
                            sent["doc_id"].split("/")[-1],
                            sent["tags"].get("crop", "?"),
                            sent["tags"].get("practice", "?"),
                            text_preview
                        )
                    
                    console.print(Panel(
                        answer_text,
                        title="[bold green]Answer[/bold green]",
                        border_style="green"
                    ))
                    console.print(table)
                
            except KeyboardInterrupt:
                console.print("\n\n[cyan]Interrupted. Goodbye![/cyan]\n")
                break
            except Exception as e:
                console.print(f"\n[bold red]Error:[/bold red] {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="QA-with-Evidence Inference System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single question
  python inference.py --question "What soil pH is recommended for canola?"
  
  # Batch processing
  python inference.py --batch data/questions.txt --output artifacts/run.jsonl
  
  # Interactive mode
  python inference.py --interactive
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--question", "-q",
        type=str,
        help="Single question to answer"
    )
    group.add_argument(
        "--batch", "-b",
        type=str,
        help="Path to questions file (one per line)"
    )
    group.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive Q&A mode"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="artifacts/run.jsonl",
        help="Output file for batch mode (default: artifacts/run.jsonl)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON (for single question mode)"
    )
    
    args = parser.parse_args()
    
    # Initialize system (loads all models/indices)
    system = QASystem()
    
    # Run appropriate mode
    if args.question:
        # Single question mode
        result = system.answer(args.question, verbose=args.verbose)
        
        if args.json:
            # Raw JSON output
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            # Pretty output
            if result["abstained"]:
                console.print(f"\n[bold red]Abstained:[/bold red] {', '.join(result['run_notes']['decision'])}\n")
            else:
                console.print(f"\n[bold green]Answer:[/bold green]\n{result['final_answer']}\n")
                console.print(f"[dim]({len(result['answer_sentences'])} evidence sentences)[/dim]\n")
    
    elif args.batch:
        # Batch mode
        system.answer_batch(Path(args.batch), Path(args.output))
    
    elif args.interactive:
        # Interactive mode
        system.interactive()


if __name__ == "__main__":
    main()

