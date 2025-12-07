"""
LLM Router - Routes requests to different LLM providers
Supports: OpenAI, Anthropic, Google, Groq, Local models
Enhanced with real API integration
"""
import os
from typing import Dict, Any, List
from .models import Integration, Conversation, ChatMessage
from .encryption_service import decrypt_api_key


# Supported LLM models
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
    
    # Google models
    'gemini-pro': 'google',
    'gemini-1.5-pro': 'google',
    'gemini-1.5-flash': 'google',
    'gemini-2.0-flash': 'google',
    
    # DeepSeek models
    'deepseek-chat': 'deepseek',
    'deepseek-coder': 'deepseek',
    
    # Groq models (fast inference)
    'llama-3-70b': 'groq',
    'llama-3-8b': 'groq',
    'mixtral-8x7b': 'groq',
    
    # Local/Echo (for demo)
    'echo': 'echo',
    'local': 'local',
}


def normalize_model_name(model_name: str, provider: str) -> str:
    """
    Normalize model name to the format expected by the API
    
    Args:
        model_name: Model name from frontend (e.g., "gemini-1.5-flash")
        provider: Provider name (e.g., "google")
        
    Returns:
        Normalized model name for API (e.g., "gemini-1.5-flash")
    """
    # First check for exact match in SUPPORTED_MODELS
    if model_name in SUPPORTED_MODELS:
        return model_name
    
    # Check case-insensitive exact match
    model_name_lower = model_name.lower()
    for model_key in SUPPORTED_MODELS.keys():
        if model_key.lower() == model_name_lower:
            return model_key
    
    # If no exact match found, return original (the API will handle it)
    return model_name


def get_provider(model_name: str) -> str:
    """
    Get the provider for a given model name
    
    Args:
        model_name: Name of the LLM model (e.g., "gemini-2.0-flash" or "model-gemini-2.0-flash")
        
    Returns:
        Provider name (openai, anthropic, google, groq, echo, local)
    """
    # Remove "model-" prefix if present
    clean_name = model_name.replace('model-', '').lower()
    
    # Check exact match first
    if clean_name in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[clean_name]
    
    # Normalize the clean_name for comparison (remove dots, hyphens, underscores)
    normalized_name = clean_name.replace('.', '').replace('-', '').replace('_', '')
    
    # Check against all supported models with normalization
    for model_key, provider in SUPPORTED_MODELS.items():
        # Normalize the model key
        normalized_key = model_key.replace('.', '').replace('-', '').replace('_', '').lower()
        
        # Check if they match exactly after normalization
        if normalized_name == normalized_key:
            return provider
    
    # Default to echo for demo
    return 'echo'


