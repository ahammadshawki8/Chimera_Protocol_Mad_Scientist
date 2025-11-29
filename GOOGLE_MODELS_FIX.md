# Fix: Google Models Not Showing

## Issue
Gemini integration shows as "online" but no models appear when trying to create a new chat.

## Root Cause
Google models were missing from the `SUPPORTED_MODELS` dictionary in `llm_router.py`.

## Fix Applied
Added Google models to `api/llm_router.py`:

```python
# Google models
'gemini-pro': 'google',
'gemini-1.5-pro': 'google',
'gemini-1.5-flash': 'google',
'gemini-2.0-flash': 'google',
```

## How to Test

### Step 1: Restart Django Server
```bash
# Stop Django (Ctrl+C)
# Start again
python manage.py runserver
```

### Step 2: Verify Integration Status
1. Go to `http://localhost:5173/app/integrations`
2. Check that Google integration shows "Connected"
3. If not, click "Test Connection"

### Step 3: Check Available Models API
Test the API directly:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/api/models/available
```

Should return Google models like:
```json
{
  "ok": true,
  "data": {
    "models": [
      {
        "id": "model-geminipro",
        "provider": "google",
        "name": "gemini-pro",
        "displayName": "Gemini Pro",
        "brainRegion": "Occipital",
        "status": "connected",
        "position": {"x": 0, "y": -1, "z": 2}
      }
    ]
  }
}
```

### Step 4: Try Creating a Chat
1. Go to `http://localhost:5173/app/chat`
2. Click "New Chat"
3. Should see Google models in the 3D brain visualization
4. Click on a model to start chatting

## Troubleshooting

### Still No Models?

#### Check 1: Integration Status
```bash
python manage.py shell
```

```python
from api.models import Integration
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()  # Or get your specific user
integrations = Integration.objects.filter(user=user)

for integration in integrations:
    print(f"{integration.provider}: {integration.status}")
```

Should show:
```
google: connected
```

If it shows `disconnected` or `error`, test the connection again in the UI.

#### Check 2: Verify Models in Code
```bash
python manage.py shell
```

```python
from api.llm_router import SUPPORTED_MODELS

google_models = {k: v for k, v in SUPPORTED_MODELS.items() if v == 'google'}
print("Google models:", google_models)
```

Should show:
```
Google models: {
    'gemini-pro': 'google',
    'gemini-1.5-pro': 'google',
    'gemini-1.5-flash': 'google',
    'gemini-2.0-flash': 'google'
}
```

#### Check 3: Test Available Models Endpoint
In browser console (F12):
```javascript
fetch('http://127.0.0.1:8000/api/models/available', {
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('auth_token')
  }
})
.then(r => r.json())
.then(d => console.log(d))
```

Should return models array with Google models.

#### Check 4: Frontend State
In browser console:
```javascript
// Check if models are loaded
console.log('Models loaded:', window.location.href.includes('model-select'))
```

## What Changed

### File: `api/llm_router.py`
**Before**:
```python
SUPPORTED_MODELS = {
    # ... OpenAI, Anthropic, Groq models ...
    # ❌ No Google models!
}
```

**After**:
```python
SUPPORTED_MODELS = {
    # ... OpenAI, Anthropic models ...
    
    # Google models ✅
    'gemini-pro': 'google',
    'gemini-1.5-pro': 'google',
    'gemini-1.5-flash': 'google',
    'gemini-2.0-flash': 'google',
    
    # ... Groq models ...
}
```

## Expected Behavior After Fix

1. ✅ Google integration shows "Connected"
2. ✅ Available models API returns Google models
3. ✅ Model selection page shows Google models in 3D brain
4. ✅ Can create new chat with Google models
5. ✅ Can send messages and get responses from Gemini

## Additional Models

If you want to add more Google models in the future, edit `api/llm_router.py`:

```python
# Add new Google model
'gemini-ultra': 'google',
```

Then restart Django.

---

**Status**: ✅ Fixed
**Restart Required**: Yes (Django server)
