#!/usr/bin/env python3
"""
Phase 2: Baseline AI Agent - Rules-Based Implementation

This is a minimal working agent that uses:
- Regex-based intent classification
- Template responses
- Simple document lookup
- Hardcoded confidence scores

Purpose: Establish baseline and expose limitations that Phase 3 will fix.
"""

import re
import json
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple

# ============================================================================
# PHASE 2: DATA LAYER (Mock Data)
# ============================================================================

class Intent(Enum):
    METRICS_QUERY = "metrics_query"
    POLICY_QUESTION = "policy_question"
    DATA_MODIFICATION = "data_modification"
    UNKNOWN = "unknown"
    ESCALATION = "escalation"

# Mock operational metrics database
METRICS_DB = {
    "Q3_2024_churn": {"value": "12%", "source": "Analytics Dashboard", "date": "2024-09-30"},
    "Q3_2023_churn": {"value": "10.5%", "source": "Analytics Dashboard", "date": "2023-09-30"},
    "Q4_2024_revenue": {"value": "$2.5M", "source": "Finance System", "date": "2024-10-31"},
    "nps_september": {"value": "45", "source": "Surveys", "date": "2024-09-30"},
    "nps_october": {"value": "42", "source": "Surveys", "date": "2024-10-31"},
    "enterprise_churn": {"value": "8%", "source": "Segment Report", "date": "2024-10-15"},
    "smb_churn": {"value": "18%", "source": "Segment Report", "date": "2024-10-15"},
}

# Mock policies document
POLICIES = {
    "discount_policy": {
        "content": "Standard discounts: SMB tier (0-10 seats): up to 10%, Mid-market (11-100): up to 20%, Enterprise (100+): up to 30%. All discounts require Finance approval. Exceptions tracked quarterly.",
        "last_updated": "2024-08-01",
    },
    "data_modification_policy": {
        "content": "Only authorized Ops and Finance roles can modify customer billing data. All changes logged and audited. Requires ticket ID and approval.",
        "last_updated": "2024-01-15",
    },
    "escalation_policy": {
        "content": "Escalate to Head of Ops: strategic decisions, policy exceptions, or decisions affecting >10% of customer base. Escalate to CFO: pricing changes, discounts >25%, revenue-impacting decisions.",
        "last_updated": "2024-03-20",
    },
}

# ============================================================================
# PHASE 2: INTENT CLASSIFICATION
# ============================================================================

class IntentClassifier:
    """Simple regex-based intent classifier. Deliberately primitive."""

    # Patterns for metrics queries
    METRICS_PATTERNS = [
        r"(churn|revenue|nps|mrr|arr|customer|retention|growth)",
        r"(what was|what is|give me|show me).*(metric|rate|score|number)",
        r"(q[1-4]|january|february|march|april|may|june|july|august|september|october|november|december)\s+(2024|2023)",
    ]

    # Patterns for policy questions
    POLICY_PATTERNS = [
        r"(policy|rule|procedure|process|guideline|when|when can|can we|should we|allowed)",
        r"(discount|approval|exception|modification|change)",
    ]

    # Patterns for dangerous requests (data modification)
    DANGEROUS_PATTERNS = [
        r"(update|modify|change|delete|remove).*(billing|status|customer|data|record)",
        r"(can you|please).*(trigger|execute|run|activate).*(workflow|action|process)",
        r"(change).*(customer|account).*(status|tier|plan)",
    ]

    @staticmethod
    def classify(query: str) -> Intent:
        """Classify user query intent using regex patterns."""
        query_lower = query.lower().strip()

        # Check for dangerous requests first (safety first)
        for pattern in IntentClassifier.DANGEROUS_PATTERNS:
            if re.search(pattern, query_lower):
                return Intent.DATA_MODIFICATION

        # Check for metrics queries
        for pattern in IntentClassifier.METRICS_PATTERNS:
            if re.search(pattern, query_lower):
                return Intent.METRICS_QUERY

        # Check for policy questions
        for pattern in IntentClassifier.POLICY_PATTERNS:
            if re.search(pattern, query_lower):
                return Intent.POLICY_QUESTION

        # Default: unknown
        return Intent.UNKNOWN


# ============================================================================
# PHASE 2: RESPONSE GENERATOR
# ============================================================================

class BaselineAgent:
    """Rules-based agent with template responses. Exposes key limitations."""

    def __init__(self):
        self.conversation_history = []
        self.interaction_log = []

    def respond(self, query: str) -> dict:
        """Main response generation method."""
        timestamp = datetime.now().isoformat()
        intent = IntentClassifier.classify(query)

        # Route based on intent
        if intent == Intent.METRICS_QUERY:
            response, confidence = self._handle_metrics(query)
        elif intent == Intent.POLICY_QUESTION:
            response, confidence = self._handle_policy(query)
        elif intent == Intent.DATA_MODIFICATION:
            response, confidence = self._handle_dangerous_request(query)
        else:
            response, confidence = self._handle_unknown(query)

        # Build response object
        result = {
            "timestamp": timestamp,
            "user_query": query,
            "intent": intent.value,
            "response": response,
            "confidence": confidence,
            "sources": self._extract_sources(response),
            "escalation_flag": self._should_escalate(query, intent, confidence),
        }

        # Log interaction
        self.conversation_history.append(result)
        self.interaction_log.append(result)

        return result

    def _handle_metrics(self, query: str) -> Tuple[str, float]:
        """Template response for metrics queries. Limited by hardcoding."""
        # LIMITATION 1: No semantic understanding - uses simple string matching
        if "churn" in query.lower() and "2024" in query.lower():
            metric = METRICS_DB["Q3_2024_churn"]
            response = f"Q3 2024 churn: {metric['value']}. Previous year (Q3 2023): {METRICS_DB['Q3_2023_churn']['value']}. Trend: +1.5% YoY. Source: {metric['source']}."
            confidence = 0.95  # LIMITATION 2: Hardcoded confidence
            return response, confidence

        elif "nps" in query.lower() and "october" in query.lower():
            metric = METRICS_DB["nps_october"]
            response = f"NPS (October 2024): {metric['value']}. September 2024: {METRICS_DB['nps_september']['value']}. Trend: -3 points. Source: {metric['source']}."
            confidence = 0.92
            return response, confidence

        elif "enterprise" in query.lower() and "churn" in query.lower():
            metric = METRICS_DB["enterprise_churn"]
            smb_metric = METRICS_DB["smb_churn"]
            response = f"Enterprise churn: {metric['value']}. SMB churn: {smb_metric['value']}. SMB segment driving higher overall churn. Recommend investigation."
            confidence = 0.90
            return response, confidence

        else:
            # LIMITATION 3: Can't handle queries outside hardcoded list
            response = "I don't have a direct answer for that metric. Please ask about: churn, NPS, revenue, or enterprise/SMB segments."
            confidence = 0.30  # Very low confidence = I'm guessing
            return response, confidence

    def _handle_policy(self, query: str) -> Tuple[str, float]:
        """Template response for policy questions."""
        # LIMITATION 1: Hardcoded policy responses
        if "discount" in query.lower():
            policy = POLICIES["discount_policy"]
            response = f"Discount Policy: {policy['content']} (Last updated: {policy['last_updated']})"
            # LIMITATION 2: No reasoning about *why* the policy exists or implications
            confidence = 0.88
            return response, confidence

        elif "escalation" in query.lower() or "when to escalate" in query.lower():
            policy = POLICIES["escalation_policy"]
            response = f"Escalation Rules: {policy['content']} (Last updated: {policy['last_updated']})"
            confidence = 0.85
            return response, confidence

        else:
            response = "I can answer questions about discount policy, escalation procedures, and data modification rules."
            confidence = 0.40
            return response, confidence

    def _handle_dangerous_request(self, query: str) -> Tuple[str, float]:
        """Refuse data modification requests. Safety-first."""
        # This is a strength of Phase 2: simple refusals are bulletproof
        response = (
            "❌ I cannot modify customer data, billing status, or trigger workflows. "
            "This requires proper authorization and audit trail. "
            "Please contact the Finance or Ops team with your request. "
            "I can help you draft a summary to escalate to them, if needed."
        )
        confidence = 1.0  # 100% sure: DON'T DO THIS
        return response, confidence

    def _handle_unknown(self, query: str) -> Tuple[str, float]:
        """Fallback for unclassified queries."""
        # LIMITATION 4: No clarification questions - just punt
        response = (
            "I'm not sure how to answer that. I can help with: "
            "1) Metrics queries (churn, NPS, revenue, etc.) "
            "2) Policy questions (discounts, escalation rules) "
            "3) Data analysis questions about our customer base. "
            "Can you rephrase your question?"
        )
        confidence = 0.20  # Very low - truly uncertain
        return response, confidence

    def _extract_sources(self, response: str) -> list:
        """Extract source citations from response."""
        sources = []
        if "Analytics Dashboard" in response:
            sources.append("Analytics Dashboard")
        if "Surveys" in response:
            sources.append("Customer Surveys")
        if "Finance System" in response:
            sources.append("Finance System")
        if "Policy" in response:
            sources.append("Ops Manual")
        return sources

    def _should_escalate(self, query: str, intent: Intent, confidence: float) -> bool:
        """Simple escalation logic."""
        # LIMITATION 5: Hardcoded escalation rules
        if intent == Intent.DATA_MODIFICATION:
            return True  # Always escalate dangerous requests
        if confidence < 0.50:
            return True  # Escalate if very uncertain
        if "policy" in query.lower() and "should we" in query.lower():
            return True  # Escalate decisions
        return False

    def get_conversation_summary(self) -> dict:
        """Return summary of conversation so far."""
        return {
            "total_turns": len(self.conversation_history),
            "avg_confidence": sum(turn["confidence"] for turn in self.conversation_history) / max(1, len(self.conversation_history)),
            "escalations": sum(1 for turn in self.conversation_history if turn["escalation_flag"]),
            "intents_seen": list(set(turn["intent"] for turn in self.conversation_history)),
        }

    def export_logs(self, filename: str = "phase2_interaction_log.json"):
        """Export interaction logs for analysis."""
        with open(filename, "w") as f:
            json.dump(self.interaction_log, f, indent=2)
        print(f"[LOG] Exported {len(self.interaction_log)} interactions to {filename}")


