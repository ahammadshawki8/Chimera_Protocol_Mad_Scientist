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
        
        # Test the API connection before saving
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 Creating integration for provider: {provider}")
        
        test_result = _test_provider_connection(provider, api_key)
        
        # Encrypt API key before storage
        encrypted_key = encrypt_api_key(api_key)
        
        # Create integration with status based on test result
        integration = Integration.objects.create(
            user=request.user,
            provider=provider,
            api_key=encrypted_key,
            status='connected' if test_result['success'] else 'error',
            last_tested=timezone.now(),
            error_message=test_result.get('error')
        )
        
        response_serializer = IntegrationSerializer(integration)
        
        # Always return ok=True since the integration was created successfully
        # The integration status field indicates whether the connection test passed
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
        
        # Always return 200 - the test completed, even if the connection failed
        # The integration status and error message indicate the result
        return Response(api_response(
            ok=True,
            data={
                'integration': serializer.data,
                'message': 'Connection test successful' if test_result['success'] else test_result.get('error', 'Connection test failed'),
                'success': test_result['success']
            }
        ))
    
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
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 Testing connection for provider: {provider}")
    
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
            
            logger.info(f"✅ OpenAI API response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            else:
                error_detail = response.text[:200] if response.text else 'No details'
                logger.error(f"❌ OpenAI API error: {response.status_code} - {error_detail}")
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
            
            logger.info(f"✅ Anthropic API response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            else:
                error_detail = response.text[:200] if response.text else 'No details'
                logger.error(f"❌ Anthropic API error: {response.status_code} - {error_detail}")
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        elif provider == 'google':
            # Test Google AI API by calling the models endpoint
            response = requests.get(
                f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}',
                timeout=10
            )
            
            logger.info(f"✅ Google API response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 400:
                # Google returns 400 for invalid API keys
                error_detail = response.text[:200] if response.text else 'No details'
                logger.error(f"❌ Google API error: {response.status_code} - {error_detail}")
                return {'success': False, 'error': 'Invalid API key'}
            else:
                error_detail = response.text[:200] if response.text else 'No details'
                logger.error(f"❌ Google API error: {response.status_code} - {error_detail}")
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        elif provider == 'deepseek':
            # Test DeepSeek API using /models endpoint (doesn't consume credits)
            # DeepSeek uses OpenAI-compatible API at api.deepseek.com
            response = requests.get(
                'https://api.deepseek.com/models',
                headers={
                    'Authorization': f'Bearer {api_key}',
                },
                timeout=10
            )
            
            logger.info(f"✅ DeepSeek API response: {response.status_code}")
            
            if response.status_code == 200:
                return {'success': True}
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid API key'}
            elif response.status_code == 402:
                # 402 means valid key but insufficient balance
                return {'success': True}  # Key is valid, just no credits
            else:
                error_detail = response.text[:200] if response.text else 'No details'
                logger.error(f"❌ DeepSeek API error: {response.status_code} - {error_detail}")
                return {'success': False, 'error': f'API returned status {response.status_code}'}
        
        else:
            return {'success': False, 'error': f'Unknown provider: {provider}'}
    
    except requests.exceptions.Timeout:
        logger.error(f"❌ Connection timeout for {provider}")
        return {'success': False, 'error': 'Connection timeout - API did not respond in time'}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error for {provider}: {str(e)}")
        return {'success': False, 'error': 'Connection error - unable to reach API'}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed for {provider}: {str(e)}")
        return {'success': False, 'error': f'Request failed: {str(e)}'}
    except Exception as e:
        logger.error(f"❌ Unexpected error for {provider}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
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
    
    # Primary model for each provider (shown in 3D brain)
    PRIMARY_MODELS = {
        'openai': 'gpt-4o',
        'anthropic': 'claude-3.5-sonnet',
        'google': 'gemini-2.0-flash',
        'deepseek': 'deepseek-chat',
        'groq': 'llama-3-70b',
    }
    
    # Build list of available models from connected integrations
    # Only show the primary model for each provider
    available_models = []
    
    for integration in connected_integrations:
        provider = integration.provider
        
        # Get the primary model for this provider
        primary_model = PRIMARY_MODELS.get(provider)
        
        if primary_model:
            # Generate display name (capitalize and replace hyphens with spaces)
            display_name = primary_model.replace('-', ' ').title()
            
            # Create model ID
            model_id = f"model-{primary_model}"
            
            available_models.append({
                'id': model_id,
                'provider': provider,
                'name': primary_model,
                'displayName': display_name,
                'brainRegion': get_brain_region(provider),
                'status': 'connected',
                'position': get_model_position(provider, len(available_models))
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
        'deepseek': 'Frontal Lobe',
        'groq': 'Temporal',
        'echo': 'Cerebellum'
    }
    return regions.get(provider, 'Unknown')


def get_model_position(provider, index=0):
    """Get 3D position for model on brain sphere surface (radius ~2.2)"""
    import math
    
    # Positions on sphere surface (radius 2.2)
    # Using spherical coordinates converted to cartesian
    radius = 2.2
    
    positions = {
        'openai': {'x': -1.8, 'y': 0.8, 'z': 1.0},      # Left upper front
        'anthropic': {'x': 1.8, 'y': 0.8, 'z': 1.0},    # Right upper front
        'google': {'x': 0, 'y': -1.2, 'z': 1.8},        # Bottom front
        'deepseek': {'x': 0, 'y': 1.8, 'z': 1.2},       # Top front
        'groq': {'x': -1.5, 'y': -0.5, 'z': 1.5},       # Left lower front
        'echo': {'x': 0, 'y': 0, 'z': 2.2}              # Center front
    }
    
    pos = positions.get(provider, {'x': 0, 'y': 0, 'z': 2.2})
    
    # Normalize to sphere surface
    length = math.sqrt(pos['x']**2 + pos['y']**2 + pos['z']**2)
    if length > 0:
        scale = radius / length
        pos = {'x': pos['x'] * scale, 'y': pos['y'] * scale, 'z': pos['z'] * scale}
    
    return pos
