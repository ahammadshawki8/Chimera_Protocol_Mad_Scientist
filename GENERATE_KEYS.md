# Generate Encryption Keys

## Generate Fernet Encryption Key

The ENCRYPTION_KEY in `.env` must be a valid Fernet key (32-byte base64-encoded string).

### Method 1: Using Python Script

Run the included script:
```bash
python generate_key.py
```

This will output a valid Fernet key that you can copy to your `.env` file.

### Method 2: Using Python Command

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Method 3: Using Python Interactive Shell

```python
python
>>> from cryptography.fernet import Fernet
>>> print(Fernet.generate_key().decode())
>>> exit()
```

## Update .env File

Copy the generated key and update your `.env` file:

```env
ENCRYPTION_KEY=your-generated-key-here
```

## Example Valid Key

```
ENCRYPTION_KEY=8JXzKc-vQR6yN5mP3wL9xE2bF7aG4hT1sU0dV6nM8kI=
```

**Important**: 
- Never commit your actual `.env` file to version control
- Each environment should have its own unique encryption key
- Keep your encryption key secure - it's used to encrypt API keys in the database

## Generate Django SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Generate JWT Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## All Keys at Once

Run this to generate all required keys:

```python
from cryptography.fernet import Fernet
from django.core.management.utils import get_random_secret_key
import secrets

print("ENCRYPTION_KEY=" + Fernet.generate_key().decode())
print("SECRET_KEY=" + get_random_secret_key())
print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
```

Save this as `generate_all_keys.py` and run:
```bash
python generate_all_keys.py
```
