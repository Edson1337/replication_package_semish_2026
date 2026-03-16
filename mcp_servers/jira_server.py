"""JIRA MCP Server - exposes JIRA tools via MCP stdio protocol."""
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add parent dir for model imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jira import JIRA
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from models.story_dto import UserStoryDTO


def get_jira_client() -> JIRA:
    """Create authenticated JIRA client from env vars."""
    url = os.getenv("JIRA_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    
    if not all([url, email, token]):
        raise ValueError("JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set in .env")
    
    return JIRA(server=url, basic_auth=(email, token))


# Create MCP Server
app = Server("jira-server")


@app.list_tools()
async def list_tools():
    """List available JIRA tools."""
    return [
        Tool(
            name="search_stories",
            description="Search for user stories in a JIRA project. Returns stories in DTO format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "JIRA project key (e.g. 'PROJ'). Defaults to JIRA_PROJECT_KEY env var."
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Issue type to filter (default: 'Story')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    }
                }
            }
        ),
        Tool(
            name="get_issue",
            description="Get a single JIRA issue by key and return it in DTO format.",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "JIRA issue key (e.g. 'PROJ-123')"
                    }
                },
                "required": ["issue_key"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    jira = get_jira_client()
    
    if name == "search_stories":
        project_key = arguments.get("project_key", os.getenv("JIRA_PROJECT_KEY", ""))
        issue_type = arguments.get("issue_type", os.getenv("JIRA_ISSUE_TYPE", "Story"))
        max_results = arguments.get("max_results", 100)
        
        if not project_key:
            return [TextContent(type="text", text="Error: project_key is required")]
        
        jql = f'project = "{project_key}" AND issuetype = "{issue_type}" ORDER BY created DESC'
        
        issues = jira.search_issues(jql, maxResults=max_results, json_result=True)
        
        # Normalize to DTOs
        stories = []
        for issue in issues.get("issues", []):
            try:
                dto = UserStoryDTO.from_jira_issue(issue)
                stories.append(dto.model_dump())
            except Exception as e:
                stories.append({"error": str(e), "key": issue.get("key", "unknown")})
        
        return [TextContent(
            type="text",
            text=json.dumps(stories, indent=2, ensure_ascii=False)
        )]
    
    elif name == "get_issue":
        issue_key = arguments.get("issue_key")
        if not issue_key:
            return [TextContent(type="text", text="Error: issue_key is required")]
        
        issue = jira.issue(issue_key)
        dto = UserStoryDTO.from_jira_issue(issue.raw)
        
        return [TextContent(
            type="text",
            text=json.dumps(dto.model_dump(), indent=2, ensure_ascii=False)
        )]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the JIRA MCP Server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    
    # Quick test mode
    if "--test" in sys.argv:
        print("Testing JIRA connection...")
        try:
            client = get_jira_client()
            project_key = os.getenv("JIRA_PROJECT_KEY", "")
            if project_key:
                projects = [p.key for p in client.projects()]
                print(f"✅ Connected! Available projects: {projects}")
            else:
                print("✅ Connected! Set JIRA_PROJECT_KEY to test story retrieval.")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        sys.exit(0)
    
    asyncio.run(main())
