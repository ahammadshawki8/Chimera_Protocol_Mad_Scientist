"""
Custom Permission Classes for Workspace Access Control
Requirements: 10.1, 10.2, 10.3, 10.4
"""
from rest_framework import permissions
from .models import Workspace, Conversation, Memory


class IsWorkspaceOwnerOrMember(permissions.BasePermission):
    """
    Permission class to check if user is workspace owner or member
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
 
   def has_object_permission(self, request, view, obj):
        """Check if user has access to workspace"""
        if isinstance(obj, Workspace):
            workspace = obj
        elif isinstance(obj, (Conversation, Memory)):
            workspace = obj.workspace
        else:
            return False
        
        # Check if user is owner or member
        is_owner = workspace.owner == request.user
        is_me
mber = workspace.members.filter(user=request.user).exists()
        
        return is_owner or is_member


class IsWorkspaceAdmin(permissions.BasePermission):
    """
    Permission class to check if user is workspace admin or owner
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is admin or owner"""
        if isinstance(obj, Workspace):
            workspace = obj
        elif isinstance(obj, (Conversation, Memory)):
            workspace = obj.workspace
        else:
            return False
        
        # Check if user is owner
        if workspace.owner == request.user:
            return True
        
        # Check if user is admin member
        return workspace.members.filter(
            user=request.user,
            role='admin'
        ).exists()
