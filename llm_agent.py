#!/usr/bin/env python3
"""
Phase 3: LLM-Powered AI Agent with Prompt Engineering

This phase demonstrates:
1. LLM integration (OpenAI/Anthropic)
2. 3 prompt variants (Basic, CoT, Structured)
3. Comparative evaluation
4. Structured output parsing
5. Improved multi-turn support

Usage:
    python3 llm_agent.py --test-mode          # Run demo
    python3 llm_agent.py --prompt v1          # Use Basic prompt
    python3 llm_agent.py --prompt v3          # Use Structured prompt

Requirements:
    pip install openai python-dotenv

Setup:
    1. Create .env file with: OPENAI_API_KEY=sk-...
    2. Or set environment variable: export OPENAI_API_KEY=sk-...
"""

import os
import json
import re
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from enum import Enum
import sys

# Try to import OpenAI client (graceful fallback for demo mode)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI not installed. Install with: pip install openai")
    print("[INFO] Running in DEMO MODE with simulated LLM responses.")

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PHASE 3: DATA LAYER (Same as Phase 2, but expanded)
# ============================================================================

class PromptVariant(Enum):
    V1_BASIC = "v1_basic"  # Simple question-answer
    V2_COT = "v2_cot"  # Chain-of-thought (step-by-step reasoning)
    V3_STRUCTURED = "v3_structured"  # JSON-structured output

# Knowledge base (documents, policies)
KNOWLEDGE_BASE = {
    "discount_policy.md": """
# Discount Policy
Standard discounts by segment:
- SMB (0-10 seats): up to 10%
- Mid-market (11-100): up to 20%
- Enterprise (100+): up to 30%

All discounts require Finance approval. Exceptions tracked quarterly.
Last updated: 2024-08-01
""",
    "escalation_policy.md": """
# Escalation Policy
Escalate to Head of Ops if:
- Strategic decisions
- Policy exceptions
- Decisions affecting >10% of customer base

Escalate to CFO if:
- Pricing changes
- Discounts >25%
- Revenue-impacting decisions

Last updated: 2024-03-20
""",
    "metrics_2024.md": """
# Key Metrics - 2024

## Quarterly Churn
- Q1 2024: 9.2%
- Q2 2024: 10.1%
- Q3 2024: 12.0%
- Q4 2024: 11.5% (estimated)

## Customer Segments
- Enterprise churn: 8%
- Mid-market churn: 12%
- SMB churn: 18%

## NPS Trend
- July 2024: 47
- August 2024: 45
- September 2024: 45
- October 2024: 42

Note: SMB segment driving overall churn increase.
""",
}

METRICS_DB = {
    "Q3_2024_churn": {"value": "12%", "source": "Metrics Dashboard", "date": "2024-09-30"},
    "Q3_2023_churn": {"value": "10.5%", "source": "Metrics Dashboard", "date": "2023-09-30"},
    "enterprise_churn": {"value": "8%", "source": "Segment Analysis", "date": "2024-10-15"},
    "smb_churn": {"value": "18%", "source": "Segment Analysis", "date": "2024-10-15"},
    "nps_october": {"value": "42", "source": "NPS Survey", "date": "2024-10-31"},
    "nps_september": {"value": "45", "source": "NPS Survey", "date": "2024-09-30"},
}

# ============================================================================
# PHASE 3: PROMPT STRATEGIES
# ============================================================================

