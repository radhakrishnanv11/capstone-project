# Phase 3: LLM Integration & Prompt Engineering

## Overview

Phase 3 upgrades the baseline agent by:
1. **Integrating an LLM** (OpenAI GPT-4 or Claude)
2. **Engineering 3 prompt variants** and comparing them
3. **Adding structured output** (confidence, reasoning, sources)
4. **Demonstrating improvement** over Phase 2
5. **Exposing new failure modes** for Phase 4+

## Architecture

```
User Input
    |
    v
[Intent Classifier] (simplified; LLM handles most)
    |
    +---> Safety Check (refuse dangerous requests immediately)
    |
    v
[LLM with Prompt Strategy]
    |
    +---> Prompt V1: Basic ("Answer this question")
    +---> Prompt V2: COT (Chain-of-Thought)
    +---> Prompt V3: Structured (JSON output with reasoning)
    |
    v
[Parse Structured Output]
    |
    v
Response + Confidence + Sources + Escalation Flag
```

## Design Decisions

**Why 3 prompt variants?**
- V1 (Basic): Baseline for comparison
- V2 (Chain-of-Thought): Forces reasoning
- V3 (Structured): Ensures consistent, parseable output

**Why LLM over rules?**
- Semantic understanding (handles synonyms, paraphrasing)
- Multi-step reasoning (can synthesize insights)
- Scales to unlimited question types
- Natural language dialogue

**What stays the same:**
- Safety-first: Refuse dangerous requests immediately
- Explicit confidence + uncertainty
- Source citations
- Conversation logging

## Key Improvements Over Phase 2

| Capability | Phase 2 | Phase 3 | Improvement |
|-----------|--------|--------|-------------|
| **Paraphrase handling** | 0% | 85%+ | Semantic understanding |
| **Reasoning** | 0% | 70%+ | Multi-step prompting |
| **Coverage** | 33% | 75%+ | LLM generalization |
| **Confidence calibration** | Hardcoded | Learned | Better trust |
| **Multi-turn memory** | None | Full context | Better UX |
| **Response latency** | <50ms | 1-3s | Trade-off for quality |
| **Safety** | 100% | 100% | Maintained |

