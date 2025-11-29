"""
Integration Management Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from .models import Integration
from .serializers_v2 import IntegrationSerializer, IntegrationCreateSerializer
from .encryption_service import encrypt_api_key, decrypt_api_key


def api_response(ok=True, data=None, error=None):
    """Standard API response envelope"""
    return {'ok': ok, 'data': data, 'error': error}


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def integrations_view(request):
    """
    GET: List all integrations for user
    POST: Create new integration
    """
    if request.method == 'GET':
        integrations = Integration.objects.filter(user=request.user)
        serializer = IntegrationSerializer(integrations, many=True)
        
        return Response(api_response(
            ok=True,
            data={
                'integrations': serializer.data,
                'total': integrations.count()
            }
        ))
    
    elif request.method == 'POST':
        serializer = IntegrationCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                api_response(ok=False, error=serializer.errors),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        provider = serializer.validated_data['provider']
        api_key = serializer.validated_data['apiKey']
        
        # Check if integration already exists
        if Integration.objects.filter(user=request.user, provider=provider).exists():
            return Response(
                api_response(ok=False, error='Integration already exists for this provider'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Encrypt API key before storage
        encrypted_key = encrypt_api_key(api_key)
        
        # Create integration
        integration = Integration.objects.create(
            user=request.user,
            provider=provider,
            api_key=encrypted_key,
            status='disconnected'
        )
        
        response_serializer = IntegrationSerializer(integration)
        
        return Response(
            api_response(ok=True, data=response_serializer.data),
            status=status.HTTP_201_CREATED
        )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def integration_detail_view(request, integration_id):
    """
    GET: Get integration details
    PUT: Update integration
    DELETE: Delete integration
    """
    try:
        integration = Integration.objects.get(id=integration_id, user=request.user)
        
        if request.method == 'GET':
            serializer = IntegrationSerializer(integration)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'PUT':
            if 'apiKey' in request.data:
                # Encrypt new API key before storage
                encrypted_key = encrypt_api_key(request.data['apiKey'])
                integration.api_key = encrypted_key
                integration.status = 'disconnected'  # Reset status when key changes
                integration.error_message = None
            
            integration.save()
            
            serializer = IntegrationSerializer(integration)
            return Response(api_response(ok=True, data=serializer.data))
        
        elif request.method == 'DELETE':
            integration.delete()
            return Response(api_response(
                ok=True,
                data={'message': 'Integration deleted successfully'}
            ))
    
    except Integration.DoesNotExist:
        return Response(
            api_response(ok=False, error='Integration not found'),
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_integration_view(request, integration_id):
    """Test API connection for integration"""
    try:
        integration = Integration.objects.get(id=integration_id, user=request.user)
        
        # Decrypt API key for testing
        try:
            api_key = decrypt_api_key(integration.api_key)
        except Exception as e:
            integration.status = 'error'
            integration.error_message = 'Failed to decrypt API key'
            integration.last_tested = timezone.now()
            integration.save()
            
            return Response(
                api_response(ok=False, error='Failed to decrypt API key'),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Test the API connection based on provider
        test_result = _test_provider_connection(integration.provider, api_key)
        
        # Update integration based on test result
        integration.status = 'connected' if test_result['success'] else 'error'
        integration.last_tested = timezone.now()
        integration.error_message = test_result.get('error')
        integration.save()
        
        serializer = IntegrationSerializer(integration)
        
        if test_result['success']:
            return Response(api_response(
                ok=True,
                data={
                    'integration': serializer.data,
                    'message': 'Connection test successful'
                }
            ))
        else:
            return Response(
                api_response(
                    ok=False,
                    error=test_result.get('error', 'Connection test failed'),
                    data={'integration': serializer.data}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Integration.DoesNotExist:
        return Response(
            api_response(ok=False, error='Integration not found'),
            status=status.HTTP_404_NOT_FOUND
        )


def _test_provider_connection(provider, api_key):
    """
    Test API connection for a specific provider
    Returns dict with 'success' boolean and optional 'error' message
    """
    import requests
    
    try:
        if provider == 'openai':
            # Test OpenAI API by calling /v1/models endpoint
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers={
                    'Authorization': f'Bearer {api_key}'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            else:
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        elif provider == 'anthropic':
            # Test Anthropic API by calling /v1/messages endpoint with minimal request
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 1,
                    'messages': [{'role': 'user', 'content': 'test'}]
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            else:
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        elif provider == 'google':
            # Test Google AI API by calling the models endpoint
            response = requests.get(
                f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}',
                timeout=10
            )
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 400:
                # Google returns 400 for invalid API keys
                return {'success': False, 'error': 'Invalid API key'}
            else:
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        else:
            return {'success': False, 'error': f'Unknown provider: {provider}'}
    
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Connection timeout - API did not respond in time'}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection error - unable to reach API'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Request failed: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_models_view(request):
    """
    List available cognitive models based on user's connected integrations
    
    Requirements 6.6: Query all user integrations with status='connected'
    and map each to cognitive model object with id, provider, name, 
    displayName, brainRegion, status, and 3D position coordinates
    """
    from .llm_router import SUPPORTED_MODELS
    
    # Get user's connected integrations
    connected_integrations = Integration.objects.filter(
        user=request.user,
        status='connected'
    )
    
    # Build list of available models from connected integrations
    available_models = []
    
    for integration in connected_integrations:
        provider = integration.provider
        
        # Get all models for this provider from SUPPORTED_MODELS
        provider_models = [
            model_name for model_name, model_provider in SUPPORTED_MODELS.items()
            if model_provider == provider
        ]
        
        # Create cognitive model object for each model
        for model_name in provider_models:
            # Generate display name (capitalize and replace hyphens with spaces)
            display_name = model_name.replace('-', ' ').title()
            
            # Create model ID (e.g., "model-gpt4o")
            model_id = f"model-{model_name.replace('.', '').replace('_', '')}"
            
            available_models.append({
                'id': model_id,
                'provider': provider,
                'name': model_name,
                'displayName': display_name,
                'brainRegion': get_brain_region(provider),
                'status': 'connected',
                'position': get_model_position(provider)
            })
    
    return Response(api_response(
        ok=True,
        data={
            'models': available_models,
            'total': len(available_models)
        }
    ))


def get_brain_region(provider):
    """Get brain region for provider"""
    regions = {
        'openai': 'Left Cortex',
        'anthropic': 'Right Cortex',
        'google': 'Occipital',
        'groq': 'Temporal',
        'echo': 'Cerebellum'
    }
    return regions.get(provider, 'Unknown')


def get_model_position(provider):
    """Get 3D position for model in brain visualization"""
    positions = {
        'openai': {'x': -2, 'y': 1, 'z': 1},
        'anthropic': {'x': 2, 'y': 1, 'z': 1},
        'google': {'x': 0, 'y': -1, 'z': 2},
        'groq': {'x': -1, 'y': 0, 'z': -1},
        'echo': {'x': 0, 'y': 0, 'z': 0}
    }
    return positions.get(provider, {'x': 0, 'y': 0, 'z': 0})
