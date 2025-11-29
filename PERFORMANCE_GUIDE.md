# Performance Testing and Optimization Guide

## Performance Targets

| Endpoint Type | Target Response Time |
|---------------|---------------------|
| Simple GET (single resource) | < 200ms |
| List GET (with pagination) | < 300ms |
| Complex GET (dashboard, stats) | < 500ms |
| POST/PUT/DELETE | < 300ms |
| Search operations | < 500ms |
| AI chat responses | < 5s (depends on provider) |

## Performance Testing Tools

### 1. Django Debug Toolbar

Install and configure:

```bash
pip install django-debug-toolbar
```

Add to `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'debug_toolbar',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    ...
]

INTERNAL_IPS = ['127.0.0.1']
```

Add to `urls.py`:

```python
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
```

**Usage:**
- Access any API endpoint in browser
- Click debug toolbar on right side
- Check SQL queries, timing, cache hits

### 2. Django Silk

For production-like profiling:

```bash
pip install django-silk
```

Configure in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'silk',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    ...
]
```

Run migrations:

```bash
python manage.py migrate
```

**Usage:**
- Access `http://localhost:8000/silk/`
- View request profiling
- Analyze slow queries

### 3. Apache Bench (ab)

Test API endpoint performance:

```bash
# Test 1000 requests with 10 concurrent
ab -n 1000 -c 10 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/workspaces
```

### 4. Locust

For load testing:

```bash
pip install locust
```

Create `locustfile.py`:

```python
from locust import HttpUser, task, between

class ChimeraUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json()['data']['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def list_workspaces(self):
        self.client.get("/api/workspaces", headers=self.headers)
    
    @task(2)
    def list_memories(self):
        self.client.get("/api/workspaces/workspace-123/memories", headers=self.headers)
    
    @task(1)
    def create_memory(self):
        self.client.post("/api/workspaces/workspace-123/memories", 
            headers=self.headers,
            json={
                "title": "Test Memory",
                "content": "Test content"
            })
```

Run:

```bash
locust -f locustfile.py
```

Access `http://localhost:8089` to start test.

## Database Query Optimization

### 1. Identify N+1 Queries

Use Django Debug Toolbar to identify N+1 queries.

**Bad Example:**
```python
workspaces = Workspace.objects.all()
for workspace in workspaces:
    print(workspace.owner.name)  # N+1 query!
```

**Good Example:**
```python
workspaces = Workspace.objects.select_related('owner').all()
for workspace in workspaces:
    print(workspace.owner.name)  # Single query
```

### 2. Use select_related for ForeignKey

```python
# Single query instead of N+1
conversations = Conversation.objects.select_related('workspace', 'workspace__owner').all()
```

### 3. Use prefetch_related for ManyToMany and Reverse ForeignKey

```python
# Efficient loading of related objects
workspaces = Workspace.objects.prefetch_related('members__user', 'conversations').all()
```

### 4. Add Database Indexes

Already added in models:

```python
class Workspace(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['owner', '-updated_at']),
        ]
```

Verify indexes:

```sql
\d api_workspace  -- In psql
```

### 5. Use only() and defer()

Load only needed fields:

```python
# Only load specific fields
memories = Memory.objects.only('id', 'title', 'snippet')

# Defer large fields
memories = Memory.objects.defer('embedding', 'content')
```

### 6. Use count() instead of len()

```python
# Bad
total = len(Workspace.objects.all())

# Good
total = Workspace.objects.count()
```

### 7. Use exists() for boolean checks

```python
# Bad
if Workspace.objects.filter(owner=user):
    ...

# Good
if Workspace.objects.filter(owner=user).exists():
    ...
```

## Caching Strategies

### 1. Django Cache Framework

Configure in `settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 2. Cache Workspace Stats

```python
from django.core.cache import cache

def calculate_workspace_stats(workspace):
    cache_key = f'workspace_stats_{workspace.id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Calculate stats
        stats = {
            'totalMemories': workspace.memories.count(),
            ...
        }
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
    
    return stats
```

### 3. Cache Available Models

```python
def get_available_models(user):
    cache_key = f'available_models_{user.id}'
    models = cache.get(cache_key)
    
    if models is None:
        # Query and build models list
        models = [...]
        # Cache for 1 hour
        cache.set(cache_key, models, 3600)
    
    return models
