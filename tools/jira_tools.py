"""JIRA tools for CrewAI via MCP Server Adapter."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_jira_config


def get_jira_mcp_tools():
    """Get JIRA tools from the MCP Server via MCPServerAdapter.
    
    Returns an MCPServerAdapter context manager.
    Use inside a `with` statement to get the list of tools.
    """
    from crewai_tools import MCPServerAdapter
    from crewai_tools.mcp import StdioServerParameters
    
    jira_cfg = get_jira_config()
    
    mcp_server_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "mcp_servers", "jira_server.py"
    )
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", mcp_server_path],
        env={
            "JIRA_URL": jira_cfg["url"],
            "JIRA_EMAIL": jira_cfg["email"],
            "JIRA_API_TOKEN": jira_cfg["api_token"],
            "JIRA_PROJECT_KEY": jira_cfg["project_key"],
            "JIRA_ISSUE_TYPE": jira_cfg["issue_type"],
        }
    )
    
    return MCPServerAdapter(server_params)
