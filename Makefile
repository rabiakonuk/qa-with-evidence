.PHONY: help install setup infer infer-batch infer-interactive eval test clean all

help:
	@echo "QA with Evidence - Makefile targets:"
	@echo ""
	@echo "═══ Setup (Run Once) ═══"
	@echo "  make install          - Install Python dependencies"
	@echo "  make setup            - Build indices & prepare system (ONE-TIME)"
	@echo ""
	@echo "═══ Inference (Run Many Times) ═══"
	@echo "  make infer            - Answer questions interactively"
	@echo "  make infer-batch      - Process all questions in data/questions.txt"
	@echo "  make infer-question Q='...' - Answer a single question"
	@echo ""
	@echo "═══ Evaluation ═══"
	@echo "  make eval             - Evaluate batch run results"
	@echo "  make test             - Run unit tests"
	@echo ""
	@echo "═══ Maintenance ═══"
	@echo "  make clean            - Remove generated artifacts"
	@echo "  make all              - Run complete pipeline (setup → infer-batch → eval)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make install    # Install dependencies"
	@echo "  2. make setup      # Build indices (ONE-TIME, ~1 min)"
	@echo "  3. make infer      # Start answering questions!"
	@echo ""

install:
	@echo "Installing dependencies..."
	pip install -U pip wheel
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

setup:
	@echo "Running setup (this may take 1-2 minutes)..."
	python setup.py
	@echo "✓ Setup complete! Ready for inference."

infer:
	@echo "Starting interactive Q&A..."
	python inference.py --interactive

infer-batch:
	@echo "Processing batch questions..."
	python inference.py --batch data/questions.txt --output artifacts/run.jsonl

infer-question:
	@test -n "$(Q)" || (echo "Error: Please provide Q='your question'" && exit 1)
	python inference.py --question "$(Q)" --verbose

eval:
	@echo "Evaluating batch run..."
	python -m src.cli eval --run artifacts/run.jsonl

test:
	@echo "Running unit tests..."
	pytest tests/ -v

clean:
	@echo "Cleaning artifacts..."
	rm -rf artifacts/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Cleaned"

all: setup infer-batch eval
	@echo ""
	@echo "✓ Complete pipeline finished!"
	@echo "  Setup: Indices built"
	@echo "  Inference: artifacts/run.jsonl"
	@echo "  Evaluation: artifacts/*.csv"


