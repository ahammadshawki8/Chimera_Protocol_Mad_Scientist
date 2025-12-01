"""
Updated serializers for frontend integration with camelCase conversion
"""
from rest_framework import serializers
from .models import (
    User, Workspace, TeamMember, Integration, Conversation, 
    ChatMessage, Memory, ConversationMemory
)
import re


def snake_to_camel(snake_str):
    """Convert snake_case string to camelCase"""
    components = snake_str.split('_')
    # Keep the first component as is, capitalize the rest
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str):
    """Convert camelCase string to snake_case"""
    # Insert an underscore before any uppercase letter and convert to lowercase
    snake_str = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_str).lower()


class CamelCaseSerializerMixin:
    """
    Mixin to automatically convert field names between snake_case and camelCase.
    
    - to_representation(): Converts snake_case to camelCase for API responses
    - to_internal_value(): Converts camelCase to snake_case for incoming data
    """
    
    def to_representation(self, instance):
        """Convert all keys in the representation to camelCase"""
        data = super().to_representation(instance)
        return {snake_to_camel(key): value for key, value in data.items()}
    
    def to_internal_value(self, data):
        """Convert all keys in the input data to snake_case"""
        snake_case_data = {camel_to_snake(key): value for key, value in data.items()}
        return super().to_internal_value(snake_case_data)


# User Serializers
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model matching frontend User interface with camelCase"""
    createdAt = serializers.DateTimeField(source='date_joined', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'avatar', 'createdAt']
        read_only_fields = ['id', 'createdAt']


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


# Team Member Serializers
class TeamMemberUserSerializer(serializers.Serializer):
    """Serializer for user info in team member"""
    id = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model"""
    userId = serializers.CharField(source='user.id', read_only=True)
    workspaceId = serializers.CharField(source='workspace.id', read_only=True)
    joinedAt = serializers.DateTimeField(source='joined_at', read_only=True)
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamMember
        fields = ['id', 'userId', 'workspaceId', 'role', 'status', 'joinedAt', 'user']
        read_only_fields = ['id', 'joinedAt']
    
    def get_user(self, obj):
        return {
            'id': str(obj.user.id),
            'name': obj.user.name if hasattr(obj.user, 'name') else obj.user.username,
            'email': obj.user.email,
        }


# Workspace Serializers
class WorkspaceStatsSerializer(serializers.Serializer):
    """Serializer for workspace statistics"""
    totalMemories = serializers.IntegerField()
    totalEmbeddings = serializers.IntegerField()
    totalConversations = serializers.IntegerField()
    systemLoad = serializers.IntegerField()
    lastActivity = serializers.DateTimeField()


class WorkspaceSerializer(serializers.ModelSerializer):
    """Serializer for Workspace model"""
    ownerId = serializers.CharField(source='owner.id', read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'ownerId', 'members', 'stats', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'ownerId', 'createdAt', 'updatedAt']
    
    def get_stats(self, obj):
        # Calculate workspace statistics
        total_memories = obj.memories.count()
        total_conversations = obj.conversations.count()
        
        # System load calculation (0-100)
        # Simple formula: based on activity
        system_load = min(100, (total_memories + total_conversations * 5))
        
        # Last activity
        last_memory = obj.memories.order_by('-updated_at').first()
        last_conv = obj.conversations.order_by('-updated_at').first()
        
        last_activity = obj.updated_at
        if last_memory and last_memory.updated_at > last_activity:
            last_activity = last_memory.updated_at
        if last_conv and last_conv.updated_at > last_activity:
            last_activity = last_conv.updated_at
        
        return {
            'totalMemories': total_memories,
            'totalEmbeddings': total_memories,  # Same as memories for now
            'totalConversations': total_conversations,
            'systemLoad': system_load,
            'lastActivity': last_activity,
        }


class WorkspaceCreateSerializer(serializers.Serializer):
    """Serializer for creating a workspace"""
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


# Integration Serializers
class IntegrationSerializer(serializers.ModelSerializer):
    """Serializer for Integration model with API key masking"""
    lastTested = serializers.DateTimeField(source='last_tested', allow_null=True, read_only=True)
    errorMessage = serializers.CharField(source='error_message', allow_null=True, read_only=True)
    apiKey = serializers.SerializerMethodField()
    
    class Meta:
        model = Integration
        fields = ['id', 'provider', 'apiKey', 'status', 'lastTested', 'errorMessage']
        read_only_fields = ['id', 'status', 'lastTested', 'errorMessage']
    
    def get_apiKey(self, obj):
        """Return masked API key for security"""
        from .encryption_service import decrypt_api_key, mask_api_key
        try:
            decrypted_key = decrypt_api_key(obj.api_key)
            return mask_api_key(decrypted_key)
        except Exception:
            return "***"


class IntegrationCreateSerializer(serializers.Serializer):
    """Serializer for creating an integration"""
    provider = serializers.ChoiceField(choices=['openai', 'anthropic', 'google', 'deepseek'])
    apiKey = serializers.CharField(min_length=10, max_length=500)


