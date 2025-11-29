# ⚠️ RESTART REQUIRED

## The Django server needs to be restarted!

When you update the `.env` file, Django doesn't automatically reload environment variables. You must restart the server.

## How to Restart

### Step 1: Stop the Server
Press `Ctrl+C` in the terminal where Django is running

### Step 2: Start the Server Again
```bash
python manage.py runserver
```

## Why Restart is Needed

- Environment variables (`.env` file) are loaded when Django starts
- Changes to `.env` are NOT picked up while the server is running
- The ENCRYPTION_KEY was just updated, so a restart is required

## What Was Fixed

1. ✅ Syntax error in `exception_handler.py`
2. ✅ Invalid ENCRYPTION_KEY in `.env` file
3. ⚠️ **Server restart needed** to load new ENCRYPTION_KEY

## After Restarting

Test the integrations page:
1. Go to `http://localhost:5173/app/integrations`
2. Add an API key for OpenAI, Anthropic, or Google
3. Should save successfully now!

## Still Getting Errors?

If you still see errors after restarting:

### Check 1: Verify .env is loaded
```python
python manage.py shell
>>> import os
>>> print(os.getenv('ENCRYPTION_KEY'))
# Should print: 8JXzKc-vQR6yN5mP3wL9xE2bF7aG4hT1sU0dV6nM8kI=
```

### Check 2: Test encryption directly
```python
python manage.py shell
>>> from api.encryption_service import encrypt_api_key, decrypt_api_key
>>> encrypted = encrypt_api_key("test-key")
>>> print(encrypted)
>>> decrypted = decrypt_api_key(encrypted)
>>> print(decrypted)
# Should print: test-key
```

### Check 3: Check Django logs
Look at the terminal where Django is running for any error messages

## Common Issues

### Issue: "Fernet key must be 32 url-safe base64-encoded bytes"
**Solution**: The ENCRYPTION_KEY in `.env` is invalid. Use the one provided or generate a new one:
```bash
python generate_key.py
```

### Issue: "Internal server error" when saving API key
**Solution**: 
1. Check Django terminal for detailed error
2. Verify ENCRYPTION_KEY is set in `.env`
3. Restart Django server

### Issue: API key saves but shows as "***"
**Solution**: This is normal! API keys are encrypted and masked for security.

## Quick Test

After restarting, run this to verify everything works:

```bash
# In Django shell
python manage.py shell

# Test encryption
from api.encryption_service import encrypt_api_key, decrypt_api_key
test_key = "sk-test123"
encrypted = encrypt_api_key(test_key)
decrypted = decrypt_api_key(encrypted)
print(f"Original: {test_key}")
print(f"Encrypted: {encrypted}")
print(f"Decrypted: {decrypted}")
print(f"Match: {test_key == decrypted}")
```

Should output:
```
Original: sk-test123
Encrypted: gAAAAAB... (long encrypted string)
Decrypted: sk-test123
Match: True
```

---

**Remember**: Always restart Django after changing `.env` file!
