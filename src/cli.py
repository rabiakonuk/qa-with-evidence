"""Command-line interface for QA with evidence system."""
import typer
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from src.utils.config import load_config
from src.ingest.sentence_split import ingest_corpus, verify_offsets
from src.ingest.tagger import enrich_tags
from src.embed.build_index import build_index
from src.retrieve.bm25 import BM25Retriever
from src.retrieve.dense import DenseRetriever
from src.retrieve.hybrid import HybridRetriever
from src.retrieve.diversity import DiversitySelector
from src.answer.assemble import assemble_answer, format_answer_with_citations
from src.answer.abstain import make_decision
from sentence_transformers import SentenceTransformer


app = typer.Typer()
console = Console()


@app.command()
def ingest(
    in_dir: str = typer.Option("data/corpus_raw", help="Input directory with markdown files"),
    out: str = typer.Option("artifacts/sentences.jsonl", help="Output JSONL file")
):
    """Ingest corpus: sentence segmentation with exact offsets."""
    console.print(f"[bold blue]Ingesting corpus from {in_dir}[/bold blue]")
    
    in_path = Path(in_dir)
    out_path = Path(out)
    
    count = ingest_corpus(in_path, out_path)
    console.print(f"[bold green]✓ Ingested {count} sentences to {out}[/bold green]")
    
    # Auto-tag
    console.print("[bold blue]Enriching tags...[/bold blue]")
    enrich_tags(out_path)
    console.print("[bold green]✓ Tags enriched[/bold green]")
    
    # Verify offsets
    console.print("[bold blue]Verifying offsets...[/bold blue]")
    verify_offsets(in_path, out_path, sample_size=200)


@app.command()
def build_index_cmd(
    sentences: str = typer.Option("artifacts/sentences.jsonl", help="Input sentences JSONL")
):
    """Build embeddings, FAISS index, and metadata store."""
    console.print("[bold blue]Building index...[/bold blue]")
    
    config = load_config()
    
    sentences_file = Path(sentences)
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
    
    console.print(f"[bold green]✓ Index built: {stats['num_sentences']} sentences, "
                  f"dim={stats['embedding_dim']}[/bold green]")


