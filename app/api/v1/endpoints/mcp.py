from typing import Any, Dict
from fastapi import APIRouter, Body, HTTPException, Query, status

from app.mcp.devrelay_client import devrelay_mcp_client
from app.mcp.tool_registry import tool_registry
from app.schemas.mcp import ToolExecutionResponse

router = APIRouter()


@router.get("/tools")
async def list_registered_mcp_tools() -> Dict[str, Any]:
    """List all registered MCP tools and their safety policies."""
    return tool_registry.list_tools()


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_mcp_tool(
    tool_name: str = Query(..., description="Name of the MCP tool to invoke"),
    arguments: Dict[str, Any] = Body(..., description="Tool arguments payload")
) -> ToolExecutionResponse:
    """Safely execute an MCP tool through DevRelay MCP client with input verification."""
    return await devrelay_mcp_client.invoke_tool(tool_name=tool_name, arguments=arguments)

