#!/bin/bash
# Phase 6 Memory Agent Demo Runner

echo "================================"
echo "Phase 6: Memory & Planning Demo"
echo "================================"
echo ""
echo "This demonstrates:"
echo "  1. Multi-turn conversation memory"
echo "  2. Reference resolution (pronouns)"
echo "  3. Query complexity assessment"
echo "  4. Plan decomposition"
echo "  5. Conversation summarization"
echo ""
echo "Running demo..."
echo ""

python3 memory_agent.py --test-mode

echo ""
echo "✅ Demo complete. Check conversation_*.json for full logs."
