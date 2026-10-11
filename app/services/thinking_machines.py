import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.crud_task import task_crud
from app.schemas.ai_plan import DailyGardenPlan, PlanActionItem
from app.schemas.task import TaskCreate
from app.services.context_builder import GardenContext, context_builder

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are GardenBuddy, an expert AI gardening assistant built for Hacktoberfest 'Touch Grass'.
Your mission is to generate a concise, actionable 'Today's Garden Plan' that encourages the user to go outside into their garden.

Instructions:
1. Synthesize the provided Garden State, Plants, Weather, RAG Gardening Knowledge, and Persistent User Memory.
2. Make intelligent, weather-aware decisions:
   - If rain is expected today or tomorrow, advise AGAINST heavy watering to prevent root rot and disease.
   - If sunny/hot, recommend early morning deep watering if soil is dry.
   - Respect user memory (e.g. past yellowing leaves, organic methods, preferred gardening times).
3. Generate 3 to 5 clear, concrete physical actions for today.
4. Output strict JSON matching this exact structure:
{
  "weather_summary": "Short weather summary",
  "reasoning_notes": "Why these specific actions were chosen based on weather + memory + plants",
  "outdoor_motivation": "Inspiring Touch Grass message encouraging outdoor gardening activity",
  "action_items": [
    {
      "title": "Action title",
      "description": "Specific rationale and instructions",
      "category": "watering|harvest|inspection|planting|soil|care",
      "plant_name": "Optional plant name or null",
      "priority": "high|medium|low"
    }
  ]
}
"""


class ThinkingMachinesService:
    """Service to generate intelligent Daily Garden Plans using Thinking Machines AI."""

    def __init__(self, timeout_seconds: float = 15.0):
        self.api_url = settings.THINKING_MACHINES_API_URL.rstrip("/")
        self.api_key = settings.THINKING_MACHINES_API_KEY
        self.model = settings.THINKING_MACHINES_MODEL
        self.timeout = timeout_seconds

    @property
    def is_configured(self) -> bool:
        """Check if Thinking Machines API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    async def generate_daily_plan(
        self,
        db: Session,
        garden_id: int,
        target_date: Optional[date] = None,
        save_tasks_to_db: bool = True
    ) -> DailyGardenPlan:
        """Generate a complete Daily Garden Plan for a given garden.

        Handles missing context, service downtime, timeouts, and invalid responses
        gracefully by falling back to the built-in deterministic reasoning engine.

        Args:
            db: Database session.
            garden_id: ID of the garden.
            target_date: Date for the plan (defaults to today).
            save_tasks_to_db: Whether to persist action items to garden_tasks table.

        Returns:
            DailyGardenPlan with reasoned action items and Touch Grass motivation.
        """
        plan_date = target_date or date.today()

        # Build complete 5-pillar context
        context = await context_builder.build_context(
            db=db,
            garden_id=garden_id,
            target_date=plan_date
        )

        plan: DailyGardenPlan

        # Attempt Thinking Machines cloud inference if configured
        if self.is_configured:
            try:
                plan = await self._call_thinking_machines_api(context)
            except Exception as exc:
                logger.warning(
                    f"Thinking Machines AI call failed or timed out ({exc}). "
                    "Engaging graceful rule-engine fallback."
                )
                plan = self._generate_rule_based_plan(context)
        else:
            logger.info("Thinking Machines API key not configured; using rule-engine reasoning.")
            plan = self._generate_rule_based_plan(context)

        # Match plant_ids where plant_name is known
        plant_lookup = {p.name.lower(): p.id for p in context.plants}
        for item in plan.action_items:
            if item.plant_name and item.plant_name.lower() in plant_lookup:
                item.plant_id = plant_lookup[item.plant_name.lower()]

        # Persist action items to database if requested
        if save_tasks_to_db:
            self._persist_plan_tasks(db=db, garden_id=garden_id, plan=plan)

        return plan

    async def _call_thinking_machines_api(self, context: GardenContext) -> DailyGardenPlan:
        """Call Thinking Machines Chat Completion API."""
        prompt_text = context.to_prompt_text()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt_text}
            ],
            "temperature": 0.3,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Thinking Machines returned status {resp.status_code}: {resp.text}")

            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._extract_json_response(content)

            action_items = [
                PlanActionItem(
                    title=item.get("title", "Garden Task"),
                    description=item.get("description", ""),
                    category=item.get("category", "care"),
                    plant_name=item.get("plant_name"),
                    priority=item.get("priority", "medium")
                )
                for item in parsed.get("action_items", [])
            ]

            return DailyGardenPlan(
                garden_id=context.garden.id,
                garden_name=context.garden.name,
                plan_date=context.target_date,
                weather_summary=parsed.get("weather_summary", context.weather_summary),
                action_items=action_items,
                reasoning_notes=parsed.get("reasoning_notes", "Reasoned by Thinking Machines AI."),
                outdoor_motivation=parsed.get(
                    "outdoor_motivation",
                    "Take a deep breath of fresh air and enjoy gardening today! 🌿"
                ),
                generated_by="thinking_machines"
            )

    def _extract_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from raw LLM output, extracting from code blocks if present."""
        cleaned = text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(cleaned)

    def _generate_rule_based_plan(self, context: GardenContext) -> DailyGardenPlan:
        """Deterministic reasoning engine executing intelligent garden logic as fallback."""
        items: List[PlanActionItem] = []
        reasoning_points: List[str] = []

        weather_data = context.weather_data or {}
        rain_tomorrow = weather_data.get("is_rain_expected_tomorrow", False)
        rain_today = weather_data.get("is_rain_expected_today", False)

        plants = context.plants
        plant_names_lower = [p.name.lower() for p in plants]

        # 1. Weather-based watering decision
        if rain_tomorrow or rain_today:
            items.append(
                PlanActionItem(
                    title="Withhold watering today",
                    description=(
                        "Rain is expected within the next 24-48 hours. Postponing irrigation protects roots "
                        "from waterlogging and conserves water."
                    ),
                    category="watering",
                    priority="high"
                )
            )
            reasoning_points.append("Withheld watering because rain is in the forecast.")
        else:
            items.append(
                PlanActionItem(
                    title="Check soil moisture before watering",
                    description=(
                        "Perform the 2-inch finger test in your garden beds or containers. "
                        "Water deeply at the base only if the sub-surface soil feels dry."
                    ),
                    category="watering",
                    priority="medium"
                )
            )
            reasoning_points.append("Advised checking 2-inch soil moisture prior to irrigation.")

        # 2. Plant-specific tasks
        if any("tomato" in name for name in plant_names_lower):
            items.append(
                PlanActionItem(
                    title="Inspect tomato foliage for yellowing",
                    description=(
                        "Check lower tomato leaves for chlorosis or blight. "
                        "Prune off yellowing leaves touching the soil line to enhance airflow."
                    ),
                    category="inspection",
                    plant_name="Tomato",
                    priority="medium"
                )
            )
            reasoning_points.append("Recommended inspecting tomato foliage for moisture/disease issues.")

        if any("coriander" in name or "cilantro" in name for name in plant_names_lower):
            items.append(
                PlanActionItem(
                    title="Harvest outer coriander leaves",
                    description=(
                        "Snip the outer stems of mature coriander. Regular harvesting delays bolting "
                        "and promotes dense fresh leaf growth."
                    ),
                    category="harvest",
                    plant_name="Coriander",
                    priority="medium"
                )
            )
            reasoning_points.append("Suggested harvesting coriander to encourage growth and prevent bolting.")

        if any("spinach" in name for name in plant_names_lower):
            items.append(
                PlanActionItem(
                    title="Harvest spinach leaves & check dampness",
                    description=(
                        "Harvest tender outer leaves and verify that spinach beds remain cool and mulched."
                    ),
                    category="harvest",
                    plant_name="Spinach",
                    priority="medium"
                )
            )
            reasoning_points.append("Scheduled spinach harvesting and mulch check.")

        if any("mint" in name for name in plant_names_lower):
            items.append(
                PlanActionItem(
                    title="Pinch back mint runners",
                    description=(
                        "Trim trailing mint stems to prevent spreading and maintain bushy container growth."
                    ),
                    category="care",
                    plant_name="Mint",
                    priority="low"
                )
            )

        # 3. Handling missing context / empty garden
        if not plants:
            items.append(
                PlanActionItem(
                    title="Prepare garden bed and soil",
                    description=(
                        "Add a layer of rich organic compost and assess sunlight exposure before planting new crops."
                    ),
                    category="soil",
                    priority="high"
                )
            )
            items.append(
                PlanActionItem(
                    title="Choose crops for planting",
                    description=(
                        "Consider planting hardy vegetables like tomatoes, spinach, or herbs suited for your location."
                    ),
                    category="planting",
                    priority="medium"
                )
            )
            reasoning_points.append("Garden has no plants registered yet; generated foundational preparation tasks.")

        # Touch grass motivation
        motivation = (
            "Put down your phone, step away from the keyboard, and go touch grass! "
            "A few minutes in the garden today will nourish both your plants and your well-being. 🌱"
        )

        return DailyGardenPlan(
            garden_id=context.garden.id,
            garden_name=context.garden.name,
            plan_date=context.target_date,
            weather_summary=context.weather_summary,
            action_items=items,
            reasoning_notes=" ".join(reasoning_points),
            outdoor_motivation=motivation,
            generated_by="rule_engine_fallback"
        )

    def _persist_plan_tasks(self, db: Session, garden_id: int, plan: DailyGardenPlan) -> None:
        """Save recommended action items into garden_tasks table."""
        # Check if tasks already exist for this date and garden to avoid duplicates
        existing = task_crud.get_todays_tasks(db=db, garden_id=garden_id, target_date=plan.plan_date)
        if existing:
            logger.info(f"Tasks already exist for garden {garden_id} on {plan.plan_date}; skipping duplicate insert.")
            return

        for item in plan.action_items:
            task_crud.create(
                db=db,
                task_in=TaskCreate(
                    garden_id=garden_id,
                    plant_id=item.plant_id,
                    title=item.title,
                    description=item.description,
                    category=item.category,
                    task_date=plan.plan_date,
                    source="ai_generated"
                )
            )
        logger.info(f"Persisted {len(plan.action_items)} action items for garden {garden_id}.")


thinking_machines_service = ThinkingMachinesService()

