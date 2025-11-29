# Requirements Document: Backend-Frontend Integration Finalization

## Introduction

This specification defines the complete backend API requirements to support the Chimera Protocol frontend application. The frontend is a React + TypeScript application using Zustand for state management, with 6 stores managing authentication, workspaces, conversations, memories, integrations, and settings. The backend must provide REST API endpoints that exactly match the data structures and operations expected by the frontend, eliminating all dummy data dependencies.

## Glossary

- **System**: The Chimera Protocol Django REST Framework backend
- **Frontend**: The React + TypeScript client application
- **User**: An authenticated person using the Chimera Protocol
- **Workspace**: A container for organizing conversations, memories, and team members
- **Conversation**: A chat session between a user and an AI model
- **Message**: An individual chat message within a conversation
- **Memory**: A stored knowledge fragment with semantic embedding
- **Integration**: An API key configuration for an AI model provider
- **Team Member**: A user with access to a specific workspace
- **Cognitive Model**: An AI model (GPT-4, Cl
aude, Gemini) available for conversations
- **Embedding**: A vector representation of text for semantic search
- **JWT**: JSON Web Token used for authentication
- **MCP**: Memory Context Protocol for memory operations

## Requirements

### Requirement 1: User Authentication and Profile Management

**User Story:** As a user, I want to register, login, and manage my profile, so that I can securely access the Chimera Protocol system.

#### Acceptance Criteria

1. WHEN a user submits registration with name, email, and password THEN the System SHALL create a new user account and return JWT tokens with user profile data including id, name, email, and createdAt timestamp
2. WHEN a user submits login credentials with email and password THEN the System SHALL validate credentials and return JWT access token, refresh token, and complete user profile
3. WHEN a user requests profile information with valid JWT THEN the System SHALL return current user data including id, name, email, and createdAt
4. WHEN a user updates profile with new name or email THEN the System SHALL validate uniqueness of email and update user record
5. WHEN a user requests logout with refresh token THEN the System SHALL blacklist the refresh token and invalidate the session
6. WHEN a user requests token refresh with valid refresh token THEN the System SHALL return a new access token

### Requirement 2: Workspace Management

**User Story:** As a user, I want to create and manage workspaces, so that I can organize my AI conversations and memories into separate projects.

#### Acceptance Criteria

1. WHEN a user requests workspace list THEN the System SHALL return all workspaces where user is owner or member, including workspace stats (totalMemories, totalEmbeddings, totalConversations, systemLoad, lastActivity)
2. WHEN a user creates a workspace with name and optional description THEN the System SHALL create workspace, assign user as owner with admin role, and return complete workspace object with gener
ated id, timestamps, and empty members array
3. WHEN a user requests workspace details by id THEN the System SHALL return complete workspace object including all team members with their roles and status
4. WHEN a user updates workspace with new name or description THEN the System SHALL validate ownership or admin role and update workspace record with new updatedAt timestamp
5. WHEN a user deletes workspace THEN the System SHALL validate ownership, cascade delete all conversations and memories, and remove workspace record
6. WHEN a user requests workspace statistics THEN the System SHALL calculate and return totalMemories count, totalEmbeddings count, totalConversations count, systemLoad percentage (0-100), and lastActivity timestamp
7. WHEN a user requests workspace dashboard data THEN the System SHALL return aggregated stats, recent activity feed (last 10 events), and neural load time series (last 24 data points)
8. WHEN a user requests workspace activity feed THEN the System SHALL return chronological list of system events including memory creation, conversation creation, team member changes, and model usage
9. WHEN a user requests neural load time series THEN the System SHALL return array of timestamp-value pairs representing system load over time with 5-minute intervals

### Requirement 3: Team Collaboration

**User Story:** As a workspace owner, I want to invite team members and manage their roles, so that multiple people can collaborate on AI projects.

#### Acceptance Criteria

1. WHEN a workspace owner requests team member list THEN the System SHALL return all team members with userId, role (admin/researcher/observer), status (online/away/offline), and joinedAt timestamp
2. WHEN a workspace owner invites user by username or email THEN the System SHALL validate user exists, create team member record with specified role, and return updated member count
3. WHEN a workspace admin updates member role THEN the System SHALL validate admin permissions, update team member role, and return updated member object
4. WHEN a workspace admin removes team member THEN the System SHALL validate admin permissions, prevent removal of workspace owner, delete team member record, and return success confirmation
5. WHEN a team member updates their status THEN the System SHALL update status field (online/away/offline) and return updated member object
6. WHEN a user accesses workspace resource THEN the System SHALL validate user is owner or team member before granting access

