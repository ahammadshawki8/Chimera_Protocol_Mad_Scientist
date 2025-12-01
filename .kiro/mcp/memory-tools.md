# Chimera MCP Memory Tools

## Overview
Chimera Protocol implements Model Context Protocol (MCP) for memory management. These tools allow AI models to store, search, and inject contextual memories into conversations.

## Available Tools

### 1. Remember Tool
Store a memory fragment for later retrieval.

**Endpoint**: `POST /api/mcp/remember`

**Request**:
```json
{
  "text": "Information to remember",
  "conversation_id": "conv-xxx",
  "tags": ["tag1", "tag2"],
  "metadata": {"source": "user", "importance": "high"}
}
```

**Response**:
```json
{
  "ok": true,
  "data": {
    "id": "memory-xxx",
    "status": "stored",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### 2. Search Tool
Search memories using semantic similarity.

**Endpoint**: `POST /api/mcp/search`

**Request**:
```json
{
  "query": "search query",
  "top_k": 5,
  "conversation_id": "conv-xxx"
}
```

**Response**:
```json
{
  "ok": true,
  "data": {
    "results": [
      {"id": "memory-xxx", "title": "...", "snippet": "...", "score": 0.95}
    ]
  }
}
```

### 3. Inject Tool
Inject relevant memories into conversation context.

**Endpoint**: `POST /api/mcp/inject`

**Request**:
```json
{
  "conversation_id": "conv-xxx",
  "max_memories": 5
}
```

**Response**:
```json
{
  "ok": true,
  "data": {
    "injected_context": "=== Injected Context ===\n...",
    "memory_count": 3,
    "memories": [...]
  }
}
```

### 4. List Memories Tool
List all memories for a conversation.

**Endpoint**: `GET /api/mcp/listMemories?conversation_id=xxx&limit=20&offset=0`

**Response**:
```json
{
  "ok": true,
  "data": {
    "memories": [...],
    "total": 42
  }
}
```

## Memory Injection Flow

1. User sends message to conversation
2. System calls `build_context()` to gather:
   - System prompt
   - Active injected memories (from ConversationMemory links)
   - Conversation history (last 10 messages)
3. Memories are formatted as text and prepended to system prompt
4. Full context sent to LLM provider

## Implementation Details

- Memories are stored per workspace
- Manual injection via UI (user selects which memories to inject)
- Injected memories can be toggled active/inactive
- Memory content is included in system prompt as context
