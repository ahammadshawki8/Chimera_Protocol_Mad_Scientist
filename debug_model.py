"""Debug script to test model ID resolution"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chimera.settings')
django.setup()

from api.models import Conversation, Integration
from api.llm_router import get_provider, normalize_model_name, SUPPORTED_MODELS

# Get latest conversation
conv = Conversation.objects.last()
if conv:
    print(f"Conversation Model ID: {conv.model_id}")
    print(f"Workspace: {conv.workspace.name}")
    
    # Test provider detection
    provider = get_provider(conv.model_id)
    print(f"Detected Provider: {provider}")
    
    # Test model name normalization
    model_name = conv.model_id.replace('model-', '')
    normalized = normalize_model_name(model_name, provider)
    print(f"Model Name: {model_name}")
    print(f"Normalized: {normalized}")
    
    # Check integrations
    integrations = Integration.objects.filter(user=conv.workspace.owner)
    print(f"\nUser Integrations:")
    for integration in integrations:
        print(f"  - {integration.provider}: {integration.status}")
    
    # Check connected integrations
    connected = Integration.objects.filter(user=conv.workspace.owner, status='connected')
    print(f"\nConnected Integrations: {connected.count()}")
    for integration in connected:
        print(f"  - {integration.provider}")
else:
    print("No conversations found")

print("\n\nSupported Models:")
for model, provider in SUPPORTED_MODELS.items():
    print(f"  {model} -> {provider}")
