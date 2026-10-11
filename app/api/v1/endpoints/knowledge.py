from typing import List, Optional
from fastapi import APIRouter, Query

from app.schemas.rag import KnowledgeQueryRequest, KnowledgeQueryResponse
from app.services.rag import rag_service

router = APIRouter()


@router.post("/retrieve", response_model=KnowledgeQueryResponse)
def retrieve_gardening_knowledge(
    request: KnowledgeQueryRequest
) -> KnowledgeQueryResponse:
    """Retrieve relevant gardening knowledge snippets for a query or garden situation."""
    return rag_service.retrieve(
        query=request.query,
        plant_names=request.plant_names,
        category=request.category,
        limit=request.limit
    )


@router.get("/search", response_model=KnowledgeQueryResponse)
def search_gardening_knowledge(
    query: str = Query(..., min_length=1, max_length=500, description="Search term or garden issue"),
    plant: Optional[str] = Query(None, description="Optional plant filter (e.g. tomato)"),
    category: Optional[str] = Query(None, description="Optional category filter (e.g. watering)"),
    limit: int = Query(3, ge=1, le=10, description="Max snippets to retrieve")
) -> KnowledgeQueryResponse:
    """GET endpoint to search gardening knowledge with query parameters."""
    plants = [plant] if plant else None
    return rag_service.retrieve(
        query=query,
        plant_names=plants,
        category=category,
        limit=limit
    )

