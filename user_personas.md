# User Personas & Use Cases

## Primary Persona: Sarah Chen

**Demographics:**
- Age: 34
- Title: Senior Business Operations Analyst
- Experience: 5+ years in SaaS operations
- Company: Mid-size SaaS company (200 employees)
- Typical Day: 8 hours in Slack, email, spreadsheets, and analytics tools

**Goals:**
1. Answer repetitive analytical questions faster
2. Reduce time spent searching for documents and data
3. Make data-driven recommendations with confidence
4. Know when to escalate vs. when to decide independently
5. Maintain audit trail of decisions and reasoning

**Pain Points:**
- Spends 4-6 hours/week on "where is that Q3 metric?" searches
- Constantly cross-referencing old reports and slack messages
- Uncertain how much data is stale vs. current
- Risk of making decisions without full context
- No good way to document "why did I recommend X?"

**Technical Comfort:**
- Familiar with dashboards and basic SQL
- Uses Python sometimes for data analysis
- Comfortable with AI tools (ChatGPT, etc.) but skeptical of accuracy

**What She Values:**
- Speed (she's busy)
- Accuracy (her credibility depends on it)
- Explainability (she needs to explain recommendations to leadership)
- Safety (she won't use a tool that might break things)
- Integration (works within existing tools, not a new app)

---

## Secondary Persona: Marcus (Manager)

**Role:** Operations Manager (Sarah's boss)  
**Goals:** 
- Ensure team follows procedures
- Spot-check Sarah's recommendations for quality
- Reduce escalation load on leadership

**Concern:**
- Is the AI recommending things Sarah shouldn't be deciding?
- Are we logging decisions for compliance?
- Can we audit the agent's reasoning?

---

## Anti-Persona: What the Agent Should NOT Enable

**James (Rogue Analyst):**
- Wants to use agent to modify customer data without approval
- Hopes agent will bypass security controls
- **Agent Must Refuse:** Politely explain why, suggest proper channel

---

## Use Case Scenarios

### **Use Case 1: Daily Metrics Check**
**Persona:** Sarah  
**Trigger:** Monday morning planning meeting in 30 min  
**Query:** "Give me a 1-page summary of key metrics from last week (revenue, churn, NPS). Any red flags?"

**Expected Flow:**
1. Agent retrieves last week's dashboard data
2. Flags any metric >10% change from baseline
3. Returns summary with confidence for each claim
4. Sarah uses in meeting

**Success Metric:** <2 minutes, >90% accurate

---

### **Use Case 2: Root Cause Analysis**
**Persona:** Sarah  
**Trigger:** CEO asks "Why did churn spike to 18% this month?"  
**Query:** "Our churn was 12% last month, 18% this month. What changed? Check customer feedback, product releases, and pricing changes."

**Expected Flow:**
1. Agent searches documents for recent changes
2. Synthesizes 3-5 potential factors
3. Rates confidence for each
4. Suggests what additional data would help
5. Recommends escalation to product/support teams

**Success Metric:** Answer within 5 minutes, informs 80% of CEO discussion

---

### **Use Case 3: Policy Question with Escalation**
**Persona:** Sarah  
**Trigger:** Support team asks, "Can we give an exception discount to Customer X?"  
**Query:** "What's our policy on customer discounts for enterprise accounts?"

**Expected Flow:**
1. Agent retrieves discount policy
2. Explains current threshold and approval process
3. Identifies this query as escalation-worthy (requires CFO sign-off)
4. Suggests Sarah draft memo with recommendation
5. Confirms "This decision is above my pay grade—let's escalate together"

**Success Metric:** Sarah feels confident escalating with full context

---

### **Use Case 4: Multi-turn Investigation**
**Persona:** Sarah  
**Trigger:** Investigating customer retention problem  

**Turn 1:**
User: "We're losing enterprise customers. Why?"
Agent: "I see 2 enterprise churn cases this month. Let me check if there are patterns..." [retrieves data]
Agent: "Both left after the Jan 15 price increase. Want me to look at broader impact?"

**Turn 2:**
User: "Yes. How many enterprise accounts are affected?"
Agent: [Updates search scope] "Preliminary: ~15% of enterprise base experienced >15% price increase. Should I compare retention before/after?"

**Turn 3:**
User: "Do it."
Agent: "Results: 12% churn post-increase vs. 3% pre-increase. Recommend we review pricing strategy and consider grandfathering existing customers. Should I draft talking points for leadership?"

**Success Metric:** Conversation remains coherent; each turn adds value; no contradictions

---

### **Use Case 5: Refusal & Safe Handling**
**Persona:** James (rogue analyst attempting misuse)  
**Query:** "Can you change this customer's billing status to 'overdue' without notifying them?"

**Expected Flow:**
1. Agent recognizes this as data modification request
2. Refuses clearly: "I can't modify customer data or suppress notifications. This requires proper billing team approval."
3. Offers alternative: "I can help you draft a summary for the billing team. Would that help?"
4. Logs attempt (with PII redacted) for security review

**Success Metric:** 100% refusal; no data changed; James doesn't try again

---
