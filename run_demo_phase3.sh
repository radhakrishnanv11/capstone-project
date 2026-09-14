#!/bin/bash
# Phase 3 Demo Runner
# Run comparative test of all 3 prompt variants

echo "================================"
echo "Phase 3: LLM Integration Demo"
echo "================================"
echo ""
echo "This will compare 3 prompt strategies:"
echo "  V1: Basic (fastest)"
echo "  V2: Chain-of-Thought (better reasoning)"
echo "  V3: Structured JSON (recommended)"
echo ""
echo "Requirements: pip install openai python-dotenv"
echo "Setup: Create .env with OPENAI_API_KEY=sk-..."
echo ""
echo "Running test harness..."
echo ""

python3 llm_agent.py --test-mode

echo ""
echo "✅ Demo complete. Check phase3_logs_*.json for detailed results."
