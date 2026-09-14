# Phase 4: Knowledge Retrieval & RAG (Retrieval-Augmented Generation)

## Overview

Phase 4 adds **semantic search and document retrieval** to the agent:

1. **Embeddings:** Convert documents and queries to semantic vectors
2. **Vector Store:** Index and search documents efficiently
3. **RAG Pipeline:** Retrieve relevant docs → Pass to LLM → Generate answer
4. **Quality Metrics:** Measure retrieval accuracy (precision, recall, MRR)
5. **Missing Data Handling:** Explicit "I don't know" when info is unavailable

## Architecture

```
User Query
    |
    v
[Safety Check]
    |
    v
[Embed Query] ---> [Vector Search] ---> [Retrieve Top K Docs]
    |                                            |
    +--------------------------------------------+
                        |
                        v
            [Build Context from Docs]
                        |
                        v
        [LLM with V3 Structured Prompt]
                        |
                        v
        [Parse Output + Add Sources]
                        |
                        v
    Response + Confidence + Document Sources
                        |
                        v
            [Log Retrieval Quality]
```

## Key Improvements Over Phase 3

| Capability | Phase 3 | Phase 4 | Benefit |
|-----------|--------|--------|----------|
| **Knowledge Source** | Hardcoded KB | Dynamic document indexing | Scales to 1000s of docs |
| **Retrieval Quality** | N/A | Measured (precision@k, recall) | Know if agent found right info |
| **Source Citations** | Manual | Automatic from retrieved docs | Higher confidence in sources |
| **Missing Data Handling** | Guesses | Explicit "not found" | Honesty over hallucination |
| **Knowledge Updates** | Code change | Add doc + re-index | No code changes needed |
| **Semantic Search** | Implicit in LLM | Explicit via embeddings | Faster, more transparent |

## Why RAG?

**Problem with Phase 3 (LLM only):**
- LLM encodes all knowledge in weights (trained data only)
- Can't access real-time data
- No way to know where answer came from
- Hallucinates when knowledge is missing

**Solution (RAG):**
- Retrieves latest documents before generating
- LLM writes based on explicit sources
- Can handle 10K+ documents efficiently
- Transparency: user sees which docs were used

