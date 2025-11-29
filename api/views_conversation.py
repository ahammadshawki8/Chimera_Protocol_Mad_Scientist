"""
Conversation Management Views (Workspace-Scoped)
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Workspace, Conversation, ChatMessage, Memory, ConversationMemory
from .serializers_v2 import (
    ConversationSerializer, ConversationListSerializer,
    ConversationCreateSerializer, MessageSerializer,
    MessageCreateSerializer
)
from .activity_service import log_conversation_created, log_message_sent


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def workspace_conversations_view(request, workspace_id):
    """
    GET: List all conversations in workspace
    POST: Create new conversation in workspace
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
            conversations = workspace.conversations.select_related('workspace').all()
            serializer = ConversationListSerializer(conversations, many=True)
            
            return Response(api_response(
                ok=True,
                data={
                    'conversations': serializer.data,
                    'total': conversations.count()
                }
            ))
        
        elif request.method == 'POST':
            serializer = ConversationCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    api_response(ok=False, error=serializer.errors),
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create conversation
            conversation = Conversation.objects.create(
                workspace=workspace,
                title=serializer.validated_data.get('title', 'New Conversation'),
                model_id=serializer.validated_data['modelId'],
                status='active'
            )
            
            # Log activity
            log_conversation_created(workspace, conversation)
            
            response_serializer = ConversationSerializer(conversation)
            
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
def conversation_detail_view(request, conversation_id):
    """
    GET: Get conversation with all messages
    PUT: Update conversation
    DELETE: Delete conversation
    """
    try:
        # Optimize query with select_related and prefetch_related
        conversation = Conversation.objects.select_related('workspace').prefetch_related('messages', 'injected_memory_links__memory').get(id=conversation_id)
        workspace = conversation.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            serializer = ConversationSerializer(conversation)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'PUT':
            if 'title' in request.data:
                conversation.title = request.data['title']
            if 'status' in request.data:
                conversation.status = request.data['status']
            
            conversation.save()
            
            serializer = ConversationSerializer(conversation)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'DELETE':
            conversation.delete()
            return Response(api_response(
                ok=True,
                data={'message': 'Conversation deleted successfully'}
            ))
    
    except Conversation.DoesNotExist:
        return Response(
            api_response(ok=False, error='Conversation not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request, conversation_id):
    """
    Send a message in conversation and get AI response
    Requirements 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        workspace = conversation.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_content = serializer.validated_data['content']
        
        # Create user message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_content,
            is_pinned=False,
            metadata={}
        )
        
        # Update conversation timestamp
        conversation.save(update_fields=['updated_at'])
        
        # Log activity
        log_message_sent(workspace, conversation, user_message)
        
        # Get AI response if requested (default: True)
        get_ai_response = request.data.get('getAiResponse', True)
        
        assistant_message = None
        if get_ai_response:
            try:
                # Get provider from model_id
                from .llm_router import get_provider, call_llm_with_conversation
                from .encryption_service import decrypt_api_key
                from .models import Integration
                
                provider = get_provider(conversation.model_id)
                
                # Get user's integration for this provider
                try:
                    integration = Integration.objects.get(
                        user=request.user,
                        provider=provider,
                        status='connected'
                    )
                    
                    # Decrypt API key
                    api_key = decrypt_api_key(integration.api_key)
                    
                    # Call AI model
                    ai_response = call_llm_with_conversation(
                        conversation=conversation,
                        user_message=user_content,
                        api_key=api_key
                    )
                    
                    if ai_response['status'] == 'success':
                        # Create assistant message
                        assistant_message = ChatMessage.objects.create(
                            conversation=conversation,
                            role='assistant',
                            content=ai_response['reply'],
                            is_pinned=False,
                            metadata={
                                'tokens': ai_response.get('tokens', 0),
                                'model_version': ai_response.get('model_used', conversation.model_id),
                                'provider': ai_response.get('provider', provider)
                            }
                        )
                        
                        # Log activity
                        log_message_sent(workspace, conversation, assistant_message)
                    else:
                        # AI call failed, return error in response
                        error_msg = ai_response.get('error', 'AI call failed')
                        response_serializer = MessageSerializer(user_message)
                        return Response(
                            api_response(
                                ok=False,
                                error=f"AI response failed: {error_msg}",
                                data={'userMessage': response_serializer.data}
                            ),
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                
                except Integration.DoesNotExist:
                    # No integration found for provider
                    response_serializer = MessageSerializer(user_message)
                    return Response(
                        api_response(
                            ok=False,
                            error=f"No connected integration found for provider: {provider}",
                            data={'userMessage': response_serializer.data}
                        ),
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            except Exception as e:
                # AI call failed, but user message was saved
                response_serializer = MessageSerializer(user_message)
                return Response(
                    api_response(
                        ok=False,
                        error=f"AI call failed: {str(e)}",
                        data={'userMessage': response_serializer.data}
                    ),
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # Return both messages
        user_serializer = MessageSerializer(user_message)
        
        if assistant_message:
            assistant_serializer = MessageSerializer(assistant_message)
            return Response(
                api_response(ok=True, data={
                    'userMessage': user_serializer.data,
                    'assistantMessage': assistant_serializer.data
                }),
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                api_response(ok=True, data={
                    'userMessage': user_serializer.data
                }),
                status=status.HTTP_201_CREATED
            )
    
    except Conversation.DoesNotExist:
        return Response(
            api_response(ok=False, error='Conversation not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def message_detail_view(request, conversation_id, message_id):
    """
    PUT: Update message (pin/unpin)
    DELETE: Delete message
    """
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        workspace = conversation.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            message = conversation.messages.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return Response(
                api_response(ok=False, error='Message not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'PUT':
            if 'isPinned' in request.data:
                message.is_pinned = request.data['isPinned']
                message.save()
                
                # Update conversation timestamp
                conversation.save(update_fields=['updated_at'])
            
            serializer = MessageSerializer(message)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'DELETE':
            message.delete()
            
            # Update conversation timestamp
            conversation.save(update_fields=['updated_at'])
            
            return Response(api_response(
                ok=True,
                data={'message': 'Message deleted successfully'}
            ))
    
    except Conversation.DoesNotExist:
        return Response(
            api_response(ok=False, error='Conversation not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inject_memory_view(request, conversation_id):
    """Inject memory into conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        workspace = conversation.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        memory_id = request.data.get('memoryId')
        if not memory_id:
            return Response(
                api_response(ok=False, error='memoryId required'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            memory = Memory.objects.get(id=memory_id, workspace=workspace)
        except Memory.DoesNotExist:
            return Response(
                api_response(ok=False, error='Memory not found'),
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or get injection
        ConversationMemory.objects.get_or_create(
            conversation=conversation,
            memory=memory
        )
        
        return Response(api_response(
            ok=True,
            data={'message': 'Memory injected successfully'}
        ))
    
    except Conversation.DoesNotExist:
        return Response(
            api_response(ok=False, error='Conversation not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_injected_memory_view(request, conversation_id, memory_id):
    """Remove injected memory from conversation"""
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        workspace = conversation.workspace
        
        # Check access
        is_owner = workspace.owner == request.user
        is_member = workspace.members.filter(user=request.user).exists()
        
        if not (is_owner or is_member):
            return Response(
                api_response(ok=False, error='Access denied'),
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            injection = ConversationMemory.objects.get(
                conversation=conversation,
                memory_id=memory_id
            )
            injection.delete()
            
            return Response(api_response(
                ok=True,
                data={'message': 'Memory removed successfully'}
            ))
        except ConversationMemory.DoesNotExist:
            return Response(
                api_response(ok=False, error='Memory injection not found'),
                status=status.HTTP_404_NOT_FOUND
            )
    
    except Conversation.DoesNotExist:
        return Response(
            api_response(ok=False, error='Conversation not found'),
            status=status.HTTP_404_NOT_FOUND
        )
