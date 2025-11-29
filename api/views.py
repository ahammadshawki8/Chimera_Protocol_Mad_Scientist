"""
Legacy API Views - Backward Compatibility
These views maintain backward compatibility with older API clients.
New code should use the modular view files (views_workspace, views_conversation, etc.)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import json
import os
import time

from .models import User, Memory
from .serializers_v2 import UserSerializer, UserRegistrationSerializer, UserLoginSerializer, MemorySerializer
from .memory_service import memory_service
from .llm_router import call_llm, get_supported_models


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint"""
    try:
        Memory.objects.count()
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return Response(api_response(ok=True, data={
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'database': db_status
    }))


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(api_response(ok=False, error=serializer.errors), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        data = serializer.validated_data
        username = data['email'].split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(username=username, email=data['email'], password=data['password'])
 
        user.name = data['name']
        user.save()
        
        refresh = RefreshToken.for_user(user)
        user_serializer = UserSerializer(user)
        
        return Response(api_response(ok=True, data={
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user_serializer.data
        }), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(api_response(ok=False, error=serializer.errors), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=serializer.validated_data['email'])
    except User.DoesNotExist:
        return Response(api_response(ok=False, error='Invalid credentials'), status=
status.HTTP_401_UNAUTHORIZED)
    
    user = authenticate(username=user.username, password=serializer.validated_data['password'])
    if user is None:
        return Response(api_response(ok=False, error='Invalid credentials'), status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    return Response(api_response(ok=True, data={
        'token': str(refresh.access_token),
  
      'refresh': str(refresh),
        'user': UserSerializer(user).data
    }))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            RefreshToken(refresh_token).blacklist()
        return Response(api_response(ok=True, data={'message': 'Successfully logged out'}))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """Refresh access token"""
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response(api_response(ok=False, error='Refresh token required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response(api_response(ok=True, data={'token': str(refresh.access_token)}))
    except Exception:
        return Response(api_response(ok=False, error='Invalid or expired refresh token'), status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """Get current user profile"""
    return Response(api_response(ok=True, data=UserSerializer(request.user).data))


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """Update user profile"""
    user = request.user
    if request.data.get('name'):
        user.name = request.data['name']
    if request.data.get('email'):
        if User.objects.filter(email=request.data['email']).exclude(id=user.id).exists():
            return Response(api_response(ok=False, error='Email already exists'), status=status.HTTP_400_BAD_REQUEST)
        user.email = request.data['email']
    user.save()
    return Response(api_response(ok=True, data=UserSerializer(user).data))


@api_view(['POST'])
@permission_classes([AllowAny])
def mcp_remember(request):
    """Store a memory (legacy MCP endpoint)"""
    text = request.data.get('text')
    conversation_id = request.data.get('conversation_id')
    if not text or not conversation_id:
        return Response(api_response(ok=False, error='text and conversation_id required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        memory = Memory.objects.create(text=text, tags=request.data.get('tags', []), 
                                      conversation_id=conversation_id, metadata=request.data.get('metadata', {}))
        return Response(api_response(ok=True, data={'id': memory.id, 'status': 'saved', 
                                                    'created_at': memory.created_at.isoformat()}), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def batch_remember(request):
    """Store multiple memories (legacy MCP endpoint)"""
    memories_data = request.data.get('memories', [])
    if not isinstance(memories_data, list):
        return Response(api_response(ok=False, error='memories array required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        created = []
        for mem_data in memories_data:
            if mem_data.get('text') and mem_data.get('conversation_id'):
                memory = Memory.objects.create(text=mem_data['text'], tags=mem_data.get('tags', []),
                                              conversation_id=mem_data['conversation_id'], metadata=mem_data.get('metadata', {}))
                created.append({'id': memory.id})
        return Response(api_response(ok=True, data={'created': len(created), 'memories': created}), status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mcp_search(request):
    """Search memories (legacy MCP endpoint)"""
    query = request.data.get('query')
    if not query:
        return Response(api_response(ok=False, error='query required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        results = memory_service.search(query, request.data.get('top_k', 5), request.data.get('conversation_id'))
        return Response(api_response(ok=True, data=results))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def mcp_inject(request):
    """Get memories for context injection (legacy MCP endpoint)"""
    conversation_id = request.data.get('conversation_id')
    if not conversation_id:
        return Response(api_response(ok=False, error='conversation_id required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        memories = Memory.objects.filter(conversation_id=conversation_id).order_by('-created_at')[:request.data.get('max_memories', 10)]
        memory_list = [{'id': m.id, 'text': m.text, 'tags': m.tags, 'created_at': m.created_at.isoformat()} for m in memories]
        context = "\n".join([f"- {m.text}" for m in memories]) if memories else "No memories found."
        return Response(api_response(ok=True, data={'injected_context': context, 'memory_count': len(memory_list), 'memories': memory_list}))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def mcp_list_memories(request):
    """List memories with pagination (legacy MCP endpoint)"""
    conversation_id = request.query_params.get('conversation_id')
    if not conversation_id:
        return Response(api_response(ok=False, error='conversation_id required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        limit = int(request.query_params.get('limit', 20))
        offset = int(request.query_params.get('offset', 0))
        memories = Memory.objects.filter(conversation_id=conversation_id).order_by('-created_at')
        total = memories.count()
        memories_page = memories[offset:offset + limit]
        return Response(api_response(ok=True, data={'memories': MemorySerializer(memories_page, many=True).data, 
                                                    'total': total, 'limit': limit, 'offset': offset}))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_view(request):
    """Chat with AI (legacy endpoint)"""
    conversation_id = request.data.get('conversation_id')
    message = request.data.get('message')
    if not conversation_id or not message:
        return Response(api_response(ok=False, error='conversation_id and message required'), status=status.HTTP_400_BAD_REQUEST)
    
    try:
        start_time = time.time()
        memories = Memory.objects.filter(conversation_id=conversation_id).order_by('-created_at')[:10]
        context = "\n".join([f"- {m.text}" for m in memories])
        
        llm_response = call_llm(request.data.get('model', 'echo'), message, context)
        
        if request.data.get('remember', False):
            Memory.objects.create(text=f"User: {message}", conversation_id=conversation_id, tags=['chat'])
            Memory.objects.create(text=f"Assistant: {llm_response['reply']}", conversation_id=conversation_id, tags=['chat'])
        
        execution_time = int((time.time() - start_time) * 1000)
        return Response(api_response(ok=True, data={
            'reply': llm_response['reply'],
            'model_used': llm_response['model_used'],
            'trace': {'model': llm_response['model_used'], 'provider': llm_response.get('provider', 'unknown'),
                     'execution_time_ms': execution_time, 'timestamp': timezone.now().isoformat()}
        }))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_supported_models(request):
    """Get list of all supported LLM models"""
    models = get_supported_models()
    return Response(api_response(ok=True, data={'models': models, 'total': sum(len(m) for m in models.values())}))


@api_view(['POST'])
@permission_classes([AllowAny])
def rebuild_memory_index(
request):
    """Rebuild memory search index"""
    try:
        memory_service.rebuild_index()
        return Response(api_response(ok=True, data={'message': 'Index rebuilt successfully'}))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def memory_index_status(request):
    """Check memory index status"""
    try:
        status_data = memory_service.get_index_status()
        return Response(api_response(ok=True, data=status_data))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def spec_hook(request):
    """Spec Hook endpoint - Auto-update spec.md"""
    try:
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.kiro', 'spec.md')
        new_entry = f"\n\n## Hook-Added Endpoint\n"
        new_entry += f"- **{request.data.get('method', 'GET')}** `{request.data.get('path', '/unknown')}`\n"
        new_entry += f"  - Description: {request.data.get('description', 'No description')}\n"
        new_entry += f"  - Type: {request.data.get('type', 'unknown')}\n"
        new_entry += f"  - Added: {timezone.now().isoformat()}\n"
        
        with open(spec_path, 'a', encoding='utf-8') as f:
            f.write(new_entry)
        
        return Response(api_response(ok=True, data={'status': 'ok', 'updated': True, 'message': 'Spec updated successfully'}))
    except Exception as e:
        return Response(api_response(ok=False, error=str(e)), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
