"""
Automatic Memory Extraction - Intelligently extracts important facts from conversations
"""
import re
from typing import List, Dict, Tuple


# Keywords that indicate important information
IMPORTANCE_KEYWORDS = {
    'high': [
        'prefer', 'like', 'love', 'hate', 'dislike', 'always', 'never',
        'important', 'critical', 'must', 'required', 'need', 'want',
        'remember', 'note', 'save', 'store', 'keep in mind'
    ],
    'medium': [
        'usually', 'often', 'sometimes', 'typically', 'generally',
        'working on', 'building', 'creating', 'developing',
        'use', 'using', 'utilize', 'employ'
    ],
    'low': [
        'might', 'maybe', 'perhaps', 'possibly', 'could',
        'thinking about', 'considering', 'exploring'
    ]
}

# Patterns that indicate factual statements
FACT_PATTERNS = [
    r"(?:I|we|user|team)\s+(?:am|is|are)\s+(.+)",
    r"(?:I|we|user|team)\s+(?:prefer|like|love|use|need)\s+(.+)",
    r"(?:my|our|the)\s+(?:name|email|phone|address|company)\s+(?:is|are)\s+(.+)",
    r"(?:I|we)\s+(?:work|working|build|building|develop|developing)\s+(?:on|with|in)\s+(.+)",
]


def should_save_memory(user_message: str, llm_reply: str) -> Tuple[bool, str]:
    """
    Determine if a conversation exchange should be saved to memory
    
    Args:
        user_message: User's message
        llm_reply: LLM's response
        
    Returns:
        Tuple of (should_save, importance_level)
    """
    # Always save conversations to build context
    # This ensures every meaningful exchange is captured
    
    # Check for explicit save requests
    save_keywords = ['remember', 'save', 'store', 'keep', 'note']
    if any(keyword in user_message.lower() for keyword in save_keywords):
        return True, 'high'
    
    # Check for high importance keywords
    for keyword in IMPORTANCE_KEYWORDS['high']:
        if keyword in user_message.lower():
            return True, 'high'
    
    # Check for medium importance keywords
    for keyword in IMPORTANCE_KEYWORDS['medium']:
        if keyword in user_message.lower():
            return True, 'medium'
    
    # Check for factual patterns
    for pattern in FACT_PATTERNS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return True, 'medium'
    
    # Check message length (longer messages often contain important info)
    if len(user_message.split()) > 10:
        return True, 'medium'
    
    # Save shorter messages as low priority
    if len(user_message.split()) > 3:
        return True, 'low'
    
    return False, 'none'


def extract_facts(text: str) -> List[Dict[str, str]]:
    """
    Extract factual statements from text
    
    Args:
        text: Text to extract facts from
        
    Returns:
        List of extracted facts with metadata
    """
    facts = []
    
    # Extract using patterns
    for pattern in FACT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            fact_text = match.group(0).strip()
            if len(fact_text) > 10:  # Minimum length
                facts.append({
                    'text': fact_text,
                    'type': 'extracted',
                    'confidence': 'medium'
                })
    
    # Extract sentences with importance keywords
    sentences = text.split('.')
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Check for high importance
        for keyword in IMPORTANCE_KEYWORDS['high']:
            if keyword in sentence.lower():
                facts.append({
                    'text': sentence,
                    'type': 'important',
                    'confidence': 'high'
                })
                break
    
    return facts


