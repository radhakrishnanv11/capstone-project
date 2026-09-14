# Phase 2: Baseline Agent - Simple Rules-Based Implementation

## Overview

This phase builds a **minimal working agent** without LLM integration. It demonstrates:
1. How to accept user input
2. Basic response generation using rules/templates
3. **Clear limitations** that justify moving to LLM in Phase 3

## Architecture

```
User Input
    |
    v
[Intent Classifier] (regex-based)
    |
    +---> Metrics Query --> [Template Response]
    +---> Policy Question --> [Document Lookup] --> [Template Response]
    +---> Refusal Trigger --> [Refusal Template]
    +---> Unknown --> [Escalation]
    |
    v
 Response + Confidence Score
```

## Design Decisions

**Why rules-based for Phase 2?**
- Establishes baseline performance
- Shows what's possible *without* LLM complexity
- Reveals exactly which limitations push us toward intelligent solutions
- Makes Phase 3 improvements measurable

**Limitations we'll expose:**
1. **No semantic understanding** - Can't handle paraphrasing
2. **No reasoning** - Can't synthesize across documents
3. **No uncertainty** - Confidence is hardcoded
4. **No learning** - Same response every time
5. **Brittle matching** - Breaks on slight query variations

## Key Artifacts

1. **baseline_agent.py** - Main agent code
2. **interaction_logs.txt** - Sample interactions showing limitations
3. **PHASE_2_EVALUATION.md** - Analysis of failures and why Phase 3 is needed
