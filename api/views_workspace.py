"""
Workspace Management Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import Workspace, TeamMember, Activity
from .serializers_v2 import (
    WorkspaceSerializer, WorkspaceCreateSerializer,
    DashboardDataSerializer, TimeSeriesDataSerializer,
    ActivityItemSerializer
)
from .workspace_service import calculate_workspace_stats
from .activity_service import log_team_member_added


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


def _generate_neural_load_time_series(base_load):
    """
    Generate neural load time series with 24 data points at 5-minute intervals.
    
    Args:
        base_load: Current system load percentage (0-100)
        
    Returns:
        list: Array of timestamp-value pairs representing system load over time
        
    Requirements: 2.9, 8.3
    """
    neural_load = []
    now = timezone.now()
    
    # Generate 24 data points at 5-minute intervals
    for i in range(24):
        timestamp = now - timedelta(minutes=i * 5)
        # Add some realistic variation around the base load
        # Use a sine wave pattern for smooth variation
        import math
        variation = int(math.sin(i * 0.5) * 10)  # ±10 variation
        value = base_load + variation
        value = max(0, min(100, value))  # Clamp to 0-100
        
        # Insert at beginning to maintain chronological order
        neural_load.insert(0, {
            'timestamp': timestamp,
            'value': value
        })
    
    return neural_load


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workspaces_view(request):
    """
    GET: List all workspaces for authenticated user
    POST: Create new workspace
    """
    if request.method == 'GET':
        # Get workspaces where user is owner or member
        # Optimize queries with select_related and prefetch_related
        owned = Workspace.objects.filter(owner=request.user).select_related('owner').prefetch_related('members__user')
        member_of = Workspace.objects.filter(members__user=request.user).select_related('owner').prefetch_related('members__user')
        workspaces = (owned | member_of).distinct()
        
        serializer = WorkspaceSerializer(workspaces, many=True)
        
        return Response(api_response(
            ok=True,
            data={
                'workspaces': serializer.data,
                'total': workspaces.count()
            }
        ))
    
    elif request.method == 'POST':
        serializer = WorkspaceCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create workspace
        workspace = Workspace.objects.create(
            name=serializer.validated_data['name'],
            description=serializer.validated_data.get('description', ''),
            owner=request.user
        )
        
        # Add owner as admin team member
        team_member = TeamMember.objects.create(
            user=request.user,
            workspace=workspace,
            role='admin',
            status='online'
        )
        
        # Log activity
        log_team_member_added(workspace, team_member)
        
        response_serializer = WorkspaceSerializer(workspace)
        
        return Response(
            api_response(ok=True, data=response_serializer.data),
            status=status.HTTP_201_CREATED
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def workspace_detail_view(request, workspace_id):
    """
    GET: Get workspace details
    PUT: Update workspace
    DELETE: Delete workspace
    """
    try:
        # Optimize query with select_related and prefetch_related
        workspace = Workspace.objects.select_related('owner').prefetch_related('members__user').get(id=workspace_id)
        
        # Check if user has access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = WorkspaceSerializer(workspace)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'PUT':
            # Only owner can update
            if not is_owner:
                return Response(
                    api_response(ok=False, error='Only owner can update workspace'),
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if 'name' in request.data:
                workspace.name = request.data['name']
            if 'description' in request.data:
                workspace.description = request.data['description']
            
            workspace.save()
            
            serializer = WorkspaceSerializer(workspace)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'DELETE':
            # Only owner can delete
            if not is_owner:
                return Response(
                    api_response(ok=False, error='Only owner can delete workspace'),
                    status=status.HTTP_403_FORBIDDEN
                )
            
            workspace.delete()
            return Response(api_response(
                ok=True,
                data={'message': 'Workspace deleted successfully'}
            ))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_stats_view(request, workspace_id):
    """Get workspace statistics"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use service function to calculate stats
        stats = calculate_workspace_stats(workspace)
        
        return Response(api_response(ok=True, data=stats))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_dashboard_view(request, workspace_id):
    """
    Get dashboard data for workspace including stats, activity feed, and neural load time series.
    
    Returns aggregated data:
    - stats: workspace statistics (totalMemories, totalEmbeddings, totalConversations, systemLoad, lastActivity)
    - recentActivity: last 10 activity events ordered by timestamp desc
    - neuralLoad: time series with 24 data points at 5-minute intervals
    
    Requirements: 2.7, 2.8, 2.9, 8.2, 8.3
    """
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Use service function to calculate stats
        stats = calculate_workspace_stats(workspace)
        
        # Get recent activity from Activity model (last 10 events, ordered by timestamp desc)
        # Requirements: 2.8, 8.2
        recent_activities = workspace.activities.order_by('-timestamp')[:10]
        recent_activity = []
        
        for activity in recent_activities:
            recent_activity.append({
                'id': activity.id,
                'type': activity.type,
                'message': activity.description,
                'timestamp': activity.timestamp,
                'metadata': activity.metadata
            })
        
        # Generate neural load time series (24 data points, 5-minute intervals)
        # Requirements: 2.9, 8.3
        neural_load = _generate_neural_load_time_series(stats['systemLoad'])
        
        dashboard_data = {
            'stats': stats,
            'neuralLoad': neural_load,
            'recentActivity': recent_activity
        }
        
        return Response(api_response(ok=True, data=dashboard_data))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_activity_view(request, workspace_id):
    """
    Get activity feed for workspace.
    
    Returns chronological list of activity events (last 10 events by default, ordered by timestamp desc).
    Supports pagination with limit parameter.
    
    Requirements: 2.8, 8.2
    """
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get limit from query params (default 10, max 100)
        limit = int(request.query_params.get('limit', 10))
        limit = min(limit, 100)  # Cap at 100
        
        # Query Activity model (last N events, ordered by timestamp desc)
        # Requirements: 2.8, 8.2
        activities_qs = workspace.activities.order_by('-timestamp')[:limit]
        
        activities = []
        for activity in activities_qs:
            activities.append({
                'id': activity.id,
                'type': activity.type,
                'message': activity.description,
                'timestamp': activity.timestamp,
                'metadata': activity.metadata
            })
        
        return Response(api_response(
            ok=True,
            data={
                'activities': activities,
                'total': len(activities)
            }
        ))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workspace_neural_load_view(request, workspace_id):
    """Get neural load time series for workspace"""
    try:
        workspace = Workspace.objects.get(id=workspace_id)
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate base load using service
        stats = calculate_workspace_stats(workspace)
        base_load = stats['systemLoad']
        
        # Generate time series (last 24 data points, 5-minute intervals)
        neural_load = []
        now = timezone.now()
        
        for i in range(24):
            timestamp = now - timedelta(minutes=i * 5)
            # Add some variation
            value = base_load + ((i * 7) % 15 - 7)  # Varies ±7
            value = max(0, min(100, value))
            
            neural_load.insert(0, {
                'timestamp': timestamp,
                'value': value
            })
        
        return Response(api_response(
            ok=True,
            data={
                'neuralLoad': neural_load,
                'currentLoad': base_load
            }
        ))
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )
