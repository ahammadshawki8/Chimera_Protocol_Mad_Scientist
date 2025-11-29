# Design Document: Backend-Frontend Integration Finalization

## Overview

This design document specifies the complete Django REST Framework backend architecture to support the Chimera Protocol React frontend. The system provides a workspace-centric API for managing AI conversations, semantic memory storage, team collaboration, and multi-model integrations. The design ensures zero dummy data dependencies by implementing all CRUD operations, real-time statistics, semantic search, and AI model integration.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│  (Zustand Stores + TypeScript + React Router)               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS/REST API
                     │ (JSON with camelCase)
┌────────────────────┴────────────────────────────────────────┐
│                  Django REST Framework                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Layer (Views)                        │  │
│  │  - Authentication  - Workspaces  - Conversations     │  │
│  │  - Memories        - Integrations - Team Management  │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────┴───────────────────────────────────────┐  │
│  │           Business Logic Layer                        │  │
│  │  - Serializers (camelCase conversion)                │  │
│  │  - Permissions (workspace access control)            │  │
│  │  - Services (stats calculation, AI routing)          │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────┴───────────────────────────────────────┐  │
│  │              Data Layer (Models)                      │  │
│  │  - User  - Workspace  - Conversation  - Message      │  │
│  │  - Memory  - Integration  - TeamMember               │  │
│  └──────────────┬───────────────────────────────────────┘  │
└─────────────────┼────────────────────────────────────────────┘
                  │
┌─────────────────┴────────────────────────────────────────────┐
│                  PostgreSQL Database                          │
│  - Indexed tables  - Foreign keys  - Transactions            │
└───────────────────────────────────────────────────────────────┘
                  │
┌─────────────────┴────────────────────────────────────────────┐
│              External Services                                │
│  - OpenAI API  - Anthropic API  - Google AI API              │
│  - Embedding Model (sentence-transformers)                   │
└───────────────────────────────────────────────────────────────┘
```

### Request Flow

1. **Frontend Request** → React component calls Zustand store action
2. **HTTP Request** → Store makes fetch() call to Django API endpoint
3. **Authentication** → JWT middleware validates token
4. **Authorization** → Permission classes check workspace/resource access
5. **Validation** → Serializer validates request data
6. **Business Logic** → View executes operation (CRUD, stats, search)
7. **Database** → ORM queries PostgreSQL with optimized joins
8. **Serialization** → Response data converted to camelCase JSON
9. **HTTP Response** → Envelope format {ok, data, error} returned
10. **Frontend Update** → Store updates state, React re-renders

## Components and Interfaces

### 1. Authentication System

**Components:**
- `register_view` - User registration
- `login_view` - User authentication
- `logout_view` - Token blacklisting
- `refresh_token_view` - Token refresh
- `user_profile_view` - Get profile
- `update_profile_view` - Update profile

**Interfaces:**
```python
# Request: POST /api/auth/register
{
  "name": str,
  "email": str,
  "password": str
}

# Response: 201 Created
{
  "ok": true,
  "data": {
    "token": str,  # JWT access token
    "refresh": str,  # JWT refresh token
    "user": {
      "id": str,
      "name": str,
      "email": str,
      "createdAt": str  # ISO 8601
    }
  },
  "error": null
}
```

### 2. Workspace Management

**Components:**
- `workspaces_view` - List/create workspaces
- `workspace_detail_view` - Get/update/delete workspace
- `workspace_stats_view` - Calculate statistics
- `workspace_dashboard_view` - Dashboard data
- `workspace_activity_view` - Activity feed
- `workspace_neural_load_view` - Time series data

**Interfaces:**
```python
# Request: GET /api/workspaces
# Response: 200 OK
{
  "ok": true,
  "data": {
    "workspaces": [
      {
        "id": str,
        "name": str,
        "description": str | null,
        "ownerId": str,
        "members": [TeamMember],
        "stats": {
          "totalMemories": int,
          "totalEmbeddings": int,
          "totalConversations": int,
          "systemLoad": int,  # 0-100
          "lastActivity": str  # ISO 8601
        },
        "createdAt": str,
        "updatedAt": str
      }
    ],
    "total": int
  },
  "error": null
}
```

### 3. Conversation Management

**Components:**
- `workspace_conversations_view` - List/create conversations
- `conversation_detail_view` - Get/update/delete conversation
- `send_message_view` - Send message
- `message_detail_view` - Update/delete message
- `inject_memory_view` - Inject memory
- `remove_injected_memory_view` - Remove injection

**Interfaces:**
```python
# Request: POST /api/workspaces/{workspace_id}/conversations
{
  "title": str,  # optional, default "New Conversation"
  "modelId": str  # e.g., "model-gpt4o"
}

