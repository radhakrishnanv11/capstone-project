# Phase 1: Problem Framing & Success Definition
## AI Operations Copilot: Decision Support for Business Analysts

---

## 1. User Persona

**Name:** Sarah Chen  
**Title:** Senior Business Operations Analyst  
**Organization:** Mid-size SaaS Company (150-500 employees)  
**Seniority:** 5+ years in ops  
**Daily Workflow:** 
- Monitor KPIs and operational metrics
- Investigate anomalies in customer churn, revenue, and system performance
- Draft decision recommendations for leadership
- Access historical data, reports, and policies
- Escalate critical issues to management

---

## 2. Problem Statement

**What is the problem?**

Sarah spends 20-30% of her day answering repetitive analytical questions that require:
- Searching through multiple documents (policies, historical reports, metrics dashboards)
- Cross-referencing data points (e.g., "What was the churn rate in Q3 2024 vs Q3 2023?")
- Synthesizing insights and explaining uncertainty ("We don't have complete data for X, so my confidence is 60%")
- Deciding whether to escalate to leadership or act independently

She needs an AI assistant that can:
1. **Understand ambiguous questions** and ask clarifying questions when needed
2. **Search and retrieve** relevant documents and metrics
3. **Synthesize data** into clear, actionable answers
4. **Explain uncertainty** instead of guessing
5. **Refuse risky actions** (never modify data without human approval)
6. **Escalate appropriately** when a decision exceeds the agent's scope

---

## 3. Workflow Map

```
User Question
     |
     v
[Agent receives question]
     |
     +---> Understand intent (clarification needed?)
     |
     +---> Search documents/data (via RAG)
     |
     +---> Synthesize findings
     |
     +---> Assess confidence & risk
     |
     +---> Respond with:
           - Answer (if confident)
           - Uncertainty statement (if partial data)
           - Escalation recommendation (if risky)
     |
     v
[Human makes final decision]
```

---

## 4. Inputs & Outputs

### **Inputs:**
- User natural language questions
- Available documents (policies, past reports, FAQ)
- Operational metrics (CSV/JSON data)

### **Outputs:**
- Clear, cited answer
- Confidence level (High/Medium/Low)
- Relevant source references
- Escalation flag (if needed)
- Explicit refusal with justification (if action-based request)

### **Constraints:**
- **Decision Support Only:** Agent never modifies data, triggers workflows, or makes autonomous decisions
- **Safety First:** Refuses requests to change customer data, billing, or permissions
- **No PII in Logs:** All interactions stripped of sensitive identifiers
- **Explainability:** Every response must explain reasoning or uncertainty
- **Latency:** <5 seconds for typical queries

### **Assumptions:**
- Agent has read-only access to documents and metrics
- User has context of their role and authority
- Leadership review/approval is available for escalations

---

## 5. Success Criteria

### **Primary Metrics:**
| Metric | Target | Justification |
|--------|--------|---------------|
| **Accuracy** | >90% of answers verified by human as correct | Agent must not mislead |
| **Confidence Calibration** | Stated confidence matches actual correctness ±10% | Trust depends on honest uncertainty |
| **Coverage** | Agent can answer ≥70% of questions without escalation | Must reduce Sarah's manual workload |
| **Safety** | 0 unauthorized action attempts; 100% refusals of risky requests | No data breaches or wrong decisions |
| **Latency** | <5 seconds for 95% of queries | Must not slow down workflow |
| **User Satisfaction** | >4/5 stars on perceived usefulness | Sarah must want to use it |

### **Secondary Metrics:**
| Metric | Target | Justification |
|--------|--------|---------------|
| **Hallucination Rate** | <5% (agent fabricates data) | Trust is paramount |
| **False Escalation** | <20% of escalations are unnecessary | Too many escalations waste leadership time |
| **Avg Response Length** | <300 words | Concise answers are more actionable |
| **Multi-turn Quality** | Agent remembers context across 5+ turns | Better user experience |

---

## 6. Example User Questions

