"""
Slack MCP Server
Provides tools for Slack integration (messages, channels, users)
"""
import logging
from typing import Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp.mcp_framework import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class SlackMCPServer(MCPServer):
    """MCP Server for Slack integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.slack_token = None
        self.client = None
        super().__init__("slack", config)
    
    def _register_tools(self):
        """Register Slack tools"""
        
        self.register_tool(MCPTool(
            name="send_message",
            description="Send a message to a Slack channel",
            parameters={
                "channel": {"type": "string", "required": True},
                "text": {"type": "string", "required": True}
            },
            handler=self._send_message,
            category="messages"
        ))
        
        self.register_tool(MCPTool(
            name="list_channels",
            description="List all Slack channels",
            parameters={},
            handler=self._list_channels,
            category="channels"
        ))
        
        self.register_tool(MCPTool(
            name="create_channel",
            description="Create a new Slack channel",
            parameters={
                "name": {"type": "string", "required": True},
                "is_private": {"type": "boolean", "required": False, "default": False}
            },
            handler=self._create_channel,
            category="channels"
        ))
        
        self.register_tool(MCPTool(
            name="get_channel_history",
            description="Get message history from a channel",
            parameters={
                "channel": {"type": "string", "required": True},
                "limit": {"type": "integer", "required": False, "default": 100}
            },
            handler=self._get_channel_history,
            category="messages"
        ))
        
        self.register_tool(MCPTool(
            name="list_users",
            description="List all Slack users",
            parameters={},
            handler=self._list_users,
            category="users"
        ))
        
        self.register_tool(MCPTool(
            name="send_direct_message",
            description="Send a direct message to a user",
            parameters={
                "user": {"type": "string", "required": True},
                "text": {"type": "string", "required": True}
            },
            handler=self._send_direct_message,
            category="messages"
        ))
        
        self.register_tool(MCPTool(
            name="upload_file",
            description="Upload a file to Slack",
            parameters={
                "channels": {"type": "string", "required": True},
                "filename": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            },
            handler=self._upload_file,
            category="files"
        ))
    
    async def connect(self) -> bool:
        """Connect to Slack"""
        try:
            self.slack_token = self.config.get("slack_token")
            
            if not self.slack_token:
                return False
            
            self.client = WebClient(token=self.slack_token)
            
            # Test connection
            response = self.client.auth_test()
            if response["ok"]:
                self.connected = True
                logger.info(f"Connected to Slack as {response['user']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error connecting to Slack: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Slack"""
        self.connected = False
    
    async def _send_message(self, channel: str, text: str) -> Dict:
        """Send message to channel"""
        try:
            response = self.client.chat_postMessage(channel=channel, text=text)
            return {
                "ts": response["ts"],
                "channel": response["channel"],
                "message": "Message sent successfully"
            }
        except SlackApiError as e:
            raise Exception(f"Error sending message: {e.response['error']}")
    
    async def _list_channels(self) -> Dict:
        """List all channels"""
        try:
            response = self.client.conversations_list()
            channels = []
            for channel in response["channels"]:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel["is_private"],
                    "num_members": channel.get("num_members", 0)
                })
            return {"channels": channels}
        except SlackApiError as e:
            raise Exception(f"Error listing channels: {e.response['error']}")
    
    async def _create_channel(self, name: str, is_private: bool = False) -> Dict:
        """Create a new channel"""
        try:
            response = self.client.conversations_create(name=name, is_private=is_private)
            return {
                "channel_id": response["channel"]["id"],
                "channel_name": response["channel"]["name"],
                "message": "Channel created successfully"
            }
        except SlackApiError as e:
            raise Exception(f"Error creating channel: {e.response['error']}")
    
    async def _get_channel_history(self, channel: str, limit: int = 100) -> Dict:
        """Get channel message history"""
        try:
            response = self.client.conversations_history(channel=channel, limit=limit)
            messages = []
            for msg in response["messages"]:
                messages.append({
                    "user": msg.get("user", "unknown"),
                    "text": msg.get("text", ""),
                    "ts": msg["ts"]
                })
            return {"messages": messages}
        except SlackApiError as e:
            raise Exception(f"Error getting history: {e.response['error']}")
    
    async def _list_users(self) -> Dict:
        """List all users"""
        try:
            response = self.client.users_list()
            users = []
            for user in response["members"]:
                if not user.get("is_bot", False) and not user.get("deleted", False):
                    users.append({
                        "id": user["id"],
                        "name": user["name"],
                        "real_name": user.get("real_name", ""),
                        "is_admin": user.get("is_admin", False)
                    })
            return {"users": users}
        except SlackApiError as e:
            raise Exception(f"Error listing users: {e.response['error']}")
    
    async def _send_direct_message(self, user: str, text: str) -> Dict:
        """Send direct message to user"""
        try:
            # Open DM channel
            dm_response = self.client.conversations_open(users=[user])
            channel = dm_response["channel"]["id"]
            
            # Send message
            response = self.client.chat_postMessage(channel=channel, text=text)
            return {
                "ts": response["ts"],
                "message": "Direct message sent successfully"
            }
        except SlackApiError as e:
            raise Exception(f"Error sending DM: {e.response['error']}")
    
    async def _upload_file(self, channels: str, filename: str, content: str) -> Dict:
        """Upload file to Slack"""
        try:
            response = self.client.files_upload(
                channels=channels,
                filename=filename,
                content=content
            )
            return {
                "file_id": response["file"]["id"],
                "message": "File uploaded successfully"
            }
        except SlackApiError as e:
            raise Exception(f"Error uploading file: {e.response['error']}")


def get_slack_server(config: Optional[Dict] = None) -> SlackMCPServer:
    """Get Slack MCP server instance"""
    return SlackMCPServer(config)
