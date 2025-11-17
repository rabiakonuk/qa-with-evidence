# GitHub Upload Guide

**Repository**: qa-with-evidence  
**Email**: r.knk.45@gmail.com  
**Date**: November 17, 2025

---

## Quick Setup (5 Minutes)

### Step 1: Initialize Git Repository

```bash
cd /Users/rabiko/qa-with-evidence

# Initialize git (if not already done)
git init

# Configure user for this repo
git config user.email "r.knk.45@gmail.com"
git config user.name "Your Name"  # Replace with your name

# Check configuration
git config user.email
git config user.name
```

### Step 2: Create .gitignore

```bash
# .gitignore is already present, verify it includes:
cat .gitignore
```

Should include:
- `__pycache__/`
- `.venv/`
- `artifacts/` (keep .gitkeep)
- `.DS_Store`
- `*.pyc`

### Step 3: Stage All Files

```bash
# Add all files
git add .

# Check what will be committed
git status

# Create first commit
git commit -m "Initial commit: QA-with-Evidence system for Doktar case study

- Evidence-based QA with exact character offsets
- Hybrid retrieval (BM25 + dense semantic)
- MMR diversity selection
- Clean training/inference separation
- Production-ready with Docker
- Comprehensive testing and documentation"
```

### Step 4: Create GitHub Repository

**Option A: Via GitHub Web UI** (Recommended)

1. Go to https://github.com/
2. Sign in with `r.knk.45@gmail.com`
3. Click "+" → "New repository"
4. Repository name: `qa-with-evidence`
5. Description: `Evidence-based QA system with exact citations for agricultural domain (Doktar ML Engineer Case Study)`
6. Visibility: **Private** (for case study submission)
7. **DO NOT** check "Initialize with README" (we already have one)
8. Click "Create repository"

**Option B: Via GitHub CLI** (if installed)

```bash
# Install GitHub CLI if needed
# brew install gh  # macOS

# Authenticate
gh auth login

# Create repository
gh repo create qa-with-evidence \
  --private \
  --description "Evidence-based QA system with exact citations for agricultural domain" \
  --source=.
```

### Step 5: Connect and Push

After creating the repo on GitHub, you'll see a URL like:
`https://github.com/YOUR_USERNAME/qa-with-evidence.git`

```bash
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/qa-with-evidence.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## What Gets Uploaded

### ✅ Included (Critical Files)

**Documentation**:
- ✅ README.md
- ✅ QUICKSTART.md
- ✅ ARCHITECTURE.md
- ✅ DEPLOYMENT.md
- ✅ SUBMISSION.md
- ✅ TRAIN_VS_INFER.md
- ✅ TESTING_COMPLETE.md
- ✅ IMPLEMENTATION_SUMMARY.md
- ✅ BUGS_FOUND.md

**Code**:
- ✅ src/ (all modules)
- ✅ tests/ (all tests)
- ✅ setup.py
- ✅ inference.py

**Configuration**:
- ✅ config.yaml
- ✅ requirements.txt
- ✅ Dockerfile
- ✅ docker-compose.yml
- ✅ Makefile

**Data**:
- ✅ data/corpus_raw/ (29 documents)
- ✅ data/questions.txt (22 questions)

### ❌ Excluded (Generated/Local Files)

- ❌ `.venv/` (virtual environment)
- ❌ `artifacts/` (generated during setup)
- ❌ `__pycache__/` (Python cache)
- ❌ `.DS_Store` (macOS files)
- ❌ `*.pyc` (compiled Python)

**Note**: Artifacts directory will be created during setup. The `.gitkeep` file ensures the directory structure is tracked.

---

## Verify .gitignore

Create/update `.gitignore` if needed:

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual Environment
.venv/
venv/
ENV/
env/

# Artifacts (generated during setup)
artifacts/*
!artifacts/.gitkeep

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
EOF
```

---

## Repository Structure on GitHub

