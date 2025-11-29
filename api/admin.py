"""
Django admin configuration
"""
from django.contrib import admin
from .models import Memory, Conversation, ChatMessage, Workspace, TeamMember, Integration


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'workspace', 'created_at']
    list_filter = ['created_at', 'workspace']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'workspace', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at', 'status']
    search_fields = ['title', 'workspace__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'role', 'content_preview', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['content', 'conversation__title']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content'


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'workspace', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status', 'joined_at']
    search_fields = ['user__username', 'workspace__name']
    readonly_fields = ['id', 'joined_at']


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'provider', 'status', 'last_tested']
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['user__username', 'provider']
    readonly_fields = ['id', 'created_at', 'updated_at']
