# Phase 6: Conversation Memory & Planning - Evaluation

## Overview

Phase 6 adds **multi-turn conversation memory** and **multi-step planning** capabilities.

---

## Key Capabilities

### 1. Conversation Memory

**What it does:**
- Stores all turns in conversation
- Extracts and tracks key facts from each turn
- Builds context window for LLM
- Enables reference resolution (pronouns)

**Example:**

Turn 1: User asks "What's our SMB churn?"
```
Memory stores:
  - query: "What's our SMB churn?"
  - response: "18.2%"
  - key_facts: {"smb_churn": 18.2, "segment": "smb"}
```

Turn 2: User asks "Is that higher than enterprise?"
```
Memory resolves:
  - "that" → "SMB churn (18.2%)" (from Turn 1)
  - Resolved query: "Is SMB churn (18.2%) higher than enterprise?"
  - Agent responds with comparison (no re-explanation needed)
```

---

### 2. Reference Resolution

**Problem in stateless systems:**
```
Turn 1: User: "What's our churn?"
Agent: "18.2%"

Turn 2: User: "Is it higher than last year?"
Agent: "What is 'it'? Please clarify." ❌ (frustrating)
```

**Solution in Phase 6:**
```
Turn 1: User: "What's our churn?"
Agent: "18.2%"
Memory: {"churn": 18.2}

Turn 2: User: "Is it higher than last year?"
Agent:
  1. [Memory Lookup] "it" → "churn (18.2%)"
  2. [Resolved Query] "Is churn (18.2%) higher than last year?"
  3. [Response] "Yes, 18.2% is up from 16.5% last year." ✅
```

---

### 3. Query Complexity Assessment

**Levels:**
1. **SIMPLE** (20% of queries)
   - Single fact lookup
   - Example: "What's our NPS?"
   - Approach: Direct answer

2. **MODERATE** (50% of queries)
   - Context + comparison
   - Example: "Is SMB churn higher than enterprise?"
   - Approach: Retrieve context + analyze

3. **COMPLEX** (30% of queries)
   - Multi-step workflow
   - Example: "Find at-risk customers, check eligibility, verify policy, recommend action"
   - Approach: Plan decomposition + sequential execution

---

### 4. Plan Decomposition for Complex Queries

**Example Complex Query:**
```
"Find our 5 highest-risk SMB customers, check if they're discount-eligible, 
verify we can offer 15% discount, and draft a retention strategy."
```

**Decomposed Plan:**
```
Step 1: Identify 5 highest-risk SMB customers
  Tool: search_customers
  Status: [Pending]
  
Step 2: Check discount eligibility for each
  Tool: check_customer_eligibility
  Depends on: Step 1
  Status: [Pending]
  
Step 3: Verify 15% discount policy compliance
  Tool: verify_policy_compliance
  Depends on: Step 2
  Status: [Pending]
  
Step 4: Synthesize retention strategy
  Type: LLM synthesis (no tool)
  Depends on: Step 1, 2, 3
  Status: [Pending]
```

**Execution:**
```
✓ Step 1 complete (5 customers identified)
✓ Step 2 complete (all eligible for some discount)
✓ Step 3 complete (15% complies with policy)
✓ Step 4 complete (strategy drafted)

[Final Synthesis]
All 5 customers are eligible for up to 15% discount under policy.
Recommended strategy:
  1. Offer tiered discounts (10%, 12%, 15% based on risk score)
  2. Couple with support improvements (faster response times)
  3. Monthly check-ins for first 90 days
  4. Success metric: Reduce 5-customer churn from 80% to <30% in 6 months
```

---

## Multi-Turn Conversation Example

### Turn 1: Initial Question
```
User: "What's our SMB churn this quarter?"

Agent: "SMB churn this quarter is 18.2% (based on 500 customers). 
This is up from 15% last quarter."

Memory State:
  turn_id: 1
  key_facts: {"smb_churn": 18.2, "segment": "smb", "period": "this_quarter"}
  references: []
```

### Turn 2: Comparison (Reference Resolution)
```
User: "Is that higher than enterprise?"

[Memory Resolution]
  1. Query has pronoun "that"
  2. Last turn key fact: {"smb_churn": 18.2}
  3. Resolved query: "Is SMB churn (18.2%) higher than enterprise churn?"

Agent: "Yes, SMB at 18.2% is significantly higher than Enterprise at 8.0%. 
This is concerning and warrants investigation."

Memory State:
  turn_id: 2
  key_facts: {
    "smb_churn": 18.2,
    "enterprise_churn": 8.0,
    "difference": 10.2,
    "comparison_made": true
  }
  references: ["Turn 1 - smb_churn"]
```

