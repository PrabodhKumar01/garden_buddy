import logging
from typing import Any, Callable, Dict, Optional

from app.schemas.mcp import ToolExecutionResponse, WeatherToolInput
from app.tools.weather_tool import WEATHER_TOOL_DEFINITION, execute_weather_tool

logger = logging.getLogger(__name__)


class MCPToolRegistry:
    """Registry of verified and safe MCP tools for GardenBuddy."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default tools adhering to AGENTS.md safety guidelines."""
        self.register_tool(
            name=WEATHER_TOOL_DEFINITION["name"],
            definition=WEATHER_TOOL_DEFINITION,
            validator=WeatherToolInput,
            handler=self._execute_safe_weather_tool,
            safety_notes="Transmits only location and forecast days; no user PII or credentials."
        )

    def register_tool(
        self,
        name: str,
        definition: Dict[str, Any],
        validator: Optional[Callable[[Dict[str, Any]], Any]],
        handler: Callable[..., Any],
        safety_notes: str
    ) -> None:
        """Register a tool with its safety schema and handler."""
        self._tools[name] = {
            "name": name,
            "definition": definition,
            "validator": validator,
            "handler": handler,
            "safety_notes": safety_notes
        }

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a registered tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools with their definitions and safety notes."""
        return {
            name: {
                "definition": item["definition"],
                "safety_notes": item["safety_notes"]
            }
            for name, item in self._tools.items()
        }

    async def execute_tool(self, name: str, raw_arguments: Dict[str, Any]) -> ToolExecutionResponse:
        """Execute a tool with strict input validation, data minimization, and error handling.

        Adheres to Phase 8.3 Tool Safety requirements:
        - Verify tool inputs.
        - Avoid unnecessary data transmission.
        - Handle tool errors.
        - Do not expose credentials.
        """
        tool = self.get_tool(name)
        if not tool:
            logger.warning(f"Attempted to invoke unregistered MCP tool: '{name}'")
            return ToolExecutionResponse(
                tool_name=name,
                success=False,
                error=f"Unregistered MCP tool: '{name}'. GardenBuddy only allows registered safe tools.",
                data_transmitted={}
            )

        # 1. Input Verification & Sanitization
        validator = tool.get("validator")
        sanitized_args = raw_arguments
        if validator:
            try:
                validated_obj = validator(**raw_arguments)
                sanitized_args = validated_obj.model_dump()
            except Exception as exc:
                logger.warning(f"MCP tool '{name}' rejected invalid input: {exc}")
                return ToolExecutionResponse(
                    tool_name=name,
                    success=False,
                    error=f"Tool input validation failed: {str(exc)}",
                    data_transmitted=raw_arguments
                )

        # 2. Safe Execution with Error Handling
        try:
            handler = tool["handler"]
            result = await handler(sanitized_args)
            return ToolExecutionResponse(
                tool_name=name,
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                data_transmitted=sanitized_args
            )
        except Exception as exc:
            logger.exception(f"Unexpected error executing MCP tool '{name}': {exc}")
            return ToolExecutionResponse(
                tool_name=name,
                success=False,
                error=f"Internal tool execution error: {str(exc)}",
                data_transmitted=sanitized_args
            )

    async def _execute_safe_weather_tool(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safe wrapper around execute_weather_tool preventing personal data leakage."""
        location = arguments.get("location", "")
        days = arguments.get("days", 3)

        raw_result = await execute_weather_tool(location=location, days=days)

        if not raw_result.get("success"):
            return {
                "success": False,
                "error": raw_result.get("error", "Weather tool failed"),
                "data": None
            }

        # Data Minimization: Return only gardening-relevant weather signals
        return {
            "success": True,
            "data": {
                "location": raw_result.get("location"),
                "current": raw_result.get("current"),
                "today": raw_result.get("today"),
                "tomorrow": raw_result.get("tomorrow"),
                "gardening_signals": raw_result.get("gardening_signals"),
            },
            "error": None
        }


tool_registry = MCPToolRegistry()