# Response: 201 Created
{
  "ok": true,
  "data": {
    "id": str,
    "workspaceId": str,
    "title": str,
    "modelId": str,
    "messages": [],
    "injectedMemories": [],
    "status": "active",
    "createdAt": str,
    "updatedAt": str
  },
  "error": null
}
```

### 4. Memory Management

**Components:**
- `workspace_memories_view` - List/create memories
- `memory_detail_view` - Get/update/delete memory
- `re_embed_memory_view` - Regenerate embedding
- `search_memories_view` - Semantic search

**Interfaces:**
```python
# Request: POST /api/workspaces/{workspace_id}/memories
{
  "title": str,
  "content": str,
  "tags": [str]
}

# Response: 201 Created
{
  "ok": true,
  "data": {
    "id": str,
    "workspaceId": str,
    "title": str,
    "content": str,
    "snippet": str,  # First 150 chars
    "tags": [str],
    "embedding": [float] | null,
    "metadata": {},
    "createdAt": str,
    "updatedAt": str,
    "version": 1
  },
  "error": null
}
```

### 5. Integration Management

**Components:**
- `integrations_view` - List/create integrations
- `integration_detail_view` - Get/update/delete integration
- `test_integration_view` - Test API connection
- `available_models_view` - List available models

**Interfaces:**
```python
# Request: POST /api/integrations
{
  "provider": "openai" | "anthropic" | "google",
  "apiKey": str
}

# Response: 201 Created
{
  "ok": true,
  "data": {
    "id": str,
    "userId": str,
    "provider": str,
    "apiKey": str,  # Masked: "sk-...xyz"
    "status": "disconnected",
    "lastTested": null,
    "errorMessage": null
  },
  "error": null
}
```

### 6. Team Management

**Components:**
- `list_team_members_view` - List members
- `invite_team_member_view` - Invite member
- `update_member_role_view` - Change role
- `update_member_status_view` - Update status
- `remove_team_member_view` - Remove member

**Interfaces:**
```python
# Request: POST /api/workspaces/{workspace_id}/team/invite
{
  "username": str,  # or email
  "role": "admin" | "researcher" | "observer"
}

# Response: 201 Created
{
  "ok": true,
  "data": {
    "id": str,
    "userId": str,
    "workspaceId": str,
    "role": str,
    "status": "offline",
    "joinedAt": str
  },
  "error": null
}
```

## Data Models

### User Model
```python
class User(AbstractUser):
    id = UUIDField(primary_key=True, default=uuid4)
    name = CharField(max_length=255)
    email = EmailField(unique=True)
    avatar = URLField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    
    # Django auth fields: username, password, etc.
```

### Workspace Model
```python
class Workspace(Model):
    id = CharField(max_length=50, primary_key=True)  # "workspace-{uuid}"
    name = CharField(max_length=255)
    description = TextField(null=True, blank=True)
    owner = ForeignKey(User, on_delete=CASCADE, related_name='owned_workspaces')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Indexes: owner, updated_at
```

### TeamMember Model
```python
class TeamMember(Model):
    id = CharField(max_length=50, primary_key=True)  # "tm-{uuid}"
    user = ForeignKey(User, on_delete=CASCADE)
    workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name='members')
    role = CharField(choices=['admin', 'researcher', 'observer'])
    status = CharField(choices=['online', 'away', 'offline'], default='offline')
    joined_at = DateTimeField(auto_now_add=True)
    
    # Unique constraint: (user, workspace)
    # Indexes: workspace, user
