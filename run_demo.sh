#!/bin/bash
# Phase 2 Demo Runner
# Run this to see the baseline agent in action

echo "================================"
echo "Phase 2: Baseline Agent Demo"
echo "================================"
echo ""
echo "This will run 5 forced demo interactions showing:"
echo "  1. What WORKS (direct queries, safety)"
echo "  2. What FAILS (paraphrasing, reasoning, scaling)"
echo ""
echo "Running..."
echo ""

python3 baseline_agent.py

echo "✅ Demo complete. Check phase2_interaction_log.json for full logs."
