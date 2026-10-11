import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.schemas.memory import (
    MemoryCreate,
    MemoryQueryResponse,
    MemoryResponse,
    MemoryType,
)

logger = logging.getLogger(__name__)


class BackboardServiceError(Exception):
    """Exception for Backboard memory operations."""
    pass


class BackboardService:
    """Service interfacing with Backboard.io for persistent AI memory.

    Provides long-term context storage (preferences, habits, plant observations)
    with a resilient local fallback for offline development and testing.
    """

    def __init__(self):
        self.api_url = settings.BACKBOARD_API_URL.rstrip("/")
        self.api_key = settings.BACKBOARD_API_KEY
        # Local in-memory store partitioned by user_id for fallback/testing
        self._local_store: Dict[int, List[Dict[str, Any]]] = {}

    @property
    def is_configured(self) -> bool:
        """Check if Backboard API credentials are configured."""
        return bool(self.api_key and self.api_key.strip())

    async def check_connection(self) -> Dict[str, Any]:
        """Verify connectivity to Backboard.io.

        Returns:
            Dict containing connection status, mode, and details.
        """
        if not self.is_configured:
            return {
                "connected": True,
                "configured": False,
                "mode": "local_fallback",
                "message": "Backboard API key not configured; using local resilient memory store."
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.api_url}/health", headers=headers)
                if res.status_code in (200, 204):
                    return {
                        "connected": True,
                        "configured": True,
                        "mode": "cloud",
                        "message": "Connected to Backboard.io successfully."
                    }
                else:
                    return {
                        "connected": False,
                        "configured": True,
                        "mode": "cloud",
                        "message": f"Backboard API responded with status {res.status_code}."
                    }
        except Exception as exc:
            logger.warning(f"Backboard connection check failed: {exc}")
            return {
                "connected": False,
                "configured": True,
                "mode": "cloud",
                "message": f"Could not reach Backboard.io: {str(exc)}"
            }

    async def create_memory(self, memory_in: MemoryCreate) -> MemoryResponse:
        """Store a meaningful gardening memory in Backboard.

        Args:
            memory_in: Validated memory payload.

        Returns:
            MemoryResponse with assigned ID and timestamp.
        """
        now = datetime.now(timezone.utc)
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"

        # When API key is configured, post to Backboard.io
        if self.is_configured:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "id": memory_id,
                "user_id": memory_in.user_id,
                "garden_id": memory_in.garden_id,
                "plant_id": memory_in.plant_id,
                "memory_type": memory_in.memory_type.value,
                "content": memory_in.content,
                "importance": memory_in.importance,
                "created_at": now.isoformat(),
            }
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(f"{self.api_url}/memories", headers=headers, json=payload)
                    if resp.status_code not in (200, 201):
                        logger.error(f"Backboard API error ({resp.status_code}): {resp.text}")
                        # Fallback to local store to avoid data loss during network hiccups
                        self._save_to_local_store(memory_id, memory_in, now)
                    else:
                        resp_data = resp.json()
                        return MemoryResponse(
                            id=resp_data.get("id", memory_id),
                            user_id=memory_in.user_id,
                            garden_id=memory_in.garden_id,
                            plant_id=memory_in.plant_id,
                            memory_type=memory_in.memory_type,
                            content=memory_in.content,
                            importance=memory_in.importance,
                            created_at=now,
                        )
            except Exception as exc:
                logger.warning(f"Backboard remote call failed, using fallback: {exc}")
                self._save_to_local_store(memory_id, memory_in, now)

        else:
            self._save_to_local_store(memory_id, memory_in, now)

        return MemoryResponse(
            id=memory_id,
            user_id=memory_in.user_id,
            garden_id=memory_in.garden_id,
            plant_id=memory_in.plant_id,
            memory_type=memory_in.memory_type,
            content=memory_in.content,
            importance=memory_in.importance,
            created_at=now,
        )

    def _save_to_local_store(self, memory_id: str, memory_in: MemoryCreate, created_at: datetime) -> None:
        """Save memory to user-partitioned local store."""
        user_list = self._local_store.setdefault(memory_in.user_id, [])
        user_list.append({
            "id": memory_id,
            "user_id": memory_in.user_id,
            "garden_id": memory_in.garden_id,
            "plant_id": memory_in.plant_id,
            "memory_type": memory_in.memory_type,
            "content": memory_in.content,
            "importance": memory_in.importance,
            "created_at": created_at,
        })

    async def retrieve_memories(
        self,
        user_id: int,
        garden_id: Optional[int] = None,
        query: Optional[str] = None,
        limit: int = 5
    ) -> MemoryQueryResponse:
        """Retrieve memories strictly scoped to a user and relevant to the query.

        Args:
            user_id: Owner user ID.
            garden_id: Optional garden ID filter.
            query: Optional topic/situation query to filter or rank memories.
            limit: Maximum memories to return (default 5).

        Returns:
            MemoryQueryResponse with filtered memories and aggregated context text.
        """
        all_user_memories = self._local_store.get(user_id, [])

        filtered: List[Dict[str, Any]] = []
        for mem in all_user_memories:
            # Filter by garden_id if provided (include garden-specific and global user memories)
            if garden_id is not None and mem.get("garden_id") is not None and mem.get("garden_id") != garden_id:
                continue
            filtered.append(mem)

        # Relevance scoring if query is provided
        if query and query.strip():
            query_terms = set(query.lower().split())

            def score_mem(m: Dict[str, Any]) -> float:
                score = float(m.get("importance", 3))
                content_lower = m["content"].lower()
                for term in query_terms:
                    if len(term) > 2 and term in content_lower:
                        score += 3.0
                return score

            filtered.sort(key=score_mem, reverse=True)
        else:
            # Sort by importance and freshness
            filtered.sort(key=lambda m: (m.get("importance", 3), m.get("created_at")), reverse=True)

        selected = filtered[:limit]

        response_models = [
            MemoryResponse(
                id=m["id"],
                user_id=m["user_id"],
                garden_id=m.get("garden_id"),
                plant_id=m.get("plant_id"),
                memory_type=m["memory_type"],
                content=m["content"],
                importance=m["importance"],
                created_at=m["created_at"],
            )
            for m in selected
        ]

        context_text = self._build_context_text(response_models)

        return MemoryQueryResponse(
            user_id=user_id,
            memories=response_models,
            count=len(response_models),
            context_text=context_text,
        )

    def _build_context_text(self, memories: List[MemoryResponse]) -> str:
        """Format memories into clean, concise context for Thinking Machines."""
        if not memories:
            return "No previous gardening memories or preferences recorded for this user."

        lines = ["[AI PERSISTENT MEMORY CONTEXT]"]
        for m in memories:
            lines.append(f"- [{m.memory_type.value.capitalize()}]: {m.content}")
        return "\n".join(lines)


backboard_service = BackboardService()