### Requirement 4: Conversation Management

**User Story:** As a user, I want to create conversations with AI models and send messages, so that I can interact with multiple cognitive models in organized chat sessions.

#### Acceptance Criteria

1. WHEN a user requests conversation list for workspace THEN the System SHALL return all conversations with id, title, modelId, status, message count, and timestamps
2. WHEN a user creates conversation with workspaceId and modelId THEN the System SHALL validate workspace access, create conversation with generated id and default title, and return complete conversation object with empty messages array
3. WHEN a user requests conversation details by id THEN the System SHALL validate access, return conversation object with all messages in chronological order, and list of injectedMemories ids
4. WHEN a user updates conversation title or status THEN the System SHALL validate access, update conversation record with new updatedAt timestamp, and return updated conversation object
5. WHEN a user deletes conversation THEN the System SHALL validate access, cascade delete all messages, remove memory injections, and return success confirmation
6. WHEN a user sends message with conversationId and content THEN the System SHALL validate access, create message with role (user/assistant), timestamp, and isPinned false, append to conversation messages, and return message object
7. WHEN a user pins or unpins message THEN the System SHALL validate access, toggle isPinned boolean, and return updated message object
8. WHEN a user deletes message THEN the System SHALL validate access, remove message from conversation, and return success confirmation
9. WHEN a user injects memory into conversation THEN the System SHALL validate access to both conversation and memory, add memory id to conversation injectedMemories array, and return success confirmation
10. WHEN a user removes injected memory from conversation THEN the System SHALL validate access, remove memory id from injectedMemories array, and return success confirmation

### Requirement 5: Memory Bank Management

**User Story:** As a user, I want to store, search, and manage knowledge fragments with semantic embeddings, so that AI models can access relevant context during conversations.

#### Acceptance Criteria

1. WHEN a user requests memory list for workspace THEN the System SHALL return all memories with id, title, snippet (first 150 chars), tags, metadata, version, and timestamps
2. WHEN a user creates memory with workspaceId, title, content, and tags THEN the System SHALL validate workspace access, generate embedding vector, create snippet, assign version 1, and return complete memory object
3. WHEN a user requests memory details by id THEN the System SHALL validate access, return complete memory object including full content and embedding vector
4. WHEN a user updates memory with new title, content, or tags THEN the System SHALL validate access, regenerate snippet if content changed, increment version number, update updatedAt timestamp, and return updated memory object
5. WHEN a user deletes memory THEN the System SHALL validate access, remove memory from all conversation injections, delete memory record, and return success confirmation
6. WHEN a user requests memory re-embedding THEN the System SHALL validate access, regenerate embedding vector using current content, increment version number, and return updated memory object
7. WHEN a user searches memories with query string THEN the System SHALL perform semantic similarity search across all workspace memories, rank by relevance score, and return top matching memories with scores
8. WHEN a user filters memories by tags THEN the System SHALL return memories containing any of the specified tags
9. WHEN a user sorts memories by date, title, or relevance THEN the System SHALL return memories in specified order

### Requirement 6: AI Model Integration Management

**User Story:** As a user, I want to configure API keys for different AI providers, so that I can use multiple cognitive models in my conversations.

#### Acceptance Criteria

1. WHEN a user requests integration list THEN the System SHALL return all user integrations with id, provider (openai/anthropic/google), status (connected/error/disconnected), lastTested timestamp, and masked apiKey
2. WHEN a user creates integration with provider and apiKey THEN the System SHALL validate provider type, store encrypted apiKey, set status to disconnected, and return integration object with masked key
3. WHEN a user updates integration apiKey THEN the System SHALL validate access, update encrypted apiKey, set status to disconnected, and return updated integration object
4. WHEN a user tests integration connection THEN the System SHALL attempt API call to provider, update status based on result, record lastTested timestamp, store errorMessage if failed, and return test result with status
5. WHEN a user deletes integration THEN the System SHALL validate access, remove integration record, and return success confirmation
6. WHEN a user requests available models THEN the System SHALL return list of all configured cognitive models with id, provider, name, displayName, brainRegion, status, and 3D position coordinates
7. WHEN System validates integration status THEN the System SHALL check if apiKey exists and lastTested is recent (within 24 hours) before marking as connected

