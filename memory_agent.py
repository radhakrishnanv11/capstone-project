#!/usr/bin/env python3
"""
Phase 6: Conversation Memory & Planning

This phase demonstrates:
1. Multi-turn conversation memory
2. Reference resolution (pronouns: "it", "that", etc.)
3. Query complexity assessment
4. Plan decomposition for complex queries
5. Conversation summarization

Requirements:
    pip install openai python-dotenv

Usage:
    python3 memory_agent.py --test-mode          # Run demo
    python3 memory_agent.py --multi-turn          # Run multi-turn scenario
    python3 memory_agent.py --complex-query       # Test plan decomposition
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum
import sys

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI not installed")

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PHASE 6: CONVERSATION MEMORY SYSTEM
# ============================================================================

class ConversationTurn:
    """Single turn in a conversation."""
    
    def __init__(self, turn_id: int, query: str, response: str, tools_used: List[str] = None):
        self.turn_id = turn_id
        self.timestamp = datetime.now().isoformat()
        self.query = query
        self.response = response
        self.tools_used = tools_used or []
        self.key_facts = {}  # Extracted entities and facts
        self.references = []  # What prior turns this references
    
    def to_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "timestamp": self.timestamp,
            "query": self.query,
            "response": self.response[:500],  # Truncate for display
            "tools_used": self.tools_used,
            "key_facts": self.key_facts,
            "references": self.references
        }


class ConversationMemory:
    """Manages conversation history and state."""
    
    def __init__(self, session_id: str = None, max_turns_in_context: int = 10):
        self.session_id = session_id or f"session_{datetime.now().timestamp()}"
        self.turns: List[ConversationTurn] = []
        self.max_turns_in_context = max_turns_in_context
        self.goals: List[str] = []  # High-level conversation goals
        self.decisions_made: List[Dict] = []  # Decisions from conversation
        self.escalations: List[Dict] = []  # Escalation items
    
    def add_turn(self, query: str, response: str, tools_used: List[str] = None, key_facts: Dict = None) -> ConversationTurn:
        """Add a turn to conversation history."""
        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            query=query,
            response=response,
            tools_used=tools_used
        )
        if key_facts:
            turn.key_facts = key_facts
        self.turns.append(turn)
        return turn
    
    def get_context_window(self) -> str:
        """Build context string from recent turns."""
        # Include last N turns plus summary of older turns
        context = f"## Conversation History (Session: {self.session_id})\n\n"
        
        if len(self.turns) > self.max_turns_in_context:
            # Summarize old turns
            old_turns = self.turns[:-self.max_turns_in_context]
            summary = f"Earlier turns ({len(old_turns)}): "
            key_facts = {}
            for turn in old_turns:
                key_facts.update(turn.key_facts)
            summary += json.dumps(key_facts, default=str)
            context += summary + "\n\n"
        
        # Include recent turns in full
        recent_turns = self.turns[-self.max_turns_in_context:]
        for turn in recent_turns:
            context += f"Turn {turn.turn_id}: User: {turn.query}\n"
            context += f"Agent: {turn.response[:200]}...\n\n"
        
        return context
    
    def resolve_references(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """Resolve pronouns and references in query."""
        resolved_query = query
        references = {}
        
        # Common pronouns and their resolution
        pronouns = ["it", "that", "these", "those", "they", "them", "this"]
        
        for pronoun in pronouns:
            if f" {pronoun} " in query.lower() or query.lower().startswith(pronoun):
                # Find most recent fact that could be referenced
                if self.turns:
                    last_turn = self.turns[-1]
                    if last_turn.key_facts:
                        # Resolve to most recent entity
                        main_fact = list(last_turn.key_facts.values())[0] if last_turn.key_facts else None
                        if main_fact:
                            resolved_query = resolved_query.replace(pronoun, str(main_fact))
                            references[pronoun] = str(main_fact)
        
        return resolved_query, references
    
    def get_summary(self) -> Dict[str, Any]:
        """Generate summary of conversation."""
        all_facts = {}
        for turn in self.turns:
            all_facts.update(turn.key_facts)
        
        return {
            "session_id": self.session_id,
            "total_turns": len(self.turns),
            "goals": self.goals,
            "key_facts": all_facts,
            "decisions_made": self.decisions_made,
            "escalations": self.escalations,
            "duration_seconds": (datetime.now() - datetime.fromisoformat(self.turns[0].timestamp)).total_seconds() if self.turns else 0
        }
    
    def export_conversation(self, filename: str = None) -> str:
        """Export conversation for audit/logging."""
        if not filename:
            filename = f"conversation_{self.session_id}.json"
        
        export_data = {
            "summary": self.get_summary(),
            "turns": [turn.to_dict() for turn in self.turns]
        }
        
        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)
        
        return filename


# ============================================================================
# PHASE 6: PLANNING SYSTEM
# ============================================================================

class QueryComplexityLevel(Enum):
    """Complexity levels for queries."""
    SIMPLE = "simple"  # Single-turn answer
    MODERATE = "moderate"  # Requires context + 1-2 tool calls
    COMPLEX = "complex"  # Requires multi-step plan


class PlanStep:
    """Single step in a multi-step plan."""
    
    def __init__(self, step_id: int, goal: str, tool_calls: List[Dict] = None, step_type: str = "tool"):
        self.step_id = step_id
        self.goal = goal
        self.tool_calls = tool_calls or []
        self.step_type = step_type  # "tool", "synthesis", "decision"
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
        self.dependencies = []  # Step IDs this depends on
    
    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "goal": self.goal,
            "tool_calls": self.tool_calls,
            "step_type": self.step_type,
            "status": self.status,
            "dependencies": self.dependencies
        }


class QueryPlanner:
    """Plans multi-step queries."""
    
    @staticmethod
    def assess_complexity(query: str, conversation_context: str = "") -> QueryComplexityLevel:
        """Assess query complexity."""
        query_lower = query.lower()
        
        # Complex queries contain action verbs + multiple entities
        complex_keywords = ["find all", "analyze", "compare", "recommend", "develop", "create", "strategy"]
        multiple_entities = query_lower.count(" and ") + query_lower.count(",")
        
        if any(kw in query_lower for kw in complex_keywords) and multiple_entities >= 2:
            return QueryComplexityLevel.COMPLEX
        elif query_lower.count("?") > 1 or "why" in query_lower:
            return QueryComplexityLevel.MODERATE
        else:
            return QueryComplexityLevel.SIMPLE
    
    @staticmethod
    def decompose_query(query: str, complexity: QueryComplexityLevel) -> List[PlanStep]:
        """Decompose complex query into steps."""
        steps = []
        
        if complexity == QueryComplexityLevel.SIMPLE:
            # Single step: answer directly
            steps.append(PlanStep(1, f"Answer: {query}", step_type="synthesis"))
        
        elif complexity == QueryComplexityLevel.MODERATE:
            # Two steps: retrieve context + answer
            steps.append(PlanStep(1, "Retrieve relevant context", step_type="tool"))
            steps.append(PlanStep(2, f"Answer query: {query}", step_type="synthesis", dependencies=[1]))
        
        elif complexity == QueryComplexityLevel.COMPLEX:
            # Multi-step plan
            if "at-risk" in query.lower() and "customer" in query.lower():
                steps.append(PlanStep(1, "Identify at-risk customers", step_type="tool"))
                steps.append(PlanStep(2, "Check discount eligibility", step_type="tool", dependencies=[1]))
                steps.append(PlanStep(3, "Verify policy compliance", step_type="tool", dependencies=[2]))
                steps.append(PlanStep(4, "Synthesize strategy", step_type="synthesis", dependencies=[1, 2, 3]))
            
            elif "find" in query.lower() and "recommend" in query.lower():
                steps.append(PlanStep(1, "Search and analyze", step_type="tool"))
                steps.append(PlanStep(2, "Identify options", step_type="tool", dependencies=[1]))
                steps.append(PlanStep(3, "Evaluate and recommend", step_type="synthesis", dependencies=[1, 2]))
        
        return steps


# ============================================================================
# PHASE 6: MEMORY-AWARE AGENT
# ============================================================================

class MemoryAgent:
    """Agent with conversation memory and planning."""
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.planner = QueryPlanner()
        self.client = None
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _simulate_tool_call(self, tool_name: str, query_fragment: str) -> str:
        """Simulate tool execution."""
        # Mock tool results based on query
        if "churn" in query_fragment.lower():
            return json.dumps({
                "smb_churn": 18.2,
                "enterprise_churn": 8.0,
                "mid_market_churn": 12.0,
                "unit": "%",
                "freshness": "today"
            })
        elif "risk" in query_fragment.lower():
            return json.dumps({
                "at_risk_customers": [
                    {"id": "cust_002", "risk_score": 0.8, "segment": "smb"},
                    {"id": "cust_005", "risk_score": 0.75, "segment": "smb"},
                ],
                "total_at_risk": 45
            })
        else:
            return json.dumps({"data": "Tool result for: " + query_fragment})
    
    def respond(self, query: str, extract_facts: Dict = None) -> str:
        """Process query with memory and planning."""
        # Step 1: Resolve references in query
        resolved_query, references = self.memory.resolve_references(query)
        
        # Step 2: Assess complexity
        complexity = self.planner.assess_complexity(resolved_query, self.memory.get_context_window())
        
        # Step 3: Plan if complex
        if complexity == QueryComplexityLevel.COMPLEX:
            plan = self.planner.decompose_query(resolved_query, complexity)
            response = f"[Complex Query Plan]\nI'll solve this in {len(plan)} steps:\n"
            for step in plan:
                response += f"  Step {step.step_id}: {step.goal}\n"
            response += "\n[Executing steps...]\n"
            
            # Simulate step execution
            results = []
            for step in plan:
                if step.step_type == "tool":
                    result = self._simulate_tool_call("generic", resolved_query)
                    results.append(result)
                    response += f"  ✓ Step {step.step_id} complete\n"
            
            response += "\n[Final Synthesis]\n"
            response += "Based on the analysis: SMB churn is 18.2%, driven by pricing concerns. "
            response += "Recommended strategy: Create SMB pricing tier, improve support SLA, "
            response += "develop retention playbook for at-risk customers."
        
        else:
            # Simple or moderate query: direct answer
            if resolved_query != query:
                response = f"[Resolving: '{query}' → '{resolved_query}']\n\n"
            else:
                response = ""
            
            # Generate response based on query
            if "churn" in resolved_query.lower():
                response += "SMB churn is 18.2% this quarter, up from 15% last quarter. "
                response += "Primary driver is price sensitivity. Enterprise remains stable at 8%."
            elif "enterprise" in resolved_query.lower():
                response += "Enterprise segment has 8% churn and NPS of 52, showing stability. "
                response += "This is our most profitable segment."
            else:
                response += "Based on our conversation so far, I can help analyze metrics, "
                response += "identify root causes, and develop strategies."
        
        # Step 4: Add turn to memory
        key_facts = extract_facts or {}
        if "churn" in resolved_query.lower():
            key_facts["churn_discussed"] = True
            key_facts["smb_churn"] = 18.2
        
        self.memory.add_turn(
            query=query,
            response=response,
            key_facts=key_facts
        )
        
        return response
    
    def multi_turn_conversation(self, queries: List[str], facts_per_query: List[Dict] = None) -> List[str]:
        """Run multi-turn conversation."""
        responses = []
        facts = facts_per_query or [{} for _ in queries]
        
        for i, (query, fact) in enumerate(zip(queries, facts)):
            print(f"\n[Turn {i+1}] User: {query}")
            response = self.respond(query, extract_facts=fact)
            print(f"[Turn {i+1}] Agent: {response}")
            responses.append(response)
        
        return responses


# ============================================================================
# PHASE 6: DEMO
# ============================================================================

def run_demo():
    """Run Phase 6 demo."""
    print("\n" + "=" * 100)
    print("PHASE 6: CONVERSATION MEMORY & PLANNING DEMO")
    print("=" * 100 + "\n")
    
    agent = MemoryAgent()
    
    # Demo 1: Multi-turn conversation
    print("DEMO 1: Multi-Turn Conversation (Reference Resolution)")
    print("=" * 100)
    
    queries = [
        "What's our SMB churn this quarter?",
        "Is that higher than enterprise?",
        "Why the big difference?",
        "What should we do about it?"
    ]
    
    facts = [
        {"metric": "churn", "segment": "smb"},
        {"comparison": "smb_vs_enterprise"},
        {"analysis_type": "root_cause"},
        {"query_type": "action_plan"}
    ]
    
    agent.multi_turn_conversation(queries, facts)
    
    # Demo 2: Complex query with planning
    print("\n" + "=" * 100)
    print("DEMO 2: Complex Query with Plan Decomposition")
    print("=" * 100 + "\n")
    
    complex_query = "Find our top 5 at-risk SMB customers, check if they're discount-eligible, and draft a retention strategy"
    print(f"[Complex Query] {complex_query}\n")
    
    complexity = agent.planner.assess_complexity(complex_query)
    print(f"[Complexity Level] {complexity.value.upper()}\n")
    
    plan = agent.planner.decompose_query(complex_query, complexity)
    print("[Execution Plan]")
    for step in plan:
        print(f"  Step {step.step_id}: {step.goal} (type: {step.step_type})")
        if step.dependencies:
            print(f"    Depends on: Step(s) {step.dependencies}")
    print()
    
    response = agent.respond(complex_query)
    print(f"[Agent Response]\n{response}\n")
    
    # Demo 3: Show conversation memory
    print("\n" + "=" * 100)
    print("DEMO 3: Conversation Memory Summary")
    print("=" * 100 + "\n")
    
    summary = agent.memory.get_summary()
    print(f"Session ID: {summary['session_id']}")
    print(f"Total Turns: {summary['total_turns']}")
    print(f"Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"Key Facts: {summary['key_facts']}")
    
    # Export conversation
    filename = agent.memory.export_conversation()
    print(f"\nConversation exported to: {filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--multi-turn":
            agent = MemoryAgent()
            agent.multi_turn_conversation([
                "What's our churn?",
                "Which segment is worst?",
                "Why that segment?",
                "What should we do?"
            ])
        elif sys.argv[1] == "--complex-query":
            agent = MemoryAgent()
            query = "Identify all at-risk customers and recommend retention strategy"
            print(f"Query: {query}")
            print(agent.respond(query))
        else:
            run_demo()
    else:
        run_demo()
