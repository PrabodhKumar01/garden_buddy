import logging
from typing import List, Optional

from app.models.garden import Garden
from app.models.plant import Plant
from app.schemas.mcp import ToolDecision

logger = logging.getLogger(__name__)

INDOOR_GARDEN_TYPES = {"indoor", "hydroponic", "aeroponic", "grow tent", "windowsill indoor"}


class ToolDecider:
    """Evaluates whether external tools are needed for the current garden state."""

    @staticmethod
    def evaluate_weather_need(garden: Garden, plants: Optional[List[Plant]] = None) -> ToolDecision:
        """Determine whether calling the weather tool is justified.

        Follows AGENTS.md Rule 11 (MCP Rules):
        1. Determine whether the tool is actually needed.
        2. Prevent unnecessary tool execution or data transmission.
        3. Do not invoke tools if the garden is completely indoors or lacks location.

        Args:
            garden: The garden entity being analyzed.
            plants: Optional list of plants in the garden.

        Returns:
            ToolDecision detailing need, rationale, and target location.
        """
        # Check location availability
        if not garden.location or not garden.location.strip():
            logger.info(f"Skipping weather tool for garden {garden.id}: No location configured.")
            return ToolDecision(
                needs_weather=False,
                reason="Garden has no location specified. Skipping weather tool invocation.",
                location=None
            )

        garden_type_lower = (garden.garden_type or "").strip().lower()

        # Check indoor vs outdoor status
        if garden_type_lower in INDOOR_GARDEN_TYPES:
            logger.info(f"Skipping weather tool for garden {garden.id}: Indoor garden type '{garden.garden_type}'.")
            return ToolDecision(
                needs_weather=False,
                reason=f"Garden type '{garden.garden_type}' is indoor and insulated from outdoor precipitation and frost.",
                location=None
            )

        # Outdoor or exposed garden (Balcony, Backyard, Raised Bed, Container, etc.)
        sanitized_loc = garden.location.strip()
        plant_count = len(plants) if plants else 0
        logger.info(
            f"Weather tool required for garden {garden.id} ('{garden.name}') at '{sanitized_loc}' "
            f"with {plant_count} plants."
        )

        return ToolDecision(
            needs_weather=True,
            reason=(
                f"Outdoor/exposed garden at '{sanitized_loc}' requires current temperature and upcoming "
                "rain probability to optimize watering and outdoor plant protection."
            ),
            location=sanitized_loc
        )


tool_decider = ToolDecider()

