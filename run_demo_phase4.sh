#!/bin/bash
# Phase 4 RAG Demo Runner

echo "================================"
echo "Phase 4: RAG Agent Demo"
echo "================================"
echo ""
echo "This demonstrates:"
echo "  1. Document indexing and retrieval"
echo "  2. Retrieval quality metrics (Precision, Recall, MRR)"
echo "  3. LLM response with source citations"
echo "  4. Missing data handling"
echo ""
echo "Running test harness..."
echo ""

python3 rag_agent.py --test-mode

echo ""
echo "✅ Demo complete. Check phase4_interaction_log.json for detailed results."
