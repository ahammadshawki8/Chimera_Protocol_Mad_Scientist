#!/usr/bin/env python
"""
Test script to verify encryption is working
Run this to check if ENCRYPTION_KEY is properly loaded
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chimera.settings')
django.setup()

from api.encryption_service import encrypt_api_key, decrypt_api_key

def test_encryption():
    """Test encryption and decryption"""
    print("=" * 60)
    print("ENCRYPTION TEST")
    print("=" * 60)
    
    # Check if ENCRYPTION_KEY is loaded
    encryption_key = os.getenv('ENCRYPTION_KEY')
    print(f"\n1. ENCRYPTION_KEY loaded: {encryption_key is not None}")
    if encryption_key:
        print(f"   Key value: {encryption_key[:20]}...")
    else:
        print("   ❌ ERROR: ENCRYPTION_KEY not found in environment!")
        print("   Make sure .env file has ENCRYPTION_KEY set")
        return False
    
    # Test encryption
    test_key = "sk-test-api-key-12345"
    print(f"\n2. Testing encryption...")
    print(f"   Original key: {test_key}")
    
    try:
        encrypted = encrypt_api_key(test_key)
        print(f"   ✅ Encrypted: {encrypted[:50]}...")
    except Exception as e:
        print(f"   ❌ Encryption failed: {e}")
        return False
    
    # Test decryption
    print(f"\n3. Testing decryption...")
    try:
        decrypted = decrypt_api_key(encrypted)
        print(f"   ✅ Decrypted: {decrypted}")
    except Exception as e:
        print(f"   ❌ Decryption failed: {e}")
        return False
    
    # Verify match
    print(f"\n4. Verifying match...")
    if test_key == decrypted:
        print(f"   ✅ SUCCESS: Original and decrypted keys match!")
        return True
    else:
        print(f"   ❌ FAIL: Keys don't match!")
        print(f"      Original:  {test_key}")
        print(f"      Decrypted: {decrypted}")
        return False

if __name__ == '__main__':
    print("\n🔐 Testing Chimera Protocol Encryption Service\n")
    
    success = test_encryption()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nEncryption is working correctly!")
        print("You can now save API keys in the integrations page.")
    else:
        print("❌ TESTS FAILED")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Check that .env file has ENCRYPTION_KEY set")
        print("2. Restart Django server after updating .env")
        print("3. Run: python generate_key.py to get a new key")
    print()