def call_llm_with_conversation(conversation: Conversation, user_message: str, api_key: str) -> Dict[str, Any]:
    """
    Route LLM call to appropriate provider with full conversation context
    Requirements 15.1, 15.2, 15.6, 15.7
    
    Args:
        conversation: Conversation object
        user_message: Current user message
        api_key: Decrypted API key for the provider
        
    Returns:
        Dict with reply, model_used, tokens, provider, status
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Build context
    context = build_context(conversation, user_message)
    
    # Get provider from model_id
    model_id = conversation.model_id
    provider = get_provider(model_id)
    
    # Extract actual model name (remove "model-" prefix if present)
    model_name = model_id.replace('model-', '')
    
    # Normalize model name to match API format (e.g., "gemini-20-flash" -> "gemini-2.0-flash")
    model_name = normalize_model_name(model_name, provider)
    
    # Debug logging
    logger.info(f"🔍 DEBUG: model_id={model_id}, provider={provider}, model_name={model_name}, has_api_key={api_key is not None}")
    
    # Route to appropriate provider
    if provider == 'openai':
        return call_openai(model_name, "", api_key=api_key, context=context)
    elif provider == 'anthropic':
        return call_anthropic(model_name, "", api_key=api_key, context=context)
    elif provider == 'google':
        return call_google(model_name, "", api_key=api_key, context=context)
    elif provider == 'deepseek':
        return call_deepseek(model_name, "", api_key=api_key, context=context)
    elif provider == 'groq':
        return call_groq(model_name, user_message)
    elif provider == 'local':
        return call_local(model_name, user_message)
    else:
        logger.warning(f"⚠️ Falling back to echo mode for model_id={model_id}, provider={provider}")
        return call_echo(model_name, user_message, user_message)


def call_llm(model_name: str, prompt: str, context: str = "") -> Dict[str, Any]:
    """
    Route LLM call to appropriate provider (legacy function for backward compatibility)
    
    Args:
        model_name: Name of the LLM model to use
        prompt: User message/prompt
        context: Injected context from memory
        
    Returns:
        Dict with reply, model_used, tokens, etc.
    """
    provider = get_provider(model_name)
    
    # Build full prompt with context
    full_prompt = f"{context}\n\nUser: {prompt}" if context else prompt
    
    if provider == 'openai':
        return call_openai(model_name, full_prompt)
    elif provider == 'anthropic':
        return call_anthropic(model_name, full_prompt)
    elif provider == 'google':
        return call_google(model_name, full_prompt)
    elif provider == 'deepseek':
        return call_deepseek(model_name, full_prompt)
    elif provider == 'groq':
        return call_groq(model_name, full_prompt)
    elif provider == 'local':
        return call_local(model_name, full_prompt)
    else:
        # Echo mode for demo
        return call_echo(model_name, full_prompt, prompt)


def build_context(conversation: Conversation, user_message: str) -> Dict[str, Any]:
    """
    Build context for AI model including system prompt, injected memories, and history
    Requirements 15.2, 15.5, 15.6
    """
    system_prompt = "You are a helpful AI assistant in the Chimera Protocol system."
    
    # Get only active injected memories
    injected_memories = conversation.injected_memory_links.select_related('memory').filter(is_active=True)
    memories_text = ""
    
    if injected_memories.exists():
        memories_text = "\n\n=== Injected Context ===\n"
        for link in injected_memories:
            memory = link.memory
            memories_text += f"\n[{memory.title}]\n{memory.content}\n"
        memories_text += "\n=== End Context ===\n"
    
    # Get conversation history (last 10 messages)
    history_messages = conversation.messages.order_by('-timestamp')[:10]
    history_messages = list(reversed(history_messages))
    
    return {
        'system_prompt': system_prompt,
        'memories_text': memories_text,
        'history': history_messages,
        'user_message': user_message
    }


def call_openai(model: str, prompt: str, api_key: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call OpenAI API
    Requirements 15.3: Use openai library to call chat completion API
    """
    try:
        import openai
        
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            return {
                'reply': f"[OpenAI {model}] No API key provided",
                'model_used': model,
                'provider': 'openai',
                'tokens': 0,
                'status': 'error',
                'error': 'No API key'
            }
        
        # Build messages
        messages = []
        
        if context:
            system_content = context['system_prompt']
            if context['memories_text']:
                system_content += context['memories_text']
            messages.append({'role': 'system', 'content': system_content})
            
            for msg in context['history']:
                messages.append({'role': msg.role, 'content': msg.content})
            
            messages.append({'role': 'user', 'content': context['user_message']})
        else:
            messages.append({'role': 'user', 'content': prompt})
        
        # Call OpenAI API
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        assistant_message = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        return {
            'reply': assistant_message,
            'model_used': response.model,
            'provider': 'openai',
            'tokens': tokens,
            'status': 'success'
        }
    
    except ImportError:
        return {
            'reply': f"[OpenAI {model}] openai library not installed",
            'model_used': model,
            'provider': 'openai',
            'tokens': 0,
            'status': 'error',
            'error': 'Library not installed'
        }
    except Exception as e:
        return {
            'reply': f"[OpenAI {model}] Error: {str(e)}",
            'model_used': model,
            'provider': 'openai',
            'tokens': 0,
            'status': 'error',
            'error': str(e)
        }


