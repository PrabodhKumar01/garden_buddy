import logging
import re
from typing import Any, Dict, List, Optional, Set

from app.knowledge.gardening_data import GARDENING_KNOWLEDGE_BASE
from app.schemas.rag import KnowledgeQueryResponse, KnowledgeSnippet

logger = logging.getLogger(__name__)

STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had",
    "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours"
}


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into meaningful terms."""
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


class RAGService:
    """Retrieval-Augmented Generation service providing relevant gardening knowledge."""

    def __init__(self, knowledge_base: Optional[List[Dict[str, Any]]] = None):
        self.knowledge_base = knowledge_base or GARDENING_KNOWLEDGE_BASE

    def retrieve(
        self,
        query: str,
        plant_names: Optional[List[str]] = None,
        category: Optional[str] = None,
        limit: int = 3,
        min_score_threshold: float = 0.5
    ) -> KnowledgeQueryResponse:
        """Retrieve the top most relevant gardening knowledge snippets.

        Enforces strict relevance scoring so that irrelevant articles are excluded,
        and limits context size for optimal AI reasoning.

        Args:
            query: The gardener's current query or situation.
            plant_names: Optional list of plants present in the user's garden.
            category: Optional category filter.
            limit: Maximum snippets to return (default 3).
            min_score_threshold: Minimum score required to be included.

        Returns:
            KnowledgeQueryResponse with sorted snippets and concatenated LLM context.
        """
        query_tokens = set(tokenize(query))
        normalized_plants = [p.lower().strip() for p in (plant_names or []) if p.strip()]

        scored_articles: List[KnowledgeSnippet] = []

        for item in self.knowledge_base:
            score = 0.0
            item_plant = (item.get("plant") or "").lower()
            item_category = (item.get("category") or "").lower()
            item_keywords = [k.lower() for k in item.get("keywords", [])]
            item_title_tokens = set(tokenize(item.get("title", "")))
            item_content_tokens = set(tokenize(item.get("content", "")))

            # 1. Plant relevance match
            if item_plant:
                if item_plant in normalized_plants:
                    score += 2.5
                if item_plant in query_tokens:
                    score += 3.5

            # 2. Category filter or match
            if category:
                if item_category == category.lower():
                    score += 2.0
                else:
                    # Penalize category mismatch when explicit category was requested
                    score -= 1.0

            # 3. Keyword matches (high signal)
            for kw in item_keywords:
                kw_tokens = set(tokenize(kw))
                if kw_tokens and kw_tokens.issubset(query_tokens):
                    score += 2.0

            # 4. Title token overlap
            title_overlap = query_tokens.intersection(item_title_tokens)
            score += len(title_overlap) * 1.5

            # 5. Content token overlap
            content_overlap = query_tokens.intersection(item_content_tokens)
            score += len(content_overlap) * 0.4

            # Include only if positive and crosses minimal threshold
            if score >= min_score_threshold:
                scored_articles.append(
                    KnowledgeSnippet(
                        id=item["id"],
                        title=item["title"],
                        category=item["category"],
                        plant=item.get("plant"),
                        content=item["content"],
                        relevance_score=round(score, 2),
                    )
                )

        # Sort descending by relevance score
        scored_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        top_results = scored_articles[:limit]

        # Generate aggregated prompt context string
        context_text = self._build_context_text(top_results)

        return KnowledgeQueryResponse(
            query=query,
            results=top_results,
            count=len(top_results),
            context_text=context_text,
        )

    def _build_context_text(self, snippets: List[KnowledgeSnippet]) -> str:
        """Format retrieved snippets into clean context for Thinking Machines."""
        if not snippets:
            return "No specific gardening knowledge found for this situation."

        lines = ["[GARDENING KNOWLEDGE BASE CONTEXT]"]
        for s in snippets:
            plant_tag = f" (Plant: {s.plant})" if s.plant else ""
            lines.append(f"- **{s.title}**{plant_tag}: {s.content}")
        return "\n".join(lines)


rag_service = RAGService()

