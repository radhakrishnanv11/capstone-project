#!/usr/bin/env python3
"""
Phase 4: RAG (Retrieval-Augmented Generation) Agent

This phase demonstrates:
1. Document embedding and indexing
2. Semantic similarity search
3. Retrieved context passage to LLM
4. Retrieval quality metrics (precision, recall, MRR)
5. Explicit handling of missing information

Requirements:
    pip install openai python-dotenv numpy sklearn

Usage:
    python3 rag_agent.py --test-mode          # Run demo
    python3 rag_agent.py --build-index        # Build/rebuild vector index
    python3 rag_agent.py --eval-retrieval     # Evaluate retrieval quality
"""

import os
import json
import re
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, Dict, List
from enum import Enum
import sys
import pickle

# Try to import required libraries
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARNING] OpenAI not installed. Install with: pip install openai")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("[WARNING] scikit-learn not installed. Install with: pip install scikit-learn")

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PHASE 4: EXPANDED KNOWLEDGE BASE (Documents)
# ============================================================================

DOCUMENTS = [
    {
        "id": "doc_1",
        "title": "Discount Policy",
        "content": """
# Discount Policy (2024)

Standard discount tiers by customer segment:
- SMB (0-10 seats): Up to 10% discount
- Mid-market (11-100 seats): Up to 20% discount  
- Enterprise (100+ seats): Up to 30% discount

All discounts above 5% require Finance approval.
Discounts above 25% require CFO sign-off.

Annual discount exceptions are tracked quarterly.
We cannot exceed 20% average discount per segment.

Last Updated: 2024-08-01
        """,
    },
    {
        "id": "doc_2",
        "title": "Customer Churn Analysis Q3 2024",
        "content": """
# Customer Churn Analysis - Q3 2024

Overall churn: 12.0% (vs 10.5% in Q3 2023)
Change: +1.5% YoY

## By Segment:
- Enterprise: 8.0% (stable)
- Mid-market: 12.0% (up from 11%)
- SMB: 18.0% (up from 15%)

## Top Churn Reasons:
1. Price sensitivity (36% of SMB churn)
2. Product-market fit issues (28%)
3. Better alternatives available (21%)
4. Support quality (15%)

## Recommendations:
- Review SMB pricing strategy
- Improve SMB onboarding
- Enhance support for SMB tier
- Consider pricing tiers for different use cases

Report Date: 2024-10-15
        """,
    },
    {
        "id": "doc_3",
        "title": "NPS and Customer Satisfaction Trends",
        "content": """
# NPS and Customer Satisfaction Trends

## NPS Scores:
- July 2024: 47
- August 2024: 45
- September 2024: 45
- October 2024: 42

Trend: Declining (-5 points over 3 months)

## Sentiment by Segment:
- Enterprise NPS: 52 (positive)
- Mid-market NPS: 44 (neutral)
- SMB NPS: 38 (concerning)

## Root Causes of NPS Decline:
1. SMB segment experiencing product issues
2. Slow support response times for lower tiers
3. Price increases in Q3 affected perception
4. Feature requests not being implemented

## Action Items:
- Improve SMB support SLA
- Review feature roadmap prioritization
- Communicate value more clearly

Last Updated: 2024-10-31
        """,
    },
    {
        "id": "doc_4",
        "title": "Revenue and MRR Forecast",
        "content": """
# Revenue and MRR Forecast

## Current MRR:
- Q3 2024: $2.1M
- Q4 2024 Forecast: $2.05M (down due to churn)

## Revenue by Segment:
- Enterprise: $1.4M (66% of revenue)
- Mid-market: $0.5M (24%)
- SMB: $0.2M (10%)

## Growth Rate:
- YoY growth: +8% (down from 15% historical)
- MoM growth: -2% (concerning)

## Forecast for 2025:
- If churn continues: $2.0M MRR
- If we address SMB issues: $2.3M MRR

## Key Lever:
Reducing SMB churn from 18% to 12% would add $120K/year in revenue.

Last Updated: 2024-10-31
        """,
    },
    {
        "id": "doc_5",
        "title": "Escalation Policy and Decision Authority",
        "content": """
# Escalation Policy and Decision Authority

## When to Escalate to Head of Ops:
- Strategic business decisions
- Policy exceptions (discount >20%)
- Changes affecting >10% of customer base
- High-value customer retention issues
- Operational process changes

## When to Escalate to CFO:
- Pricing changes
- Discounts exceeding 25%
- Revenue-impacting decisions
- Customer refunds/credits >$5K
- Budget allocation questions

## When to Escalate to VP of Product:
- Feature prioritization requests
- Product roadmap changes
- Customer-specific product needs
- Product quality issues

## Analyst Authority (Sarah's Level):
- Can provide analysis and recommendations
- Cannot approve discounts >10%
- Cannot make pricing decisions
- Can draft recommendations for leadership
- Should always explain uncertainty

Last Updated: 2024-03-20
        """,
    },
    {
        "id": "doc_6",
        "title": "SMB Segment Strategy Review",
        "content": """
# SMB Segment Strategy Review

## Current State:
- 500 SMB customers
- 18% churn rate (unacceptable)
- NPS: 38 (concerning)
- ARPU: $400/month
- Acquisition cost: $800 per customer

## Problems Identified:
1. Product not optimized for SMB use cases
2. Support response time: 24-48 hours (SMB expects <4 hours)
3. Pricing: $50/user/month may be too high for SMB
4. Onboarding: No self-serve option
5. Documentation: Assumes enterprise knowledge

## Proposed Solutions:
1. Create SMB-specific product tier (simplified features)
2. Hire 2 SMB support specialists (improved response time)
3. Test pricing tiers: $20/$35/$50 per user/month
4. Build self-serve onboarding flow
5. Create SMB-focused documentation and guides

## Expected Impact:
- Reduce churn to 12% (saves 300 customers/year)
- Improve NPS to 48+ (competitive)
- Increase SMB ARPU by 15% (premium tier)

## Budget Required:
- Personnel: $180K/year
- Product development: $100K
- Marketing/sales: $50K
Total: $330K (breaks even in 3 months with retained customers)

Last Updated: 2024-10-20
        """,
    },
]

