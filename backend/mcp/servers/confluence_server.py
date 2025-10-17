"""
Confluence MCP Server
Provides tools for interacting with Confluence (pages, spaces, content)
"""
import logging
from typing import Dict, Optional
import requests
from mcp.mcp_framework import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class ConfluenceMCPServer(MCPServer):
    """MCP Server for Confluence integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.confluence_url = None
        self.confluence_email = None
        self.confluence_api_token = None
        self.session = None
        super().__init__("confluence", config)
    
    def _register_tools(self):
        """Register Confluence-specific tools"""
        
        self.register_tool(MCPTool(
            name="create_page",
            description="Create a new Confluence page",
            parameters={
                "space_key": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            },
            handler=self._create_page,
            category="pages"
        ))
        
        self.register_tool(MCPTool(
            name="get_page",
            description="Get a Confluence page by ID",
            parameters={
                "page_id": {"type": "string", "required": True}
            },
            handler=self._get_page,
            category="pages"
        ))
        
        self.register_tool(MCPTool(
            name="update_page",
            description="Update a Confluence page",
            parameters={
                "page_id": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            },
            handler=self._update_page,
            category="pages"
        ))
        
        self.register_tool(MCPTool(
            name="search_content",
            description="Search Confluence content",
            parameters={
                "cql": {"type": "string", "required": True},
                "limit": {"type": "integer", "required": False, "default": 25}
            },
            handler=self._search_content,
            category="search"
        ))
        
        self.register_tool(MCPTool(
            name="list_spaces",
            description="List all Confluence spaces",
            parameters={},
            handler=self._list_spaces,
            category="spaces"
        ))
    
    async def connect(self) -> bool:
        """Connect to Confluence"""
        try:
            self.confluence_url = self.config.get("confluence_url")
            self.confluence_email = self.config.get("confluence_email")
            self.confluence_api_token = self.config.get("confluence_api_token")
            
            if not all([self.confluence_url, self.confluence_email, self.confluence_api_token]):
                return False
            
            self.session = requests.Session()
            self.session.auth = (self.confluence_email, self.confluence_api_token)
            self.session.headers.update({"Accept": "application/json"})
            
            # Test connection
            response = self.session.get(f"{self.confluence_url}/rest/api/user/current")
            self.connected = response.status_code == 200
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to Confluence: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Confluence"""
        if self.session:
            self.session.close()
        self.connected = False
    
    async def _create_page(self, space_key: str, title: str, content: str) -> Dict:
        """Create a new page"""
        url = f"{self.confluence_url}/rest/api/content"
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            return {"page_id": data["id"], "title": data["title"], "url": data["_links"]["webui"]}
        raise Exception(f"Failed to create page: {response.text}")
    
    async def _get_page(self, page_id: str) -> Dict:
        """Get page by ID"""
        url = f"{self.confluence_url}/rest/api/content/{page_id}"
        response = self.session.get(url, params={"expand": "body.storage,version"})
        if response.status_code == 200:
            data = response.json()
            return {
                "id": data["id"],
                "title": data["title"],
                "content": data["body"]["storage"]["value"],
                "version": data["version"]["number"]
            }
        raise Exception(f"Failed to get page: {response.text}")
    
    async def _update_page(self, page_id: str, title: str, content: str) -> Dict:
        """Update an existing page"""
        # Get current version first
        page = await self._get_page(page_id)
        
        url = f"{self.confluence_url}/rest/api/content/{page_id}"
        payload = {
            "version": {"number": page["version"] + 1},
            "title": title,
            "type": "page",
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        response = self.session.put(url, json=payload)
        if response.status_code == 200:
            return {"message": f"Page {page_id} updated successfully"}
        raise Exception(f"Failed to update page: {response.text}")
    
    async def _search_content(self, cql: str, limit: int = 25) -> Dict:
        """Search content using CQL"""
        url = f"{self.confluence_url}/rest/api/content/search"
        response = self.session.get(url, params={"cql": cql, "limit": limit})
        if response.status_code == 200:
            data = response.json()
            results = [{"id": r["id"], "title": r["title"], "type": r["type"]} for r in data["results"]]
            return {"total": data["totalSize"], "results": results}
        raise Exception(f"Failed to search: {response.text}")
    
    async def _list_spaces(self) -> Dict:
        """List all spaces"""
        url = f"{self.confluence_url}/rest/api/space"
        response = self.session.get(url)
        if response.status_code == 200:
            data = response.json()
            spaces = [{"key": s["key"], "name": s["name"]} for s in data["results"]]
            return {"spaces": spaces}
        raise Exception(f"Failed to list spaces: {response.text}")


def get_confluence_server(config: Optional[Dict] = None) -> ConfluenceMCPServer:
    """Get Confluence MCP server instance"""
    return ConfluenceMCPServer(config)
