# Implementation Plan: Backend-Frontend Integration

## Overview

This implementation plan provides a step-by-step guide to finalize the Django backend for seamless integration with the React frontend. Each task builds incrementally, ensuring the backend provides all necessary endpoints and functionality to eliminate dummy data dependencies from the frontend.

---

## Tasks

- [x] 1. Update User Model and Authentication Serializers






  - Add `name` field to User model (CharField, max_length=255)
  - Add `avatar` field to User model (URLField, null=True, blank=True)
  - Update UserSerializer to include id, name, email, avatar, createdAt in camelCase
  - Update registration view to accept and store name field
  - Update login response to include complete user profile
  - _Requirements: 1.1, 1.2, 1.3, 9.2_

- [x] 2. Verify Workspace Models and Add Activity Model





  - Verify Workspace model has all required fields (id, name, description, owner, created_at, updated_at)
  - Verify TeamMember model has all required fields (id, user, workspace, role, status, joined_at)
  - Create Activity model for tracking workspace events
  - Add indexes on workspace (owner, updated_at) and team_member (workspace, user)
  - _Requirements: 2.1, 2.2, 8.2_

- [x] 3. Implement Workspace Statistics Calculation




  - Create `calculate_workspace_stats()` service function
  - Calculate totalMemories (count of workspace memories)
  - Calculate totalEmbeddings (count of memories with non-null embedding)
  - Calculate totalConversations (count of workspace conversations)
  - Calculate systemLoad using formula: (active_conversations * 10 + messages_last_hour) capped at 100
  - Calculate lastActivity (most recent timestamp across all entities)
  - Update workspace_stats_view to use calculation service
  - _Requirements: 2.6, 8.1, 8.4_

- [x] 4. Implement Workspace Dashboard and Activity Feed



  - Create workspace_dashboard_view to return aggregated data
  - Implement activity feed query (last 10 events, ordered by timestamp desc)
  - Create activity creation helper for automatic event logging
  - Add activity logging to memory creation, conversation creation, message sending
  - Implement neural load time series generation (24 data points, 5-minute intervals)
  - _Requirements: 2.7, 2.8, 2.9, 8.2, 8.3_

- [x] 5. Update Conversation Models and Serializers

  - Verify Conversation model has workspace FK (not user FK)
  - Verify Message model has is_pinned field and timestamp field
  - Verify ConversationMemory junction table exists
  - Create ConversationSerializer with camelCase fields
  - Create MessageSerializer with camelCase fields
  - Include injectedMemories array in conversation serialization
  - _Requirements: 4.1, 4.2, 4.6, 9.4, 9.5_

- [x] 6. Implement Message Operations

  - Implement send_message_view to create messages
  - Implement message pin/unpin functionality in message_detail_view
  - Implement message deletion with access validation
  - Update conversation updatedAt timestamp on message operations
  - _Requirements: 4.6, 4.7, 4.8_

- [x] 7. Implement Memory Injection System

  - Implement inject_memory_view to add memory to conversation
  - Prevent duplicate memory injections (check if already in array)
  - Implement remove_injected_memory_view to remove memory from conversation
  - Return updated conversation with injectedMemories array
  - _Requirements: 4.9, 4.10_

- [x] 8. Update Memory Models and Implement Embedding Generation

  - Verify Memory model has workspace FK, title, snippet, version fields
  - Install sentence-transformers library (pip install sentence-transformers)
  - Create embedding service using all-MiniLM-L6-v2 model
  - Implement generate_embedding() function to create vectors
  - Auto-generate snippet (first 150 chars) on memory save
  - Auto-generate embedding on memory creation and update
  - Store embedding as pickled numpy array in BinaryField
  - _Requirements: 5.1, 5.2, 14.1_

- [x] 9. Implement Memory Update and Re-embedding

  - Implement memory update in memory_detail_view
  - Increment version number on every update
  - Regenerate snippet if content changed
  - Regenerate embedding if content changed
  - Implement re_embed_memory_view for manual re-embedding
  - _Requirements: 5.4, 5.6_

- [x] 10. Implement Semantic Memory Search

  - Create search_memories_view endpoint
  - Generate query embedding using same model
  - Load all workspace memory embeddings from database
  - Calculate cosine similarity between query and all memories
  - Rank results by similarity score (descending)
  - Return top K results (default 10) with scores
  - Handle empty query (return all memories sorted by updatedAt)
  - _Requirements: 5.7, 14.2_

- [x] 11. Implement Integration Management

  - Verify Integration model exists with all fields
  - Install cryptography library (pip install cryptography)
  - Create encryption service for API keys using Fernet
  - Implement integrations_view for list/create operations
  - Implement integration_detail_view for get/update/delete operations
  - Mask API keys in serialization (show only first 3 and last 3 chars)
  - Encrypt API keys before database storage
  - Decrypt API keys only when needed for API calls
  - _Requirements: 6.1, 6.2
, 6.3, 10.7_

- [x] 12. Implement Integration Testing

  - Implement test_integration_view endpoint
  - For OpenAI: make test API call to /v1/models endpoint
  - For Anthropic: make test API call to /v1/messages endpoint
  - For Google: make test API call to appropriate endpoint
  - Update integration status based on test result (connected/error)
  - Store error message if test fails
  - Update lastTested timestamp
  - Return test result to frontend
  - _Requirements: 6.4_

- [x] 13. Implement Available Models Endpoint

  - Create available_models_view endpoint
  - Query all user integrations with status='connected'
  - Map each integration to cognitive model object
  - Include id, provider, name, displayName, brainRegion, status
  - Include 3D position coordinates for brain visualization
  - OpenAI: position (-2, 1, 1), brainRegion "Left Cortex"
  - Anthropic: position (2, 1, 1), brainRegion "Right Cortex"
  - Google: position (0, -1, 2), brainRegion "Occipital"
  - _Requirements: 6.6_

