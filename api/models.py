"""
Database models for Chimera Protocol API
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """
    Custom User model with additional fields for Chimera Protocol
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Full name of the user")
    avatar = models.URLField(null=True, blank=True, help_text="URL to user's avatar image")
    # email is already in AbstractUser but we ensure it's unique
    email = models.EmailField(unique=True)
    
    # Memory retention settings
    auto_store = models.BooleanField(default=True, help_text="Automatically store memories")
    retention_period = models.CharField(
        max_length=50,
        default='indefinite-84',
        help_text="Memory retention period: 7-days, 30-days, 90-days, indefinite-84, indefinite-forever"
    )
    
    # created_at equivalent (date_joined is already in AbstractUser)
    
    def __str__(self):
        return f"{self.name} ({self.username})"
    
    class Meta:
        db_table = 'auth_user'


class Workspace(models.Model):
    """
    Workspace for organizing conversations and memories
    Supports team collaboration
    """
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
        ]

    def __str__(self):
        return f"Workspace: {self.name}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"workspace-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class TeamMember(models.Model):
    """
    Team member in a workspace with role-based access
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('researcher', 'Researcher'),
        ('observer', 'Observer'),
    ]
    
    STATUS_CHOICES = [
        ('online', 'Online'),
        ('away', 'Away'),
        ('offline', 'Offline'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='researcher')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'workspace']
        indexes = [
            models.Index(fields=['workspace', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.workspace.name} ({self.role})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"tm-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class Integration(models.Model):
    """
    API integration for cognitive models (OpenAI, Anthropic, Google)
    """
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google'),
    ]
    
    STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('error', 'Error'),
        ('disconnected', 'Disconnected'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integrations')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    api_key = models.CharField(max_length=255)  # Should be encrypted in production
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disconnected')
    last_tested = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'provider']
        indexes = [
            models.Index(fields=['user', 'provider']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.provider} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"int-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class Conversation(models.Model):
    """
    Represents a conversation session between user and AI
    Belongs to a workspace and uses a specific cognitive model
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default='New Conversation')
    model_id = models.CharField(max_length=50, help_text="ID of the cognitive model used")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['workspace', '-updated_at']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"Conversation: {self.title} ({self.workspace.name})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"conv-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class Memory(models.Model):
    """
    Stores memory fragments with vector embeddings for semantic search
    Belongs to a workspace
    """
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memories')
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="The memory content")
    snippet = models.CharField(max_length=200, blank=True, help_text="First 150 chars preview")
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    embedding = models.BinaryField(
        null=True, 
        blank=True,
        help_text="Vector embedding for similarity search"
    )
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Additional metadata (source, conversationId, modelUsed)"
    )
    version = models.IntegerField(default=1, help_text="Version number for tracking updates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Memory: {self.title} ({self.workspace.name})"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"memory-{uuid.uuid4().hex[:12]}"
        # Auto-generate snippet from content
        if not self.snippet and self.content:
            self.snippet = self.content[:150] + ('...' if len(self.content) > 150 else '')
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
    """
    Stores individual chat messages
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.CharField(max_length=50, primary_key=True, editable=False)
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False, help_text="Whether this message is pinned")
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"msg-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class ConversationMemory(models.Model):
    """
    Junction table for tracking which memories are injected into conversations
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='injected_memory_links')
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name='injected_in_conversations')
    injected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['conversation', 'memory']
        indexes = [
            models.Index(fields=['conversation', 'injected_at']),
        ]

    def __str__(self):
        return f"{self.memory.title} injected in {self.conversation.title}"


class Activity(models.Model):
    """
    Tracks workspace activity events for the activity feed
    """
    TYPE_CHOICES = [
        ('memory_created', 'Memory Created'),
        ('conversation_created', 'Conversation Created'),
        ('message_sent', 'Message Sent'),
        ('team_member_added', 'Team Member Added'),
        ('model_used', 'Model Used'),
    ]
    
    id = models.CharField(max_length=50, primary_key=True, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='activities')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField(help_text="Human-readable description of the activity")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional activity metadata")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['workspace', '-timestamp']),
        ]
        verbose_name_plural = 'Activities'

    def __str__(self):
        return f"{self.workspace.name}: {self.type} at {self.timestamp}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"activity-{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)
