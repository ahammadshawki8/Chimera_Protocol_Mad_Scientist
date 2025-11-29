#!/usr/bin/env python
"""
Test script to debug message sending
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chimera.settings')
django.setup()

from api.models import Conversation, ChatMessage, User
from api.serializers_v2 import MessageCreateSerializer

def test_message_serializer():
    """Test the message serializer with different inputs"""
    print("=" * 60)
    print("MESSAGE SERIALIZER TEST")
    print("=" * 60)
    
    # Test 1: Valid data
    print("\n1. Testing valid data:")
    data1 = {'content': 'Hello, AI!'}
    serializer1 = MessageCreateSerializer(data=data1)
    print(f"   Data: {data1}")
    print(f"   Valid: {serializer1.is_valid()}")
    if not serializer1.is_valid():
        print(f"   Errors: {serializer1.errors}")
    else:
        print(f"   Validated: {serializer1.validated_data}")
    
    # Test 2: With getAiResponse (should be ignored by serializer)
    print("\n2. Testing with getAiResponse:")
    data2 = {'content': 'Hello!', 'getAiResponse': True}
    serializer2 = MessageCreateSerializer(data=data2)
    print(f"   Data: {data2}")
    print(f"   Valid: {serializer2.is_valid()}")
    if not serializer2.is_valid():
        print(f"   Errors: {serializer2.errors}")
    else:
        print(f"   Validated: {serializer2.validated_data}")
    
    # Test 3: Empty content
    print("\n3. Testing empty content:")
    data3 = {'content': ''}
    serializer3 = MessageCreateSerializer(data=data3)
    print(f"   Data: {data3}")
    print(f"   Valid: {serializer3.is_valid()}")
    if not serializer3.is_valid():
        print(f"   Errors: {serializer3.errors}")
    
    # Test 4: Missing content
    print("\n4. Testing missing content:")
    data4 = {}
    serializer4 = MessageCreateSerializer(data=data4)
    print(f"   Data: {data4}")
    print(f"   Valid: {serializer4.is_valid()}")
    if not serializer4.is_valid():
        print(f"   Errors: {serializer4.errors}")

def test_conversation_exists():
    """Check if conversations exist"""
    print("\n" + "=" * 60)
    print("CONVERSATION CHECK")
    print("=" * 60)
    
    conversations = Conversation.objects.all()[:5]
    print(f"\nTotal conversations: {Conversation.objects.count()}")
    
    if conversations:
        print("\nRecent conversations:")
        for conv in conversations:
            print(f"  - {conv.id}: {conv.title} (workspace: {conv.workspace.name})")
            print(f"    Model: {conv.model_id}, Status: {conv.status}")
            print(f"    Messages: {conv.messages.count()}")
    else:
        print("\n⚠️  No conversations found!")
        print("   Create a conversation first in the UI")

def test_user_integrations():
    """Check user integrations"""
    print("\n" + "=" * 60)
    print("INTEGRATION CHECK")
    print("=" * 60)
    
    from api.models import Integration
    
    users = User.objects.all()[:3]
    for user in users:
        integrations = Integration.objects.filter(user=user)
        print(f"\nUser: {user.username}")
        if integrations:
            for integration in integrations:
                print(f"  - {integration.provider}: {integration.status}")
        else:
            print("  No integrations")

if __name__ == '__main__':
    print("\n🧪 Testing Message Sending Components\n")
    
    test_message_serializer()
    test_conversation_exists()
    test_user_integrations()
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)
    print("\nIf serializer tests pass but messages still fail:")
    print("1. Check Django logs for detailed error")
    print("2. Verify conversation ID exists in database")
    print("3. Check user has access to the workspace")
    print("4. Verify integration is connected for the model's provider")
    print()
