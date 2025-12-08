"""
LLM Router - Routes requests to different LLM providers
Supports: OpenAI, Anthropic, Google Gemini, Groq, DeepSeek
Optimized for low memory usage on free tier hosting
"""
import os
import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Supported LLM models - Dec 2025
SUPPORTED_MODELS = {
    # OpenAI models
    'gpt-4': 'openai',
    'gpt-4-turbo': 'openai',
    'gpt-4o': 'openai',
    'gpt-3.5-turbo': 'openai',
    
    # Anthropic models
    'claude-3-opus': 'anthropic',
    'claude-3-sonnet': 'anthropic',
    'claude-3-haiku': 'anthropic',
    'claude-3.5-sonnet': 'anthropic',
    
    # Google Gemini models (Dec 2025)
    'gemini-2.0-flash': 'google',
    'gemini-2.0-flash-exp': 'google',
    'gemini-1.5-flash': 'google',
    'gemini-1.5-pro': 'google',
    
    # DeepSeek models
    'deepseek-chat': 'deepseek',
    'deepseek-coder': 'deepseek',
    
    # Groq models (FREE - fast inference) - Dec 2025
    'llama-3.3-70b-versatile': 'groq',
    'llama-3.1-8b-instant': 'groq',
    'mixtral-8x7b-32768': 'groq',
    'gemma2-9b-it': 'groq',
    
    # Echo mode for demo
    'echo': 'echo',
}


def get_provider(model_name: str) -> str:
    """Get provider for a model name"""
    clean_name = model_name.replace('model-', '')
    
    if clean_name in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[clean_name]
    
    # Case-insensitive fallback
    for key, provider in SUPPORTED_MODELS.items():
        if key.lower() == clean_name.lower():
            return provider
    
    return 'echo'


def build_context(conversation, user_message: str) -> Dict[str, Any]:
    """Build context for AI model - optimized to limit history"""
    system_prompt = "You are a helpful AI assistant in the Chimera Protocol system."
    
    # Get only active injected memories
    injected_memories = conversation.injected_memory_links.select_related('memory').filter(is_active=True)
    memories_text = ""
    
    if injected_memories.exists():
        memories_text = "\n\n=== Injected Context ===\n"
        for link in injected_memories[:5]:  # Limit to 5 memories
            memory = link.memory
            # Truncate long memories
            content = memory.content[:1000] if len(memory.content) > 1000 else memory.content
            memories_text += f"\n[{memory.title}]\n{content}\n"
        memories_text += "\n=== End Context ===\n"
    
    # Get conversation history (limit to last 5 messages for memory efficiency)
    history_messages = list(conversation.messages.order_by('-timestamp')[:5])
    history_messages.reverse()
    
    return {
        'system_prompt': system_prompt,
        'memories_text': memories_text,
        'history': history_messages,
        'user_message': user_message
    }


def call_llm_with_conversation(conversation, user_message: str, api_key: str) -> Dict[str, Any]:
    """Route LLM call to appropriate provider with conversation context"""
    context = build_context(conversation, user_message)
    model_id = conversation.model_id
    model_name = model_id.replace('model-', '')
    provider = get_provider(model_id)
    
    logger.info(f"🔍 LLM call: model={model_name}, provider={provider}")
    
    if provider == 'openai':
        return call_openai(model_name, api_key, context)
    elif provider == 'anthropic':
        return call_anthropic(model_name, api_key, context)
    elif provider == 'google':
        return call_google(model_name, api_key, context)
    elif provider == 'deepseek':
        return call_deepseek(model_name, api_key, context)
    elif provider == 'groq':
        return call_groq(model_name, api_key, context)
    else:
        return call_echo(model_name, user_message)


def build_messages(context: Dict[str, Any]) -> List[Dict[str, str]]:
    """Build messages array for OpenAI-compatible APIs"""
    messages = []
    
    # System message with memories
    system_content = context['system_prompt']
    if context['memories_text']:
        system_content += context['memories_text']
    messages.append({'role': 'system', 'content': system_content})
    
    # History
    for msg in context['history']:
        messages.append({'role': msg.role, 'content': msg.content})
    
    # Current message
    messages.append({'role': 'user', 'content': context['user_message']})
    
    return messages


def call_openai(model: str, api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenAI API using requests (lightweight)"""
    if not api_key:
        return error_response(model, 'openai', 'No API key provided')
    
    try:
        messages = build_messages(context)
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'reply': data['choices'][0]['message']['content'],
                'model_used': data.get('model', model),
                'provider': 'openai',
                'tokens': data.get('usage', {}).get('total_tokens', 0),
                'status': 'success'
            }
        else:
            error_msg = response.json().get('error', {}).get('message', response.text[:200])
            return error_response(model, 'openai', error_msg)
            
    except requests.exceptions.Timeout:
        return error_response(model, 'openai', 'Request timeout')
    except Exception as e:
        return error_response(model, 'openai', str(e))


def call_anthropic(model: str, api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Call Anthropic Claude API using requests"""
    if not api_key:
        return error_response(model, 'anthropic', 'No API key provided')
    
    try:
        # Build system and messages
        system_content = context['system_prompt']
        if context['memories_text']:
            system_content += context['memories_text']
        
        messages = []
        for msg in context['history']:
            if msg.role != 'system':
                messages.append({'role': msg.role, 'content': msg.content})
        messages.append({'role': 'user', 'content': context['user_message']})
        
        # Map model names to Anthropic format
        model_map = {
            'claude-3.5-sonnet': 'claude-3-5-sonnet-20241022',
            'claude-3-opus': 'claude-3-opus-20240229',
            'claude-3-sonnet': 'claude-3-sonnet-20240229',
            'claude-3-haiku': 'claude-3-haiku-20240307',
        }
        api_model = model_map.get(model, model)
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            },
            json={
                'model': api_model,
                'system': system_content,
                'messages': messages,
                'max_tokens': 2000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'reply': data['content'][0]['text'],
                'model_used': data.get('model', model),
                'provider': 'anthropic',
                'tokens': data.get('usage', {}).get('input_tokens', 0) + data.get('usage', {}).get('output_tokens', 0),
                'status': 'success'
            }
        else:
            error_msg = response.json().get('error', {}).get('message', response.text[:200])
            return error_response(model, 'anthropic', error_msg)
            
    except requests.exceptions.Timeout:
        return error_response(model, 'anthropic', 'Request timeout')
    except Exception as e:
        return error_response(model, 'anthropic', str(e))


