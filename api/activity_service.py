"""
Activity Logging Service

This module provides helper functions for creating activity records
to track workspace events for the activity feed.

Requirements: 2.7, 2.8, 2.9, 8.2, 8.3
"""
from .models import Activity


def log_activity(workspace, activity_type, description, metadata=None):
    """
    Create an activity record for workspace event logging.
    
    Args:
        workspace: Workspace model instance
        activity_type: Type of activity (memory_created, conversation_created, etc.)
        description: Human-readable description of the activity
        metadata: Optional dictionary with additional activity data
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2, 8.3
    """
    if metadata is None:
        metadata = {}
    
    activity = Activity.objects.create(
        workspace=workspace,
        type=activity_type,
        description=description,
        metadata=metadata
    )
    
    return activity


def log_memory_created(workspace, memory):
    """
    Log memory creation activity.
    
    Args:
        workspace: Workspace model instance
        memory: Memory model instance
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2
    """
    return log_activity(
        workspace=workspace,
        activity_type='memory_created',
        description=f"Memory '{memory.title}' created",
        metadata={
            'memoryId': memory.id,
            'memoryTitle': memory.title
        }
    )


def log_conversation_created(workspace, conversation):
    """
    Log conversation creation activity.
    
    Args:
        workspace: Workspace model instance
        conversation: Conversation model instance
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2
    """
    return log_activity(
        workspace=workspace,
        activity_type='conversation_created',
        description=f"Conversation '{conversation.title}' started",
        metadata={
            'conversationId': conversation.id,
            'conversationTitle': conversation.title,
            'modelId': conversation.model_id
        }
    )


def log_message_sent(workspace, conversation, message):
    """
    Log message sending activity.
    
    Args:
        workspace: Workspace model instance
        conversation: Conversation model instance
        message: ChatMessage model instance
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2
    """
    # Truncate content for description
    content_preview = message.content[:50]
    if len(message.content) > 50:
        content_preview += '...'
    
    return log_activity(
        workspace=workspace,
        activity_type='message_sent',
        description=f"Message sent in '{conversation.title}': {content_preview}",
        metadata={
            'conversationId': conversation.id,
            'messageId': message.id,
            'role': message.role
        }
    )


def log_team_member_added(workspace, team_member):
    """
    Log team member addition activity.
    
    Args:
        workspace: Workspace model instance
        team_member: TeamMember model instance
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2
    """
    return log_activity(
        workspace=workspace,
        activity_type='team_member_added',
        description=f"Team member {team_member.user.name} added as {team_member.role}",
        metadata={
            'teamMemberId': team_member.id,
            'userId': str(team_member.user.id),
            'role': team_member.role
        }
    )


def log_model_used(workspace, conversation, model_id):
    """
    Log AI model usage activity.
    
    Args:
        workspace: Workspace model instance
        conversation: Conversation model instance
        model_id: ID of the model used
        
    Returns:
        Activity: Created activity instance
        
    Requirements: 2.8, 8.2
    """
    return log_activity(
        workspace=workspace,
        activity_type='model_used',
        description=f"Model {model_id} used in '{conversation.title}'",
        metadata={
            'conversationId': conversation.id,
            'modelId': model_id
        }
    )