```

### 4. Invalidate Cache on Updates

```python
def update_workspace(workspace):
    workspace.save()
    # Invalidate cache
    cache.delete(f'workspace_stats_{workspace.id}')
```

## API Response Optimization

### 1. Pagination

Already implemented:

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
}
```

### 2. Field Filtering

Allow clients to request specific fields:

```python
# GET /api/memories?fields=id,title,snippet
```

### 3. Compression

Enable gzip compression in `settings.py`:

```python
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    ...
]
```

### 4. ETags

Enable conditional requests:

```python
MIDDLEWARE = [
    'django.middleware.http.ConditionalGetMiddleware',
    ...
]
```

## Memory Optimization

### 1. Streaming Large Responses

For data export:

```python
from django.http import StreamingHttpResponse

def export_data_view(request):
    def generate():
        yield '{"workspaces": ['
        for workspace in workspaces:
            yield json.dumps(serialize_workspace(workspace))
            yield ','
        yield ']}'
    
    return StreamingHttpResponse(generate(), content_type='application/json')
```

### 2. Batch Operations

Use bulk_create and bulk_update:

```python
# Bad
for item in items:
    Memory.objects.create(**item)

# Good
Memory.objects.bulk_create([Memory(**item) for item in items])
```

### 3. Iterator for Large Querysets

```python
# Bad - loads all into memory
for memory in Memory.objects.all():
    process(memory)

# Good - streams from database
for memory in Memory.objects.iterator():
    process(memory)
```

## Embedding Search Optimization

### 1. Use NumPy for Vector Operations

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def search_memories(query_embedding, memory_embeddings):
    # Convert to numpy arrays
    query_vec = np.array(query_embedding).reshape(1, -1)
    memory_vecs = np.array(memory_embeddings)
    
    # Compute similarities (vectorized)
    similarities = cosine_similarity(query_vec, memory_vecs)[0]
    
    # Get top K
    top_indices = np.argsort(similarities)[::-1][:k]
    
    return top_indices, similarities[top_indices]
```

### 2. Consider FAISS for Large Scale

For 10,000+ memories:

```bash
pip install faiss-cpu
```

```python
import faiss

# Build index
dimension = 384  # embedding size
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# Search
distances, indices = index.search(query_embedding, k=10)
```

## Monitoring and Profiling

### 1. Application Performance Monitoring (APM)

Consider using:
- New Relic
- Datadog
- Sentry (for error tracking)

### 2. Database Query Monitoring

```python
# Log slow queries
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### 3. Custom Metrics

```python
import time
from functools import wraps

def track_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        # Log or send to monitoring service
        print(f"{func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

@track_time
def expensive_operation():
    ...
```

## Performance Testing Checklist

- [ ] Install performance testing tools
- [ ] Profile all API endpoints
- [ ] Identify and fix N+1 queries
- [ ] Add database indexes
- [ ] Implement caching for expensive operations
- [ ] Enable response compression
- [ ] Test with 100+ concurrent users
- [ ] Test with large datasets (1000+ records)
- [ ] Monitor memory usage
- [ ] Check for memory leaks
- [ ] Optimize embedding search
- [ ] Set up APM monitoring
- [ ] Document performance baselines
- [ ] Create performance regression tests

## Performance Benchmarks

After optimization, expected results:

| Operation | Before | After | Target |
|-----------|--------|-------|--------|
| List workspaces | 500ms | 150ms | < 200ms |
| Get dashboard | 1200ms | 400ms | < 500ms |
| Search memories | 800ms | 300ms | < 500ms |
| Create memory | 400ms | 200ms | < 300ms |
| Send message | 2500ms | 1800ms | < 2000ms |

## Optimization Priorities

1. **High Priority:**
   - Fix N+1 queries
   - Add database indexes
   - Implement pagination

2. **Medium Priority:**
   - Add caching for stats
   - Optimize embedding search
   - Enable compression

3. **Low Priority:**
   - Field filtering
   - Streaming responses
   - Advanced caching strategies

## Continuous Monitoring

Set up alerts for:
- Response time > 1s
- Error rate > 1%
- Database connection pool exhaustion
- Memory usage > 80%
- CPU usage > 80%

## Next Steps

1. Run performance tests
2. Document baseline metrics
3. Implement optimizations
4. Re-test and compare
5. Set up monitoring
6. Create performance regression tests
7. Document optimization strategies
