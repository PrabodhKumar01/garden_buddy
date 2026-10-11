import logging
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.crud.crud_garden import garden_crud
from app.crud.crud_plant import plant_crud
from app.crud.crud_task import task_crud
from app.mcp.devrelay_client import devrelay_mcp_client
from app.mcp.tool_decision import tool_decider
from app.models.garden import Garden
from app.models.plant import Plant
from app.schemas.ai_plan import DailyGardenPlan, PlanActionItem
from app.schemas.task import TaskCreate
from app.services.backboard import backboard_service
from app.services.rag import rag_service
from app.services.thinking_machines import thinking_machines_service

logger = logging.getLogger(__name__)


class DailyGardenAgent:
    """The central orchestrator of the GardenBuddy Daily Garden Plan.

    Executes the 8-step workflow defined in PROJECT.md Section 13:
    1. Retrieve garden state
    2. Retrieve plant information
    3. Retrieve relevant AI memory (Backboard)
    4. Determine weather tool requirement
    5. Retrieve weather through DevRelay MCP (if required)
    6. Retrieve relevant gardening knowledge through RAG
    7. Reason over all context via Thinking Machines
    8. Generate and persist structured Today's Garden Plan
    """

    async def execute_daily_workflow(
        self,
        db: Session,
        garden_id: int,
        target_date: Optional[date] = None,
        save_to_database: bool = True
    ) -> DailyGardenPlan:
        """Execute the full end-to-end Daily Garden Agent workflow.

        Args:
            db: Database session.
            garden_id: ID of the garden.
            target_date: Date for the plan (defaults to today).
            save_to_database: Whether to save action items to the database task table.

        Returns:
            DailyGardenPlan with reasoned real-world tasks and formatted motivation.

        Raises:
            ValueError: If the requested garden does not exist.
        """
        plan_date = target_date or date.today()
        logger.info(f"DailyGardenAgent: Starting daily workflow for garden_id={garden_id} on {plan_date}")

        # 1. Retrieve Garden State
        garden = garden_crud.get(db=db, garden_id=garden_id)
        if not garden:
            raise ValueError(f"Garden with ID {garden_id} not found.")

        # 2. Retrieve Plants in Garden
        plants = plant_crud.list(db=db, garden_id=garden_id)

        # 3. Retrieve Relevant AI Memory from Backboard
        plant_names = [p.name for p in plants]
        memory_resp = await backboard_service.retrieve_memories(
            user_id=garden.user_id,
            garden_id=garden.id,
            query=" ".join(plant_names),
            limit=4
        )

        # 4. Determine Weather Requirement & Execute DevRelay MCP Tool (if needed)
        tool_decision = tool_decider.evaluate_weather_need(garden=garden, plants=plants)
        weather_summary = tool_decision.reason
        weather_data = None

        if tool_decision.needs_weather and tool_decision.location:
            mcp_res = await devrelay_mcp_client.invoke_tool(
                tool_name="get_weather_forecast",
                arguments={"location": tool_decision.location, "days": 3}
            )
            if mcp_res.success and mcp_res.data:
                signals = mcp_res.data.get("gardening_signals", {})
                weather_summary = signals.get("summary", "Weather retrieved successfully.")
                weather_data = {
                    "is_rain_expected_today": signals.get("is_rain_expected_today", False),
                    "is_rain_expected_tomorrow": signals.get("is_rain_expected_tomorrow", False),
                    "current_temperature_c": signals.get("current_temperature_c", 20.0),
                    "condition": mcp_res.data.get("current", {}).get("condition", "Clear"),
                }
            else:
                weather_summary = f"Weather lookup note: {mcp_res.error or 'Weather data unavailable.'}"

        # 5. Retrieve Relevant Gardening Knowledge via RAG
        rag_query_parts = []
        if plant_names:
            rag_query_parts.append(f"Care and watering for {', '.join(plant_names)}")
        if weather_data and weather_data.get("is_rain_expected_tomorrow"):
            rag_query_parts.append("rain tomorrow watering guidelines")
        rag_query = " ".join(rag_query_parts) if rag_query_parts else "garden soil and maintenance"

        rag_resp = rag_service.retrieve(
            query=rag_query,
            plant_names=plant_names,
            limit=3
        )

        # 6. Thinking Machines AI Reasoning
        plan = await thinking_machines_service.generate_daily_plan(
            db=db,
            garden_id=garden_id,
            target_date=plan_date,
            save_tasks_to_db=save_to_database
        )

        logger.info(
            f"DailyGardenAgent: Completed plan generation for '{garden.name}' with "
            f"{len(plan.action_items)} action items."
        )
        return plan

    @staticmethod
    def format_plan_as_markdown(plan: DailyGardenPlan) -> str:
        """Format the Daily Garden Plan into an inspiring, readable Touch Grass checklist."""
        lines = [
            f"# 🌱 Today's Garden Plan — {plan.garden_name}",
            f"**Date:** {plan.plan_date.isoformat()}",
            f"**Weather:** {plan.weather_summary}",
            "",
            "### Recommended Outdoor Actions:",
        ]

        if not plan.action_items:
            lines.append("No outdoor actions needed today. Enjoy your garden!")
        else:
            for idx, item in enumerate(plan.action_items, 1):
                icon = {
                    "watering": "💧",
                    "harvest": "🌿",
                    "inspection": "🔍",
                    "planting": "🌱",
                    "soil": "🪴",
                    "care": "✂️"
                }.get(item.category.lower(), "🌱")

                plant_tag = f" ({item.plant_name})" if item.plant_name else ""
                lines.append(f"{idx}. {icon} **{item.title}**{plant_tag}")
                lines.append(f"   _{item.description}_")

        lines.extend([
            "",
            "### Why this plan?",
            f"> {plan.reasoning_notes}",
            "",
            "### 🌿 Touch Grass Reminder:",
            f"> {plan.outdoor_motivation}"
        ])

        return "\n".join(lines)


daily_garden_agent = DailyGardenAgent()

