# Chimera Protocol API Documentation

## Base URL

```
Development: http://localhost:8000/api
Production: https://api.chimera-protocol.com/api
```

## Authentication

All protected endpoints require JWT authentication.

### Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Response Format

All API responses follow this envelope format:

```json
{
  "ok": true,
  "data": { ... },
  "error": null
}
```

Error responses:

```json
{
  "ok": false,
  "data": null,
  "error": "Error message"
}
```

## Authentication Endpoints

### Register User

```http
POST /auth/register
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "ok": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "avatar": null,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  },
  "error": null
}
```

### Login

```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": { ... }
  },
  "error": null
}
```

### Refresh Token

```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "token": "new_access_token"
  },
  "error": null
}
```

## Workspace Endpoints

### List Workspaces

```http
GET /workspaces
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "workspaces": [
      {
        "id": "workspace-abc123",
        "name": "My Workspace",
        "description": "Description",
        "ownerId": "uuid",
        "members": [...],
        "stats": {
          "totalMemories": 10,
          "totalEmbeddings": 10,
          "totalConversations": 5,
          "systemLoad": 45,
          "lastActivity": "2024-01-01T00:00:00Z"
        },
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

### Create Workspace

```http
POST /workspaces
```

**Request Body:**
```json
{
  "name": "New Workspace",
  "description": "Optional description"
}
```

**Response:** `201 Created`

### Get Workspace

```http
GET /workspaces/{workspace_id}
```

**Response:** `200 OK`

### Update Workspace

```http
PUT /workspaces/{workspace_id}
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**Response:** `200 OK`

### Delete Workspace

```http
DELETE /workspaces/{workspace_id}
```

**Response:** `200 OK`

### Get Workspace Dashboard

```http
GET /workspaces/{workspace_id}/dashboard
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "stats": { ... },
    "neuralLoad": [
      {
        "timestamp": "2024-01-01T00:00:00Z",
        "value": 45
      }
    ],
    "recentActivity": [
      {
        "id": "activity-123",
        "type": "memory_created",
        "message": "Created memory: Important Note",
        "timestamp": "2024-01-01T00:00:00Z",
        "metadata": {}
      }
    ]
  },
  "error": null
}
```

## Conversation Endpoints

### List Conversations

```http
GET /workspaces/{workspace_id}/conversations
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "conversations": [
      {
        "id": "conv-abc123",
        "workspaceId": "workspace-abc123",
        "title": "Chat with AI",
        "modelId": "model-gpt4o",
        "status": "active",
        "messageCount": 10,
        "lastUpdated": "2024-01-01T00:00:00Z",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

### Create Conversation

```http
POST /workspaces/{workspace_id}/conversations
```

**Request Body:**
```json
{
  "title": "New Chat",
  "modelId": "model-gpt4o"
}
```

**Response:** `201 Created`

### Get Conversation

```http
GET /conversations/{conversation_id}
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "id": "conv-abc123",
    "workspaceId": "workspace-abc123",
    "title": "Chat with AI",
    "modelId": "model-gpt4o",
    "messages": [
      {
        "id": "msg-123",
        "conversationId": "conv-abc123",
        "role": "user",
        "content": "Hello",
        "timestamp": "2024-01-01T00:00:00Z",
        "isPinned": false,
        "metadata": {}
      }
    ],
    "injectedMemories": ["memory-123"],
    "status": "active",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "error": null
}
```

### Send Message

```http
POST /conversations/{conversation_id}/messages
```

**Request Body:**
```json
{
  "content": "Hello, AI!",
  "getAiResponse": true
}
```

**Response:** `201 Created`
```json
{
  "ok": true,
  "data": {
    "userMessage": { ... },
    "assistantMessage": { ... }
  },
  "error": null
}
```

### Update Message (Pin/Unpin)

```http
PUT /conversations/{conversation_id}/messages/{message_id}
```

**Request Body:**
```json
{
  "isPinned": true
}
```

**Response:** `200 OK`

### Delete Message

```http
DELETE /conversations/{conversation_id}/messages/{message_id}
```

**Response:** `200 OK`

### Inject Memory

```http
POST /conversations/{conversation_id}/inject-memory
```

**Request Body:**
```json
{
  "memoryId": "memory-123"
}
```

**Response:** `200 OK`

### Remove Injected Memory

```http
DELETE /conversations/{conversation_id}/inject-memory/{memory_id}
```

**Response:** `200 OK`

## Memory Endpoints

### List Memories

```http
GET /workspaces/{workspace_id}/memories?search=query&sortBy=recent
```

**Query Parameters:**
- `search` (optional): Search query
- `sortBy` (optional): `recent` or `title`

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "memories": [
      {
        "id": "memory-123",
        "workspaceId": "workspace-abc123",
        "title": "Important Note",
        "content": "Full content...",
        "snippet": "First 150 characters...",
        "tags": ["important", "project"],
        "embedding": null,
        "metadata": {},
        "version": 1,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "total": 1
  },
  "error": null
}
```

