# Quick Start Guide

Get the QA-with-Evidence system running in **3 simple steps**.

---

## 🚀 **3-Step Setup**

### **Step 1: Install Dependencies** (30 seconds)

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
make install
```

### **Step 2: Build Indices** (1-2 minutes, **ONE-TIME ONLY**)

```bash
make setup
```

This will:
- ✅ Process 29 agricultural documents (43K+ sentences)
- ✅ Build FAISS index for semantic search
- ✅ Create BM25 index for lexical search
- ✅ Generate metadata database

**You only need to do this ONCE!**

### **Step 3: Start Answering Questions** (instant)

```bash
# Interactive mode
make infer

# Or answer a single question
make infer-question Q="What soil pH is recommended for canola?"

# Or process all 22 questions
make infer-batch
```

---

## 📚 **Usage Examples**

### **Interactive Q&A** (Recommended)

```bash
make infer
```

Then type your questions:
```
Question: What soil pH is recommended for canola?
Question: How deep should corn be planted?
Question: quit
```

### **Single Question**

```bash
# With verbose output
make infer-question Q="What is the optimum seeding depth for canola?"

# Or using inference.py directly
python inference.py --question "What is canola?" --json
```

### **Batch Processing**

```bash
# Process all questions in data/questions.txt
make infer-batch

# Or specify a different file
python inference.py --batch my_questions.txt --output results.jsonl
```

### **Evaluation**

```bash
# After batch processing, evaluate results
make eval
```

---

## 🐳 **Docker Quick Start**

```bash
# Build image
docker-compose build

# Run setup (ONE-TIME)
docker-compose run --rm qa-with-evidence python setup.py

# Interactive inference
docker-compose run --rm qa-with-evidence python inference.py --interactive

# Batch inference
docker-compose run --rm qa-with-evidence python inference.py --batch data/questions.txt
```

---

## 🔍 **Understanding the System**

### **Two-Phase Architecture**

```
┌─────────────────────────────────────────────────────┐
│  PHASE 1: Setup (Run ONCE)                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Input: 29 markdown docs                            │
│  ↓                                                   │
│  1. Sentence splitting (exact offsets)              │
│  2. Tag enrichment (crop + practice)                │
│  3. Embedding generation (384-dim vectors)          │
│  4. FAISS index building                            │
│  5. BM25 index building                             │
│  ↓                                                   │
│  Output: Pre-built indices (artifacts/)             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  PHASE 2: Inference (Run MANY times, FAST)         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  Input: Question                                    │
│  ↓                                                   │
│  1. Load pre-built indices (once)                   │
│  2. Hybrid retrieval (BM25 + dense)                 │
│  3. MMR diversity selection                         │
│  4. Answer assembly                                 │
│  5. Abstention check                                │
│  ↓                                                   │
│  Output: Answer with citations (~400ms)             │
└─────────────────────────────────────────────────────┘
```

### **Why This Separation?**

**Setup Phase** (Run Once):
- ⏱️ Takes 1-2 minutes
- 💾 Builds all indices and embeddings
- 📦 Creates reusable artifacts

**Inference Phase** (Run Many Times):
- ⚡ **Fast**: ~400ms per question
- 🔄 Reuses pre-built indices
- 💻 Loads models into memory once

**This is how production systems work!**

---

## 📊 **Output Format**

### **JSON Schema** (for single question)

```json
{
  "question": "What soil pH is recommended for canola?",
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
      "support_count": 3
    }
  }
}
```

### **Batch Output** (JSONL format)

File `artifacts/run.jsonl` contains one JSON object per line for each question.

---

## 🧪 **Testing**

```bash
# Run unit tests
make test

# Test retrieval
python -m src.cli retrieve --q "What is canola?" --k 10

# Verify setup
ls -lh artifacts/
# Should see: sentences.jsonl, embeddings.npy, faiss_index.bin, meta.sqlite
```

---

## ❓ **Troubleshooting**

### **Problem: "Missing artifacts"**

**Solution**: Run setup first
```bash
make setup
```

### **Problem: "Module not found"**

**Solution**: Activate virtual environment
```bash
source .venv/bin/activate
make install
```

### **Problem: "Slow inference"**

**Check**: Are you loading indices every time?
- ✅ **Good**: `python inference.py --interactive` (loads once)
- ❌ **Bad**: Running `python -m src.cli answer` repeatedly (loads every time)

**Use `inference.py` for fast repeated queries!**

### **Problem: "Out of memory"**

**Solution**: Reduce batch size or use smaller corpus

Current memory usage:
- Setup: ~800MB RAM
- Inference: ~500MB RAM
- Docker: Limit to 4GB

---

## 📈 **Performance**

| Operation | Time | Notes |
|-----------|------|-------|
| Setup (one-time) | 1-2 min | Builds all indices |
| Load models (one-time) | 5-10 sec | Done once per session |
| Single question | ~400ms | After models loaded |
| Batch (22 questions) | ~10 sec | Sequential processing |

**Key Insight**: The setup cost is amortized across many queries!

---

## 🎯 **For Reviewers**

### **Minimal Test** (2 minutes)

```bash
# 1. Setup
make install
make setup

# 2. Test single question
make infer-question Q="What is canola?"

# 3. Done!
```

### **Complete Evaluation** (5 minutes)

```bash
# 1. Setup
make install
make setup

# 2. Run all 22 questions
make infer-batch

# 3. Evaluate
make eval

# 4. Check results
cat artifacts/run.jsonl | jq .
```

### **Interactive Testing**

```bash
make infer
# Try these questions:
# - What soil pH is recommended for canola?
# - How deep should corn be planted?
# - What is the difference between determinate and indeterminate tomatoes?
```

---

## 📝 **Next Steps**

- **Configuration**: Edit `config.yaml` to tune parameters
- **Evaluation**: See `EVALUATION.md` for metrics explanation
- **Architecture**: Read `ARCHITECTURE.md` for design decisions
- **Deployment**: Check `DEPLOYMENT.md` for production setup

---

## 🆘 **Need Help?**

- **Documentation**: See `README.md` for full documentation
- **Architecture**: See `ARCHITECTURE.md` for design decisions
- **Issues**: Check if artifacts exist: `ls -lh artifacts/`

---

**Happy Q&A! 🎉**

