"""
URL routing for API endpoints - Updated for Frontend Integration
"""
from django.urls import path
from . import views
from . import views_workspace, views_team, views_conversation, views_memory, views_integration, views_settings

urlpatterns = [
    # ============================================
    # WORKSPACE ENDPOINTS (NEW)
    # ============================================
    path('workspaces', views_workspace.workspaces_view, name='workspaces'),
    path('workspaces/<str:workspace_id>', views_workspace.workspace_detail_view, name='workspace-detail'),
    path('workspaces/<str:workspace_id>/stats', views_workspace.workspace_stats_view, name='workspace-stats'),
    path('workspaces/<str:workspace_id>/dashboard', views_workspace.workspace_dashboard_view, name='workspace-dashboard'),
    path('workspaces/<str:workspace_id>/activity', views_workspace.workspace_activity_view, name='workspace-activity'),
    path('workspaces/<str:workspace_id>/neural-load', views_workspace.workspace_neural_load_view, name='workspace-neural-load'),
    
    # ============================================
    # TEAM MANAGEMENT ENDPOINTS (NEW)
    # ============================================
    path('workspaces/<str:workspace_id>/team', views_team.list_team_members_view, name='team-list'),
    path('workspaces/<str:workspace_id>/team/invite', views_team.invite_team_member_view, name='team-invite'),
    path('workspaces/<str:workspace_id>/team/<str:user_id>/role', views_team.update_member_role_view, name='team-update-role'),
    path('workspaces/<str:workspace_id>/team/<str:user_id>/status', views_team.update_member_status_view, name='team-update-status'),
    path('workspaces/<str:workspace_id>/team/<str:user_id>', views_team.remove_team_member_view, name='team-remove'),
    
    # ============================================
    # CONVERSATION ENDPOINTS (UPDATED - Workspace-Scoped)
    # ============================================
    path('workspaces/<str:workspace_id>/conversations', views_conversation.workspace_conversations_view, name='workspace-conversations'),
    path('conversations/<str:conversation_id>', views_conversation.conversation_detail_view, name='conversation-detail'),
    path('conversations/<str:conversation_id>/messages', views_conversation.send_message_view, name='send-message'),
    path('conversations/<str:conversation_id>/messages/<str:message_id>', views_conversation.message_detail_view, name='message-detail'),
    path('conversations/<str:conversation_id>/inject-memory', views_conversation.inject_memory_view, name='inject-memory'),
    path('conversations/<str:conversation_id>/inject-memory/<str:memory_id>', views_conversation.remove_injected_memory_view, name='remove-injected-memory'),
    
    # ============================================
    # MEMORY ENDPOINTS (UPDATED - Workspace-Scoped)
    # ============================================
    path('workspaces/<str:workspace_id>/memories', views_memory.workspace_memories_view, name='workspace-memories'),
    path('memories/<str:memory_id>', views_memory.memory_detail_view, name='memory-detail'),
    path('memories/<str:memory_id>/re-embed', views_memory.re_embed_memory_view, name='memory-re-embed'),
    path('memories/search', views_memory.search_memories_view, name='memory-search'),
    
    # ============================================
    # INTEGRATION ENDPOINTS (NEW)
    # ============================================
    path('integrations', views_integration.integrations_view, name='integrations'),
    path('integrations/<str:integration_id>', views_integration.integration_detail_view, name='integration-detail'),
    path('integrations/<str:integration_id>/test', views_integration.test_integration_view, name='integration-test'),
    path('models/available', views_integration.available_models_view, name='available-models'),
    
    # ============================================
    # AUTHENTICATION ENDPOINTS
    # ============================================
    path('auth/register', views.register_view, name='register'),
    path('auth/login', views.login_view, name='login'),
    path('auth/logout', views.logout_view, name='logout'),
    path('auth/refresh', views.refresh_token_view, name='refresh-token'),
    path('auth/profile', views.user_profile_view, name='user-profile'),
    path('auth/profile/update', views.update_profile_view, name='update-profile'),
    
    # ============================================
    # SETTINGS AND DATA EXPORT ENDPOINTS (NEW)
    # ============================================
    path('settings', views_settings.settings_view, name='settings'),
    path('settings/profile', views_settings.update_profile_view, name='settings-update-profile'),
    path('settings/memory-retention', views_settings.update_memory_retention_view, name='settings-update-memory-retention'),
    path('export', views_settings.export_data_view, name='export-data'),
    
    # ============================================
    # HEALTH & UTILITY
    # ============================================
    path('health', views.health_check, name='health'),
    path('hooks/spec-update', views.spec_hook, name='spec-hook'),
    
    # ============================================
    # LEGACY ENDPOINTS (Backward Compatibility)
    # ============================================
    path('models', views.get_supported_models, name='supported-models'),
    path('chat', views.chat_view, name='chat'),
    path('mcp/remember', views.mcp_remember, name='mcp-remember'),
    path('mcp/batch-remember', views.batch_remember, name='batch-remember'),
    path('mcp/search', views.mcp_search, name='mcp-search'),
    path('mcp/inject', views.mcp_inject, name='mcp-inject'),
    path('mcp/listMemories', views.mcp_list_memories, name='mcp-list-memories'),
    path('mcp/index/rebuild', views.rebuild_memory_index, name='rebuild-index'),
    path('mcp/index/status', views.memory_index_status, name='index-status'),
]