### Requirement 7: Settings and Preferences

**User Story:** As a user, I want to configure my preferences for memory retention and profile settings, so that I can customize my Chimera Protocol experience.

#### Acceptance Criteria

1. WHEN a user requests current settings THEN the System SHALL return profile settings (name, email) and memoryRetention settings (autoStore boolean, retentionPeriod string)
2. WHEN a user updates profile settings with new name or email THEN the System SHALL validate email uniqueness, update user record, and return updated settings object
3. WHEN a user updates memory retention settings THEN the System SHALL validate retentionPeriod value (7-days/30-days/90-days/indefinite-84/indefinite-forever), update user preferences, and return updated settings
4. WHEN a user requests data export THEN the System SHALL generate JSON file containing all user workspaces, conversations, messages, memories, and settings, and return download URL or file stream
5. WHEN a user requests account deletion THEN the System SHALL validate authentication, cascade delete all owned workspaces and associated data, remove user from all team memberships, delete user record, and return success confirmation

### Requirement 8: Real-time Statistics and Monitoring

**User Story:** As a user, I want to view real-time statistics about my workspace activity, so that I can monitor system usage and performance.

#### Acceptance Criteria

1. WHEN a user requests workspace stats THEN the System SHALL calculate totalMemories by counting workspace memories, totalEmbeddings by counting memories with non-null embedding, totalConversations by counting workspace conversations, systemLoad as percentage of active conversations, and lastActivity as most recent timestamp across all workspace entities
2. WHEN a user requests activity feed THEN the System SHALL return chronological list of events with timestamp, type (memory_created/conversation_created/message_sent/team_member_added/model_used), description, and metadata
3. WHEN a user requests neural load graph data THEN the System SHALL generate time series with 5-minute intervals for last 24 hours, calculate load value (0-100) based on active conversations and message frequency, and return array of timestamp-value pairs
4. WHEN System calculates systemLoad THEN the System SHALL use formula: (active_conversations * 10 + messages_last_hour) capped at 100
5. WHEN System generates activity event THEN the System SHALL automatically create activity record on memory creation, conversation creation, message sending, team member changes, and model usage

### Requirement 9: Data Serialization and API Response Format

**User Story:** As a frontend developer, I want consistent API response formats with camelCase field names, so that I can easily integrate with the React application.

#### Acceptance Criteria

1. WHEN the System returns any API response THEN the System SHALL use envelope format with ok boolean, data object, and error string fields
2. WHEN the System serializes User object THEN the System SHALL include id, name, email, avatar (optional), and createdAt in ISO 8601 format
3. WHEN the System serializes Workspace object THEN the System SHALL include id, name, description, ownerId, members array, stats object, createdAt, and updatedAt in camelCase
4. WHEN the System serializes Conversation object THEN the System SHALL include id, workspaceId, title, modelId, messages array, injectedMemories array, status, createdAt, and updatedAt
5. WHEN the System serializes Message object THEN the System SHALL include id, conversationId, role, content, timestamp, isPinned, and metadata object
6. WHEN the System serializes Memory object THEN the System SHALL include id, workspaceId, title, content, snippet, tags array, embedding array (optional), metadata object, createdAt, updatedAt, and version
7. WHEN the System serializes Integration object THEN the System SHALL include id, userId, provider, apiKey (masked), status, lastTested, and errorMessage (optional)
8. WHEN the System serializes TeamMember object THEN the System SHALL include id, userId, workspaceId, role, status, and joinedAt
9. WHEN the System serializes date fields THEN the System SHALL use ISO 8601 format with timezone
10. WHEN the System encounters error THEN the System SHALL return appropriate HTTP status code (400/401/403/404/500) with ok false and descriptive error message

### Requirement 10: Authentication and Authorization

**User Story:** As a system administrator, I want secure authentication and authorization, so that only authorized users can access their data.

#### Acceptance Criteria

1. WHEN a user accesses protected endpoint without JWT THEN the System SHALL return 401 Unauthorized with error message
2. WHEN a user accesses workspace resource THEN the System SHALL validate user is workspace owner or team member before granting access
3. WHEN a user attempts admin action THEN the System SHALL validate user has admin or owner role before allowing operation
4. WHEN a user accesses conversation or memory THEN the System SHALL validate user has access to parent workspace
5. WHEN JWT token expires THEN the System SHALL return 401 Unauthorized and require token refresh
6. WHEN a user provides invalid refresh token THEN the System SHALL return 401 Unauthorized and require re-authentication
7. WHEN the System stores API keys THEN the System SHALL encrypt keys before database storage and decrypt only when needed for API calls

