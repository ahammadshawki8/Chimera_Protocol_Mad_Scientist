"""
Team Management Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from .models import Workspace, TeamMember
from .serializers_v2 import (
    TeamMemberSerializer, TeamInviteSerializer,
    TeamRoleUpdateSerializer, TeamStatusUpdateSerializer
)


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_team_members_view(request, workspace_id):
    """List all team members in a workspace"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check if user has access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        members = workspace.members.all()
        serializer = TeamMemberSerializer(members, many=True)
        
        return Response(api_response(
            ok=True,
            data={
                'members': serializer.data,
                'total': members.count()
            }
        ))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_team_member_view(request, workspace_id):
    """Invite a team member to workspace"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Only owner or admin can invite
        is_owner = workspace.owner == request.user
        is_admin = workspace.members.filter(
            user=request.user, 
            role='admin'
        ).exists()
        
        if not (is_owner or is_admin):
            return Response(
                api_response(ok=False, error='Only admins can invite members'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeamInviteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = serializer.validated_data['email']
        role = serializer.validated_data['role']
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                api_response(ok=False, error='User not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if workspace.members.filter(user=user).exists():
            return Response(
                api_response(ok=False, error='User is already a member'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create team member
        team_member = TeamMember.objects.create(
            user=user,
            workspace=workspace,
            role=role,
            status='offline'
        )
        
        response_serializer = TeamMemberSerializer(team_member)
        
        return Response(
            api_response(ok=True, data=response_serializer.data),
            status=status.HTTP_201_CREATED
        )
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_member_role_view(request, workspace_id, user_id):
    """Update team member role"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Only owner or admin can update roles
        is_owner = workspace.owner == request.user
        is_admin = workspace.members.filter(
            user=request.user, 
            role='admin'
        ).exists()
        
        if not (is_owner or is_admin):
            return Response(
                api_response(ok=False, error='Only admins can update roles'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeamRoleUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get team member
        try:
            target_user = User.objects.get(id=user_id)
            team_member = workspace.members.get(user=target_user)
        except (User.DoesNotExist, TeamMember.DoesNotExist):
            return Response(
                api_response(ok=False, error='Team member not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot change owner's role
        if target_user == workspace.owner:
            return Response(
                api_response(ok=False, error='Cannot change owner role'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update role
        team_member.role = serializer.validated_data['role']
        team_member.save()
        
        response_serializer = TeamMemberSerializer(team_member)
        
        return Response(api_response(ok=True, data=response_serializer.data))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_team_member_view(request, workspace_id, user_id):
    """Remove team member from workspace"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Only owner or admin can remove members
        is_owner = workspace.owner == request.user
        is_admin = workspace.members.filter(
            user=request.user, 
            role='admin'
        ).exists()
        
        if not (is_owner or is_admin):
            return Response(
                api_response(ok=False, error='Only admins can remove members'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get team member
        try:
            target_user = User.objects.get(id=user_id)
            team_member = workspace.members.get(user=target_user)
        except (User.DoesNotExist, TeamMember.DoesNotExist):
            return Response(
                api_response(ok=False, error='Team member not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cannot remove owner
        if target_user == workspace.owner:
            return Response(
                api_response(ok=False, error='Cannot remove workspace owner'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove member
        team_member.delete()
        
        return Response(api_response(
            ok=True,
            data={'message': 'Team member removed successfully'}
        ))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_member_status_view(request, workspace_id, user_id):
    """Update team member status (online/away/offline)"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check if user has access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = TeamStatusUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get team member
        try:
            target_user = User.objects.get(id=user_id)
            team_member = workspace.members.get(user=target_user)
        except (User.DoesNotExist, TeamMember.DoesNotExist):
            return Response(
                api_response(ok=False, error='Team member not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Users can only update their own status
        if target_user != request.user:
            return Response(
                api_response(ok=False, error='Can only update your own status'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status
        team_member.status = serializer.validated_data['status']
        team_member.save()
        
        response_serializer = TeamMemberSerializer(team_member)
        
        return Response(api_response(ok=True, data=response_serializer.data))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )
