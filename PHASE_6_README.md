# Phase 6: Conversation Memory & Planning

## Overview

Phase 6 adds **stateful conversation memory and multi-step planning**:

1. **Conversation Memory:** Agent remembers prior context across turns
2. **Planning/Reasoning:** Break complex queries into multi-step workflows
3. **State Management:** Track conversation state and goals
4. **Task Decomposition:** Convert high-level requests into tool call sequences
5. **Context Enrichment:** Build richer context from conversation history

## Architecture

```
Turn N User Query
    |
    v
[Retrieve Conversation History] ---> [Build Context Window]
    |                                        |
    +--------+--------+--------+--------+----+
             |        |        |        |
          Turn 1   Turn 2   ...   Turn N-1
             |        |        |        |
    [Extract Key Facts & Decisions]
             |
             v
[Safety Check + RAG Retrieval]
             |
             v
[LLM with Planning Prompt]
       |
       +---> [Need multi-step plan?]
             |
             +---> [YES] --> [Decompose into steps]
                                 |
                                 v
                        [Execute step 1] -> [Tool calls]
                                 |
                                 v
                        [Execute step 2] -> [Tool calls]
                                 |
                                 v
                        [Synthesize results]
             |
             +---> [NO] --> [Direct answer]
                                 |
                                 v
    Response + Memory Update + Audit Trail
```

## Key Improvements Over Phase 5

| Capability | Phase 5 | Phase 6 | Benefit |
|-----------|---------|--------|----------|
| **Context Memory** | Independent queries | Full conversation history | Understand references ("it", "that") |
| **Multi-Turn Reasoning** | Single query/response | Multi-step plans | Handle complex workflows |
| **Planning** | Tool selection per query | Multi-query planning | Orchestrate sequences |
| **State Tracking** | Query-level state | Conversation-level state | Remember decisions |
| **Context Window** | Current query only | Last 10 turns + summary | Richer context |
| **Follow-up Handling** | Requires full re-context | Implicit from history | Better UX |

## Memory System Design

### Conversation State
```python
{
    "session_id": "session_abc123",
    "created_at": "2024-10-15T14:30:00Z",
    "turns": [
        {
            "turn_id": 1,
            "query": "What's our SMB churn?",
            "response": "18.2%...",
            "tools_used": ["get_customer_metrics"],
            "key_facts": {"smb_churn": 18.2, "sample_size": 500}
        },
        {
            "turn_id": 2,
            "query": "Why is it so high?",  # "it" = SMB churn
            "resolved_query": "Why is SMB churn (18.2%) so high?",
            "response": "Root causes: price (36%), product-fit (28%)...",
            "tools_used": ["search_documents"],
            "key_facts": {"primary_cause": "price_sensitivity"}
        },
        {
            "turn_id": 3,
            "query": "What should we do about it?",  # "it" = high SMB churn
            "resolved_query": "What should we do about high SMB churn (18.2%) caused by price?",
            "response": "Recommend: create SMB tier, test pricing, improve support...",
            "tools_used": ["verify_policy_compliance"],
            "key_facts": {"recommendations": ["create_smb_tier", "test_pricing", "improve_support"]}
        }
    ],
    "goals": ["Understand SMB churn", "Identify root cause", "Develop action plan"],
    "decisions_made": ["SMB churn is priority", "Price is key lever"],
    "outstanding_questions": ["What's budget for SMB improvements?", "When should we implement?"],
    "escalations": [{"turn": 3, "type": "cost_analysis", "owner": "CFO"}]
}
```

## Planning System Design

### Query Analysis
```python
{
    "query": "Find all SMB customers at risk and recommend discount strategy",
    "complexity": "high",  # Single-step vs. multi-step
    "plan": [
        {
            "step": 1,
            "goal": "Identify at-risk SMB customers",
            "tool_calls": [
                {"tool": "search_customers", "params": {"segment": "smb", "criteria": "at_risk"}}
            ]
        },
        {
            "step": 2,
            "goal": "Check discount eligibility for each",
            "tool_calls": [
                {"tool": "check_customer_eligibility", "params": {"customer_id": "cust_X"}}
                # ... for each at-risk customer
            ],
            "depends_on": [1]
        },
        {
            "step": 3,
            "goal": "Verify policy compliance for recommended discounts",
            "tool_calls": [
                {"tool": "verify_policy_compliance", "params": {"action_type": "discount", "amount": 15}}
            ],
            "depends_on": [2]
        },
        {
            "step": 4,
            "goal": "Synthesize strategy",
            "type": "synthesis",  # No tool, just LLM reasoning
            "depends_on": [1, 2, 3]
        }
    ]
}
```