- [x] 14. Implement Settings and Data Export

  - Create settings endpoint to return user preferences
  - Implement profile update in update_profile_view
  - Create data export endpoint
  - Generate JSON containing all user workspaces, conversations, messages, memories
  - Include settings in export
  - Return file download or presigned URL
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 15. Implement Account Deletion

  - Create account deletion endpoint
  - Validate user authentication
  - Cascade delete all owned workspaces
  - Remove user from all team memberships
  - Delete all user integrations
  - Delete user account
  - Blacklist all user tokens
  - Return success confirmation
  - _Requirements: 7.5_

- [x] 16. Implement Team Management Endpoints

  - Verify all team endpoints exist in views_team.py
  - Implement list_team_members_view
  - Implement invite_team_member_view with user lookup by username/email
  - Implement update_member_role_view with admin permission check
  - Implement update_member_status_view
  - Implement remove_team_member_view with owner protection
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 17. Implement AI Chat Integration

  - Create AI routing service to select provider based on modelId
  - Implement context building: system prompt + injected memories + history
  - For OpenAI: use openai library to call chat completion API
  - For Anthropic: use anthropic library to call messages API
  - For Google: use google-generativeai library
  - Create assistant message with AI response
  - Store token count and model version in message metadata
  - Handle API errors gracefully
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [x] 18. Implement Comprehensive Error Handling

  - Ensure all views return envelope format {ok, data, error}
  - Implement custom exception handler for DRF
  - Return 400 for validation errors with field details
  - Return 401 for authentication errors
  - Return 403 for permission errors
  - Return 404 for not found errors
  - Return 500 for unexpected errors (with logging)
  - Add error logging for all 500 errors
  - _Requirements: 9.1, 12.1, 12.2, 12.3, 12.4_

- [x] 19. Implement CamelCase Serialization

  - Create custom serializer base class with camelCase conversion
  - Override to_representation() to convert all keys to camelCase
  - Override to_internal_value() to convert camelCase to snake_case
  - Apply to all serializers (User, Workspace, Conversation, Message, Memory, Integration, TeamMember)
  - Test date serialization (ISO 8601 format)
  - _Requirements: 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

- [x] 20. Implement Authentication and Authorization


  - Verify JWT authentication is configured with SimpleJWT
  - Add permission classes to all protected endpoints
  - Implement IsWorkspaceOwnerOrMember permission class
  - Implement IsWorkspaceAdmin permission class
  - Add workspace access validation to all workspace resource endpoints
  - Add conversation access validation (via workspace)
  - Add memory access validation (via workspace)
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 21. Configure CORS for Frontend

  - Update settings.py with CORS configuration
  - Add localhost:5173 to CORS_ALLOWED_ORIGINS (Vite dev server)
  - Add production frontend URL to CORS_ALLOWED_ORIGINS
  - Set CORS_ALLOW_CREDENTIALS = True
  - Configure CORS_ALLOW_HEADERS for authorization
  - Test preflight OPTIONS requests
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 22. Optimize Database Queries


  - Add select_related() for foreign key queries (workspace.owner, conversation.workspace)
  - Add prefetch_related() for reverse foreign keys (workspace.members, conversation.messages)
  - Add database indexes on frequently queried fields
  - Implement pagination for list endpoints (default 20, max 100)
  - Test query count for each endpoint (target < 10 queries)
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 23. Create Database Migrations


  - Run makemigrations for all model changes
  - Review migration files for correctness
  - Create data migration for existing data if needed
  - Test migrations on clean database
  - Test migrations with existing data
  - Document migration steps in README
  - _Requirements: All_

- [x] 24. Update API Documentation


  - Update spec.md with all new endpoints
  - Document request/response formats
  - Document authentication requirements
  - Document error responses
  - Add example requests for each endpoint
  - Generate Swagger/OpenAPI documentation
  - _Requirements: All_

- [x] 25. Create Environment Configuration

  - Create .env.example with all required variables
  - Document SECRET_KEY generation
  - Document ENCRYPTION_KEY generation (Fernet)
  - Document DATABASE_URL format
  - Document CORS configuration
  - Document optional AI provider API keys
  - _Requirements: All_

- [x] 26. Test Frontend Integration


  - Start Django backend server
  - Start React frontend dev server
  - Test user registration from frontend
  - Test user login from frontend
  - Test workspace creation and switching
  - Test conversation creation and messaging
  - Test memory creation and search
  - Test integration management
  - Test team management
  - Verify no CORS errors
  - Verify all API responses match frontend expectations
  - _Requirements: All_

- [x] 27. Performance Testing and Optimization



  - Test API response times for all endpoints
  - Optimize slow queries (target < 200ms for simple, < 500ms for complex)
  - Add caching for frequently accessed data (workspace stats)
  - Test concurrent user access
  - Test large dataset performance (1000+ memories, conversations)
  - Profile memory usage
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

---

## Summary

This implementation plan provides 27 major tasks ordered to build incrementally:

1. **Tasks 1-4**: User authentication and workspace foundation
2. **Tasks 5-10**: Conversation, message management, and memory system
3. **Tasks 11-13**: Integration management and available models
4. **Tasks 14-16**: Settings, export, account deletion, and team management
5. **Tasks 17-19**: AI integration, error handling, and serialization
6. **Tasks 20-22**: Authentication, CORS, and performance optimization
7. **Tasks 23-27**: Migrations, documentation, configuration, and final integration testing

Each task references specific requirements and builds upon previous tasks to ensure a complete, production-ready backend for the React frontend.
