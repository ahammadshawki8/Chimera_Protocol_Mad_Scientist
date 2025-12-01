---
trigger: fileMatch
filePattern: "api/views_*.py"
description: Guidelines for API endpoint development
---

# API Endpoint Development Hook

## Response Format
Always use the standard envelope:
```python
def api_response(ok=True, data=None, error=None):
    return {'ok': ok, 'data': data, 'error': error}
```

## Authentication
- Use `@permission_classes([IsAuthenticated])` for protected endpoints
- Access user via `request.user`

## Error Handling
```python
try:
    # operation
except Model.DoesNotExist:
    return Response(
        api_response(ok=False, error='Not found'),
        status=status.HTTP_404_NOT_FOUND
    )
```

## Checklist
- [ ] Uses api_response envelope
- [ ] Has proper authentication
- [ ] Handles errors gracefully
- [ ] Uses serializers for validation
- [ ] Returns appropriate HTTP status codes
