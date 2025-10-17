"""
Workspace Service
Team collaboration with RBAC (Role-Based Access Control)
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Manages team workspaces and collaboration"""
    
    # Role definitions with permissions
    ROLES = {
        "owner": {
            "name": "Owner",
            "permissions": ["*"],  # All permissions
            "description": "Full access to workspace"
        },
        "admin": {
            "name": "Administrator",
            "permissions": [
                "projects.create", "projects.read", "projects.update", "projects.delete",
                "members.invite", "members.remove", "members.update_role",
                "deployments.approve", "deployments.rollback",
                "settings.update", "analytics.view"
            ],
            "description": "Manage projects and team members"
        },
        "developer": {
            "name": "Developer",
            "permissions": [
                "projects.create", "projects.read", "projects.update",
                "deployments.request", "code.review", "code.commit"
            ],
            "description": "Create and manage projects"
        },
        "reviewer": {
            "name": "Reviewer",
            "permissions": [
                "projects.read", "code.review", "code.approve", "code.request_changes"
            ],
            "description": "Review and approve code"
        },
        "viewer": {
            "name": "Viewer",
            "permissions": [
                "projects.read", "analytics.view"
            ],
            "description": "Read-only access"
        }
    }
    
    def __init__(self, db):
        self.db = db
    
    async def create_workspace(
        self,
        name: str,
        owner_id: str,
        owner_email: str,
        settings: Optional[Dict] = None
    ) -> Dict:
        """Create a new workspace"""
        
        workspace_id = str(uuid.uuid4())
        
        workspace = {
            "id": workspace_id,
            "name": name,
            "owner_id": owner_id,
            "members": [
                {
                    "user_id": owner_id,
                    "email": owner_email,
                    "role": "owner",
                    "invited_at": datetime.now(timezone.utc).isoformat(),
                    "joined_at": datetime.now(timezone.utc).isoformat(),
                    "status": "active"
                }
            ],
            "projects": [],
            "settings": settings or self._default_settings(),
            "billing": {
                "plan": "free",
                "usage_limit": 100000,  # tokens
                "current_usage": 0
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            await self.db.workspaces.insert_one(workspace)
            logger.info(f"Created workspace {workspace_id} for {owner_email}")
            
            return {
                "success": True,
                "workspace_id": workspace_id,
                "name": name,
                "message": "Workspace created successfully"
            }
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _default_settings(self) -> Dict:
        """Get default workspace settings"""
        return {
            "allow_external_collaborators": False,
            "require_code_review": True,
            "require_deployment_approval": True,
            "default_llm_provider": "emergent",
            "auto_backup": True,
            "retention_days": 90
        }
    
    async def invite_member(
        self,
        workspace_id: str,
        email: str,
        role: str,
        invited_by: str
    ) -> Dict:
        """Invite member to workspace"""
        
        # Validate role
        if role not in self.ROLES:
            return {
                "success": False,
                "error": f"Invalid role. Must be one of: {', '.join(self.ROLES.keys())}"
            }
        
        # Check if already a member
        workspace = await self.db.workspaces.find_one({"id": workspace_id})
        if not workspace:
            return {"success": False, "error": "Workspace not found"}
        
        existing_member = next(
            (m for m in workspace["members"] if m["email"] == email),
            None
        )
        
        if existing_member:
            return {
                "success": False,
                "error": "User is already a member of this workspace"
            }
        
        # Add member
        member = {
            "user_id": str(uuid.uuid4()),  # Will be updated when they join
            "email": email,
            "role": role,
            "invited_by": invited_by,
            "invited_at": datetime.now(timezone.utc).isoformat(),
            "joined_at": None,
            "status": "pending"
        }
        
        try:
            await self.db.workspaces.update_one(
                {"id": workspace_id},
                {
                    "$push": {"members": member},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            
            logger.info(f"Invited {email} to workspace {workspace_id} as {role}")
            
            # TODO: Send invitation email
            
            return {
                "success": True,
                "message": f"Invitation sent to {email}",
                "role": role
            }
        except Exception as e:
            logger.error(f"Error inviting member: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace details"""
        try:
            workspace = await self.db.workspaces.find_one({"id": workspace_id})
            return workspace
        except Exception as e:
            logger.error(f"Error getting workspace: {e}")
            return None
    
    async def list_user_workspaces(self, user_id: str) -> List[Dict]:
        """List all workspaces user belongs to"""
        try:
            workspaces = await self.db.workspaces.find(
                {"members.user_id": user_id}
            ).to_list(length=None)
            
            # Add user's role to each workspace
            for workspace in workspaces:
                user_member = next(
                    (m for m in workspace["members"] if m["user_id"] == user_id),
                    None
                )
                workspace["user_role"] = user_member["role"] if user_member else None
            
            return workspaces
        except Exception as e:
            logger.error(f"Error listing workspaces: {e}")
            return []
    
    async def update_member_role(
        self,
        workspace_id: str,
        user_id: str,
        new_role: str,
        updated_by: str
    ) -> Dict:
        """Update member's role"""
        
        if new_role not in self.ROLES:
            return {"success": False, "error": "Invalid role"}
        
        try:
            # Check if updater has permission
            workspace = await self.db.workspaces.find_one({"id": workspace_id})
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            updater = next(
                (m for m in workspace["members"] if m["user_id"] == updated_by),
                None
            )
            
            if not updater or updater["role"] not in ["owner", "admin"]:
                return {"success": False, "error": "Insufficient permissions"}
            
            # Can't change owner role
            target_member = next(
                (m for m in workspace["members"] if m["user_id"] == user_id),
                None
            )
            
            if not target_member:
                return {"success": False, "error": "Member not found"}
            
            if target_member["role"] == "owner":
                return {"success": False, "error": "Cannot change owner role"}
            
            # Update role
            await self.db.workspaces.update_one(
                {"id": workspace_id, "members.user_id": user_id},
                {
                    "$set": {
                        "members.$.role": new_role,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            logger.info(f"Updated {user_id} role to {new_role} in workspace {workspace_id}")
            
            return {
                "success": True,
                "message": f"Role updated to {new_role}"
            }
        except Exception as e:
            logger.error(f"Error updating member role: {e}")
            return {"success": False, "error": str(e)}
    
    async def remove_member(
        self,
        workspace_id: str,
        user_id: str,
        removed_by: str
    ) -> Dict:
        """Remove member from workspace"""
        
        try:
            workspace = await self.db.workspaces.find_one({"id": workspace_id})
            if not workspace:
                return {"success": False, "error": "Workspace not found"}
            
            # Check permissions
            remover = next(
                (m for m in workspace["members"] if m["user_id"] == removed_by),
                None
            )
            
            if not remover or remover["role"] not in ["owner", "admin"]:
                return {"success": False, "error": "Insufficient permissions"}
            
            # Can't remove owner
            target = next(
                (m for m in workspace["members"] if m["user_id"] == user_id),
                None
            )
            
            if not target:
                return {"success": False, "error": "Member not found"}
            
            if target["role"] == "owner":
                return {"success": False, "error": "Cannot remove owner"}
            
            # Remove member
            await self.db.workspaces.update_one(
                {"id": workspace_id},
                {
                    "$pull": {"members": {"user_id": user_id}},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            
            logger.info(f"Removed {user_id} from workspace {workspace_id}")
            
            return {
                "success": True,
                "message": "Member removed successfully"
            }
        except Exception as e:
            logger.error(f"Error removing member: {e}")
            return {"success": False, "error": str(e)}
    
    def check_permission(
        self,
        user_role: str,
        required_permission: str
    ) -> bool:
        """Check if role has permission"""
        
        if user_role not in self.ROLES:
            return False
        
        role_permissions = self.ROLES[user_role]["permissions"]
        
        # Owner has all permissions
        if "*" in role_permissions:
            return True
        
        # Check specific permission
        return required_permission in role_permissions
    
    async def add_project_to_workspace(
        self,
        workspace_id: str,
        project_id: str
    ) -> Dict:
        """Add project to workspace"""
        
        try:
            await self.db.workspaces.update_one(
                {"id": workspace_id},
                {
                    "$addToSet": {"projects": project_id},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
            )
            
            # Also update project with workspace_id
            await self.db.projects.update_one(
                {"id": project_id},
                {"$set": {"workspace_id": workspace_id}}
            )
            
            return {"success": True}
        except Exception as e:
            logger.error(f"Error adding project to workspace: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_workspace_analytics(self, workspace_id: str) -> Dict:
        """Get workspace analytics"""
        
        try:
            workspace = await self.db.workspaces.find_one({"id": workspace_id})
            if not workspace:
                return {"error": "Workspace not found"}
            
            # Get project stats
            project_ids = workspace.get("projects", [])
            
            total_cost = 0
            total_tokens = 0
            
            for project_id in project_ids:
                project = await self.db.projects.find_one({"id": project_id})
                if project:
                    total_cost += project.get("total_cost", 0)
                    total_tokens += project.get("total_tokens", 0)
            
            return {
                "members": len(workspace.get("members", [])),
                "projects": len(project_ids),
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "plan": workspace.get("billing", {}).get("plan", "free"),
                "usage_limit": workspace.get("billing", {}).get("usage_limit", 0),
                "current_usage": total_tokens
            }
        except Exception as e:
            logger.error(f"Error getting workspace analytics: {e}")
            return {"error": str(e)}


def get_workspace_service(db) -> WorkspaceService:
    """Factory function to get workspace service"""
    return WorkspaceService(db)