## Memory Retention Strategy

### Short-term Memory (Context Window)
- **Last 10 turns** in full detail
- **Older turns** summarized ("Earlier we discussed churn; key findings: SMB=18.2%, cause=price")
- **Total tokens:** ~3000-4000 (fits in GPT-4 context)

### Long-term Memory (Persistent)
- **Session summaries** (key decisions, facts, escalations)
- **User profile** (Sarah's role, authority, preferences)
- **Decision log** (what was decided, why, by whom)
- **Action items** (outstanding tasks, owners, deadlines)

### Memory Pruning
- Delete after 30 days (or configurable)
- Archive important decisions
- Export for compliance/audit

## Planning Prompts

### Prompt 1: Query Complexity Assessment
```
Determine if this query needs a multi-step plan:

Query: "[user_query]"

Respond:
{
  "is_complex": true/false,
  "reasoning": "Why (or why not)?",
  "steps_needed": ["step 1", "step 2", ...] if complex
}
```

### Prompt 2: Plan Decomposition
```
Break down this complex query into steps:

Query: "[user_query]"
Context: "[conversation_history]"

Create a plan with:
1. Each step's goal
2. Which tools to use
3. Dependencies between steps
4. Success criteria for each step
```

### Prompt 3: Multi-Turn Synthesis
```
Summarize the conversation and provide final recommendation:

Conversation history:
[Turn 1] ...
[Turn 2] ...
[Turn 3] ...

Based on all turns, provide:
- Key findings
- Decisions made
- Recommended next actions
- Outstanding questions
```

## Demo Scenarios

### Scenario 1: Multi-Turn Conversation (Works)
**Turns:**
1. "What's our churn by segment?"
2. "Which segment is worst?"
3. "Why is that segment struggling?"
4. "What's the financial impact?"
5. "What should we do about it?"

**Memory Usage:**
- Turn 1: Agent learns about churn rates
- Turn 2: Agent remembers churn context; identifies SMB
- Turn 3: Agent knows "that segment" = SMB; searches for root cause
- Turn 4: Agent links SMB churn to revenue impact (uses prior context)
- Turn 5: Agent synthesizes 4 prior turns into action plan

**Evidence:** Each turn builds on prior without re-explaining context

---

### Scenario 2: Plan Decomposition (Complex Query)
**Query:** "Find our 5 highest-risk SMB customers, check if they're discount-eligible, verify we can offer up to 15%, and draft a retention strategy"

**Planning:**
```
Step 1: Identify 5 highest-risk SMB customers
  Tools: [search_customers]
  
Step 2: Check discount eligibility for each
  Tools: [check_customer_eligibility] × 5
  Depends on: Step 1
  
Step 3: Verify 15% discount complies with policy
  Tools: [verify_policy_compliance]
  Depends on: Step 2
  
Step 4: Synthesize strategy
  Type: LLM reasoning
  Depends on: Step 1, 2, 3
```

**Execution:** Agent runs steps sequentially, tracking results

---

### Scenario 3: Reference Resolution (Memory Works)
**Turn 1:**
```
User: "What's our SMB churn rate?"
Agent: "SMB churn is 18.2% this quarter."
Memory: {"smb_churn": 18.2, "segment": "smb", "period": "this_quarter"}
```

**Turn 2:**
```
User: "Is that higher than enterprise?"
Agent:
  1. Resolve "that" → "SMB churn"
  2. Compare with enterprise churn (tool call)
  3. Respond: "Yes, SMB at 18.2% is much higher than Enterprise at 8%."
Memory: {"comparison": "smb_vs_enterprise", "smb_higher_by": "10.2pp"}
```

**Turn 3:**
```
User: "Why the difference?"
Agent:
  1. Resolve "the difference" → "Why is SMB 10.2pp higher than Enterprise?"
  2. Search for root cause analysis
  3. Respond with causes
Memory: {"root_cause_smb": ["price_sensitivity", "product_fit", "support_quality"]}
```

**Evidence:** Agent resolves pronouns from context; no ambiguity

---
