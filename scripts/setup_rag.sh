#!/bin/bash
# RAG Setup Script for Docker Desktop
# Installs dependencies and prepares environment

set -e

echo "🚀 Setting up RAG Ingest Pipeline..."
echo ""

# Check if running in Docker
if [ ! -f /.dockerenv ]; then
    echo "⚠️  This script should be run inside the backend container"
    echo "Run: docker exec -it catalyst-backend bash /app/scripts/setup_rag.sh"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --quiet pypdf qdrant-client openai requests

# Create data directory
echo "📁 Creating data directory..."
mkdir -p /app/data
chmod 777 /app/data

# Check Qdrant connection
echo "🔍 Checking Qdrant connection..."
QDRANT_URL="${QDRANT_URL:-http://qdrant:6333}"

if curl -s "$QDRANT_URL/collections" > /dev/null 2>&1; then
    echo "✅ Qdrant is accessible at $QDRANT_URL"
else
    echo "❌ Qdrant is not accessible at $QDRANT_URL"
    echo "   Make sure Qdrant container is running"
    exit 1
fi

# Check EMERGENT_LLM_KEY
if [ -z "$EMERGENT_LLM_KEY" ]; then
    echo "⚠️  EMERGENT_LLM_KEY is not set"
    echo "   Embeddings will use fallback (random vectors)"
    echo "   Set EMERGENT_LLM_KEY in .env for production use"
else
    echo "✅ EMERGENT_LLM_KEY is configured"
fi

# Test ingest module
echo "🧪 Testing ingest module..."
if python -m tools.ingest --help > /dev/null 2>&1; then
    echo "✅ Ingest CLI is working"
else
    echo "❌ Ingest CLI failed"
    exit 1
fi

echo ""
echo "✅ RAG setup complete!"
echo ""
echo "Usage examples:"
echo "  # Ingest PDFs"
echo "  python -m tools.ingest --pdf /app/docs/"
echo ""
echo "  # Ingest Confluence"
echo "  python -m tools.ingest --confluence-space MYSPACE"
echo ""
echo "  # Ingest Jira"
echo "  python -m tools.ingest --jira-jql \"project=CATALYST\""
echo ""
echo "  # Search API"
echo "  curl -X POST http://localhost:8001/api/search -H \"Content-Type: application/json\" -d '{\"query\":\"test\"}'"
echo ""