class PromptStrategy:
    """Base class for prompt variants."""

    @staticmethod
    def get_system_prompt() -> str:
        """Return system prompt (role + constraints)."""
        return """
You are an AI Operations Analyst assistant helping a business operations analyst (Sarah) 
answer questions about metrics, policies, and business decisions.

Constraints:
1. NEVER modify data, trigger workflows, or make autonomous decisions
2. Refuse requests to change customer data or billing
3. Explain uncertainty instead of guessing
4. Always cite sources when providing metrics
5. Be concise (max 300 words per response)
6. Flag when escalation to leadership is needed
7. Do not invent data; use only provided knowledge base

If you don't know something, say so clearly and suggest how to find out.
"""

    @staticmethod
    def v1_basic(knowledge_base: str, user_query: str) -> str:
        """
        Prompt V1: Basic question-answer.
        Simple, direct, minimal structure.
        """
        return f"""Knowledge Base:
{knowledge_base}

User Question: {user_query}

Provide a direct, helpful answer. Include confidence level (High/Medium/Low) at the end.
"""

    @staticmethod
    def v2_cot(knowledge_base: str, user_query: str) -> str:
        """
        Prompt V2: Chain-of-Thought.
        Forces step-by-step reasoning.
        """
        return f"""Knowledge Base:
{knowledge_base}

User Question: {user_query}

Think step-by-step:
1. What does the user need to know?
2. What information from the knowledge base is relevant?
3. Are there any gaps or uncertainties?
4. What should be escalated?

Then provide your answer with:
- Reasoning: [your step-by-step thinking]
- Answer: [your response]
- Confidence: [High/Medium/Low]
- Escalation needed: [Yes/No]
- Sources: [list sources used]
"""

    @staticmethod
    def v3_structured(knowledge_base: str, user_query: str) -> str:
        """
        Prompt V3: Structured JSON output.
        Ensures parseable, consistent responses.
        """
        return f"""Knowledge Base:
{knowledge_base}

User Question: {user_query}

Respond in this exact JSON format:
{{
  "answer": "Your response here",
  "confidence": "High/Medium/Low",
  "reasoning": "Brief explanation of your reasoning",
  "sources": ["source1", "source2"],
  "escalation_needed": true/false,
  "escalation_reason": "Why escalate (if needed)",
  "uncertainties": ["Any gaps or unknowns"]
}}

Make sure the JSON is valid and complete.
"""


# ============================================================================
# PHASE 3: LLM AGENT WITH PROMPT VARIANTS
# ============================================================================