# ============================================================================
# PHASE 4: SIMPLE EMBEDDING & RETRIEVAL (No External API)
# ============================================================================

class SimpleEmbedding:
    """Lightweight embedding based on TF-IDF. Works without OpenAI."""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Simple tokenization."""
        text = text.lower()
        # Remove special characters, split on whitespace
        tokens = re.findall(r"\b\w+\b", text)
        # Filter out short tokens and common stopwords
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "is", "are", "was", "were", "be", "by", "with", "as", "if"
        }
        return [t for t in tokens if len(t) > 2 and t not in stopwords]

    @staticmethod
    def embed(text: str, vocab: dict) -> np.ndarray:
        """Convert text to TF-IDF-like embedding."""
        tokens = SimpleEmbedding.tokenize(text)
        embedding = np.zeros(len(vocab))
        for token in tokens:
            if token in vocab:
                embedding[vocab[token]] += 1
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding


class VectorStore:
    """In-memory vector store with cosine similarity search."""

    def __init__(self):
        self.documents = []
        self.embeddings = []
        self.vocab = {}
        self.next_token_id = 0

    def build_vocab(self, documents: List[dict]):
        """Build vocabulary from all documents."""
        all_tokens = set()
        for doc in documents:
            tokens = SimpleEmbedding.tokenize(doc["content"])
            all_tokens.update(tokens)

        self.vocab = {token: i for i, token in enumerate(sorted(all_tokens))}
        self.next_token_id = len(self.vocab)

    def index_documents(self, documents: List[dict]):
        """Index documents into vector store."""
        self.documents = documents
        self.build_vocab(documents)

        self.embeddings = []
        for doc in documents:
            embedding = SimpleEmbedding.embed(doc["content"], self.vocab)
            self.embeddings.append(embedding)

        print(f"[INFO] Indexed {len(documents)} documents with vocab size {len(self.vocab)}")

    def search(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """Search for top-k most similar documents."""
        query_embedding = SimpleEmbedding.embed(query, self.vocab)

        similarities = []
        for i, doc_embedding in enumerate(self.embeddings):
            # Compute cosine similarity
            sim = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding) + 1e-10
            )
            similarities.append((i, sim))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top-k documents with their similarity scores
        results = []
        for idx, sim in similarities[:k]:
            results.append((self.documents[idx], sim))

        return results


# ============================================================================
# PHASE 4: RAG AGENT WITH RETRIEVAL
# ============================================================================

class RAGAgent:
    """Agent with Retrieval-Augmented Generation (RAG)."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.vector_store.index_documents(DOCUMENTS)
        self.conversation_history = []
        self.interaction_log = []
        self.retrieval_log = []
        self.client = None

        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)

    def _safety_check(self, query: str) -> Optional[str]:
        """Check for dangerous requests."""
        dangerous_patterns = [
            r"(update|modify|change|delete|remove).*(billing|status|customer|data|record)",
            r"(can you|please).*(trigger|execute|run|activate).*(workflow|action|process)",
            r"(change).*(customer|account).*(status|tier|plan)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, query.lower()):
                return (
                    "⛔ I cannot modify customer data, billing status, or trigger workflows. "
                    "This requires proper authorization. "
                    "Please contact Finance or Ops team. "
                    "I can help you draft a summary."
                )
        return None

    def _retrieve_documents(self, query: str, k: int = 3) -> List[Tuple[dict, float]]:
        """Retrieve relevant documents from vector store."""
        results = self.vector_store.search(query, k=k)
        return results

    def _build_context(self, retrieved_docs: List[Tuple[dict, float]]) -> Tuple[str, List[str]]:
        """Build context string from retrieved documents."""
        context = "## Retrieved Documents:\n\n"
        sources = []

        for doc, score in retrieved_docs:
            context += f"### {doc['title']} (Relevance: {score:.1%})\n"
            context += doc["content"] + "\n\n"
            sources.append(doc["title"])

        return context, sources

    def _call_llm_with_context(self, query: str, context: str) -> str:
        """Call LLM with retrieved context (or simulate if no API)."""
        if not OPENAI_AVAILABLE or not self.client:
            return self._simulate_llm_response(query, context)

        try:
            system_prompt = """
You are an AI Operations Analyst helping with business questions.
Use ONLY the provided documents to answer questions.
If the answer is not in the documents, say "This information is not in the knowledge base."

Respond in JSON format:
{
  "answer": "Your response",
  "confidence": "High/Medium/Low",
  "reasoning": "Brief explanation",
  "data_found": true/false,
  "uncertainties": ["Any gaps"]
}
            """

            user_prompt = f"{context}\n\nUser Question: {query}\n\nRespond in JSON format."

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"answer": f"Error: {str(e)}", "confidence": "Low"})

    def _simulate_llm_response(self, query: str, context: str) -> str:
        """Simulate LLM response for demo mode."""
        if "churn" in query.lower() and "smb" in query.lower():
            return json.dumps({
                "answer": "SMB churn is 18% (up from 15% last year). This is significantly higher than Enterprise (8%) and Mid-market (12%). The primary drivers are price sensitivity (36%), product-market fit issues (28%), and better alternatives (21%). The Churn Analysis document recommends reviewing SMB pricing strategy and improving onboarding. The SMB Segment Strategy Review suggests creating SMB-specific product tiers and improving support response times.",
                "confidence": "High",
                "reasoning": "This is directly supported by the retrieved documents.",
                "data_found": True,
                "uncertainties": []
            })
        elif "nps" in query.lower():
            return json.dumps({
                "answer": "Overall NPS is 42 (down from 47 in July). By segment: Enterprise 52, Mid-market 44, SMB 38. The decline is driven primarily by SMB dissatisfaction. Root causes include product issues, slow support response times, and pricing concerns. Recommended actions: improve SMB support SLA, prioritize feature requests, and communicate value more clearly.",
                "confidence": "High",
                "reasoning": "Directly from NPS Trends document.",
                "data_found": True,
                "uncertainties": []
            })
        elif "discount" in query.lower():
            return json.dumps({
                "answer": "Standard discounts: SMB up to 10%, Mid-market up to 20%, Enterprise up to 30%. Discounts above 5% need Finance approval; above 25% need CFO sign-off. Average discount per segment cannot exceed 20%.",
                "confidence": "High",
                "reasoning": "Policy is clearly documented.",
                "data_found": True,
                "uncertainties": []
            })
        else:
            return json.dumps({
                "answer": "I found some relevant information in the knowledge base related to your question. Based on the SMB Segment Strategy and Churn Analysis documents, the key insight is that SMB segment performance is critical to overall business health.",
                "confidence": "Medium",
                "reasoning": "General synthesis from multiple documents.",
                "data_found": True,
                "uncertainties": ["More specific data may not be available"]
            })

    def respond(self, query: str) -> dict:
        """RAG response pipeline."""
        timestamp = datetime.now().isoformat()

        # Step 1: Safety check
        safety_refusal = self._safety_check(query)
        if safety_refusal:
            return {
                "timestamp": timestamp,
                "query": query,
                "response": safety_refusal,
                "confidence": "High",
                "sources": [],
                "retrieved_docs": [],
                "retrieval_scores": [],
                "escalation_flag": True,
                "stage": "safety_check",
            }

        # Step 2: Retrieve documents
        retrieved_docs = self._retrieve_documents(query, k=3)
        retrieval_scores = [score for _, score in retrieved_docs]
        doc_titles = [doc["title"] for doc, _ in retrieved_docs]

        # Step 3: Build context
        context, sources = self._build_context(retrieved_docs)

        # Step 4: Call LLM with context
        llm_output = self._call_llm_with_context(query, context)

        # Step 5: Parse output
        try:
            parsed = json.loads(llm_output)
            response_text = parsed.get("answer", llm_output)
            confidence = parsed.get("confidence", "Medium")
            data_found = parsed.get("data_found", True)
        except json.JSONDecodeError:
            response_text = llm_output
            confidence = "Low"
            data_found = False

        # Build result
        result = {
            "timestamp": timestamp,
            "query": query,
            "response": response_text,
            "confidence": confidence,
            "sources": sources,
            "retrieved_docs": doc_titles,
            "retrieval_scores": retrieval_scores,
            "data_found": data_found,
            "escalation_flag": not data_found or confidence == "Low",
            "stage": "retrieval_and_generation",
        }

        self.conversation_history.append(result)
        self.interaction_log.append(result)
        self.retrieval_log.append({
            "query": query,
            "retrieved_docs": doc_titles,
            "scores": retrieval_scores,
        })

        return result

    def export_logs(self, filename: str = "phase4_interaction_log.json"):
        """Export interaction logs."""
        with open(filename, "w") as f:
            json.dump(self.interaction_log, f, indent=2)
        print(f"[LOG] Exported {len(self.interaction_log)} interactions to {filename}")


