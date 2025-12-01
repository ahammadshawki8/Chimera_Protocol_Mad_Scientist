---
inclusion: always
---

# Chimera Protocol Backend - Project Context

## Overview
Django REST Framework backend for Chimera Protocol - a neural-themed AI memory management system. Provides APIs for authentication, workspaces, conversations, memories, and multi-LLM integration.

## Key Features
1. **Multi-LLM Router** - Route requests to OpenAI, Anthropic, Google, DeepSeek
2. **Memory System** - Store, search, and inject memories into conversations
3. **Workspace Isolation** - Separate data per workspace
4. **Team Collaboration** - Invite members with role-based access
5. **Encrypted API Keys** - Secure storage of provider credentials

## Architecture
```
api/
├── models.py           # Database models
├── views_*.py          # API endpoints by domain
├── serializers_v2.py   # Request/response serialization
├── llm_router.py       # Multi-LLM routing logic
├── memory_service.py   # Memory operations
├── encryption_service.py # API key encryption
└── urls.py             # URL routing
```

## Database Models
- User, Workspace, TeamMember
- Conversation, ChatMessage
- Memory, ConversationMemory (junction)
- Integration (API keys)

## API Response Format
All endpoints return:
```json
{
  "ok": true/false,
  "data": {...},
  "error": "message" or null
}
```