@app.command()
def retrieve(
    q: str = typer.Option(..., help="Query string"),
    k: int = typer.Option(10, help="Number of results to show")
):
    """Test retrieval on a single query."""
    console.print(f"[bold blue]Query:[/bold blue] {q}\n")
    
    config = load_config()
    
    # Load retrievers
    console.print("Loading retrievers...")
    bm25 = BM25Retriever(Path(config["paths"]["sentences_file"]))
    dense = DenseRetriever(
        Path(config["paths"]["index_file"]),
        config["embedding"]["model"],
        config["embedding"]["normalize"]
    )
    hybrid = HybridRetriever(
        bm25,
        dense,
        Path(config["paths"]["meta_file"]),
        config["retrieval"]["alpha_lexical"],
        config["retrieval"]["tag_boost_crop"],
        config["retrieval"]["tag_boost_practice"]
    )
    
    # Retrieve
    results = hybrid.retrieve(
        q,
        config["retrieval"]["bm25_topk"],
        config["retrieval"]["dense_topk"]
    )
    
    # Display top k
    table = Table(title=f"Top {k} Results")
    table.add_column("Rank", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Crop", style="yellow")
    table.add_column("Practice", style="magenta")
    table.add_column("Text", style="white")
    
    for i, (sent_id, score, meta) in enumerate(results[:k], 1):
        text_preview = meta["text"][:100] + "..." if len(meta["text"]) > 100 else meta["text"]
        table.add_row(
            str(i),
            f"{score:.3f}",
            meta["crop"],
            meta["practice"],
            text_preview
        )
    
    console.print(table)


@app.command()
def answer(
    q: str = typer.Option(..., help="Question to answer")
):
    """Answer a single question and output JSON."""
    config = load_config()
    
    # Load all components
    bm25 = BM25Retriever(Path(config["paths"]["sentences_file"]))
    dense = DenseRetriever(
        Path(config["paths"]["index_file"]),
        config["embedding"]["model"],
        config["embedding"]["normalize"]
    )
    hybrid = HybridRetriever(
        bm25,
        dense,
        Path(config["paths"]["meta_file"]),
        config["retrieval"]["alpha_lexical"],
        config["retrieval"]["tag_boost_crop"],
        config["retrieval"]["tag_boost_practice"]
    )
    
    model = SentenceTransformer(config["embedding"]["model"])
    selector = DiversitySelector(
        model,
        config["selection"]["mmr_lambda"],
        config["selection"]["max_sim_threshold"],
        config["selection"]["min_support"],
        max_support=6
    )
    
    # Retrieve
    candidates = hybrid.retrieve(
        q,
        config["retrieval"]["bm25_topk"],
        config["retrieval"]["dense_topk"]
    )
    
    # Get max score
    max_score = candidates[0][1] if candidates else 0.0
    
    # Select diverse sentences
    selected, metrics = selector.select(
        q,
        candidates,
        config["selection"]["rerank_topk"]
    )
    
    # Assemble answer
    answer_data = format_answer_with_citations(selected)
    
    # Make decision
    decision = make_decision(
        q,
        selected,
        max_score,
        metrics,
        config,
        answer_data["is_valid"],
        answer_data["validation_reason"]
    )
    
    # Build output
    output = {
        "question": q,
        "abstained": decision["abstained"],
        "answer_sentences": answer_data["answer_sentences"],
        "final_answer": answer_data["final_answer"] if not decision["abstained"] else "",
        "run_notes": {
            "retriever": "hybrid_bm25_dense",
            "k_initial": len(candidates),
            "rerank_topk": config["selection"]["rerank_topk"],
            "decision": decision["reasons"] if decision["abstained"] else ["answered"],
            "scores": decision["scores"]
        }
    }
    
    # Print JSON
    print(json.dumps(output, indent=2, ensure_ascii=False))


@app.command()
def batch(
    questions: str = typer.Option("data/questions.txt", help="Input questions file"),
    out: str = typer.Option("artifacts/run.jsonl", help="Output JSONL file")
):
    """Run batch processing on all questions."""
    console.print(f"[bold blue]Processing questions from {questions}[/bold blue]")
    
    config = load_config()
    
    # Load questions
    questions_path = Path(questions)
    question_list = []
    with open(questions_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if line:
                # Support format: "id\tquestion" or just "question"
                if '\t' in line:
                    qid, qtext = line.split('\t', 1)
                else:
                    qid = str(i)
                    qtext = line
                question_list.append((qid, qtext))
    
    console.print(f"Loaded {len(question_list)} questions")
    
    # Load all components
    console.print("Loading retrieval components...")
    bm25 = BM25Retriever(Path(config["paths"]["sentences_file"]))
    dense = DenseRetriever(
        Path(config["paths"]["index_file"]),
        config["embedding"]["model"],
        config["embedding"]["normalize"]
    )
    hybrid = HybridRetriever(
        bm25,
        dense,
        Path(config["paths"]["meta_file"]),
        config["retrieval"]["alpha_lexical"],
        config["retrieval"]["tag_boost_crop"],
        config["retrieval"]["tag_boost_practice"]
    )
    
    model = SentenceTransformer(config["embedding"]["model"])
    selector = DiversitySelector(
        model,
        config["selection"]["mmr_lambda"],
        config["selection"]["max_sim_threshold"],
        config["selection"]["min_support"],
        max_support=6
    )
    
    # Process each question
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    with console.status("[bold green]Processing questions...") as status:
        for qid, qtext in question_list:
            status.update(f"[bold green]Processing Q{qid}: {qtext[:50]}...")
            
            # Retrieve
            candidates = hybrid.retrieve(
                qtext,
                config["retrieval"]["bm25_topk"],
                config["retrieval"]["dense_topk"]
            )
            
            # Get max score
            max_score = candidates[0][1] if candidates else 0.0
            
            # Select diverse sentences
            selected, metrics = selector.select(
                qtext,
                candidates,
                config["selection"]["rerank_topk"]
            )
            
            # Assemble answer
            answer_data = format_answer_with_citations(selected)
            
            # Make decision
            decision = make_decision(
                qtext,
                selected,
                max_score,
                metrics,
                config,
                answer_data["is_valid"],
                answer_data["validation_reason"]
            )
            
            # Build output
            output = {
                "question_id": qid,
                "question": qtext,
                "abstained": decision["abstained"],
                "answer_sentences": answer_data["answer_sentences"],
                "final_answer": answer_data["final_answer"] if not decision["abstained"] else "",
                "run_notes": {
                    "retriever": "hybrid_bm25_dense",
                    "k_initial": len(candidates),
                    "rerank_topk": config["selection"]["rerank_topk"],
                    "decision": decision["reasons"] if decision["abstained"] else ["answered"],
                    "scores": decision["scores"]
                }
            }
            
            results.append(output)
    
    # Write results
    with open(out_path, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    # Print summary
    answered = sum(1 for r in results if not r["abstained"])
    console.print(f"\n[bold green]✓ Processed {len(results)} questions[/bold green]")
    console.print(f"  Answered: {answered}")
    console.print(f"  Abstained: {len(results) - answered}")
    console.print(f"  Output: {out}")


@app.command()
def eval(
    run: str = typer.Option("artifacts/run.jsonl", help="Run JSONL file to evaluate")
):
    """Evaluate a batch run."""
    from src.eval.run_eval import evaluate_run
    
    console.print(f"[bold blue]Evaluating {run}[/bold blue]")
    
    run_path = Path(run)
    config = load_config()
    
    stats = evaluate_run(run_path, Path(config["paths"]["corpus_dir"]))
    
    # Print summary
    console.print("\n[bold green]Evaluation Results[/bold green]")
    console.print(f"  Total questions: {stats['total_questions']}")
    console.print(f"  Answered: {stats['answered']} ({stats['answer_rate']:.1f}%)")
    console.print(f"  Abstained: {stats['abstained']}")
    console.print(f"  Redundancy reduction: {stats['redundancy_reduction']:.1f}%")
    console.print(f"  Offset validation: {stats['offset_pass_rate']:.1f}% passed")


if __name__ == "__main__":
    app()


