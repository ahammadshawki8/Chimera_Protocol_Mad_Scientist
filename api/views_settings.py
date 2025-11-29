"""
Settings and Data Export Views for Chimera Protocol
Requirements: 7.1, 7.2, 7.4
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
import json

from .models import User, Workspace, Conversation, ChatMessage, Memory, Integration, TeamMember
from .serializers_v2 import UserSerializer


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {
        'ok': ok,
        'data': data,
        'error': error
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def settings_view(request):
    """
    Get current user settings
    Requirements: 7.1 - Return profile settings and memoryRetention settings
    """
    user = request.user
    
    settings_data = {
        'profile': {
            'name': user.name,
            'email': user.email
        },
        'memoryRetention': {
            'autoStore': user.auto_store,
            'retentionPeriod': user.retention_period
        }
    }
    
    return Response(api_response(
        ok=True,
        data=settings_data
    ))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Update user profile settings
    Requirements: 7.2 - Update profile settings with new name or email
    """
    user = request.user
    
    name = request.data.get('name')
    email = request.data.get('email')
    
    # Validate email uniqueness if provided
    if email and email != user.email:
        if User.objects.filter(email=email).exists():
            return Response(
                api_response(
                    ok=False,
                    error='Email already exists'
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        user.email = email
    
    # Update name if provided
    if name:
        user.name = name
    
    user.save()
    
    # Return updated settings
    settings_data = {
        'profile': {
            'name': user.name,
            'email': user.email
        },
        'memoryRetention': {
            'autoStore': user.auto_store,
            'retentionPeriod': user.retention_period
        }
    }
    
    return Response(api_response(
        ok=True,
        data=settings_data
    ))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_memory_retention_view(request):
    """
    Update memory retention settings
    Requirements: 7.3 - Update memory retention settings
    """
    user = request.user
    
    auto_store = request.data.get('autoStore')
    retention_period = request.data.get('retentionPeriod')
    
    # Validate retention period
    valid_periods = ['7-days', '30-days', '90-days', 'indefinite-84', 'indefinite-forever']
    
    if retention_period and retention_period not in valid_periods:
        return Response(
            api_response(
                ok=False,
                error=f'Invalid retention period. Must be one of: {", ".join(valid_periods)}'
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Update settings
    if auto_store is not None:
        user.auto_store = auto_store
    
    if retention_period:
        user.retention_period = retention_period
    
    user.save()
    
    # Return updated settings
    settings_data = {
        'profile': {
            'name': user.name,
            'email': user.email
        },
        'memoryRetention': {
            'autoStore': user.auto_store,
            'retentionPeriod': user.retention_period
        }
    }
    
    return Response(api_response(
        ok=True,
        data=settings_data
    ))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data_view(request):
    """
    Export all user data as JSON
    Requirements: 7.4 - Generate JSON containing all user workspaces, conversations, messages, memories, and settings
    """
    user = request.user
    
    try:
        # Collect all user data
        export_data = {
            'user': {
                'id': str(user.id),
                'name': user.name,
                'email': user.email,
                'createdAt': user.date_joined.isoformat() if user.date_joined else None
            },
            'settings': {
                'profile': {
                    'name': user.name,
                    'email': user.email
                },
                'memoryRetention': {
                    'autoStore': user.auto_store,
                    'retentionPeriod': user.retention_period
                }
            },
            'workspaces': [],
            'integrations': []
        }
        
        # Get all workspaces where user is owner or member
        owned_workspaces = Workspace.objects.filter(owner=user)
        member_workspaces = Workspace.objects.filter(members__user=user).distinct()
        all_workspaces = (owned_workspaces | member_workspaces).distinct()
        
        for workspace in all_workspaces:
            workspace_data = {
                'id': workspace.id,
                'name': workspace.name,
                'description': workspace.description,
                'ownerId': str(workspace.owner.id),
                'isOwner': workspace.owner == user,
                'createdAt': workspace.created_at.isoformat(),
                'updatedAt': workspace.updated_at.isoformat(),
                'conversations': [],
                'memories': []
            }
            
            # Get conversations for this workspace
            conversations = Conversation.objects.filter(workspace=workspace)
            for conversation in conversations:
                conversation_data = {
                    'id': conversation.id,
                    'title': conversation.title,
                    'modelId': conversation.model_id,
                    'status': conversation.status,
                    'createdAt': conversation.created_at.isoformat(),
                    'updatedAt': conversation.updated_at.isoformat(),
                    'messages': []
                }
                
                # Get messages for this conversation
                messages = ChatMessage.objects.filter(conversation=conversation).order_by('timestamp')
                for message in messages:
                    message_data = {
                        'id': message.id,
                        'role': message.role,
                        'content': message.content,
                        'isPinned': message.is_pinned,
                        'timestamp': message.timestamp.isoformat(),
                        'metadata': message.metadata
                    }
                    conversation_data['messages'].append(message_data)
                
                workspace_data['conversations'].append(conversation_data)
            
            # Get memories for this workspace
            memories = Memory.objects.filter(workspace=workspace)
            for memory in memories:
                memory_data = {
                    'id': memory.id,
                    'title': memory.title,
                    'content': memory.content,
                    'snippet': memory.snippet,
                    'tags': memory.tags,
                    'metadata': memory.metadata,
                    'version': memory.version,
                    'createdAt': memory.created_at.isoformat(),
                    'updatedAt': memory.updated_at.isoformat()
                }
                workspace_data['memories'].append(memory_data)
            
            export_data['workspaces'].append(workspace_data)
        
        # Get user integrations
        integrations = Integration.objects.filter(user=user)
        for integration in integrations:
            integration_data = {
                'id': integration.id,
                'provider': integration.provider,
                'status': integration.status,
                'lastTested': integration.last_tested.isoformat() if integration.last_tested else None,
                'createdAt': integration.created_at.isoformat()
            }
            export_data['integrations'].append(integration_data)
        
        # Create JSON response with file download
        json_data = json.dumps(export_data, indent=2)
        
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="chimera_data_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        
        return response
        
    except Exception as e:
        return Response(
            api_response(
                ok=False,
                error=f'Failed to export data: {str(e)}'
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_account_view(request):
    """
    Delete user account and all associated data
    Requirements: 7.5 - Cascade delete all owned workspaces, remove from team memberships, delete integrations, delete user
    """
    user = request.user
    
    try:
        with transaction.atomic():
            # 1. Cascade delete all owned workspaces       
     # This will automatically cascade delete:
            # - All conversations in those workspaces
            # - All messages in those conversations
            # - All memories in those workspaces
            # - All team members in those workspaces
            owned_workspaces = Workspace.objects.filter(owner=user)
            owned_workspaces.delete()
            
            # 2. Remove user from all team memberships
            TeamMember.objects.filter(user=user).delete()
            
            # 3. Delete all user integrations
            Integration.objects.filter(user=user).delete()
            
            # 4. Delete user account
            user.delete()
        
        return Response(api_response(
            ok=True,
            data={'message': 'Account successfully deleted'}
        ))
        
    except Exception as e:
        return Response(
            api_response(
                ok=False,
                error=f'Failed to delete account: {str(e)}'
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