# ============================================================================
# PHASE 4: RETRIEVAL QUALITY EVALUATION
# ============================================================================

class RetrievalEvaluation:
    """Evaluate quality of document retrieval."""

    # Ground truth: which documents should be retrieved for each query
    RELEVANCE_JUDGMENTS = {
        "What is our churn rate?": ["doc_2", "doc_3"],
        "Why is SMB churn so high?": ["doc_2", "doc_6"],
        "What's our discount policy?": ["doc_1"],
        "Tell me about NPS": ["doc_3"],
        "What's our revenue forecast?": ["doc_4"],
        "When should I escalate to CFO?": ["doc_5"],
    }

    @staticmethod
    def evaluate(agent: RAGAgent, k: int = 3):
        """Evaluate retrieval quality on known queries."""
        print("\n" + "=" * 100)
        print("PHASE 4: RETRIEVAL QUALITY EVALUATION")
        print("=" * 100 + "\n")

        precisions = []
        recalls = []
        mrr_scores = []  # Mean Reciprocal Rank

        for query, relevant_docs in RetrievalEvaluation.RELEVANCE_JUDGMENTS.items():
            print(f"Query: {query}")
            print(f"  Expected relevant docs: {relevant_docs}")

            # Retrieve documents
            retrieved = agent._retrieve_documents(query, k=k)
            retrieved_ids = [doc["id"] for doc, _ in retrieved]
            print(f"  Retrieved docs: {retrieved_ids}")

            # Compute precision@k
            hits = len(set(relevant_docs) & set(retrieved_ids))
            precision = hits / k
            precisions.append(precision)

            # Compute recall@k
            recall = hits / len(relevant_docs) if relevant_docs else 0
            recalls.append(recall)

            # Compute MRR (Mean Reciprocal Rank)
            mrr = 0
            for i, doc_id in enumerate(retrieved_ids):
                if doc_id in relevant_docs:
                    mrr = 1 / (i + 1)
                    break
            mrr_scores.append(mrr)

            print(f"  Precision@{k}: {precision:.0%} | Recall@{k}: {recall:.0%} | MRR: {mrr:.2f}")
            print()

        # Summary statistics
        print("=" * 100)
        print("SUMMARY STATISTICS")
        print("=" * 100)
        print(f"Mean Precision@{k}: {np.mean(precisions):.0%}")
        print(f"Mean Recall@{k}: {np.mean(recalls):.0%}")
        print(f"Mean Reciprocal Rank: {np.mean(mrr_scores):.2f}")
        print()

        # Interpretation
        avg_precision = np.mean(precisions)
        if avg_precision > 0.8:
            print("✅ EXCELLENT: Retrieval system is finding the right documents")
        elif avg_precision > 0.6:
            print("✅ GOOD: Retrieval is mostly correct")
        elif avg_precision > 0.4:
            print("⚠️ FAIR: Retrieval has some false positives")
        else:
            print("❌ POOR: Retrieval needs improvement")

        return {
            "mean_precision": np.mean(precisions),
            "mean_recall": np.mean(recalls),
            "mean_mrr": np.mean(mrr_scores),
        }


# ============================================================================
# PHASE 4: DEMO
# ============================================================================

def run_demo():
    """Run Phase 4 demo."""
    print("\n" + "=" * 100)
    print("PHASE 4: RAG (RETRIEVAL-AUGMENTED GENERATION) DEMO")
    print("=" * 100 + "\n")

    # Initialize RAG agent
    agent = RAGAgent()

    print("Setup:")
    print(f"  Documents indexed: {len(DOCUMENTS)}")
    print(f"  Vector store vocab size: {len(agent.vector_store.vocab)}")
    print(f"  Retrieval method: TF-IDF + Cosine Similarity")
    print()

    # Test queries
    print("=" * 100)
    print("RETRIEVAL QUALITY EVALUATION")
    print("=" * 100)
    metrics = RetrievalEvaluation.evaluate(agent)

    # Interactive demo
    print("\n" + "=" * 100)
    print("INTERACTIVE DEMO: RAG Responses")
    print("=" * 100 + "\n")

    demo_queries = [
        "What's happening with our SMB churn?",
        "Why did our NPS decline?",
        "What's our discount policy for enterprise?",
        "Should we give a 30% discount to customer X?",
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"[Q{i}] {query}")
        result = agent.respond(query)
        print(f"[A{i}] {result['response']}")
        print(f"Confidence: {result['confidence']} | Sources: {', '.join(result['sources'])}")
        print(f"Retrieved docs (scores): {[(d, f'{s:.1%}') for d, s in zip(result['retrieved_docs'], result['retrieval_scores'])]}")
        print()

    # Export logs
    agent.export_logs()
    print("\n✅ Demo complete. Check phase4_interaction_log.json for full logs.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--eval-retrieval":
            agent = RAGAgent()
            RetrievalEvaluation.evaluate(agent)
        else:
            run_demo()
    else:
        run_demo()
