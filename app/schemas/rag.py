from typing import List, Optional
from pydantic import BaseModel, Field


class KnowledgeSnippet(BaseModel):
    """A retrieved knowledge snippet for garden planning."""

    id: str = Field(..., description="Unique article ID")
    title: str = Field(..., description="Title of the gardening topic")
    category: str = Field(..., description="Category: watering, sunlight, soil, pests, planting, care")
    plant: Optional[str] = Field(None, description="Associated plant if plant-specific, or None for general advice")
    content: str = Field(..., description="Actionable gardening knowledge text")
    relevance_score: float = Field(0.0, description="Relevance ranking score")


class KnowledgeQueryRequest(BaseModel):
    """Request schema for querying the RAG knowledge base."""

    query: str = Field(..., min_length=1, max_length=500, description="Gardening situation, question, or problem")
    plant_names: Optional[List[str]] = Field(default=None, description="Optional list of plants in user's garden")
    category: Optional[str] = Field(default=None, description="Optional category filter")
    limit: int = Field(default=3, ge=1, le=10, description="Maximum number of snippets to retrieve")


class KnowledgeQueryResponse(BaseModel):
    """Response schema containing retrieved snippets."""

    query: str
    results: List[KnowledgeSnippet]
    count: int
    context_text: str = Field(..., description="Concise aggregated text ready for Thinking Machines prompt context")

