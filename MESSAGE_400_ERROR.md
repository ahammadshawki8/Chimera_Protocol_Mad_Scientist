# Troubleshooting: 400 Error When Sending Messages

## Error
```
WARNING "POST /api/conversations/conv-a66a3ec47aef/messages HTTP/1.1" 400
```

## Possible Causes

### 1. No Integration for Model's Provider
The most common cause - you're trying to use a model but don't have a connected integration for its provider.

**Solution**:
1. Go to Integrations page
2. Make sure the provider for your model is "Connected"
3. If not, add API key and test connection

### 2. Empty Message Content
Sending an empty message.

**Solution**: Make sure you're typing a message before sending.

### 3. Conversation Not Found
The conversation ID doesn't exist in the database.

**Solution**: Create a new conversation from the model selection page.

### 4. Access Denied
You don't have access to the workspace.

**Solution**: Make sure you're logged in and have access to the workspace.

## How to Debug

### Step 1: Check Django Logs
Look at the terminal where Django is running. You should see a detailed error message explaining what went wrong.

Common errors:
- `"No connected integration found for provider: google"` - Add Google API key
- `"content: This field is required"` - Message content is empty
- `"Conversation not found"` - Invalid conversation ID

### Step 2: Run Test Script
```bash
python test_send_message.py
```

This will check:
- Message serializer validation
- Existing conversations
- User integrations

### Step 3: Check Integration Status
```bash
python manage.py shell
```

```python
from api.models import Integration, User

user = User.objects.first()  # Or get your specific user
integrations = Integration.objects.filter(user=user)

for integration in integrations:
    print(f"{integration.provider}: {integration.status}")
```

Should show:
```
google: connected
```

If it shows `disconnected` or `error`, go to Integrations page and test the connection.

### Step 4: Check Conversation
```bash
python manage.py shell
```

```python
from api.models import Conversation

# Check if conversation exists
conv_id = "conv-a66a3ec47aef"  # Use your actual ID
try:
    conv = Conversation.objects.get(id=conv_id)
    print(f"Found: {conv.title}")
    print(f"Model: {conv.model_id}")
    print(f"Workspace: {conv.workspace.name}")
except Conversation.DoesNotExist:
    print("Conversation not found!")
```

## Common Scenarios

### Scenario 1: "No connected integration found for provider: google"

**Problem**: You selected a Google model but don't have Google integration connected.

**Solution**:
1. Go to `http://localhost:5173/app/integrations`
2. Find "Google Gemini" section
3. Enter your Google AI API key
4. Click "Save Key"
5. Click "Test Connection"
6. Should show "Connected"
7. Try sending message again

### Scenario 2: Message appears to send but gets 400 error

**Problem**: Frontend is sending the request but backend rejects it.

**Solution**:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try sending a message
4. Click on the failed request
5. Check "Response" tab for error message
6. Check Django terminal for detailed error

### Scenario 3: Can't create conversation

**Problem**: Model selection page shows "No Models Connected"

**Solution**:
1. Go to Integrations page
2. Add at least one API key
3. Test the connection
4. Go back to model selection
5. Should now see models

## Quick Fixes

### Fix 1: Restart Django
Sometimes Django needs a restart after adding integrations:
```bash
# Stop Django (Ctrl+C)
python manage.py runserver
```

### Fix 2: Re-test Integration
1. Go to Integrations page
2. Click "Test Connection" for your provider
3. Should show "Connected"

### Fix 3: Create New Conversation
If conversation is corrupted:
1. Go to Chat List
2. Click "New Chat"
3. Select a model
4. Try sending message in new conversation

## Expected Flow

1. ✅ User has integration connected (e.g., Google)
2. ✅ User creates conversation with Google model
3. ✅ User types message
4. ✅ User clicks send
5. ✅ Backend validates message
6. ✅ Backend finds integration for Google
7. ✅ Backend calls Google API
8. ✅ Backend saves both messages
9. ✅ Frontend displays both messages

## Still Not Working?

### Check Backend Logs
The Django terminal will show the exact error. Look for:
```
ERROR: <detailed error message>
```

### Enable Debug Mode
In `.env`:
```env
DEBUG=True
```

Restart Django and try again. You'll see more detailed error messages.

### Check Browser Console
Open DevTools (F12) and check Console tab for JavaScript errors.

### Test API Directly
Use curl to test the endpoint:
```bash
curl -X POST http://127.0.0.1:8000/api/conversations/YOUR_CONV_ID/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!", "getAiResponse": true}'
```

Replace:
- `YOUR_CONV_ID` with actual conversation ID
- `YOUR_TOKEN` with your JWT token (from localStorage)

---

**Most Common Fix**: Add/test the integration for the model's provider in the Integrations page!
