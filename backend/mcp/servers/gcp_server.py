"""
GCP (Google Cloud Platform) MCP Server
Provides tools for GCP services (Compute Engine, Cloud Storage, Cloud Functions)
"""
import logging
from typing import Dict, Optional
from google.cloud import compute_v1, storage, functions_v1
from mcp.mcp_framework import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class GCPMCPServer(MCPServer):
    """MCP Server for GCP integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.project_id = None
        self.credentials_path = None
        self.compute_client = None
        self.storage_client = None
        self.functions_client = None
        super().__init__("gcp", config)
    
    def _register_tools(self):
        """Register GCP tools"""
        
        # Compute Engine Tools
        self.register_tool(MCPTool(
            name="list_instances",
            description="List Compute Engine instances",
            parameters={"zone": {"type": "string", "required": True}},
            handler=self._list_instances,
            category="compute"
        ))
        
        self.register_tool(MCPTool(
            name="start_instance",
            description="Start a Compute Engine instance",
            parameters={
                "zone": {"type": "string", "required": True},
                "instance": {"type": "string", "required": True}
            },
            handler=self._start_instance,
            category="compute"
        ))
        
        self.register_tool(MCPTool(
            name="stop_instance",
            description="Stop a Compute Engine instance",
            parameters={
                "zone": {"type": "string", "required": True},
                "instance": {"type": "string", "required": True}
            },
            handler=self._stop_instance,
            category="compute"
        ))
        
        # Cloud Storage Tools
        self.register_tool(MCPTool(
            name="list_buckets",
            description="List Cloud Storage buckets",
            parameters={},
            handler=self._list_buckets,
            category="storage"
        ))
        
        self.register_tool(MCPTool(
            name="upload_to_storage",
            description="Upload file to Cloud Storage",
            parameters={
                "bucket": {"type": "string", "required": True},
                "blob_name": {"type": "string", "required": True},
                "content": {"type": "string", "required": True}
            },
            handler=self._upload_to_storage,
            category="storage"
        ))
        
        # Cloud Functions Tools
        self.register_tool(MCPTool(
            name="list_functions",
            description="List Cloud Functions",
            parameters={"location": {"type": "string", "required": True}},
            handler=self._list_functions,
            category="functions"
        ))
        
        self.register_tool(MCPTool(
            name="call_function",
            description="Invoke a Cloud Function",
            parameters={
                "function_name": {"type": "string", "required": True},
                "data": {"type": "object", "required": False}
            },
            handler=self._call_function,
            category="functions"
        ))
    
    async def connect(self) -> bool:
        """Connect to GCP"""
        try:
            self.project_id = self.config.get("project_id")
            self.credentials_path = self.config.get("credentials_path")
            
            if not self.project_id:
                return False
            
            # Set credentials if provided
            if self.credentials_path:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path
            
            # Initialize GCP clients
            self.compute_client = compute_v1.InstancesClient()
            self.storage_client = storage.Client(project=self.project_id)
            self.functions_client = functions_v1.CloudFunctionsServiceClient()
            
            # Test connection
            list(self.storage_client.list_buckets(max_results=1))
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to GCP: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from GCP"""
        self.connected = False
    
    async def _list_instances(self, zone: str) -> Dict:
        """List Compute Engine instances"""
        request = compute_v1.ListInstancesRequest(project=self.project_id, zone=zone)
        instances = self.compute_client.list(request=request)
        
        result = []
        for instance in instances:
            result.append({
                "name": instance.name,
                "status": instance.status,
                "machine_type": instance.machine_type.split("/")[-1]
            })
        return {"instances": result}
    
    async def _start_instance(self, zone: str, instance: str) -> Dict:
        """Start Compute Engine instance"""
        request = compute_v1.StartInstanceRequest(
            project=self.project_id,
            zone=zone,
            instance=instance
        )
        self.compute_client.start(request=request)
        return {"message": f"Instance {instance} starting"}
    
    async def _stop_instance(self, zone: str, instance: str) -> Dict:
        """Stop Compute Engine instance"""
        request = compute_v1.StopInstanceRequest(
            project=self.project_id,
            zone=zone,
            instance=instance
        )
        self.compute_client.stop(request=request)
        return {"message": f"Instance {instance} stopping"}
    
    async def _list_buckets(self) -> Dict:
        """List Cloud Storage buckets"""
        buckets = self.storage_client.list_buckets()
        result = [{"name": bucket.name, "location": bucket.location} for bucket in buckets]
        return {"buckets": result}
    
    async def _upload_to_storage(self, bucket: str, blob_name: str, content: str) -> Dict:
        """Upload to Cloud Storage"""
        bucket_obj = self.storage_client.bucket(bucket)
        blob = bucket_obj.blob(blob_name)
        blob.upload_from_string(content)
        return {"message": f"Uploaded to gs://{bucket}/{blob_name}"}
    
    async def _list_functions(self, location: str) -> Dict:
        """List Cloud Functions"""
        parent = f"projects/{self.project_id}/locations/{location}"
        functions = self.functions_client.list_functions(parent=parent)
        
        result = []
        for func in functions:
            result.append({
                "name": func.name.split("/")[-1],
                "runtime": func.runtime,
                "status": func.status.name
            })
        return {"functions": result}
    
    async def _call_function(self, function_name: str, data: Dict = None) -> Dict:
        """Invoke Cloud Function"""
        import json
        import requests
        
        # Get function URL
        name = f"projects/{self.project_id}/locations/us-central1/functions/{function_name}"
        func = self.functions_client.get_function(name=name)
        
        # Call function
        response = requests.post(func.https_trigger.url, json=data or {})
        return {"result": response.json()}


def get_gcp_server(config: Optional[Dict] = None) -> GCPMCPServer:
    """Get GCP MCP server instance"""
    return GCPMCPServer(config)
