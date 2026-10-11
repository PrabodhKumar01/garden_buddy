import logging
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.crud.crud_garden import garden_crud
from app.crud.crud_plant import plant_crud
from app.mcp.devrelay_client import devrelay_mcp_client
from app.mcp.tool_decision import tool_decider
from app.models.garden import Garden
from app.models.plant import Plant
from app.services.backboard import backboard_service
from app.services.rag import rag_service

logger = logging.getLogger(__name__)


class GardenContext:
    """Assembled multi-source context ready for Thinking Machines reasoning."""

    def __init__(
        self,
        garden: Garden,
        plants: List[Plant],
        weather_summary: str,
        weather_data: Optional[Dict[str, Any]],
        knowledge_context: str,
        memory_context: str,
        target_date: date,
    ):
        self.garden = garden
        self.plants = plants
        self.weather_summary = weather_summary
        self.weather_data = weather_data
        self.knowledge_context = knowledge_context
        self.memory_context = memory_context
        self.target_date = target_date

    def to_prompt_text(self) -> str:
        """Render the complete context into structured prompt text for the AI."""
        plants_text = "No plants added yet."
        if self.plants:
            plant_lines = []
            for p in self.plants:
                planted_str = f" planted on {p.date_planted}" if p.date_planted else ""
                loc_str = f" at {p.location_in_garden}" if p.location_in_garden else ""
                notes_str = f" (Notes: {p.notes})" if p.notes else ""
                plant_lines.append(f"- {p.name}{planted_str}{loc_str}{notes_str}")
            plants_text = "\n".join(plant_lines)

        return (
            f"=== TARGET DATE: {self.target_date.isoformat()} ===\n\n"
            f"### 1. GARDEN STATE\n"
            f"- Name: {self.garden.name}\n"
            f"- Location: {self.garden.location or 'Not specified'}\n"
            f"- Type: {self.garden.garden_type or 'General'}\n"
            f"- Sunlight: {self.garden.sunlight or 'Moderate'}\n\n"
            f"### 2. PLANTS IN GARDEN\n"
            f"{plants_text}\n\n"
            f"### 3. WEATHER CONTEXT\n"
            f"{self.weather_summary}\n\n"
            f"### 4. RELEVANT GARDENING KNOWLEDGE (RAG)\n"
            f"{self.knowledge_context}\n\n"
            f"### 5. PERSISTENT USER MEMORY (BACKBOARD)\n"
            f"{self.memory_context}\n"
        )


class ContextBuilder:
    """Assembles all five context pillars: Garden, Plants, Weather, RAG Knowledge, and Memory."""

    async def build_context(
        self,
        db: Session,
        garden_id: int,
        target_date: Optional[date] = None
    ) -> GardenContext:
        """Fetch and assemble the 5 context pillars for a garden.

        Args:
            db: Database session.
            garden_id: Target garden ID.
            target_date: Target plan date (defaults to today).

        Returns:
            GardenContext object containing all assembled information.

        Raises:
            ValueError: If garden is not found.
        """
        plan_date = target_date or date.today()

        # 1. Garden State
        garden = garden_crud.get(db=db, garden_id=garden_id)
        if not garden:
            raise ValueError(f"Garden with ID {garden_id} does not exist.")

        # 2. Plants in Garden
        plants = plant_crud.list(db=db, garden_id=garden_id)
        plant_names = [p.name for p in plants]

        # 3. Weather Retrieval via Agent Tool Decision & DevRelay MCP
        tool_decision = tool_decider.evaluate_weather_need(garden=garden, plants=plants)
        weather_summary = tool_decision.reason
        weather_data = None

        if tool_decision.needs_weather and tool_decision.location:
            mcp_response = await devrelay_mcp_client.invoke_tool(
                tool_name="get_weather_forecast",
                arguments={"location": tool_decision.location, "days": 3}
            )
            if mcp_response.success and mcp_response.data:
                w_data = mcp_response.data
                signals = w_data.get("gardening_signals", {})
                summary_text = signals.get("summary", "Weather retrieved successfully.")
                loc_prefix = f"[{tool_decision.location}] " if tool_decision.location and tool_decision.location.lower() not in summary_text.lower() else ""
                weather_summary = f"{loc_prefix}{summary_text}"
                weather_data = {
                    "is_rain_expected_today": signals.get("is_rain_expected_today", False),
                    "is_rain_expected_tomorrow": signals.get("is_rain_expected_tomorrow", False),
                    "current_temperature_c": signals.get("current_temperature_c", 20.0),
                    "condition": w_data.get("current", {}).get("condition", "Clear"),
                }
            else:
                weather_summary = f"Weather tool reported: {mcp_response.error or 'Failed to retrieve weather.'}"

        # 4. RAG Gardening Knowledge
        query_parts = []
        if plant_names:
            query_parts.append(f"Care and watering for {', '.join(plant_names)}")
        if weather_data and weather_data.get("is_rain_expected_tomorrow"):
            query_parts.append("rain tomorrow watering decisions")
        rag_query = " ".join(query_parts) if query_parts else "general garden maintenance and watering"

        rag_resp = rag_service.retrieve(
            query=rag_query,
            plant_names=plant_names,
            limit=3
        )
        knowledge_context = rag_resp.context_text

        # 5. Persistent AI Memory (Backboard.io)
        memory_resp = await backboard_service.retrieve_memories(
            user_id=garden.user_id,
            garden_id=garden.id,
            query=" ".join(plant_names),
            limit=4
        )
        memory_context = memory_resp.context_text

        return GardenContext(
            garden=garden,
            plants=plants,
            weather_summary=weather_summary,
            weather_data=weather_data,
            knowledge_context=knowledge_context,
            memory_context=memory_context,
            target_date=plan_date,
        )


context_builder = ContextBuilder()

