"""
Memory Management Views (Workspace-Scoped)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Workspace, Memory
from .serializers_v2 import MemorySerializer, MemoryCreateSerializer, MemorySearchSerializer
from .memory_service import memory_service
from .activity_service import log_memory_created


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workspace_memories_view(request, workspace_id):
    """
    GET: List all memories in workspace
    POST: Create new memory in workspace
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
        
        if request.method == 'GET':
            # Optimize query with select_related
            memories = workspace.memories.select_related('workspace').all()
            
            # Apply search filter if provided
            search_query = request.query_params.get('search', '')
            if search_query:
                memories = memories.filter(
                    title__icontains=search_query
                ) | memories.filter(
                    content__icontains=search_query
                )
            
            # Apply sorting
            sort_by = request.query_params.get('sortBy', 'recent')
            if sort_by == 'title':
                memories = memories.order_by('title')
            elif sort_by == 'recent':
                memories = memories.order_by('-updated_at')
            
            serializer = MemorySerializer(memories, many=True)
            
            return Response(api_response(
                ok=True,
                data={
                    'memories': serializer.data,
                    'total': memories.count()
                }
            ))
        
        elif request.method == 'POST':
            serializer = MemoryCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    api_response(ok=False, error=serializer.errors),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create memory
            memory = Memory.objects.create(
                workspace=workspace,
                title=serializer.validated_data['title'],
                content=serializer.validated_data['content'],
                tags=serializer.validated_data.get('tags', []),
                metadata=serializer.validated_data.get('metadata', {})
            )
            
            # Store in search index
            memory_service.store(memory.content, memory.id)
            
            # Log activity
            log_memory_created(workspace, memory)
            
            response_serializer = MemorySerializer(memory)
            
            return Response(
                api_response(ok=True, data=response_serializer.data),
                status=status.HTTP_201_CREATED
            )
    
    except Workspace.DoesNotExist:
        return Response(
            api_response(ok=False, error='Workspace not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def memory_detail_view(request, memory_id):
    """
    GET: Get memory details
    PUT: Update memory
    DELETE: Delete memory
    """
    try:
        memory = Memory.objects.get(id=memory_id)
        workspace = memory.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = MemorySerializer(memory)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'PUT':
            content_changed = False
            
            if 'title' in request.data:
                memory.title = request.data['title']
            if 'content' in request.data:
                old_content = memory.content
                memory.content = request.data['content']
                content_changed = (old_content != memory.content)
                
                # Regenerate snippet if content changed
                if content_changed:
                    memory.snippet = memory.content[:150] + ('...' if len(memory.content) > 150 else '')
                    # Regenerate embedding
                    memory_service.store(memory.content, memory.id)
            if 'tags' in request.data:
                memory.tags = request.data['tags']
            if 'metadata' in request.data:
                memory.metadata = request.data['metadata']
            
            # Increment version number on every update
            memory.version += 1
            memory.save()
            
            serializer = MemorySerializer(memory)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'DELETE':
            memory.delete()
            return Response(api_response(
                ok=True,
                data={'message': 'Memory deleted successfully'}
            ))
    
    except Memory.DoesNotExist:
        return Response(
            api_response(ok=False, error='Memory not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def re_embed_memory_view(request, memory_id):
    """Re-generate embedding for memory"""
    try:
        memory = Memory.objects.get(id=memory_id)
        workspace = memory.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Re-store in search index (regenerates embedding)
        memory_service.store(memory.content, memory.id)
        
        memory.version += 1
        memory.save()
        
        serializer = MemorySerializer(memory)
        return Response(api_response(ok=True, data=serializer.data))
    
    except Memory.DoesNotExist:
        return Response(
            api_response(ok=False, error='Memory not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_memories_view(request):
    """Search memories using semantic search"""
    serializer = MemorySearchSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            api_response(ok=False, error=serializer.errors),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    query = serializer.validated_data['query']
    workspace_id = serializer.validated_data.get('workspaceId')
    top_k = serializer.validated_data.get('top_k', 5)
    
    # If workspace_id provided, check access
    if workspace_id:
        try:
            workspace = Workspace.objects.get(id=workspace_id)
            
            is_owner = workspace.owner == request.user
            is_member = workspace.members.filter(user=request.user).exists()
            
            if not (is_owner or is_member):
                return Response(
                    api_response(ok=False, error='Access denied'),
                    status=status.HTTP_403_FORBIDDEN
                )
        except Workspace.DoesNotExist:
            return Response(
                api_response(ok=False, error='Workspace not found'),
                status=status.HTTP_404_NOT_FOUND
            )
    
    # Search using memory service
    results = memory_service.search(query, top_k, workspace_id)
    
    return Response(api_response(ok=True, data={'results': results}))
