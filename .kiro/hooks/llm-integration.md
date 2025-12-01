---
trigger: fileMatch
filePattern: "api/llm_router.py"
description: Guidelines for adding new LLM providers
---

# LLM Integration Hook

## Adding a New Provider

1. Add model mapping in `SUPPORTED_MODELS`:
```python
SUPPORTED_MODELS = {
    'model-name': 'provider',
}
```

2. Create call function:
```python
def call_provider(model: str, prompt: str, api_key: str = None, context: Dict = None):
    # Implementation
```

3. Add to router in `route_to_model()` and `route_to_model_with_context()`

4. Add connection test in `views_integration.py`

5. Add to `PRIMARY_MODELS` for 3D brain display

## Context Injection
Use the `context` parameter to inject memories:
```python
if context:
    system_content = context['system_prompt']
    if context['memories_text']:
        system_content += context['memories_text']
```

## Checklist
- [ ] Model mapping added
- [ ] Call function implemented
- [ ] Router updated
- [ ] Connection test added
- [ ] Brain position configured