### Requirement 11: CORS and Frontend Integration

**User Story:** As a frontend developer, I want proper CORS configuration, so that the React application can communicate with the backend API.

#### Acceptance Criteria

1. WHEN frontend makes request from localhost:5173 THEN the System SHALL accept request with proper CORS headers
2. WHEN frontend makes request from production domain THEN the System SHALL accept request if domain is in allowed origins list
3. WHEN frontend sends preflight OPTIONS request THEN the System SHALL respond with allowed methods, headers, and credentials
4. WHEN the System returns response THEN the System SHALL include Access-Control-Allow-Origin, Access-Control-Allow-Credentials, and Access-Control-Allow-Methods headers
5. WHEN frontend sends credentials THEN the System SHALL accept and process cookies and authorization headers

### Requirement 12: Error Handling and Validation

**User Story:** As a user, I want clear error messages when something goes wrong, so that I can understand and fix issues.

#### Acceptance Criteria

1. WHEN a user submits invalid data THEN the System SHALL return 400 Bad Request with specific field validation errors
2. WHEN a user accesses non-existent resource THEN the System SHALL return 404 Not Found with descriptive error message
3. WHEN a user lacks permission for action THEN the System SHALL return 403 Forbidden with explanation
4. WHEN System encounters internal error THEN the System SHALL return 500 Internal Server Error with generic message and log detailed error
5. WHEN a user submits duplicate email THEN the System SHALL return 400 Bad Request with "Email already exists" message
6. WHEN a user submits empty required field THEN the System SHALL return 400 Bad Request with "Field is required" message
7. WHEN database operation fails THEN the System SHALL rollback transaction and return appropriate error response

### Requirement 13: Performance and Optimization

**User Story:** As a user, I want fast API responses, so that the application feels responsive and smooth.

#### Acceptance Criteria

1. WHEN a user requests workspace list THEN the System SHALL return response within 200ms using database indexes on owner and member relationships
2. WHEN a user requests conversation with messages THEN the System SHALL use select_related and prefetch_related to minimize database queries
3. WHEN a user searches memories THEN the System SHALL use vector similarity search with indexed embeddings to return results within 500ms
4. WHEN the System serializes large datasets THEN the System SHALL implement pagination with limit and offset parameters
5. WHEN multiple users access same workspace THEN the System SHALL use database connection pooling to handle concurrent requests efficiently

### Requirement 14: Semantic Memory Search

**User Story:** As a user, I want to search memories by meaning rather than exact keywords, so that I can find relevant information even with different wording.

#### Acceptance Criteria

1. WHEN a user creates or updates memory THEN the System SHALL generate embedding vector using sentence transformer or similar model
2. WHEN a user searches memories with query THEN the System SHALL generate query embedding and compute cosine similarity with all workspace memory embeddings
3. WHEN the System ranks search results THEN the System SHALL sort by similarity score in descending order and return top K results (default 10)
4. WHEN a user searches with empty query THEN the System SHALL return all workspace memories sorted by updatedAt descending
5. WHEN the System generates embeddings THEN the System SHALL use consistent model (e.g., all-MiniLM-L6-v2) for all memories to ensure comparable vectors

### Requirement 15: AI Model Chat Integration

**User Story:** As a user, I want to send messages and receive AI responses, so that I can have conversations with cognitive models.

#### Acceptance Criteria

1. WHEN a user sends message in conversation THEN the System SHALL retrieve conversation modelId, lookup corresponding integration, and validate API key exists
2. WHEN the System calls AI model API THEN the System SHALL include conversation history (last 10 messages) and injected memory content as context
3. WHEN AI model returns response THEN the System SHALL create assistant message with response content, store in conversation, and return to user
4. WHEN AI API call fails THEN the System SHALL return error message to user and log failure details
5. WHEN conversation has injected memories THEN the System SHALL prepend memory content to system prompt before sending to AI model
6. WHEN the System formats context for AI THEN the System SHALL structure as: system prompt + injected memories + conversation history + user message
7. WHEN AI response includes metadata THEN the System SHALL store token count, model version, and response time in message metadata

This completes the requirements specification for backend-frontend integration.