### Create Memory

```http
POST /workspaces/{workspace_id}/memories
```

**Request Body:**
```json
{
  "title": "New Memory",
  "content": "Memory content...",
  "tags": ["tag1", "tag2"],
  "metadata": {}
}
```

**Response:** `201 Created`

### Get Memory

```http
GET /memories/{memory_id}
```

**Response:** `200 OK`

### Update Memory

```http
PUT /memories/{memory_id}
```

**Request Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content",
  "tags": ["new-tag"]
}
```

**Response:** `200 OK`

### Delete Memory

```http
DELETE /memories/{memory_id}
```

**Response:** `200 OK`

### Re-embed Memory

```http
POST /memories/{memory_id}/re-embed
```

**Response:** `200 OK`

### Search Memories

```http
POST /memories/search
```

**Request Body:**
```json
{
  "query": "search query",
  "workspaceId": "workspace-abc123",
  "top_k": 5
}
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "results": [
      {
        "id": "memory-123",
        "title": "Relevant Memory",
        "snippet": "Preview...",
        "score": 0.95
      }
    ]
  },
  "error": null
}
```

## Integration Endpoints

### List Integrations

```http
GET /integrations
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "integrations": [
      {
        "id": "int-123",
        "provider": "openai",
        "apiKey": "sk-...xyz",
        "status": "connected",
        "lastTested": "2024-01-01T00:00:00Z",
        "errorMessage": null
      }
    ],
    "total": 1
  },
  "error": null
}
```

### Create Integration

```http
POST /integrations
```

**Request Body:**
```json
{
  "provider": "openai",
  "apiKey": "sk-..."
}
```

**Response:** `201 Created`

### Update Integration

```http
PUT /integrations/{integration_id}
```

**Request Body:**
```json
{
  "apiKey": "new-api-key"
}
```

**Response:** `200 OK`

### Delete Integration

```http
DELETE /integrations/{integration_id}
```

**Response:** `200 OK`

### Test Integration

```http
POST /integrations/{integration_id}/test
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "integration": { ... },
    "message": "Connection test successful"
  },
  "error": null
}
```

### Get Available Models

```http
GET /models/available
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "models": [
      {
        "id": "model-gpt4o",
        "provider": "openai",
        "name": "gpt-4o",
        "displayName": "GPT 4O",
        "brainRegion": "Left Cortex",
        "status": "connected",
        "position": { "x": -2, "y": 1, "z": 1 }
      }
    ],
    "total": 1
  },
  "error": null
}
```

## Team Management Endpoints

### List Team Members

```http
GET /workspaces/{workspace_id}/team
```

**Response:** `200 OK`

### Invite Team Member

```http
POST /workspaces/{workspace_id}/team/invite
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "role": "researcher"
}
```

**Response:** `201 Created`

### Update Member Role

```http
PUT /workspaces/{workspace_id}/team/{user_id}/role
```

**Request Body:**
```json
{
  "role": "admin"
}
```

**Response:** `200 OK`

### Update Member Status

```http
PUT /workspaces/{workspace_id}/team/{user_id}/status
```

**Request Body:**
```json
{
  "status": "online"
}
```

**Response:** `200 OK`

### Remove Team Member

```http
DELETE /workspaces/{workspace_id}/team/{user_id}
```

**Response:** `200 OK`

## Settings Endpoints

### Get Settings

```http
GET /settings
```

**Response:** `200 OK`
```json
{
  "ok": true,
  "data": {
    "profile": {
      "name": "John Doe",
      "email": "john@example.com"
    },
    "memoryRetention": {
      "autoStore": true,
      "retentionPeriod": "indefinite-84"
    }
  },
  "error": null
}
```

### Update Profile

```http
PUT /settings/profile
```

**Request Body:**
```json
{
  "name": "New Name",
  "email": "newemail@example.com"
}
```

**Response:** `200 OK`

### Update Memory Retention

```http
PUT /settings/memory-retention
```

**Request Body:**
```json
{
  "autoStore": false,
  "retentionPeriod": "30-days"
}
```

**Response:** `200 OK`

### Export Data

```http
GET /export
```

**Response:** `200 OK` (File Download)

Returns a JSON file containing all user data.

### Delete Account

```http
DELETE /settings/account
```

**Response:** `200 OK`

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Missing or invalid authentication |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

## Rate Limiting

- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour

## Pagination

List endpoints support pagination:

```http
GET /workspaces/{workspace_id}/memories?limit=20&offset=0
```

**Query Parameters:**
- `limit`: Number of items per page (default: 20, max: 100)
- `offset`: Number of items to skip

## WebSocket Support

Coming soon: Real-time updates for conversations and team collaboration.

## Support

For API support, contact: support@chimera-protocol.com