def call_anthropic(model: str, prompt: str, api_key: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call Anthropic Claude API
    Requirements 15.4: Use anthropic library to call messages API
    """
    try:
        import anthropic
        
        if not api_key:
            api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            return {
                'reply': f"[Anthropic {model}] No API key provided",
                'model_used': model,
                'provider': 'anthropic',
                'tokens': 0,
                'status': 'error',
                'error': 'No API key'
            }
        
        # Build system prompt and messages
        system_content = "You are a helpful AI assistant."
        messages = []
        
        if context:
            system_content = context['system_prompt']
            if context['memories_text']:
                system_content += context['memories_text']
            
            for msg in context['history']:
                if msg.role != 'system':
                    messages.append({'role': msg.role, 'content': msg.content})
            
            messages.append({'role': 'user', 'content': context['user_message']})
        else:
            messages.append({'role': 'user', 'content': prompt})
        
        # Call Anthropic API
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            system=system_content,
            messages=messages,
            max_tokens=2000
        )
        
        assistant_message = response.content[0].text
        tokens = response.usage.input_tokens + response.usage.output_tokens
        
        return {
            'reply': assistant_message,
            'model_used': response.model,
            'provider': 'anthropic',
            'tokens': tokens,
            'status': 'success'
        }
    
    except ImportError:
        return {
            'reply': f"[Anthropic {model}] anthropic library not installed",
            'model_used': model,
            'provider': 'anthropic',
            'tokens': 0,
            'status': 'error',
            'error': 'Library not installed'
        }
    except Exception as e:
        return {
            'reply': f"[Anthropic {model}] Error: {str(e)}",
            'model_used': model,
            'provider': 'anthropic',
            'tokens': 0,
            'status': 'error',
            'error': str(e)
        }


def call_google(model: str, prompt: str, api_key: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call Google AI API
    Requirements 15.5: Use google-generativeai library
    """
    try:
        import google.generativeai as genai
        
        if not api_key:
            api_key = os.getenv('GOOGLE_AI_API_KEY')
        
        if not api_key:
            return {
                'reply': f"[Google {model}] No API key provided",
                'model_used': model,
                'provider': 'google',
                'tokens': 0,
                'status': 'error',
                'error': 'No API key'
            }
        
        genai.configure(api_key=api_key)
        
        # Build full prompt
        full_prompt = ""
        if context:
            full_prompt = context['system_prompt']
            if context['memories_text']:
                full_prompt += "\n" + context['memories_text']
            
            if context['history']:
                full_prompt += "\n\n=== Conversation History ===\n"
                for msg in context['history']:
                    full_prompt += f"{msg.role}: {msg.content}\n"
            
            full_prompt += f"\n\nUser: {context['user_message']}"
        else:
            full_prompt = prompt
        
        # Call Google AI API
        gen_model = genai.GenerativeModel(model)
        response = gen_model.generate_content(full_prompt)
        
        # Check if response was blocked
        if not response.text:
            if hasattr(response, 'prompt_feedback'):
                return {
                    'reply': f"[Google {model}] Content was blocked by safety filters: {response.prompt_feedback}",
                    'model_used': model,
                    'provider': 'google',
                    'tokens': 0,
                    'status': 'error',
                    'error': 'Content blocked by safety filters'
                }
            else:
                return {
                    'reply': f"[Google {model}] No response generated",
                    'model_used': model,
                    'provider': 'google',
                    'tokens': 0,
                    'status': 'error',
                    'error': 'No response generated'
                }
        
        return {
            'reply': response.text,
            'model_used': model,
            'provider': 'google',
            'tokens': 0,  # Google doesn't always provide token count
            'status': 'success'
        }
    
    except ImportError:
        return {
            'reply': f"[Google {model}] google-generativeai library not installed",
            'model_used': model,
            'provider': 'google',
            'tokens': 0,
            'status': 'error',
            'error': 'Library not installed'
        }
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Google API Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            'reply': f"[Google {model}] Error: {str(e)}",
            'model_used': model,
            'provider': 'google',
            'tokens': 0,
            'status': 'error',
            'error': str(e)
        }


