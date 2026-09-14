# Phase 5: Tool Usage & Function Calling

## Overview

Phase 5 enables the agent to **select and use tools** to answer questions:

1. **Tool Definitions:** Define what tools exist and their parameters
2. **Function Calling:** LLM decides which tool to use for each query
3. **Tool Execution:** Run the tool and capture results
4. **Error Handling:** Handle tool failures gracefully
5. **Loop Prevention:** Stop infinite tool call loops
6. **Safeguards:** Prevent dangerous tool misuse

## Architecture

```
User Query
    |
    v
[Safety Check]
    |
    v
[Retrieve Documents via RAG]
    |
    v
[LLM decides: Use tool or answer directly?]
    |
    +---> [No tool needed] --> [Generate answer]
    |
    +---> [Tool needed] --> [Extract tool + parameters]
                                 |
                                 v
                          [Execute Tool]
                                 |
                                 v
                        [Parse tool result]
                                 |
                                 v
                        [Call LLM again with tool result]
                                 |
                                 v
                        [Generate final answer]
                                 |
                                 v
                    Response + Sources + Tool Usage Log
```

## Key Improvements Over Phase 4

| Capability | Phase 4 | Phase 5 | Benefit |
|-----------|--------|--------|----------|
| **Knowledge Source** | Static documents | Dynamic + tool outputs | Real-time data |
| **Query Capabilities** | Answer questions | Answer + execute actions | More useful |
| **Data Validation** | Trust documents | Query system for verification | Higher accuracy |
| **Decision Support** | Recommendations only | Recommendations + data checks | Better confidence |
| **Adaptability** | Fixed KB | KB + dynamic tool results | Future-proof |
| **Error Handling** | Generic refusals | Graceful tool error handling | Robust |

## Tool Definitions for Phase 5

### Tool 1: `get_customer_metrics`
**Purpose:** Query real-time customer metrics

**Parameters:**
- `segment` (required): "enterprise" | "mid-market" | "smb"
- `metric` (required): "churn" | "nps" | "revenue" | "retention"
- `period` (optional): "this_month" | "this_quarter" | "ytd" (default: "this_quarter")

**Returns:** `{metric_value, confidence, data_freshness, sample_size}`

**Example:**
```json
Tool: get_customer_metrics
Input: {"segment": "smb", "metric": "churn", "period": "this_quarter"}
Output: {"value": 18.2%, "confidence": 0.95, "freshness": "today", "n_customers": 500}
```

---

### Tool 2: `check_customer_eligibility`
**Purpose:** Determine if customer qualifies for a discount or action

**Parameters:**
- `customer_id` (required): Unique customer identifier
- `check_type` (required): "discount_eligible" | "renewal_at_risk" | "upsell_opportunity"
- `threshold` (optional): Numeric threshold for the check

**Returns:** `{eligible, reason, recommendation, risk_score}`

**Example:**
```json
Tool: check_customer_eligibility
Input: {"customer_id": "cust_12345", "check_type": "discount_eligible"}
Output: {"eligible": true, "reason": "Enterprise tier + 3-year contract", "recommendation": "Up to 30% discount", "risk_score": 0.2}
```

---

### Tool 3: `verify_policy_compliance`
**Purpose:** Check if a proposed action complies with policies

**Parameters:**
- `action` (required): Description of proposed action
- `action_type` (required): "discount" | "pricing_change" | "refund" | "data_access"
- `customer_segment` (optional): Segment this applies to
- `amount` (optional): Numeric amount (discount %, price change, refund $)

**Returns:** `{compliant, violations, approval_required, escalation_path}`

**Example:**
```json
Tool: verify_policy_compliance
Input: {"action": "Apply 35% discount", "action_type": "discount", "amount": 35, "customer_segment": "enterprise"}
Output: {"compliant": false, "violations": ["Exceeds 30% discount limit"], "approval_required": true, "escalation_path": "CFO"}
```

---

## Safety Guardrails

