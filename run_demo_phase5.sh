#!/bin/bash
# Phase 5 Tool Agent Demo Runner

echo "================================"
echo "Phase 5: Tool Usage Demo"
echo "================================"
echo ""
echo "This demonstrates:"
echo "  1. Tool definitions and schemas"
echo "  2. Automatic tool selection by LLM"
echo "  3. Correct tool usage"
echo "  4. Policy enforcement via tools"
echo "  5. Loop prevention safeguards"
echo ""
echo "Running safeguard tests..."
echo ""

python3 tool_agent.py --test-mode

echo ""
echo "✅ Demo complete. Check phase5_interaction_log.json for detailed results."
