#!/bin/bash
# Quick setup script for QA with Evidence

set -e

echo "🚀 Setting up QA with Evidence..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install -U pip wheel --quiet
pip install -r requirements.txt --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate the environment:  source .venv/bin/activate"
echo "  2. Run the pipeline:          make all"
echo "  3. Or step by step:"
echo "     - make ingest   # Process corpus"
echo "     - make index    # Build embeddings"
echo "     - make batch    # Run questions"
echo "     - make eval     # Evaluate results"
echo ""
echo "To test a single question:"
echo "  python -m src.cli answer --q \"What is canola?\""
echo ""