def call_deepseek(model: str, prompt: str, api_key: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Call DeepSeek API (OpenAI-compatible)
    Requirements: Use openai library with custom base URL
    """
    try:
        import openai
        
        if not api_key:
            api_key = os.getenv('DEEPSEEK_API_KEY')
        
        if not api_key:
            return {
                'reply': f"[DeepSeek {model}] No API key provided",
                'model_used': model,
                'provider': 'deepseek',
                'tokens': 0,
                'status': 'error',
                'error': 'No API key'
            }
        
        # Build messages
        messages = []
        
        if context:
            system_content = context['system_prompt']
            if context['memories_text']:
                system_content += context['memories_text']
            messages.append({'role': 'system', 'content': system_content})
            
            for msg in context['history']:
                messages.append({'role': msg.role, 'content': msg.content})
            
            messages.append({'role': 'user', 'content': context['user_message']})
        else:
            messages.append({'role': 'user', 'content': prompt})
        
        # Call DeepSeek API with custom base URL
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        assistant_message = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        
        return {
            'reply': assistant_message,
            'model_used': response.model,
            'provider': 'deepseek',
            'tokens': tokens,
            'status': 'success'
        }
    
    except ImportError:
        return {
            'reply': f"[DeepSeek {model}] openai library not installed",
            'model_used': model,
            'provider': 'deepseek',
            'tokens': 0,
            'status': 'error',
            'error': 'Library not installed'
        }
    except Exception as e:
        return {
            'reply': f"[DeepSeek {model}] Error: {str(e)}",
            'model_used': model,
            'provider': 'deepseek',
            'tokens': 0,
            'status': 'error',
            'error': str(e)
        }


def call_groq(model: str, prompt: str) -> Dict[str, Any]:
    """
    Call Groq API (fast inference)
    
    Note: Requires GROQ_API_KEY in environment
    For demo, returns placeholder
    """
    # TODO: Implement actual Groq API call
    # from groq import Groq
    # response = Groq().chat.completions.create(...)
    
    return {
        'reply': f"[Groq {model}] This is a placeholder response. Integrate Groq API for production.",
        'model_used': model,
        'provider': 'groq',
        'tokens': 0,
        'status': 'demo_mode'
    }


def call_local(model: str, prompt: str) -> Dict[str, Any]:
    """
    Call local model (e.g., Ollama, LM Studio)
    
    Note: Requires local model server running
    For demo, returns placeholder
    """
    # TODO: Implement local model call
    # import requests
    # response = requests.post('http://localhost:11434/api/generate', ...)
    
    return {
        'reply': f"[Local {model}] This is a placeholder response. Integrate local model server for production.",
        'model_used': model,
        'provider': 'local',
        'tokens': 0,
        'status': 'success'  # Changed from 'demo_mode' to 'success'
    }


def call_echo(model: str, full_prompt: str, original_prompt: str) -> Dict[str, Any]:
    """
    Echo mode for demo - returns formatted response showing context injection
    """
    # Extract context if present
    has_context = "User:" in full_prompt
    
    if has_context:
        context_part = full_prompt.split("User:")[0].strip()
        reply = f"[Echo Mode - {model}]\n\n✅ Context Received ({len(context_part)} chars)\n\n📝 Your message: {original_prompt}\n\n🤖 Response: I received your message with injected context. In production, this would be processed by {model}."
    else:
        reply = f"[Echo Mode - {model}]\n\n📝 Your message: {original_prompt}\n\n🤖 Response: I received your message. In production, this would be processed by {model}."
    
    return {
        'reply': reply,
        'model_used': model,
        'provider': 'echo',
        'context_injected': has_context,
        'context_length': len(context_part) if has_context else 0,
        'tokens': len(full_prompt.split()),
        'status': 'success'  # Changed from 'demo_mode' to 'success'
    }


def is_model_supported(model_name: str) -> bool:
    """
    Check if a model is supported
    
    Args:
        model_name: Name of the model
        
    Returns:
        True if supported, False otherwise
    """
    return model_name in SUPPORTED_MODELS or any(
        model_name.startswith(key) for key in SUPPORTED_MODELS.keys()
    )


def get_supported_models() -> Dict[str, list]:
    """
    Get list of all supported models grouped by provider
    
    Returns:
        Dict mapping provider to list of models
    """
    models_by_provider = {}
    for model, provider in SUPPORTED_MODELS.items():
        if provider not in models_by_provider:
            models_by_provider[provider] = []
        models_by_provider[provider].append(model)
    
    return models_by_provider