# ============================================================================
# PHASE 2: DEMO / TEST INTERACTIONS
# ============================================================================

def run_demo():
    """Run 5 forced demo interactions showing both strengths and limitations."""
    agent = BaselineAgent()

    print("\n" + "=" * 80)
    print("PHASE 2: BASELINE AGENT DEMO")
    print("=" * 80 + "\n")

    # Test 1: Direct metric query (works)
    print("[Test 1] Direct Metric Query (Should Work)")
    print("-" * 80)
    query1 = "What was our churn rate in Q3 2024 compared to Q3 2023?"
    print(f"USER: {query1}")
    result1 = agent.respond(query1)
    print(f"AGENT: {result1['response']}")
    print(f"Confidence: {result1['confidence']:.0%} | Escalate: {result1['escalation_flag']}")
    print()

    # Test 2: Paraphrased metric query (breaks)
    print("[Test 2] Paraphrased Query (LIMITATION: No Semantic Understanding)")
    print("-" * 80)
    query2 = "How much customer attrition did we see last quarter?"
    print(f"USER: {query2}")
    result2 = agent.respond(query2)
    print(f"AGENT: {result2['response']}")
    print(f"Confidence: {result2['confidence']:.0%} | Expected: Would need semantic understanding")
    print(f"LIMITATION: Agent doesn't know 'attrition' = 'churn'")
    print()

    # Test 3: Policy question (works)
    print("[Test 3] Policy Question (Works)")
    print("-" * 80)
    query3 = "What's our discount approval process?"
    print(f"USER: {query3}")
    result3 = agent.respond(query3)
    print(f"AGENT: {result3['response']}")
    print(f"Confidence: {result3['confidence']:.0%}")
    print()

    # Test 4: Reasoning question (breaks)
    print("[Test 4] Why Question Requiring Synthesis (LIMITATION: No Reasoning)")
    print("-" * 80)
    query4 = "Why did our NPS drop from September to October?"
    print(f"USER: {query4}")
    result4 = agent.respond(query4)
    print(f"AGENT: {result4['response']}")
    print(f"LIMITATION: Agent can report numbers but can't synthesize root cause without LLM")
    print()

    # Test 5: Dangerous request (correctly refused)
    print("[Test 5] Safety Test: Data Modification Request (Correctly Refused)")
    print("-" * 80)
    query5 = "Can you update customer X's billing status to overdue?"
    print(f"USER: {query5}")
    result5 = agent.respond(query5)
    print(f"AGENT: {result5['response']}")
    print(f"Confidence: {result5['confidence']:.0%} (1.0 = REFUSE NO MATTER WHAT)")
    print(f"Escalation: {result5['escalation_flag']}")
    print()

    # Summary
    print("=" * 80)
    print("PHASE 2 SUMMARY")
    print("=" * 80)
    summary = agent.get_conversation_summary()
    print(f"Total interactions: {summary['total_turns']}")
    print(f"Average confidence: {summary['avg_confidence']:.0%}")
    print(f"Escalations triggered: {summary['escalations']}")
    print()
    print("KEY LIMITATIONS EXPOSED:")
    print("1. No semantic understanding (paraphrasing breaks the agent)")
    print("2. No multi-step reasoning (can't answer 'why' questions)")
    print("3. No cross-document synthesis (can't connect data to insights)")
    print("4. No clarification (punts on ambiguous questions)")
    print("5. Hardcoded responses (brittle, doesn't scale)")
    print()
    print("WHY WE NEED PHASE 3 (LLM Integration):")
    print("- LLM provides semantic understanding and reasoning")
    print("- Can handle novel question phrasings")
    print("- Can synthesize insights from multiple data points")
    print("- Can ask clarifying questions")
    print("\n")

    # Export logs
    agent.export_logs()


if __name__ == "__main__":
    run_demo()