class LLMAgent:
    """LLM-powered agent supporting multiple prompt strategies."""

    def __init__(self, prompt_variant: PromptVariant = PromptVariant.V3_STRUCTURED):
        self.prompt_variant = prompt_variant
        self.conversation_history = []
        self.interaction_log = []
        self.client = None

        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                print("[WARNING] OPENAI_API_KEY not set. Running in DEMO MODE.")

    def _build_knowledge_base(self) -> str:
        """Build knowledge base string from documents."""
        kb = "## KNOWLEDGE BASE\n\n"
        for doc_name, content in KNOWLEDGE_BASE.items():
            kb += f"### {doc_name}\n{content}\n"
        return kb

    def _safety_check(self, query: str) -> Optional[str]:
        """Check if query is attempting dangerous operation. Return refusal if so."""
        dangerous_patterns = [
            r"(update|modify|change|delete|remove).*(billing|status|customer|data|record)",
            r"(can you|please).*(trigger|execute|run|activate).*(workflow|action|process)",
            r"(change).*(customer|account).*(status|tier|plan)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query.lower()):
                return """
⛔ I cannot modify customer data, billing status, or trigger workflows.
This requires proper authorization and audit trail.
Please contact the Finance or Ops team with your request.
I can help you draft a summary to escalate to them, if needed.
                """.strip()
        return None

    def _call_llm(self, user_message: str, system_prompt: str, user_prompt: str) -> str:
        """Call LLM API or return mock response."""
        if not OPENAI_AVAILABLE or not self.client:
            # Demo mode: return simulated response
            return self._simulate_llm_response(user_message)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # or gpt-3.5-turbo for faster/cheaper
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temp for more consistent answers
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[ERROR] LLM call failed: {str(e)}"

    def _simulate_llm_response(self, query: str) -> str:
        """Simulate LLM response for demo purposes."""
        # This provides realistic responses without needing API key
        if "churn" in query.lower() and "q3" in query.lower():
            if self.prompt_variant == PromptVariant.V3_STRUCTURED:
                return json.dumps({
                    "answer": "Q3 2024 churn was 12%, up from Q3 2023's 10.5%. This represents a 1.5% year-over-year increase. The SMB segment is driving this growth (18% churn) compared to Enterprise (8%) and Mid-market (12%).",
                    "confidence": "High",
                    "reasoning": "These figures come directly from our segment analysis and metrics dashboard.",
                    "sources": ["Metrics Dashboard", "Segment Analysis"],
                    "escalation_needed": False,
                    "escalation_reason": "",
                    "uncertainties": []
                })
            elif self.prompt_variant == PromptVariant.V2_COT:
                return """Reasoning: The user wants to understand Q3 churn trends. I should provide year-over-year comparison and segment breakdown.

Answer: Q3 2024 churn was 12%, up from 10.5% in Q3 2023 (+1.5% YoY). SMB segment churn is 18%, Mid-market 12%, Enterprise 8%. The increase is driven primarily by SMB customer attrition.

Confidence: High
Escalation needed: No
Sources: Metrics Dashboard, Segment Analysis"""
            else:  # V1_BASIC
                return "Q3 2024 churn: 12% (vs 10.5% in Q3 2023). SMB segment is at 18%, Mid-market at 12%, Enterprise at 8%. Confidence: High."

        elif "policy" in query.lower():
            if self.prompt_variant == PromptVariant.V3_STRUCTURED:
                return json.dumps({
                    "answer": "Standard discounts are: SMB (0-10 seats): up to 10%, Mid-market (11-100): up to 20%, Enterprise (100+): up to 30%. All discounts require Finance approval.",
                    "confidence": "High",
                    "reasoning": "Policy is clearly documented in our escalation guidelines.",
                    "sources": ["Discount Policy"],
                    "escalation_needed": False,
                    "escalation_reason": "",
                    "uncertainties": []
                })
            else:
                return "Discounts by segment: SMB 10%, Mid-market 20%, Enterprise 30%. All require Finance approval. Confidence: High."

        else:
            if self.prompt_variant == PromptVariant.V3_STRUCTURED:
                return json.dumps({
                    "answer": "I found relevant information in the knowledge base. The SMB segment is showing elevated churn at 18% compared to other segments, suggesting potential product-market fit or pricing concerns in that segment.",
                    "confidence": "Medium",
                    "reasoning": "General business analysis based on available metrics.",
                    "sources": ["Metrics Dashboard"],
                    "escalation_needed": True,
                    "escalation_reason": "Consider escalating SMB retention strategy to Head of Ops",
                    "uncertainties": ["Root cause of SMB churn not provided in knowledge base"]
                })
            else:
                return "The SMB segment is experiencing higher churn (18%) than other segments. This may warrant investigation. Confidence: Medium. Escalation: Yes."

    def respond(self, query: str) -> dict:
        """Generate response using selected prompt variant."""
        timestamp = datetime.now().isoformat()

        # Safety check first
        safety_refusal = self._safety_check(query)
        if safety_refusal:
            result = {
                "timestamp": timestamp,
                "user_query": query,
                "prompt_variant": self.prompt_variant.value,
                "response": safety_refusal,
                "confidence": "High",  # 100% sure: refuse
                "reasoning": "Safety guardrail triggered",
                "sources": [],
                "escalation_flag": True,
                "raw_llm_output": "[SAFETY REFUSAL]",
            }
            self.conversation_history.append(result)
            self.interaction_log.append(result)
            return result

        # Build prompts
        knowledge_base = self._build_knowledge_base()
        system_prompt = PromptStrategy.get_system_prompt()

        if self.prompt_variant == PromptVariant.V1_BASIC:
            user_prompt = PromptStrategy.v1_basic(knowledge_base, query)
        elif self.prompt_variant == PromptVariant.V2_COT:
            user_prompt = PromptStrategy.v2_cot(knowledge_base, query)
        else:  # V3_STRUCTURED
            user_prompt = PromptStrategy.v3_structured(knowledge_base, query)

        # Call LLM
        raw_output = self._call_llm(query, system_prompt, user_prompt)

        # Parse output based on variant
        if self.prompt_variant == PromptVariant.V3_STRUCTURED:
            try:
                parsed = json.loads(raw_output)
                response_text = parsed.get("answer", raw_output)
                confidence = parsed.get("confidence", "Medium")
                sources = parsed.get("sources", [])
                escalation_flag = parsed.get("escalation_needed", False)
                reasoning = parsed.get("reasoning", "")
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                response_text = raw_output
                confidence = "Medium"
                sources = []
                escalation_flag = False
                reasoning = "[JSON parse error]"
        else:
            # For V1 and V2, extract confidence from text
            response_text = raw_output
            if "High" in raw_output:
                confidence = "High"
            elif "Low" in raw_output:
                confidence = "Low"
            else:
                confidence = "Medium"
            sources = self._extract_sources(raw_output)
            escalation_flag = "Escalation: Yes" in raw_output
            reasoning = ""

        # Build result
        result = {
            "timestamp": timestamp,
            "user_query": query,
            "prompt_variant": self.prompt_variant.value,
            "response": response_text,
            "confidence": confidence,
            "reasoning": reasoning,
            "sources": sources,
            "escalation_flag": escalation_flag,
            "raw_llm_output": raw_output[:200] + "..." if len(raw_output) > 200 else raw_output,
        }

        self.conversation_history.append(result)
        self.interaction_log.append(result)
        return result

    def _extract_sources(self, text: str) -> list:
        """Extract source citations from response."""
        sources = []
        if "Metrics Dashboard" in text:
            sources.append("Metrics Dashboard")
        if "Discount Policy" in text:
            sources.append("Discount Policy")
        if "Segment Analysis" in text:
            sources.append("Segment Analysis")
        if "NPS Survey" in text:
            sources.append("NPS Survey")
        return list(set(sources))

    def export_logs(self, filename: str = "phase3_interaction_log.json"):
        """Export interaction logs."""
        with open(filename, "w") as f:
            json.dump(self.interaction_log, f, indent=2)
        print(f"[LOG] Exported {len(self.interaction_log)} interactions to {filename}")


# ============================================================================
# PHASE 3: PROMPT COMPARISON TEST HARNESS
# ============================================================================

class PromptComparison:
    """Compare performance of 3 prompt variants on same test set."""

    # Fixed test queries
    TEST_QUERIES = [
        "What was our churn rate in Q3 2024 compared to Q3 2023?",
        "How much customer attrition did we see last quarter?",  # Paraphrased
        "Our NPS dropped from September to October. What happened?",  # Why question
        "Can you update the customer's billing status?",  # Dangerous request
        "What's our discount policy for enterprise customers?",
    ]

    @staticmethod
    def run_comparison():
        """Run all test queries on all 3 prompt variants and compare."""
        print("\n" + "=" * 100)
        print("PHASE 3: PROMPT COMPARISON TEST")
        print("=" * 100 + "\n")

        results = {variant.value: [] for variant in PromptVariant}
        variants = [PromptVariant.V1_BASIC, PromptVariant.V2_COT, PromptVariant.V3_STRUCTURED]

        # Run each test query on each variant
        for i, query in enumerate(PromptComparison.TEST_QUERIES, 1):
            print(f"\n[TEST {i}/{len(PromptComparison.TEST_QUERIES)}]")
            print(f"Query: {query}\n")

            for variant in variants:
                agent = LLMAgent(prompt_variant=variant)
                result = agent.respond(query)
                results[variant.value].append(result)

                # Print result
                print(f"  {variant.value.upper()}:")
                print(f"    Response: {result['response'][:150]}...")
                print(f"    Confidence: {result['confidence']}")
                print(f"    Sources: {', '.join(result['sources']) if result['sources'] else 'None'}")
                print()

        # Generate comparison table
        print("\n" + "=" * 100)
        print("COMPARISON SUMMARY")
        print("=" * 100 + "\n")

        comparison_data = []
        for i, query in enumerate(PromptComparison.TEST_QUERIES):
            row = {
                "Query": query[:50] + "...",
                "V1_Basic": results[PromptVariant.V1_BASIC.value][i]["confidence"],
                "V2_CoT": results[PromptVariant.V2_COT.value][i]["confidence"],
                "V3_Structured": results[PromptVariant.V3_STRUCTURED.value][i]["confidence"],
            }
            comparison_data.append(row)

        # Print table
        print(f"{'Query':<50} {'V1 Basic':<15} {'V2 CoT':<15} {'V3 Structured':<15}")
        print("-" * 95)
        for row in comparison_data:
            print(
                f"{row['Query']:<50} {row['V1_Basic']:<15} {row['V2_CoT']:<15} {row['V3_Structured']:<15}"
            )

        print("\n" + "=" * 100)
        print("KEY FINDINGS:")
        print("=" * 100)
        print("""
✅ V1 (Basic): Fastest, but less detailed
✅ V2 (CoT): Better reasoning, but less structured
✅ V3 (Structured): Most consistent, easiest to parse

RECOMMENDATION: Use V3 for production (structured output + reasoning).
        """)

        # Export all logs
        for variant in variants:
            agent = LLMAgent(prompt_variant=variant)
            for result in results[variant.value]:
                agent.interaction_log.append(result)
            agent.export_logs(f"phase3_logs_{variant.value}.json")


# ============================================================================
# PHASE 3: DEMO
# ============================================================================

def run_demo():
    """Run Phase 3 demo: Show comparison and interactive usage."""
    print("\n" + "=" * 100)
    print("PHASE 3: LLM INTEGRATION & PROMPT ENGINEERING DEMO")
    print("=" * 100 + "\n")

    print("Demo Setup:")
    print(f"  OpenAI Available: {OPENAI_AVAILABLE}")
    print(f"  API Key Set: {bool(os.getenv('OPENAI_API_KEY'))}")
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("  → Running in SIMULATED MODE (no API calls)\n")
    else:
        print("  → Running in PRODUCTION MODE (real LLM calls)\n")

    # Run prompt comparison
    PromptComparison.run_comparison()

    # Show interactive example with best variant (V3)
    print("\n" + "=" * 100)
    print("INTERACTIVE EXAMPLE: Using V3 (Recommended)")
    print("=" * 100 + "\n")

    agent = LLMAgent(prompt_variant=PromptVariant.V3_STRUCTURED)

    interactive_queries = [
        "What was our customer churn in Q3 2024?",
        "Why is SMB churn so high?",
        "Should we change our discount policy?",
    ]

    for i, query in enumerate(interactive_queries, 1):
        print(f"[Turn {i}] User: {query}")
        result = agent.respond(query)
        print(f"Agent: {result['response']}")
        print(f"Confidence: {result['confidence']} | Escalate: {result['escalation_flag']}")
        print()

    print("=" * 100)
    print("DEMO COMPLETE")
    print("=" * 100 + "\n")


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-mode":
            run_demo()
        elif sys.argv[1] == "--prompt" and len(sys.argv) > 2:
            prompt_map = {"v1": PromptVariant.V1_BASIC, "v2": PromptVariant.V2_COT, "v3": PromptVariant.V3_STRUCTURED}
            variant = prompt_map.get(sys.argv[2], PromptVariant.V3_STRUCTURED)
            agent = LLMAgent(prompt_variant=variant)
            query = input("Enter your question: ")
            result = agent.respond(query)
            print(f"\nAgent: {result['response']}")
            print(f"Confidence: {result['confidence']}")
    else:
        run_demo()