```

### Conversation Model
```python
class Conversation(Model):
    id = CharField(max_length=50, primary_key=True)  # "conv-{uuid}"
    workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name='conversations')
    title = CharField(max_length=255, default='New Conversation')
    model_id = CharField(max_length=50)  # e.g., "model-gpt4o"
    status = CharField(choices=['active', 'completed', 'archived'], default='active')
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Indexes: workspace, updated_at
```

### Message Model
```python
class ChatMessage(Model):
    id = CharField(max_length=50, primary_key=True)  # "msg-{uuid}"
    conversation = ForeignKey(Conversation, on_delete=CASCADE, related_name='messages')
    role = CharField(choices=['user', 'assistant', 'system'])
    content = TextField()
    is_pinned = BooleanField(default=False)
    metadata = JSONField(default=dict, blank=True)
    timestamp = DateTimeField(auto_now_add=True)
    
    # Indexes: conversation, timestamp
```

### Memory Model
```python
class Memory(Model):
    id = CharField(max_length=50, primary_key=True)  # "memory-{uuid}"
    workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name='memories')
    title = CharField(max_length=255)
    content = TextField()
    snippet = CharField(max_length=200, blank=True)
    tags = JSONField(default=list, blank=True)
    embedding = BinaryField(null=True, blank=True)  # Pickled numpy array
    metadata = JSONField(default=dict, blank=True)
    version = IntegerField(default=1)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Indexes: workspace, created_at
```

### ConversationMemory Model (Junction Table)
```python
class ConversationMemory(Model):
    conversation = ForeignKey(Conversation, on_delete=CASCADE)
    memory = ForeignKey(Memory, on_delete=CASCADE)
    injected_at = DateTimeField(auto_now_add=True)
    
    # Unique constraint: (conversation, memory)
    # Indexes: conversation, injected_at