### 1. **Pre-Tool Checks**
- Verify safety check still passes after retrieval
- Never allow data modification via tools
- Require explicit user approval for risky actions

### 2. **Tool Execution Limits**
- Max 3 tool calls per query (prevent loops)
- Max 2 retries per tool (prevent retry storms)
- 5-second timeout per tool call
- Track tool call history

### 3. **Output Validation**
- Verify tool outputs are valid JSON
- Check result against expected schema
- Flag suspicious outputs (e.g., 0% churn)
- Log all tool calls for audit

### 4. **Escalation Triggers**
- Tool returns error → escalate query
- Tool call limit exceeded → escalate
- Policy compliance violation found → escalate
- Unusual data pattern detected → escalate

---

## Failure Modes & Handling

| Failure Mode | Cause | Detection | Recovery |
|--------------|-------|-----------|----------|
| **Tool timeout** | Slow API | Exceeds 5s | Return error; escalate |
| **Invalid JSON output** | Tool bug | JSON parse fails | Return cached last value; escalate |
| **Policy violation** | User request violates policy | check_customer_eligibility fails | Refuse + explain; escalate |
| **Infinite loop** | LLM keeps calling tool | >3 calls | Stop; escalate |
| **Inconsistent results** | Multiple tool calls conflict | Results contradict | Flag conflict; escalate |
| **Missing data** | Tool can't find customer/metric | Null/empty result | Say "Not found"; escalate |

---

## Demo Scenarios

### Scenario 1: Direct Tool Usage (Works)
**Query:** "What's our SMB churn this quarter?"

**Flow:**
1. LLM sees query needs current data
2. LLM calls: `get_customer_metrics(segment="smb", metric="churn", period="this_quarter")`
3. Tool returns: `{value: 18.2%, confidence: 0.95, freshness: "today"}`
4. LLM generates: "SMB churn is 18.2% this quarter (based on 500 customers as of today)"
5. Response includes tool call log

**Evidence:** Tool call succeeded, data fresh, confident answer

---

### Scenario 2: Policy Compliance Check (Safeguard Works)
**Query:** "Can we give customer XYZ a 40% discount?"

**Flow:**
1. LLM extracts: discount=40%, customer_id="XYZ"
2. LLM calls: `verify_policy_compliance(action="Apply 40% discount", action_type="discount", amount=40, segment="smb")`
3. Tool returns: `{compliant: false, violations: ["Exceeds 30% limit"], escalation_path: "CFO"}`
4. LLM responds: "I cannot approve that discount. SMB discounts are capped at 30%. Please escalate to CFO."
5. Escalation flag set

**Evidence:** Safeguard prevented policy violation

---

### Scenario 3: Tool Failure Handling (Graceful Degradation)
**Query:** "Is customer ABC at risk of churning?"

**Flow:**
1. LLM calls: `check_customer_eligibility(customer_id="ABC", check_type="renewal_at_risk")`
2. Tool times out (API down)
3. LLM detects timeout; doesn't retry
4. LLM falls back: "I can't check current risk status (system unavailable). Based on historical data, SMB segment has 18% churn. Recommend escalating to support team."
5. Escalation flag set

**Evidence:** Graceful failure; explicit uncertainty

---

### Scenario 4: Loop Prevention (Safeguard Works)
**Query:** "How many high-risk customers do we have?"

**Flow:**
1. LLM calls: `get_customer_metrics(segment="all", metric="at_risk_count")`  [Call 1]
2. Tool returns: `{value: 45, confidence: 0.7}`
3. LLM wants more detail; calls tool again [Call 2]
4. LLM wants even more detail; tries to call again [Call 3]
5. LLM realizes it needs to stop: "We have 45 customers at risk (70% confidence). This likely breaks down as: Enterprise ~6, Mid-market ~13, SMB ~26. For detailed breakdown, please escalate to the Analytics team."
6. **Prevents Call 4** (max 3 reached)

**Evidence:** Loop prevention safeguard triggered

---
