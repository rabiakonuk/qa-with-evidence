# QA with Evidence

A retrieval-based question-answering system that provides answers with exact source evidence and citations. Built for agricultural domain questions with crop-specific corpus.

## Features

- **Exact offset preservation**: All answer sentences maintain precise character offsets to source documents
- **Hybrid retrieval**: Combines BM25 (lexical) and dense (semantic) retrieval
- **Tag-aware boosting**: Query-sensitive boosting based on crop type and agricultural practice
- **MMR diversity selection**: Reduces redundancy while maintaining relevance
- **Numeric safeguard**: Ensures numerical values in answers are grounded in source text
- **Intelligent abstention**: Refuses to answer when confidence is low or evidence is insufficient

## Architecture

```
┌─────────────┐
│   Corpus    │
│  (29 docs)  │
└──────┬──────┘
       │
       ├─────► Sentence Split (exact offsets) ────► sentences.jsonl
       │
       ├─────► Tag Enrichment (crop + practice) ──► enriched sentences
       │
       └─────► Embedding + FAISS Index ──────────► embeddings.npy
                                                    faiss_index.bin
                                                    meta.sqlite

┌─────────────┐
│   Question  │
└──────┬──────┘
       │
       ├─────► BM25 Retrieval (top 50)
       │                    │
       ├─────► Dense Retrieval (top 50)
       │                    │
       └─────► Hybrid Fusion + Tag Boost
                    │
                    ├─────► Reranking (top 20)
                    │
                    ├─────► MMR Selection (3-6 sentences)
                    │
                    ├─────► Numeric Safeguard
                    │
                    └─────► Abstention Check ────► Final Answer
```

## Quickstart

### **3-Step Setup** ⚡

```bash
# 1. Install dependencies (30 seconds)
python3 -m venv .venv
source .venv/bin/activate
make install

# 2. Build indices - ONE-TIME ONLY (1-2 minutes)
make setup

# 3. Start answering questions - FAST (instant)
make infer
```

**That's it!** See `QUICKSTART.md` for detailed guide.

### **Two-Phase Architecture**

This system separates **training** (run once) from **inference** (run many times):

```
┌─────────────────────────────────┐
│  SETUP (Run Once)              │
│  python setup.py               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│  • Ingest corpus               │
│  • Build indices               │
│  • Create embeddings           │
│  Time: ~1-2 minutes            │
└─────────────────────────────────┘
           ↓
┌─────────────────────────────────┐
│  INFERENCE (Run Many Times)    │
│  python inference.py           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│  • Load pre-built indices      │
│  • Answer questions            │
│  Time: ~400ms per question     │
└─────────────────────────────────┘
```

### **Usage Examples**

```bash
# Interactive Q&A
make infer

# Single question
make infer-question Q="What is canola?"

# Batch processing (22 questions)
make infer-batch

# Evaluate results
make eval
```

### **Docker Quick Start**

```bash
docker-compose build
docker-compose run --rm qa-with-evidence python setup.py
docker-compose run --rm qa-with-evidence python inference.py --interactive
```

## Pipeline Steps

Once environment is set up (Docker or local), run the pipeline:

### 1. Ingest Corpus

Process markdown documents into sentences with exact offsets:

```bash
# Docker
docker-compose run --rm qa-with-evidence python -m src.cli ingest

# Local
python -m src.cli ingest --in data/corpus_raw --out artifacts/sentences.jsonl
```

This will:
- Extract sentences from all markdown files
- Preserve exact character offsets
- Parse YAML frontmatter for metadata
- Enrich with crop and practice tags
- Verify offset correctness (random sample)

### 2. Build Index

Create embeddings and search indices:

```bash
# Docker
docker-compose run --rm qa-with-evidence python -m src.cli build-index

# Local
python -m src.cli build-index --sentences artifacts/sentences.jsonl
```

This will:
- Generate sentence embeddings using `all-MiniLM-L6-v2`
- Build FAISS index for dense retrieval
- Create SQLite metadata store
- Save artifacts for fast loading

### 3. Run Questions

Process batch questions:

```bash
# Docker
docker-compose run --rm qa-with-evidence python -m src.cli batch

# Local
python -m src.cli batch --questions data/questions.txt --out artifacts/run.jsonl
```

Or answer single question:

```bash
# Docker
docker-compose run --rm qa-with-evidence \
  python -m src.cli answer --q "What soil pH is recommended for canola?"

# Local
python -m src.cli answer --q "What soil pH is recommended for canola?"
```

### 4. Evaluate

Compute metrics on a run:

```bash
# Docker
docker-compose run --rm qa-with-evidence python -m src.cli eval

# Local
python -m src.cli eval --run artifacts/run.jsonl
```

Outputs:
- Answer rate (answered vs abstained)
- Redundancy reduction (before/after MMR)
- Coverage diversity (unique crop×practice pairs)
- Offset validation (100% correctness check)

## Configuration

All parameters are in `config.yaml`:

| Section | Parameter | Default | Description |
|---------|-----------|---------|-------------|
| **paths** | `corpus_dir` | `data/corpus_raw` | Source markdown files |
| | `sentences_file` | `artifacts/sentences.jsonl` | Processed sentences |
| | `embeddings_file` | `artifacts/embeddings.npy` | Sentence embeddings |
| | `index_file` | `artifacts/faiss_index.bin` | FAISS index |
| | `meta_file` | `artifacts/meta.sqlite` | Metadata store |
| **retrieval** | `bm25_topk` | 50 | BM25 candidates |
| | `dense_topk` | 50 | Dense candidates |
| | `alpha_lexical` | 0.40 | BM25 weight in fusion |
| | `tag_boost_crop` | 0.08 | Boost for matching crop |
| | `tag_boost_practice` | 0.05 | Boost for matching practice |
| **selection** | `rerank_topk` | 20 | Reranking cutoff |
| | `mmr_lambda` | 0.70 | MMR relevance weight |
| | `max_sim_threshold` | 0.82 | Max similarity to selected |
| | `min_support` | 3 | Min sentences to answer |
| | `abstain_score_thresh` | 0.35 | Min retrieval score |
| **embedding** | `model` | `all-MiniLM-L6-v2` | Sentence transformer |
| | `normalize` | `true` | L2-normalize embeddings |

## Output Schema

Each answer in `run.jsonl` has this structure:

```json
{
  "question_id": "1",
  "question": "What soil pH band is commonly recommended for canola and tomato?",
  "abstained": false,
  "answer_sentences": [
    {
      "text": "Canola grows best at pH 6.0-7.0.",
      "doc_id": "canola/canola crop guide.md",
      "start": 1234,
      "end": 1268,
      "tags": {
        "crop": "canola",
        "practice": "soil"
      }
    }
  ],
  "final_answer": "Canola grows best at pH 6.0-7.0.",
  "run_notes": {
    "retriever": "hybrid_bm25_dense",
    "k_initial": 73,
    "rerank_topk": 20,
    "decision": ["answered"],
    "scores": {
      "max_retrieval": 0.742,
      "support_count": 3,
      "redundancy_before": 0.65,
      "redundancy_after": 0.31
    }
  }
}
```

## CLI Commands

```bash
# Ingest corpus
python -m src.cli ingest [--in DIR] [--out FILE]

# Build index
python -m src.cli build-index [--sentences FILE]

# Test retrieval
python -m src.cli retrieve --q "QUESTION" [--k NUM]

# Answer single question
python -m src.cli answer --q "QUESTION"

# Batch processing
python -m src.cli batch [--questions FILE] [--out FILE]

# Evaluate run
python -m src.cli eval [--run FILE]
```

## Testing

Run unit tests:

```bash
pytest tests/ -v
```

Test coverage:
- Offset exactness and round-trip verification
- Numeric safeguard (passing and failing cases)
- MMR diversity properties
- Determinism of all components

## Design Principles

### 1. Exact Offsets
Every answer sentence maintains `(start, end)` byte offsets into the original raw markdown. No whitespace normalization or text editing before computing offsets. This enables:
- Perfect reproducibility
- Citation verification
- Confidence in evidence provenance

### 2. Determinism
All components are deterministic:
- Sentence splitting: regex-based, no ML
- Tagging: keyword matching
- Retrieval: same inputs → same outputs
- MMR: greedy algorithm, stable order

### 3. Conservative Answering
Multiple safeguards prevent hallucination:
- Numeric safeguard: reject if numbers aren't in sources
- Score threshold: reject if retrieval confidence low
- Support count: reject if too few supporting sentences
- Abstention is better than incorrect answers

### 4. Transparency
Every answer includes:
- Full source sentences with exact offsets
- Retrieval and selection scores
- Decision rationale (for abstentions)
- Redundancy metrics

## Performance

Expected metrics on agricultural corpus (29 docs, ~2000 sentences):

- **Answer rate**: 70-85% (depending on threshold)
- **Redundancy reduction**: ≥20% (MMR vs naïve top-k)
- **Offset verification**: 100% exact match
- **Indexing time**: ~30 seconds (on CPU)
- **Query time**: ~1-2 seconds per question

## Troubleshooting

**Low answer rate?**
- Reduce `abstain_score_thresh` (e.g., 0.32 → 0.28)
- Increase `rerank_topk` (e.g., 20 → 30)
- Check if corpus covers question topics

**Too much redundancy?**
- Increase `max_sim_threshold` (e.g., 0.82 → 0.85)
- Decrease `mmr_lambda` (more diversity weight)

**Offset mismatches?**
- Ensure no text preprocessing before ingestion
- Check for encoding issues (use UTF-8)
- Verify regex doesn't delete/insert characters

## Directory Structure

```
qa-with-evidence/
├── config.yaml           # Configuration
├── requirements.txt      # Dependencies
├── README.md            # This file
├── Makefile             # Convenience targets
├── data/
│   ├── corpus_raw/      # Input markdown files
│   │   ├── canola/
│   │   ├── corn/
│   │   ├── tomato/
│   │   └── wheat/
│   └── questions.txt    # Questions (one per line)
├── artifacts/           # Generated files
│   ├── sentences.jsonl
│   ├── embeddings.npy
│   ├── faiss_index.bin
│   ├── meta.sqlite
│   ├── run.jsonl
│   └── *.csv           # Evaluation reports
├── src/
│   ├── ingest/         # Sentence splitting & tagging
│   ├── embed/          # Embedding & indexing
│   ├── retrieve/       # BM25, dense, hybrid, MMR
│   ├── answer/         # Assembly & abstention
│   ├── eval/           # Evaluation scripts
│   ├── utils/          # Config loader
│   └── cli.py          # Command-line interface
└── tests/              # Unit tests
```

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.