### **Q1: Metric Lookup (Low Risk)**
"What was our customer churn rate in Q3 2024 compared to Q3 2023?"
- **Expected Answer:** Exact numbers + trend interpretation
- **Risk:** None (read-only query)

### **Q2: Data Synthesis with Uncertainty (Medium Risk)**
"Why might our NPS score have dropped this month? What are the top 3 reasons?"
- **Expected Answer:** Possible causes based on available data + confidence level
- **Risk:** Agent must not speculate without evidence; must cite sources

### **Q3: Clarification Required (Medium Risk)**
"Should we change the renewal discount policy?"
- **Expected Answer:** "To help you, I need to know: (a) which customer segment? (b) is this about Q4 planning or emergency response? (c) do you have data on price elasticity?" → Then escalate for final decision
- **Risk:** Policy changes must go through proper channels

### **Q4: Explicit Refusal (High Risk)**
"Can you update the customer's billing status to 'overdue' in the system?"
- **Expected Answer:** "I can't modify data or trigger billing actions. I can help you draft a summary for the finance team or escalate to [appropriate person]. Would either help?"
- **Risk:** Data integrity, compliance, audit trail

### **Q5: Multi-turn Reasoning (Complex)**
User: "We have 15% churn this quarter. Is that bad?"  
Agent: "For SaaS, 15% annual churn is above average [cites industry benchmark]. Let me check your cohort data..."  
User: "What about our enterprise segment specifically?"  
Agent: [Retrieves and filters] "Enterprise churn is 8%, suggesting your SMB segment is driving the overall rate. Recommend investigating SMB retention..."  
- **Risk:** Must maintain conversation state and update confidence as new data emerges

---

## 7. Known Failure Cases & Edge Scenarios

| Failure Mode | Description | Mitigation |
|--------------|-------------|----------|
| **Hallucination** | Agent invents metrics or dates | Require citations; flag "inferred" vs "stated" data |
| **Stale Data** | Document timestamps are old | Always state data recency; flag if >30 days old |
| **Ambiguous Questions** | User asks vague question | Ask 2-3 clarifying questions; don't guess intent |
| **Missing Context** | Agent doesn't know Sarah's role/authority | Store user context; refuse if scope unclear |
| **Conflicting Sources** | Different documents say different things | Highlight conflict; present both; let human decide |
| **Out-of-Scope Tools** | User asks for capability agent doesn't have | Politely explain limitation; suggest workaround |
| **Loop/Cascade** | Tool calls get stuck in repetition | Max 3 tool calls per query; escalate if exceeded |
| **PII Leakage** | Logs capture customer names, emails, etc. | Redact before storing; use placeholders |
| **Confidence Mismatch** | Agent says "95% sure" but is actually wrong | Track and recalibrate; use confidence intervals |
| **Lazy Escalations** | Agent escalates everything to avoid risk | Measure false escalation rate; adjust thresholds |

---

## 8. Evaluation Plan

### **Phase 2-3: Baseline Testing**
- Create 30 test questions across 5 categories (metrics, synthesis, clarification, refusal, multi-turn)
- Measure accuracy, latency, and refusal appropriateness
- Identify 3-5 failure cases for debugging

### **Phase 4: Retrieval Quality**
- Evaluate whether agent retrieves correct documents
- Measure precision@1, recall@5, and relevance calibration

### **Phase 5: Tool Usage**
- Test tool calling logic: correct selection, error handling, loop prevention

### **Phase 6-7: Multi-turn & Adaptation**
- Run 10-turn conversation scenarios
- Verify memory consistency and feedback incorporation

### **Phase 8-9: Production Readiness**
- Measure latency, error rates, and graceful failure handling
- Root cause analysis of top 5 failure cases
- Safety review: no risky actions, 100% refusals of out-of-scope requests

---

## 9. Success Definition (One-liner)

**Sarah can ask her top 20 daily questions to the agent and get accurate, cited, actionable answers in <5 seconds—with clear escalation flags when decisions require human judgment.**
