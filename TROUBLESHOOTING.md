# Troubleshooting: API Key Not Saving (500 Error)

## Current Issue

Getting `500 Internal Server Error` when trying to save API keys in the integrations page.

## Root Cause

The Django server is still using the OLD invalid ENCRYPTION_KEY. The `.env` file was updated, but **Django doesn't reload environment variables automatically**.

## ✅ Solution: Restart Django Server

### Step 1: Stop Django
In the terminal where Django is running, press:
```
Ctrl + C
```

### Step 2: Start Django Again
```bash
cd Chimera_Protocol_Mad_Scientist
python manage.py runserver
```

### Step 3: Test Encryption
Before trying the frontend again, verify encryption works:
```bash
python test_encryption.py
```

You should see:
```
✅ ALL TESTS PASSED
Encryption is working correctly!
```

### Step 4: Try Frontend Again
1. Go to `http://localhost:5173/app/integrations`
2. Enter an API key
3. Click "Save Key"
4. Should work now! ✅

## Still Not Working?

### Check 1: Verify .env File

Open `Chimera_Protocol_Mad_Scientist/.env` and check:

```env
ENCRYPTION_KEY=8JXzKc-vQR6yN5mP3wL9xE2bF7aG4hT1sU0dV6nM8kI=
```

- ✅ Should be a long base64 string (44 characters)
- ❌ Should NOT be "your-fernet-encryption-key-here"

### Check 2: Test in Django Shell

```bash
python manage.py shell
```

Then run:
```python
import os
print("ENCRYPTION_KEY:", os.getenv('ENCRYPTION_KEY'))

from api.encryption_service import encrypt_api_key, decrypt_api_key
test = "sk-test123"
encrypted = encrypt_api_key(test)
decrypted = decrypt_api_key(encrypted)
print(f"Original: {test}")
print(f"Decrypted: {decrypted}")
print(f"Match: {test == decrypted}")
```

Should output:
```
ENCRYPTION_KEY: 8JXzKc-vQR6yN5mP3wL9xE2bF7aG4hT1sU0dV6nM8kI=
Original: sk-test123
Decrypted: sk-test123
Match: True
```

### Check 3: Look at Django Terminal

When you try to save an API key, look at the Django terminal for error messages. Common errors:

#### Error: "Fernet key must be 32 url-safe base64-encoded bytes"
**Solution**: ENCRYPTION_KEY is invalid. Generate a new one:
```bash
python generate_key.py
```
Copy the output to `.env` and restart Django.

#### Error: "Integration already exists"
**Solution**: You already have an integration for that provider. Delete it first or use the update endpoint.

#### Error: "Authentication credentials were not provided"
**Solution**: You're not logged in. Go to login page first.

### Check 4: Check Browser Console

Open browser DevTools (F12) and look for errors. Common issues:

#### Error: "Failed to load resource: 500"
**Solution**: Django server error. Check Django terminal for details.

#### Error: "Network Error"
**Solution**: Django server not running or wrong URL.

## Quick Diagnostic Commands

### 1. Check if Django is running
```bash
curl http://127.0.0.1:8000/api/health
```
Should return: `{"status": "ok"}`

### 2. Check if you're logged in
In browser console:
```javascript
console.log(localStorage.getItem('auth_token'))
```
Should show a JWT token, not `null`

### 3. Test encryption directly
```bash
python test_encryption.py
```

### 4. Check Django logs
Look at the terminal where Django is running for error messages

## Common Mistakes

1. ❌ **Not restarting Django** after updating `.env`
   - ✅ Always restart: `Ctrl+C` then `python manage.py runserver`

2. ❌ **Invalid ENCRYPTION_KEY** in `.env`
   - ✅ Use the provided key or generate new one with `python generate_key.py`

3. ❌ **Not logged in** when testing
   - ✅ Register/login first at `http://localhost:5173/auth/login`

4. ❌ **Django not running**
   - ✅ Start with `python manage.py runserver`

5. ❌ **Wrong API URL** in frontend
   - ✅ Check `chimera/.env` has `VITE_API_BASE_URL=http://127.0.0.1:8000/api`

## Step-by-Step Fresh Start

If nothing works, try this:

### 1. Stop Everything
- Stop Django (Ctrl+C)
- Stop Frontend (Ctrl+C)

### 2. Verify .env
```bash
cd Chimera_Protocol_Mad_Scientist
cat .env | grep ENCRYPTION_KEY
```
Should show: `ENCRYPTION_KEY=8JXzKc-vQR6yN5mP3wL9xE2bF7aG4hT1sU0dV6nM8kI=`

### 3. Test Encryption
```bash
python test_encryption.py
```
Should pass all tests.

### 4. Start Django
```bash
python manage.py runserver
```

### 5. Start Frontend
```bash
cd ../chimera
npm run dev
```

### 6. Test in Browser
1. Go to `http://localhost:5173`
2. Login or register
3. Go to Integrations page
4. Add an API key
5. Should work! ✅

## Still Having Issues?

Check these files for errors:

1. **Backend logs**: Terminal where Django is running
2. **Frontend logs**: Browser console (F12)
3. **Network tab**: Check the actual request/response
4. **Django error log**: `Chimera_Protocol_Mad_Scientist/logs/error.log`

## Need More Help?

Run the diagnostic script:
```bash
python test_encryption.py
```

This will tell you exactly what's wrong.

---

**Remember**: The #1 cause of this error is **not restarting Django** after updating `.env`!