# Message Serializers
class MessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model"""
    conversationId = serializers.CharField(source='conversation.id', read_only=True)
    isPinned = serializers.BooleanField(source='is_pinned')
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'conversationId', 'role', 'content', 'timestamp', 'isPinned', 'metadata']
        read_only_fields = ['id', 'timestamp']


class MessageCreateSerializer(serializers.Serializer):
    """Serializer for creating a message"""
    content = serializers.CharField()
    role = serializers.ChoiceField(choices=['user', 'assistant', 'system'], default='user')
    getAiResponse = serializers.BooleanField(required=False, default=True)
    
    class Meta:
        # Allow extra fields to be passed through
        extra_kwargs = {
            'getAiResponse': {'write_only': True}
        }


# Conversation Serializers
class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    workspaceId = serializers.CharField(source='workspace.id', read_only=True)
    modelId = serializers.CharField(source='model_id')
    messages = MessageSerializer(many=True, read_only=True)
    injectedMemories = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'workspaceId', 'title', 'modelId', 'messages', 'injectedMemories', 'status', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'workspaceId', 'createdAt', 'updatedAt']
    
    def get_injectedMemories(self, obj):
        # Return list of memory objects with id and isActive status
        return [
            {
                'id': link.memory_id,
                'isActive': link.is_active
            }
            for link in obj.injected_memory_links.all()
        ]


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer for creating a conversation"""
    title = serializers.CharField(max_length=255, required=False, default='New Conversation')
    modelId = serializers.CharField()


class ConversationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for conversation list"""
    workspaceId = serializers.CharField(source='workspace.id', read_only=True)
    modelId = serializers.CharField(source='model_id')
    messageCount = serializers.SerializerMethodField()
    lastUpdated = serializers.DateTimeField(source='updated_at', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'workspaceId', 'title', 'modelId', 'status', 'messageCount', 'lastUpdated', 'createdAt']
        read_only_fields = ['id', 'workspaceId', 'createdAt', 'lastUpdated']
    
    def get_messageCount(self, obj):
        return obj.messages.count()


# Memory Serializers
class MemorySerializer(serializers.ModelSerializer):
    """Serializer for Memory model"""
    workspaceId = serializers.CharField(source='workspace.id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    embedding = serializers.SerializerMethodField()
    
    class Meta:
        model = Memory
        fields = ['id', 'workspaceId', 'title', 'content', 'snippet', 'tags', 'embedding', 'metadata', 'version', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'workspaceId', 'snippet', 'version', 'createdAt', 'updatedAt']
    
    def get_embedding(self, obj):
        """Generate a visual signature from the memory content using a hash-based approach"""
        import hashlib
        import math
        
        # Use content + title to generate unique signature
        text = f"{obj.title}:{obj.content}"
        
        # Generate hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        # Convert to 100 float values between -1 and 1 for visualization
        signature = []
        for i in range(100):
            # Use different parts of the hash with some variation
            byte_idx = i % len(hash_bytes)
            prev_byte = hash_bytes[(i - 1) % len(hash_bytes)]
            
            # Combine bytes for more variation
            combined = (hash_bytes[byte_idx] + prev_byte * (i % 7)) % 256
            
            # Add sine wave component based on position for smoother curves
            wave = math.sin(i * 0.3 + hash_bytes[i % len(hash_bytes)] * 0.1)
            
            # Normalize to -1 to 1 range
            value = ((combined / 255.0) * 2 - 1) * 0.5 + wave * 0.5
            signature.append(round(value, 4))
        
        return signature


class MemoryCreateSerializer(serializers.Serializer):
    """Serializer for creating a memory"""
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    metadata = serializers.DictField(required=False, default=dict)


class MemorySearchSerializer(serializers.Serializer):
    """Serializer for memory search"""
    query = serializers.CharField()
    workspaceId = serializers.CharField(required=False)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=50)


# Dashboard Serializers
class TimeSeriesDataSerializer(serializers.Serializer):
    """Serializer for time series data"""
    timestamp = serializers.DateTimeField()
    value = serializers.IntegerField()


class ActivityItemSerializer(serializers.Serializer):
    """Serializer for activity feed items"""
    id = serializers.CharField()
    type = serializers.CharField()
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
    metadata = serializers.DictField(required=False)


class DashboardDataSerializer(serializers.Serializer):
    """Serializer for dashboard data"""
    stats = WorkspaceStatsSerializer()
    neuralLoad = TimeSeriesDataSerializer(many=True)
    recentActivity = ActivityItemSerializer(many=True)


# Team Management Serializers
class TeamInviteSerializer(serializers.Serializer):
    """Serializer for inviting team members"""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=['admin', 'researcher', 'observer'], default='researcher')


class TeamRoleUpdateSerializer(serializers.Serializer):
    """Serializer for updating team member role"""
    role = serializers.ChoiceField(choices=['admin', 'researcher', 'observer'])


class TeamStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating team member status"""
    status = serializers.ChoiceField(choices=['online', 'away', 'offline'])
