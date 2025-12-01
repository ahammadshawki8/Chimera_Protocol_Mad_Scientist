# Chimera Protocol - Backend

Django REST Framework backend for Chimera Protocol - a neural-themed AI memory management system with multi-LLM support and MCP (Model Context Protocol) integration.

![Chimera Protocol](https://img.shields.io/badge/Chimera-Protocol-cyan)
![License](https://img.shields.io/badge/license-MIT-green)
![Django](https://img.shields.io/badge/Django-5-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)

## 🧠 Features

- **Multi-LLM Router** - Route requests to OpenAI, Anthropic, Google, DeepSeek
- **MCP Memory Tools** - Store, search, and inject memories into conversations
- **Workspace Isolation** - Separate data per workspace with team collaboration
- **Encrypted API Keys** - Secure Fernet encryption for provider credentials
- **Memory Extraction** - Auto-extract memories from completed conversations
- **URL/File Import** - Import memories from web pages and documents

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (or SQLite for development)
- Virtual environment

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/chimera-backend.git
cd chimera-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Generate encryption key
python generate_key.py

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### Environment Variables

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DATABASE_URL=postgres://user:pass@localhost:5432/chimera

# Encryption
ENCRYPTION_KEY=your-fernet-key

# Optional: Default API keys (users can add their own)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=sk-...
```

## 📁 Project Structure

```
chimera/                 # Django project settings
├── settings.py
├── urls.py
└── wsgi.py

api/                     # Main application
├── models.py           # Database models
├── views_*.py          # API endpoints by domain
│   ├── views.py        # Auth endpoints
│   ├── views_workspace.py
│   ├── views_conversation.py
│   ├── views_memory.py
│   ├── views_integration.py
│   ├── views_team.py
│   └── views_settings.py
├── serializers_v2.py   # Request/response serialization
├── llm_router.py       # Multi-LLM routing logic
├── memory_service.py   # Memory operations
├── memory_extractor.py # Auto-extract memories
├── encryption_service.py # API key encryption
├── url_scraper.py      # Web page import
├── file_parser.py      # Document import
└── urls.py             # URL routing

.kiro/                   # Kiro configuration
├── specs/              # Feature specifications
├── steering/           # Project guidelines
├── hooks/              # Agent hooks
└── mcp/                # MCP tool documentation
```

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT |
| POST | `/api/auth/logout` | Logout (blacklist token) |
| POST | `/api/auth/refresh` | Refresh access token |

### Workspaces
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces` | List user workspaces |
| POST | `/api/workspaces` | Create workspace |
| GET | `/api/workspaces/{id}` | Get workspace details |
| DELETE | `/api/workspaces/{id}` | Delete workspace |

### Conversations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/conversations` | List conversations |
| POST | `/api/workspaces/{id}/conversations` | Create conversation |
| POST | `/api/conversations/{id}/messages` | Send message |
| POST | `/api/conversations/{id}/inject-memory` | Inject memory |
| POST | `/api/conversations/{id}/close` | Close & extract memory |

### Memories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/workspaces/{id}/memories` | List memories |
| POST | `/api/workspaces/{id}/memories` | Create memory |
| POST | `/api/workspaces/{id}/memories/import-url` | Import from URL |
| POST | `/api/workspaces/{id}/memories/import-file` | Import from file |
| POST | `/api/memories/search` | Search memories |

### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/integrations` | List user integrations |
| POST | `/api/integrations` | Add API key |
| POST | `/api/integrations/{id}/test` | Test connection |
| GET | `/api/models/available` | Get available models |

### MCP Tools
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mcp/remember` | Store memory |
| POST | `/api/mcp/search` | Search memories |
| POST | `/api/mcp/inject` | Inject context |
| GET | `/api/mcp/listMemories` | List memories |

## 🤖 Supported LLM Providers

| Provider | Models | Status |
|----------|--------|--------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5-turbo | ✅ |
| Anthropic | Claude 3.5 Sonnet, Claude 3 | ✅ |
| Google | Gemini 2.0 Flash, Gemini Pro | ✅ |
| DeepSeek | DeepSeek Chat, DeepSeek Coder | ✅ |

## 🔐 Security

- JWT authentication with refresh tokens
- Fernet encryption for API keys at rest
- CORS configuration for frontend
- Input validation via serializers
- SQL injection prevention via ORM

## 🛠️ Development

```bash
# Run development server
python manage.py runserver

# Run with auto-reload
python manage.py runserver --noreload

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Run tests
python manage.py test
```

## 📦 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL database
- [ ] Set strong `SECRET_KEY`
- [ ] Configure HTTPS
- [ ] Set up static file serving

### Docker (Optional)
```bash
docker build -t chimera-backend .
docker run -p 8000:8000 chimera-backend
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🔗 Related

- [Frontend Repository](../chimera) - React/TypeScript UI
- [API Documentation](API_DOCUMENTATION.md)
