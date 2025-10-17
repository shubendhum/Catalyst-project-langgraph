"""
AWS MCP Server
Provides tools for AWS services (EC2, S3, Lambda, etc.)
"""
import logging
from typing import Dict, Optional
import boto3
from mcp.mcp_framework import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class AWSMCPServer(MCPServer):
    """MCP Server for AWS integration"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.aws_access_key = None
        self.aws_secret_key = None
        self.aws_region = None
        self.ec2_client = None
        self.s3_client = None
        self.lambda_client = None
        super().__init__("aws", config)
    
    def _register_tools(self):
        """Register AWS tools"""
        
        # EC2 Tools
        self.register_tool(MCPTool(
            name="list_ec2_instances",
            description="List all EC2 instances",
            parameters={},
            handler=self._list_ec2_instances,
            category="ec2"
        ))
        
        self.register_tool(MCPTool(
            name="start_ec2_instance",
            description="Start an EC2 instance",
            parameters={"instance_id": {"type": "string", "required": True}},
            handler=self._start_ec2_instance,
            category="ec2"
        ))
        
        self.register_tool(MCPTool(
            name="stop_ec2_instance",
            description="Stop an EC2 instance",
            parameters={"instance_id": {"type": "string", "required": True}},
            handler=self._stop_ec2_instance,
            category="ec2"
        ))
        
        # S3 Tools
        self.register_tool(MCPTool(
            name="list_s3_buckets",
            description="List all S3 buckets",
            parameters={},
            handler=self._list_s3_buckets,
            category="s3"
        ))
        
        self.register_tool(MCPTool(
            name="upload_to_s3",
            description="Upload file to S3",
            parameters={
                "bucket": {"type": "string", "required": True},
                "key": {"type": "string", "required": True},
                "body": {"type": "string", "required": True}
            },
            handler=self._upload_to_s3,
            category="s3"
        ))
        
        # Lambda Tools
        self.register_tool(MCPTool(
            name="list_lambda_functions",
            description="List Lambda functions",
            parameters={},
            handler=self._list_lambda_functions,
            category="lambda"
        ))
        
        self.register_tool(MCPTool(
            name="invoke_lambda",
            description="Invoke a Lambda function",
            parameters={
                "function_name": {"type": "string", "required": True},
                "payload": {"type": "object", "required": False}
            },
            handler=self._invoke_lambda,
            category="lambda"
        ))
    
    async def connect(self) -> bool:
        """Connect to AWS"""
        try:
            self.aws_access_key = self.config.get("aws_access_key_id")
            self.aws_secret_key = self.config.get("aws_secret_access_key")
            self.aws_region = self.config.get("aws_region", "us-east-1")
            
            if not all([self.aws_access_key, self.aws_secret_key]):
                return False
            
            # Initialize AWS clients
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            
            self.ec2_client = session.client('ec2')
            self.s3_client = session.client('s3')
            self.lambda_client = session.client('lambda')
            
            # Test connection
            self.ec2_client.describe_regions()
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Error connecting to AWS: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from AWS"""
        self.connected = False
    
    async def _list_ec2_instances(self) -> Dict:
        """List EC2 instances"""
        response = self.ec2_client.describe_instances()
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    "instance_id": instance['InstanceId'],
                    "state": instance['State']['Name'],
                    "type": instance['InstanceType']
                })
        return {"instances": instances}
    
    async def _start_ec2_instance(self, instance_id: str) -> Dict:
        """Start EC2 instance"""
        self.ec2_client.start_instances(InstanceIds=[instance_id])
        return {"message": f"Instance {instance_id} starting"}
    
    async def _stop_ec2_instance(self, instance_id: str) -> Dict:
        """Stop EC2 instance"""
        self.ec2_client.stop_instances(InstanceIds=[instance_id])
        return {"message": f"Instance {instance_id} stopping"}
    
    async def _list_s3_buckets(self) -> Dict:
        """List S3 buckets"""
        response = self.s3_client.list_buckets()
        buckets = [{"name": b['Name'], "created": b['CreationDate'].isoformat()} for b in response['Buckets']]
        return {"buckets": buckets}
    
    async def _upload_to_s3(self, bucket: str, key: str, body: str) -> Dict:
        """Upload to S3"""
        self.s3_client.put_object(Bucket=bucket, Key=key, Body=body)
        return {"message": f"Uploaded to s3://{bucket}/{key}"}
    
    async def _list_lambda_functions(self) -> Dict:
        """List Lambda functions"""
        response = self.lambda_client.list_functions()
        functions = [{"name": f['FunctionName'], "runtime": f['Runtime']} for f in response['Functions']]
        return {"functions": functions}
    
    async def _invoke_lambda(self, function_name: str, payload: Dict = None) -> Dict:
        """Invoke Lambda function"""
        import json
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload or {})
        )
        result = json.loads(response['Payload'].read())
        return {"result": result}


def get_aws_server(config: Optional[Dict] = None) -> AWSMCPServer:
    """Get AWS MCP server instance"""
    return AWSMCPServer(config)
