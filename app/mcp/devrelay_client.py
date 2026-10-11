import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.mcp.tool_registry import tool_registry
from app.schemas.mcp import ToolExecutionResponse

logger = logging.getLogger(__name__)


class DevRelayMCPClient:
    """Client for dispatching tool calls through the DevRelay MCP gateway.

    Coordinates the workflow:
    Thinking Machines -> DevRelay MCP -> Weather Tool -> Weather API -> Weather Result -> Thinking Machines.
    Includes seamless local fallback to tool_registry if the gateway is running in embedded mode.
    """

    def __init__(self, timeout_seconds: float = 10.0):
        self.gateway_url = (settings.DEVRELAY_GATEWAY_URL or "http://localhost:8080").rstrip("/")
        self.timeout = timeout_seconds

    async def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResponse:
        """Invoke an MCP tool through DevRelay MCP gateway or safe local registry.

        Args:
            tool_name: The name of the tool (e.g. 'get_weather_forecast').
            arguments: Tool arguments dictionary.

        Returns:
            ToolExecutionResponse with execution status, sanitized data, and public transmission trace.
        """
        logger.info(f"DevRelay MCP dispatching tool invocation: '{tool_name}' with args: {arguments}")

        # Attempt remote DevRelay Gateway if reachable
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.post(
                    f"{self.gateway_url}/tools/{tool_name}/execute",
                    json={"arguments": arguments}
                )
                if res.status_code == 200:
                    data = res.json()
                    return ToolExecutionResponse(
                        tool_name=tool_name,
                        success=data.get("success", True),
                        data=data.get("data"),
                        error=data.get("error"),
                        data_transmitted=arguments
                    )
        except Exception:
            # Fallback to local registered safe tool dispatcher
            pass

        # Local dispatch through safe tool registry
        return await tool_registry.execute_tool(name=tool_name, raw_arguments=arguments)


devrelay_mcp_client = DevRelayMCPClient()