def call_google(model: str, api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Google Gemini API using REST API (Dec 2025)
    Docs: https://ai.google.dev/gemini-api/docs/text-generation
    """
    if not api_key:
        return error_response(model, 'google', 'No API key provided')
    
    try:
        # Build contents for Gemini
        contents = []
        
        # Add system instruction as first user turn
        system_text = context['system_prompt']
        if context['memories_text']:
            system_text += context['memories_text']
        
        # Add history
        for msg in context['history']:
            role = 'user' if msg.role == 'user' else 'model'
            contents.append({
                'role': role,
                'parts': [{'text': msg.content}]
            })
        
        # Add current message with system context if first message
        user_text = context['user_message']
        if not contents:
            user_text = f"{system_text}\n\nUser: {user_text}"
        
        contents.append({
            'role': 'user',
            'parts': [{'text': user_text}]
        })
        
        # Use v1beta API endpoint
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            json={
                'contents': contents,
                'generationConfig': {
                    'temperature': 0.7,
                    'maxOutputTokens': 2000,
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract text from response
            if 'candidates' in data and data['candidates']:
                candidate = data['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    return {
                        'reply': text,
                        'model_used': model,
                        'provider': 'google',
                        'tokens': 0,
                        'status': 'success'
                    }
            
            return error_response(model, 'google', 'No response generated')
        
        elif response.status_code == 429:
            return error_response(model, 'google', 'Rate limit exceeded. Try Groq instead (free).')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]
            return error_response(model, 'google', error_msg)
            
    except requests.exceptions.Timeout:
        return error_response(model, 'google', 'Request timeout')
    except Exception as e:
        logger.error(f"Google API error: {str(e)}")
        return error_response(model, 'google', str(e))


def call_groq(model: str, api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Groq API (FREE, fast inference) - Dec 2025
    Docs: https://console.groq.com/docs/api-reference
    Uses OpenAI-compatible API
    """
    if not api_key:
        return error_response(model, 'groq', 'No API key provided')
    
    try:
        messages = build_messages(context)
        
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            timeout=30  # Groq is fast
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'reply': data['choices'][0]['message']['content'],
                'model_used': data.get('model', model),
                'provider': 'groq',
                'tokens': data.get('usage', {}).get('total_tokens', 0),
                'status': 'success'
            }
        else:
            try:
                error_msg = response.json().get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]
            return error_response(model, 'groq', error_msg)
            
    except requests.exceptions.Timeout:
        return error_response(model, 'groq', 'Request timeout')
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return error_response(model, 'groq', str(e))


def call_deepseek(model: str, api_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Call DeepSeek API (OpenAI-compatible)"""
    if not api_key:
        return error_response(model, 'deepseek', 'No API key provided')
    
    try:
        messages = build_messages(context)
        
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': messages,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'reply': data['choices'][0]['message']['content'],
                'model_used': data.get('model', model),
                'provider': 'deepseek',
                'tokens': data.get('usage', {}).get('total_tokens', 0),
                'status': 'success'
            }
        else:
            try:
                error_msg = response.json().get('error', {}).get('message', response.text[:200])
            except:
                error_msg = response.text[:200]
            return error_response(model, 'deepseek', error_msg)
            
    except requests.exceptions.Timeout:
        return error_response(model, 'deepseek', 'Request timeout')
    except Exception as e:
        return error_response(model, 'deepseek', str(e))


def call_echo(model: str, user_message: str) -> Dict[str, Any]:
    """Echo mode for demo/testing"""
    return {
        'reply': f"[Echo Mode] Received: {user_message}\n\nThis is a demo response. Connect an LLM provider to get real AI responses.",
        'model_used': model,
        'provider': 'echo',
        'tokens': len(user_message.split()),
        'status': 'success'
    }


def error_response(model: str, provider: str, error: str) -> Dict[str, Any]:
    """Standard error response"""
    return {
        'reply': f"[{provider.upper()} Error] {error}",
        'model_used': model,
        'provider': provider,
        'tokens': 0,
        'status': 'error',
        'error': error
    }


# Legacy function for backward compatibility
def call_llm(model_name: str, prompt: str, context: str = "") -> Dict[str, Any]:
    """Legacy LLM call function"""
    provider = get_provider(model_name)
    full_prompt = f"{context}\n\nUser: {prompt}" if context else prompt
    
    # Build simple context
    simple_context = {
        'system_prompt': 'You are a helpful AI assistant.',
        'memories_text': '',
        'history': [],
        'user_message': full_prompt
    }
    
    if provider == 'echo':
        return call_echo(model_name, prompt)
    
    return error_response(model_name, provider, 'Use call_llm_with_conversation for full functionality')


def is_model_supported(model_name: str) -> bool:
    """Check if a model is supported"""
    clean_name = model_name.replace('model-', '')
    return clean_name in SUPPORTED_MODELS or clean_name.lower() in [k.lower() for k in SUPPORTED_MODELS.keys()]


def get_supported_models() -> Dict[str, str]:
    """Get all supported models"""
    return SUPPORTED_MODELS.copy()