```
qa-with-evidence/
├── README.md                      # Main documentation
├── QUICKSTART.md                  # 3-step setup guide
├── ARCHITECTURE.md                # Technical design
├── DEPLOYMENT.md                  # Production deployment
├── SUBMISSION.md                  # For reviewers
├── TRAIN_VS_INFER.md             # Architecture explanation
├── TESTING_COMPLETE.md           # Test results
├── BUGS_FOUND.md                 # Issues found
│
├── setup.py                       # Training/setup script
├── inference.py                   # Fast inference script
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Orchestration
├── .dockerignore                  # Docker build optimization
├── Makefile                       # Build automation
├── config.yaml                    # Configuration
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
│
├── src/                           # Source code
│   ├── cli.py
│   ├── ingest/
│   ├── embed/
│   ├── retrieve/
│   ├── answer/
│   ├── eval/
│   └── utils/
│
├── tests/                         # Unit tests
│   ├── test_offsets.py
│   ├── test_numeric_safeguard.py
│   ├── test_mmr.py
│   └── test_determinism.py
│
├── data/                          # Input data
│   ├── corpus_raw/
│   │   ├── canola/
│   │   ├── corn/
│   │   ├── tomato/
│   │   └── wheat/
│   └── questions.txt
│
└── artifacts/                     # Generated files (empty on GitHub)
    └── .gitkeep
```

---

## Post-Upload Verification

### 1. Verify on GitHub

```bash
# Open repository in browser
open "https://github.com/YOUR_USERNAME/qa-with-evidence"
```

Check:
- ✅ README displays correctly
- ✅ All source files present
- ✅ Documentation files visible
- ✅ Data files uploaded
- ✅ No artifacts/ content (only .gitkeep)
- ✅ No .venv/ directory

### 2. Test Clone

```bash
# Clone to a different directory to verify
cd /tmp
git clone https://github.com/YOUR_USERNAME/qa-with-evidence.git
cd qa-with-evidence

# Verify structure
ls -la

# Quick test
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python setup.py  # Should work!
```

---

## Share Repository

### For Doktar Submission

**Option 1**: Add Doktar reviewers as collaborators
1. Go to repository Settings → Collaborators
2. Add reviewer email addresses
3. They get read access to private repo

**Option 2**: Share access token/link
1. Generate personal access token
2. Share repo URL with token

**Option 3**: Make public temporarily
```bash
# Via web UI: Settings → General → Change visibility → Public
```

### Repository URL Format

```
Private: https://github.com/YOUR_USERNAME/qa-with-evidence
Public:  https://github.com/YOUR_USERNAME/qa-with-evidence
Clone:   git@github.com:YOUR_USERNAME/qa-with-evidence.git
```

---

## Update Files Before Push (Optional)

### Add GitHub-specific Files

**1. LICENSE** (if you want to add one):
```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy...
EOF
```

**2. .github/workflows/test.yml** (CI/CD - optional):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

---

## Troubleshooting

### Issue: "Permission denied (publickey)"

**Solution**: Use HTTPS instead of SSH
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/qa-with-evidence.git
```

### Issue: "Repository size too large"

Check size:
```bash
du -sh .
git count-objects -vH
```

If artifacts were accidentally added:
```bash
git rm -r --cached artifacts/
git commit -m "Remove artifacts from git"
```

### Issue: "Authentication failed"

**Solution 1**: Use Personal Access Token
1. GitHub Settings → Developer settings → Personal access tokens
2. Generate token with `repo` scope
3. Use token as password when pushing

**Solution 2**: Use GitHub CLI
```bash
gh auth login
gh repo push
```

---

## Complete Command Sequence

```bash
cd /Users/rabiko/qa-with-evidence

# 1. Configure Git
git config user.email "r.knk.45@gmail.com"
git config user.name "Your Name"

# 2. Initialize and commit
git init
git add .
git commit -m "Initial commit: QA-with-Evidence for Doktar case study"

# 3. Create repo on GitHub (via web UI)
# https://github.com/new

# 4. Connect and push
git remote add origin https://github.com/YOUR_USERNAME/qa-with-evidence.git
git branch -M main
git push -u origin main

# 5. Verify
open "https://github.com/YOUR_USERNAME/qa-with-evidence"
```

---

## Security Notes

### Before Pushing, Verify:

```bash
# Check for secrets/keys
grep -r "API_KEY\|SECRET\|PASSWORD" . --exclude-dir=.venv --exclude-dir=.git

# Check for large files
find . -type f -size +10M

# Verify .gitignore working
git status --ignored
```

### Sensitive Files to Exclude:
- ❌ API keys
- ❌ Credentials
- ❌ Private data
- ❌ Large model files (>100MB)

Our repo is clean - no secrets! ✅

---

## Next Steps After Upload

1. ✅ Verify repository on GitHub
2. ✅ Add description and topics
3. ✅ Update README if needed
4. ✅ Share URL with Doktar
5. ✅ Consider adding:
   - Repository topics: `question-answering`, `ml-engineering`, `retrieval`, `nlp`
   - About section
   - Website link (if any)

---

**Ready to upload!** 🚀

Just run the commands above and your repository will be on GitHub, ready for submission to Doktar.

