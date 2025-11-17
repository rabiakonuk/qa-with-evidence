# Testing Log

**Date**: November 17, 2025  
**Purpose**: Systematic testing of QA-with-Evidence system  
**Approach**: Test each component, document results, fix issues

---

## Test Plan

### Phase 1: Setup & Dependencies
- [ ] Test 1: Environment setup
- [ ] Test 2: Dependency installation
- [ ] Test 3: File structure verification

### Phase 2: Training/Setup
- [ ] Test 4: Corpus ingestion
- [ ] Test 5: Tagging enrichment
- [ ] Test 6: Offset verification
- [ ] Test 7: Embedding generation
- [ ] Test 8: Index building (FAISS + BM25)
- [ ] Test 9: Artifact verification

### Phase 3: Inference
- [ ] Test 10: Single question (inference.py)
- [ ] Test 11: Batch processing
- [ ] Test 12: Interactive mode
- [ ] Test 13: JSON output format

### Phase 4: Quality Checks
- [ ] Test 14: Unit tests (pytest)
- [ ] Test 15: Offset correctness
- [ ] Test 16: Abstention logic
- [ ] Test 17: Numeric safeguard

### Phase 5: Integration
- [ ] Test 18: Makefile targets
- [ ] Test 19: Docker build
- [ ] Test 20: End-to-end workflow

---

## Test Results

### Test 1: Environment Setup
**Status**: ⏳ In Progress  
**Command**: 
```bash
cd /Users/rabiko/qa-with-evidence
python3 -m venv .venv
source .venv/bin/activate
```
**Expected**: Virtual environment created  
**Actual**:  
**Issues**:  
**Resolution**:

---

*Test results will be logged below as we progress...*