```

### Integration Model
```python
class Integration(Model):
    id = CharField(max_length=50, primary_key=True)  # "int-{uuid}"
    user = ForeignKey(User, on_delete=CASCADE, related_name='integrations')
    provider = CharField(choices=['openai', 'anthropic', 'google'])
    api_key = CharField(max_length=255)  # Encrypted
    status = CharField(choices=['connected', 'error', 'disconnected'], default='disconnected')
    last_tested = DateTimeField(null=True, blank=True)
    error_message = TextField(null=True, blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    # Unique constraint: (user, provider)
    # Indexes: user, provider
```

### Activity Model (New)
```python
class Activity(Model):
    id = CharField(max_length=50, primary_key=True)  # "activity-{uuid}"
    workspace = ForeignKey(Workspace, on_delete=CASCADE, related_name='activities')
    type = CharField(choices=[
        'memory_created', 'conversation_created', 'message_sent',
        'team_member_added', 'model_used'
    ])
    description = TextField()
    metadata = JSONField(default=dict, blank=True)
    timestamp = DateTimeField(auto_now_add=True)
    
    # Indexes: workspace, timestamp
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*



### Property 1: User Registration Creates Valid Account
*For any* valid registration data (name, email, password), the system should create a user account and return JWT tokens with complete user profile including id, name, email, and createdAt.
**Validates: Requirements 1.1**

### Property 2: Authentication Returns Valid Tokens
*For any* registered user with correct credentials, login should return both access and refresh JWT tokens that can be used for subsequent authenticated requests.
**Validates: Requirements 1.2**

### Property 3: Profile Retrieval Matches User
*For any* valid JWT token, the profile endpoint should return user data that matches the user ID encoded in the token.
**Validates: Requirements 1.3**

### Property 4: Email Uniqueness Enforced
*For any* profile update with a new email, if the email already exists for a different user, the system should reject the update with a 400 error.
**Validates: Requirements 1.4**

### Property 5: Workspace List Filtered By Access
*For any* user, the workspace list should only contain workspaces where the user is either the owner or a team member, and should not include workspaces where the user has no access.
**Validates: Requirements 2.1**

### Property 6: Workspace Creation Assigns Ownership
*For any* valid workspace creation request, the creating user should be set as the owner and automatically added as a team member with admin role.
**Validates: Requirements 2.2**

### Property 7: Workspace Stats Accuracy
*For any* workspace, the stats should accurately reflect the count of memories, embeddings (memories with non-null embedding), conversations, and the calculated system load should be between 0 and 100.
**Validates: Requirements 2.6, 8.1, 8.4**

### Property 8: Team Member List Completeness
*For any* workspace, the team member list should include all users who have been added to the workspace, with no duplicates and no missing members.
**Validates: Requirements 3.1**

### Property 9: Team Invitation Creates Member
*For any* valid user invitation to a workspace, a team member record should be created with the specified role, and the member count should increase by one.
**Validates: Requirements 3.2**

### Property 10: Owner Cannot Be Removed
*For any* workspace, attempting to remove the workspace owner from the team should fail with a 400 error, regardless of who attempts the removal.
**Validates: Requirements 3.4**

### Property 11: Conversation List Completeness
*For any* workspace, the conversation list should include all conversations created in that workspace, with accurate message counts and status.
**Validates: Requirements 4.1**

### Property 12: Conversation Creation Initializes Correctly
*For any* valid conversation creation request, the new conversation should have an empty messages array, empty injectedMemories array, status set to "active", and the specified modelId.
**Validates: Requirements 4.2**

### Property 13: Message Sending Appends to Conversation
*For any* valid message sent to a conversation, the message should be appended to the conversation's messages array, and the conversation's updatedAt timestamp should be updated.
**Validates: Requirements 4.6**

### Property 14: Message Pin Toggle
*For any* message, pinning it should set isPinned to true, and unpinning should set it to false. Pinning twice should have no additional effect.
**Validates: Requirements 4.7**

### Property 15: Memory Injection Adds to Array
*For any* valid memory injection into a conversation, the memory ID should be added to the conversation's injectedMemories array if not already present, and should not create duplicates.
**Validates: Requirements 4.9**

### Property 16: Memory List Completeness
*For any* workspace, the memory list should include all memories created in that workspace, with accurate snippets (first 150 characters of content).
**Validates: Requirements 5.1**

### Property 17: Memory Creation Generates Embedding
*For any* memory created with content, the system should generate an embedding vector, create a snippet, and set version to 1.
**Validates: Requirements 5.2, 14.1**

### Property 18: Memory Update Increments Version
*For any* memory update, the version number should increment by exactly 1, and if content changed, the snippet should be regenerated.
**Validates: Requirements 5.4**

### Property 19: Re-embedding Increments Version
*For any* memory re-embedding request, the version number should increment by 1, and a new embedding vector should be generated.
**Validates: Requirements 5.6**

### Property 20: Semantic Search Ranks By Similarity
*For any* search query, the results should be ranked by cosine similarity score in descending order, with the most similar memories first.
**Validates: Requirements 5.7, 14.2**

### Property 21: Integration API Key Masking
*For any* integration returned by the API, the apiKey field should be masked (showing only first and last few characters) and never return the full key in responses.
**Validates: Requirements 6.1**

### Property 22: Integration Creation Encrypts Key
*For any* integration created, the API key should be encrypted before storage in the database, and status should be set to "disconnected" initially.
**Validates: Requirements 6.2**

### Property 23: Integration Test Updates Status
*For any* integration test, the status should be updated to "connected" on success or "error" on failure, and lastTested timestamp should be set to current time.
**Validates: Requirements 6.4**

### Property 24: Data Export Completeness
*For any* user data export request, the generated JSON should include all workspaces, conversations, messages, memories, and settings owned by or accessible to the user.
**Validates: Requirements 7.4**

### Property 25: API Response Envelope Format
*For any* API endpoint response, the response should have the structure {ok: boolean, data: object | null, error: string | null} with ok=true for success and ok=false for errors.
**Validates: Requirements 9.1**

### Property 26: Serialization CamelCase Conversion
*For any* model serialization, all field names should be converted from snake_case to camelCase (e.g., created_at → createdAt, workspace_id → workspaceId).
**Validates: Requirements 9.2-9.8**

### Property 27: Authentication Required for Protected Endpoints
*For any* protected endpoint request without a valid JWT token, the system should return 401 Unauthorized with an error message.
**Validates: Requirements 10.1**

### Property 28: Workspace Access Control
*For any* workspace resource access, if the user is not the owner or a team member, the system should return 403 Forbidden.
**Validates: Requirements 10.2**

### Property 29: Validation Error Specificity
*For any* request with invalid data, the system should return 400 Bad Request with specific field-level error messages indicating which fields are invalid and why.
**Validates: Requirements 12.1**

### Property 30: Not Found Error Handling
*For any* request for a non-existent resource ID, the system should return 404 Not Found with a descriptive error message.
**Validates: Requirements 12.2**

### Property 31: AI Context Includes Injected Memories
*For any* conversation with injected memories, when sending a message to the AI model, the system prompt should include the content of all injected memories before the conversation history.
**Validates: Requirements 15.5**

## Error Handling

### Error Response Format

All errors follow the envelope format:
```json
{
  "ok": false,
  "data": null,
  "error": "Descriptive error message"
}
```

### HTTP Status Codes

- **200 OK** - Successful GET, PUT, DELETE
- **201 Created** - Successful POST creating resource
- **400 Bad Request** - Validation errors, invalid data
- **401 Unauthorized** - Missing or invalid JWT token
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource does not exist
- **500 Internal Server Error** - Unexpected server error

### Validation Errors

For validation errors, return detailed field-level errors:
```json
{
  "ok": false,
  "data": null,
  "error": {
    "email": ["Email already exists"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### Error Logging

- Log all 500 errors with full stack trace
- Log authentication failures for security monitoring
- Log API integration failures with provider details
- Do not log sensitive data (passwords, API keys)

### Transaction Rollback

- Wrap multi-step operations in database transactions
- Rollback on any error to maintain consistency
- Example: Workspace creation (create workspace + add owner as member)

## Testing Strategy

### Unit Testing

**Framework**: Django TestCase, pytest

**Coverage Areas**:
1. **Model Tests**
   - Test model creation with valid data
   - Test unique constraints (email, user+workspace)
   - Test cascade deletions
   - Test custom ID generation
   - Test default values

2. **Serializer Tests**
   - Test camelCase conversion
   - Test field validation
   - Test nested serialization (workspace with members)
   - Test API key masking
   - Test date formatting (ISO 8601)

3. **View Tests**
   - Test authentication requirements
   - Test permission checks
   - Test CRUD operations
   - Test error responses
   - Test pagination

4. **Service Tests**
   - Test stats calculation
   - Test embedding generation
   - Test semantic search
   - Test AI model routing

**Example Unit Test**:
```python
def test_workspace_creation_assigns_owner():
    user = User.objects.create_user(username='test', email='test@example.com')
    workspace = Workspace.objects.create(name='Test', owner=user)
    
    # Verify owner is added as admin team member
    member = TeamMember.objects.get(workspace=workspace, user=user)
    assert member.role == 'admin'
    assert member.status == 'offline'
```

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**: Each property test should run minimum 100 iterations

**Property Test Examples**:

```python
from hypothesis import given, strategies as st
from hypothesis.extra.django import TestCase

class WorkspacePropertyTests(TestCase):
    @given(
        name=st.text(min_size=1, max_size=255),
        description=st.text(max_size=1000) | st.none()
    )
    def test_workspace_creation_property(self, name, description):
        """
        Feature: backend-frontend-integration, Property 6: Workspace Creation Assigns Ownership
        
        For any valid workspace data, the creating user should be owner
        and automatically added as admin team member.
        """
        user = self.create_test_user()
        workspace = Workspace.objects.create(
            name=name,
            description=description,
            owner=user
        )
        
        # Property: Owner is always added as admin member
        member = TeamMember.objects.get(workspace=workspace, user=user)
        assert member.role == 'admin'
        assert workspace.owner == user

    @given(
        content=st.text(min_size=1, max_size=10000),
        tags=st.lists(st.text(min_size=1, max_size=50), max_size=10)
    )
    def test_memory_version_increment_property(self, content, tags):
        """
        Feature: backend-frontend-integration, Property 18: Memory Update Increments Version
        
        For any memory update, version should increment by exactly 1.
        """
        workspace = self.create_test_workspace()
        memory = Memory.objects.create(
            workspace=workspace,
            title='Test',
            content=content,
            tags=tags
        )
        initial_version = memory.version
        
        # Update memory
        memory.content = content + " updated"
        memory.save()
        
        # Property: Version increments by 1
        assert memory.version == initial_version + 1

    @given(
        email=st.emails(),
        name=st.text(min_size=1, max_size=255)
    )
    def test_email_uniqueness_property(self, email, name):
        """
        Feature: backend-frontend-integration, Property 4: Email Uniqueness Enforced
        
        For any email that already exists, profile update should be rejected.
        """
        # Create first user with email
        user1 = User.objects.create_user(
            username='user1',
            email=email,
            password='pass123'
        )
        
        # Create second user with different email
        user2 = User.objects.create_user(
            username='user2',
            email='different@example.com',
            password='pass123'
        )
        
        # Property: Cannot update user2's email to user1's email
        user2.email = email
        with pytest.raises(IntegrityError):
            user2.save()
```

### Integration Testing

**Scope**: Test complete request-response cycles

**Areas**:
1. Authentication flow (register → login → access protected endpoint)
2. Workspace creation → team invitation → conversation creation
3. Memory creation → embedding generation → semantic search
4. Integration creation → test connection → use in conversation
5. Message sending → AI response → memory injection

**Example Integration Test**:
```python
def test_complete_conversation_flow():
    # Register user
    response = client.post('/api/auth/register', {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'secure123'
    })
    assert response.status_code == 201
    token = response.json()['data']['token']
    
    # Create workspace
    response = client.post('/api/workspaces', {
        'name': 'Test Workspace'
    }, headers={'Authorization': f'Bearer {token}'})
    workspace_id = response.json()['data']['id']
    
    # Create conversation
    response = client.post(f'/api/workspaces/{workspace_id}/conversations', {
        'modelId': 'model-gpt4o',
        'title': 'Test Chat'
    }, headers={'Authorization': f'Bearer {token}'})
    conversation_id = response.json()['data']['id']
    
    # Send message
    response = client.post(f'/api/conversations/{conversation_id}/messages', {
        'content': 'Hello AI'
    }, headers={'Authorization': f'Bearer {token}'})
    
    assert response.status_code == 201
    assert response.json()['data']['role'] == 'user'
```

### Performance Testing

**Tools**: Django Debug Toolbar, django-silk

**Metrics**:
- API response time < 200ms for simple queries
- API response time < 500ms for complex queries (search, stats)
- Database queries per request < 10 (use select_related, prefetch_related)
- Memory usage < 100MB per request

**Optimization Strategies**:
1. Database indexing on foreign keys and frequently queried fields
2. Query optimization with select_related for foreign keys
3. Query optimization with prefetch_related for reverse foreign keys
4. Pagination for list endpoints (default 20 items)
5. Caching for frequently accessed data (workspace stats)

### Test Coverage Goals

- **Line Coverage**: > 90%
- **Branch Coverage**: > 85%
- **Property Tests**: All 31 correctness properties
- **Integration Tests**: All major user flows
- **Performance Tests**: All list and search endpoints

## Security Considerations

### API Key Encryption

```python
from cryptography.fernet import Fernet
import os

# Generate key from environment variable
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_api_key(api_key: str) -> str:
    return cipher.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    return cipher.decrypt(encrypted_key.encode()).decode()
```

### JWT Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}
```

### CORS Configuration

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',  # Alternative dev port
    'https://chimera-protocol.netlify.app',  # Production
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'origin',
]
```

### Rate Limiting

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## Deployment Considerations

### Environment Variables

```bash
# Django
SECRET_KEY=<random-secret-key>
DEBUG=False
ALLOWED_HOSTS=api.chimera-protocol.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Security
ENCRYPTION_KEY=<fernet-key>
JWT_SECRET_KEY=<jwt-secret>

# CORS
FRONTEND_URL=https://chimera-protocol.netlify.app

# AI Providers (optional, users provide their own)
OPENAI_API_KEY=<optional-default-key>
ANTHROPIC_API_KEY=<optional-default-key>
GOOGLE_AI_API_KEY=<optional-default-key>
```

### Database Migrations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Production Checklist

- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up PostgreSQL database
- [ ] Configure CORS for production domain
- [ ] Set up HTTPS/SSL
- [ ] Configure static file serving
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy
- [ ] Set up rate limiting
- [ ] Enable security headers
- [ ] Test all API endpoints
- [ ] Run performance tests
- [ ] Document API with Swagger/OpenAPI

This completes the design document for backend-frontend integration.