def generate_tags(text: str) -> List[str]:
    """
    Generate relevant tags for a memory
    
    Args:
        text: Memory text
        
    Returns:
        List of tags
    """
    tags = []
    text_lower = text.lower()
    
    # Category tags
    if any(word in text_lower for word in ['prefer', 'like', 'love', 'favorite']):
        tags.append('preference')
    
    if any(word in text_lower for word in ['building', 'working', 'developing', 'creating']):
        tags.append('project')
    
    if any(word in text_lower for word in ['python', 'javascript', 'java', 'code', 'programming']):
        tags.append('programming')
    
    if any(word in text_lower for word in ['design', 'ui', 'ux', 'interface', 'layout']):
        tags.append('design')
    
    if any(word in text_lower for word in ['api', 'backend', 'server', 'database']):
        tags.append('backend')
    
    if any(word in text_lower for word in ['frontend', 'react', 'vue', 'angular']):
        tags.append('frontend')
    
    if any(word in text_lower for word in ['team', 'colleague', 'member', 'collaborate']):
        tags.append('team')
    
    if any(word in text_lower for word in ['important', 'critical', 'must', 'required']):
        tags.append('important')
    
    # Default tag if none found
    if not tags:
        tags.append('general')
    
    return tags


def calculate_importance_score(text: str, context: Dict = None) -> float:
    """
    Calculate importance score for a memory (0.0 to 1.0)
    
    Args:
        text: Memory text
        context: Optional context (user_message, llm_reply, etc.)
        
    Returns:
        Importance score between 0.0 and 1.0
    """
    score = 0.5  # Base score
    text_lower = text.lower()
    
    # Boost for high importance keywords
    for keyword in IMPORTANCE_KEYWORDS['high']:
        if keyword in text_lower:
            score += 0.1
    
    # Boost for explicit save requests
    if any(word in text_lower for word in ['remember', 'save', 'important']):
        score += 0.2
    
    # Boost for factual patterns
    for pattern in FACT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.1
            break
    
    # Boost for length (more detailed = more important)
    word_count = len(text.split())
    if word_count > 50:
        score += 0.1
    elif word_count > 20:
        score += 0.05
    
    # Cap at 1.0
    return min(score, 1.0)


def auto_extract_and_save(user_message: str, llm_reply: str, conversation, model_used: str = None):
    """
    Automatically extract and save important information from conversation
    
    Args:
        user_message: User's message
        llm_reply: LLM's response
        conversation: Conversation object
        model_used: Model that generated the reply
        
    Returns:
        List of created memory objects
    """
    from .models import Memory
    from .memory_service import memory_service
    
    created_memories = []
    
    # Check if we should save
    should_save, importance = should_save_memory(user_message, llm_reply)
    
    if not should_save:
        return created_memories
    
    # Extract facts from user message
    user_facts = extract_facts(user_message)
    
    for fact in user_facts:
        tags = generate_tags(fact['text'])
        importance_score = calculate_importance_score(fact['text'])
        
        # Create title from first 50 chars
        title = fact['text'][:50] + ('...' if len(fact['text']) > 50 else '')
        
        memory = Memory.objects.create(
            workspace=conversation.workspace,
            title=title,
            content=fact['text'],
            tags=tags,
            metadata={
                'source': 'user',
                'auto_extracted': True,
                'importance': importance,
                'importance_score': importance_score,
                'extraction_type': fact['type'],
                'model_used': model_used,
                'conversation_id': conversation.id
            }
        )
        
        # Store in search index
        memory_service.store(memory.content, memory.id)
        
        created_memories.append(memory)
    
    # Save full exchange if high importance
    if importance == 'high':
        tags = generate_tags(user_message + ' ' + llm_reply)
        exchange_text = f"User: {user_message}\n\nAssistant: {llm_reply}"
        
        # Create title from user message
        title = f"Important: {user_message[:40]}..." if len(user_message) > 40 else f"Important: {user_message}"
        
        memory = Memory.objects.create(
            workspace=conversation.workspace,
            title=title,
            content=exchange_text,
            tags=tags + ['full-exchange', 'high-importance'],
            metadata={
                'source': 'exchange',
                'auto_extracted': True,
                'importance': importance,
                'model_used': model_used,
                'conversation_id': conversation.id
            }
        )
        
        # Store in search index
        memory_service.store(memory.content, memory.id)
        
        created_memories.append(memory)
    
    return created_memories