### Turn 3: Root Cause Analysis
```
User: "Why the big difference?"

[Memory Resolution]
  1. Query has phrase "the big difference"
  2. Prior context: SMB 18.2% vs Enterprise 8.0% = 10.2pp difference
  3. Resolved query: "Why is SMB churn (18.2%) so much higher than Enterprise (8.0%)?"

Agent: "The root causes differ by segment:

  SMB (18.2% churn):
    - Price sensitivity (36%): SMB budget-conscious, hesitant at $50/user/month
    - Product-market fit (28%): Features overbuilt for SMB use cases
    - Support issues (15%): Response time 24-48h (acceptable for Enterprise, too slow for SMB)
    - Better alternatives (21%): Market has cheaper competitors
  
  Enterprise (8% churn):
    - Long contracts (multi-year, hard to leave)
    - ROI already proven (embedded workflows)
    - Dedicated support (strong relationships)"

Memory State:
  turn_id: 3
  key_facts: {
    ...[all prior facts]...,
    "smb_churn_reasons": ["price_sensitivity", "product_fit", "support_issues", "competition"],
    "primary_smb_cause": "price_sensitivity"
  }
```

### Turn 4: Action Planning
```
User: "What should we do about it?"

[Memory Resolution]
  1. "it" → "high SMB churn (18.2% vs enterprise 8%)"
  2. Prior context: SMB churn driven by price sensitivity
  3. Resolved query: "What should we do about SMB churn (18.2%) caused by price sensitivity?"

Agent: "Recommendation: Three-pronged approach

  1. Pricing Strategy (leverage: highest impact)
     - Create SMB tier: $25/user/month (vs $50 current)
     - Test with 50 SMB customers for 3 months
     - Expected impact: Reduce churn 5-10pp
  
  2. Product Optimization
     - Survey top 20 SMB customers: Which features matter?
     - Build SMB-specific feature set (simplified UX)
     - Create self-serve onboarding
     - Expected impact: Reduce churn 2-3pp
  
  3. Support Improvements
     - Hire 2 SMB support specialists
     - Reduce response time to <4 hours
     - Implement proactive success checks
     - Expected impact: Reduce churn 1-2pp
  
  Total expected impact: Reduce SMB churn from 18.2% to ~10-12%
  Investment required: ~$330K/year
  Payback period: 3-4 months (based on retention value)

This should escalate to CFO for budget approval."

Memory State:
  turn_id: 4
  key_facts: {
    ...[all prior facts]...,
    "recommendations": ["pricing_tier", "product_optimization", "support_improvement"],
    "expected_impact": "18.2% → 10-12%",
    "investment_required": 330000,
    "escalation_target": "CFO"
  }
```

---

## Memory Retention

### Context Window (Active)
- **Last 10 turns:** Full detail
- **Older turns:** Summarized
- **Total tokens:** ~3000-4000 (fits in GPT-4)
- **Purpose:** LLM can see recent context for reasoning

### Persistent Storage (Archive)
- **Session summaries:** Key decisions, escalations
- **Decision log:** What, why, who, when
- **User profile:** Role, authority, preferences
- **Purpose:** Compliance, audit, future reference

### Pruning Policy
- **Delete after:** 30 days (or configurable)
- **Archive important turns:** Before deletion
- **Export:** On demand or triggered by escalation
- **Purpose:** Data hygiene, compliance

---

## Comparison: Phase 5 vs Phase 6

### Single-Turn (Phase 5)
```
User: "What's our churn?"
Agent: "SMB: 18.2%, Enterprise: 8%, Mid-market: 12%"

(If user follows up with "Why the difference?", agent has NO context)
```

### Multi-Turn (Phase 6)
```
User: "What's our churn?"
Agent: "SMB: 18.2%, Enterprise: 8%, Mid-market: 12%"
Memory: {segments: [smb, enterprise, mid-market], values: [18.2, 8, 12]}

User: "Why the difference?"
Agent: (Recalls prior turn) "The difference is primarily driven by..."
(Agent doesn't need user to re-specify segments)
```

---

## Test Results

### Scenario 1: Reference Resolution ✅
```
Test: "What's X? ... Is that higher than Y?"
Result: Agent correctly resolves "that" to X
Status: PASS
```

### Scenario 2: Multi-Turn Synthesis ✅
```
Test: 4-turn conversation about SMB churn → final recommendation
Result: Agent synthesizes all 4 turns into coherent action plan
Status: PASS
```

### Scenario 3: Plan Decomposition ✅
```
Test: Complex query → multi-step plan
Result: Agent breaks into 4 sequential steps with dependencies
Status: PASS
```

### Scenario 4: Memory Persistence ✅
```
Test: Export conversation to JSON
Result: All turns, facts, decisions logged
Status: PASS
```

---

## What Improved from Phase 5

| Aspect | Phase 5 | Phase 6 | Benefit |
|--------|---------|---------|----------|
| **Multi-turn support** | Independent queries | Full context | Understand references |
| **Planning** | Single-step tool use | Multi-step plans | Handle workflows |
| **State tracking** | No state | Conversation state | Persistent context |
| **Reference resolution** | "Please clarify" | Automatic | Better UX |
| **Conversation export** | Interaction log only | Full session export | Audit trail |
| **Complexity handling** | Simple/moderate only | Simple/moderate/complex | Enterprise-grade |

---

## What's Next (Phase 7)

**Phase 7: Adaptive Behavior & Learning**
- Learn from user feedback
- Adapt response style based on preferences
- Track which recommendations were successful
- Build user-specific knowledge
- Improve confidence calibration over time

---
