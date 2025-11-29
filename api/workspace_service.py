"""
Workspace Statistics Calculation Service

This module provides functions for calculating workspace statistics
including memory counts, conversation counts, system load, and last activity.
"""
from django.utils import timezone
from django.db.models import Q, Max, Count
from datetime import timedelta


def calculate_workspace_stats(workspace):
    """
    Calculate comprehensive statistics for a workspace.
    
    Args:
        workspace: Workspace model instance
        
    Returns:
        dict: Statistics including:
            - totalMemories: Count of all memories in workspace
            - totalEmbeddings: Count of memories with non-null embedding
            - totalConversations: Count of all conversations in workspace
            - systemLoad: Calculated load percentage (0-100)
            - lastActivity: Most recent timestamp across all entities
    
    Requirements: 2.6, 8.1, 8.4
    """
    # Calculate totalMemories (count of workspace memories)
    total_memories = workspace.memories.count()
    
    # Calculate totalEmbeddings (count of memories with non-null embedding)
    total_embeddings = workspace.memories.filter(embedding__isnull=False).count()
    
    # Calculate totalConversations (count of workspace conversations)
    total_conversations = workspace.conversations.count()
    
    # Calculate systemLoad using formula: (active_conversations * 10 + messages_last_hour) capped at 100
    system_load = _calculate_system_load(workspace)
    
    # Calculate lastActivity (most recent timestamp across all entities)
    last_activity = _calculate_last_activity(workspace)
    
    return {
        'totalMemories': total_memories,
        'totalEmbeddings': total_embeddings,
        'totalConversations': total_conversations,
        'systemLoad': system_load,
        'lastActivity': last_activity
    }


def _calculate_system_load(workspace):
    """
    Calculate system load using the formula:
    (active_conversations * 10 + messages_last_hour) capped at 100
    
    Args:
        workspace: Workspace model instance
        
    Returns:
        int: System load percentage (0-100)
        
    Requirements: 8.4
    """
    # Count active conversations
    active_conversations = workspace.conversations.filter(status='active').count()
    
    # Count messages in the last hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    messages_last_hour = 0
    
    # Get all conversations and count their messages from last hour
    for conversation in workspace.conversations.all():
        messages_last_hour += conversation.messages.filter(
            timestamp__gte=one_hour_ago
        ).count()
    
    # Apply formula: (active_conversations * 10 + messages_last_hour) capped at 100
    system_load = (active_conversations * 10) + messages_last_hour
      
    system_load = min(100, system_load)
    
    return system_load


def _calculate_last_activity(workspace):
    """
    Calculate the most recent timestamp across all workspace entities.
    
    Checks:
    - Workspace updated_at
    - Most recent memory updated_at
    - Most recent conversation updated_at
    - Most recent message timestamp
    - Most recent activity timestamp
    
    Args:
        workspace: Workspace model instance
        
    Returns:
        datetime: Most recent timestamp
        
    Requirements: 2.6, 8.1
    """
    # Start with workspace updated_at
    last_activity = workspace.updated_at
    
    # Check most recent memory
    latest_memory = workspace.memories.order_by('-updated_at').first()
    if latest_memory and latest_memory.updated_at > last_activity:
        last_activity = latest_memory.updated_at
    
    # Check most recent conversation
    latest_conversation = workspace.conversations.order_by('-updated_at').first()
    if latest_conversation and latest_conversation.updated_at > last_activity:
        last_activity = latest_conversation.updated_at
    
    # Check most recent message across all conversations
    # Use aggregate to get max timestamp efficiently
    from .models import ChatMessage
    latest_message_time = ChatMessage.objects.filter(
        conversation__workspace=workspace
    ).aggregate(Max('timestamp'))['timestamp__max']
    
    if latest_message_time and latest_message_time > last_activity:
        last_activity = latest_message_time
    
    # Check most recent activity
    latest_activity = workspace.activities.order_by('-timestamp').first()
    if latest_activity and latest_activity.timestamp > last_activity:
        last_activity = latest_activity.timestamp
    
    return last_activity
