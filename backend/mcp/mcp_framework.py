"""
Universal MCP (Model Context Protocol) Framework
Base classes for creating and consuming MCP servers
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class MCPTool:
    """
    Represents a single MCP tool
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict,
        handler: Callable,
        category: str = "general"
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.category = category
        self.execution_count = 0
        self.last_executed = None
    
    async def execute(self, **kwargs) -> Dict:
        """Execute the tool with given parameters"""
        try:
            self.execution_count += 1
            self.last_executed = datetime.now(timezone.utc)
            
            result = await self.handler(**kwargs)
            
            return {
                "status": "success",
                "result": result,
                "tool": self.name,
                "executed_at": self.last_executed.isoformat()
            }
        except Exception as e:
            logger.error(f"Error executing MCP tool {self.name}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "tool": self.name,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }
    
    def to_dict(self) -> Dict:
        """Convert tool to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None
        }


class MCPServer(ABC):
    """
    Base class for MCP servers
    Each integration (Jira, AWS, etc.) extends this
    """
    
    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.tools: Dict[str, MCPTool] = {}
        self.connected = False
        self.connection_time = None
        
        # Initialize tools
        self._register_tools()
    
    @abstractmethod
    def _register_tools(self):
        """Register all tools for this MCP server"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the external service"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the external service"""
        pass
    
    def register_tool(self, tool: MCPTool):
        """Register a tool with this server"""
        self.tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name} on {self.name}")
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict:
        """Execute a specific tool"""
        if tool_name not in self.tools:
            return {
                "status": "error",
                "error": f"Tool '{tool_name}' not found on server '{self.name}'"
            }
        
        if not self.connected:
            connect_result = await self.connect()
            if not connect_result:
                return {
                    "status": "error",
                    "error": f"Failed to connect to {self.name} server"
                }
        
        tool = self.tools[tool_name]
        return await tool.execute(**kwargs)
    
    def list_tools(self) -> List[Dict]:
        """List all available tools"""
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_tools_by_category(self, category: str) -> List[Dict]:
        """Get tools filtered by category"""
        return [
            tool.to_dict() 
            for tool in self.tools.values() 
            if tool.category == category
        ]
    
    def get_server_info(self) -> Dict:
        """Get server information"""
        return {
            "name": self.name,
            "connected": self.connected,
            "connection_time": self.connection_time.isoformat() if self.connection_time else None,
            "tools_count": len(self.tools),
            "categories": list(set(tool.category for tool in self.tools.values()))
        }


class MCPClient:
    """
    Client for consuming MCP servers
    Agents use this to interact with MCP tools
    """
    
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.servers: Dict[str, MCPServer] = {}
    
    def register_server(self, server: MCPServer):
        """Register an MCP server"""
        self.servers[server.name] = server
        logger.info(f"Registered MCP server: {server.name}")
    
    async def connect_all(self) -> Dict[str, bool]:
        """Connect to all registered servers"""
        results = {}
        for name, server in self.servers.items():
            try:
                results[name] = await server.connect()
            except Exception as e:
                logger.error(f"Error connecting to {name}: {str(e)}")
                results[name] = False
        return results
    
    async def disconnect_all(self):
        """Disconnect from all servers"""
        for server in self.servers.values():
            try:
                await server.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from {server.name}: {str(e)}")
    
    async def execute_tool(self, server_name: str, tool_name: str, **kwargs) -> Dict:
        """Execute a tool on a specific server"""
        if server_name not in self.servers:
            return {
                "status": "error",
                "error": f"Server '{server_name}' not registered"
            }
        
        server = self.servers[server_name]
        result = await server.execute_tool(tool_name, **kwargs)
        
        # Log execution to database
        await self._log_execution(server_name, tool_name, kwargs, result)
        
        return result
    
    async def discover_tools(self, query: Optional[str] = None, category: Optional[str] = None) -> Dict:
        """
        Discover available tools across all servers
        Optionally filter by query or category
        """
        all_tools = {}
        
        for server_name, server in self.servers.items():
            if category:
                tools = server.get_tools_by_category(category)
            else:
                tools = server.list_tools()
            
            if query:
                tools = [
                    tool for tool in tools
                    if query.lower() in tool["name"].lower() or 
                       query.lower() in tool["description"].lower()
                ]
            
            all_tools[server_name] = tools
        
        return all_tools
    
    async def suggest_tools(self, context: str, llm_client) -> List[Dict]:
        """
        Use LLM to suggest relevant tools based on context
        """
        from langchain_core.messages import HumanMessage
        
        # Get all available tools
        all_tools = await self.discover_tools()
        
        # Flatten tools for LLM
        tools_list = []
        for server_name, tools in all_tools.items():
            for tool in tools:
                tools_list.append({
                    "server": server_name,
                    "tool": tool["name"],
                    "description": tool["description"],
                    "category": tool["category"]
                })
        
        # Ask LLM to suggest relevant tools
        prompt = f"""Given this context: "{context}"

Available MCP tools:
{json.dumps(tools_list, indent=2)}

Suggest the 3 most relevant tools for this task. Return JSON array:
[
  {{"server": "...", "tool": "...", "reason": "..."}},
  ...
]"""

        try:
            response = await llm_client.ainvoke([HumanMessage(content=prompt)])
            
            # Parse JSON response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response.content)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions
        except Exception as e:
            logger.error(f"Error suggesting tools: {str(e)}")
        
        return []
    
    def list_all_servers(self) -> List[Dict]:
        """List all registered servers"""
        return [server.get_server_info() for server in self.servers.values()]
    
    async def _log_execution(self, server_name: str, tool_name: str, params: Dict, result: Dict):
        """Log tool execution to database"""
        try:
            log_doc = {
                "server": server_name,
                "tool": tool_name,
                "parameters": params,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": result.get("status", "unknown")
            }
            await self.db.mcp_executions.insert_one(log_doc)
        except Exception as e:
            logger.error(f"Error logging MCP execution: {str(e)}")


# Global MCP client instance
_mcp_client = None


def get_mcp_client(db, manager) -> MCPClient:
    """Get or create MCP client singleton"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(db, manager)
    return _mcp_client
