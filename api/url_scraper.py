"""
URL Content Scraper - Lightweight version using requests + BeautifulSoup
No Playwright dependency to save memory on free tier hosting
"""
import re
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
MAX_CONTENT_LENGTH = 30000
REQUEST_TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'


def clean_text(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def scrape_url(url: str) -> dict:
    """Scrape content from URL. JS-heavy sites not supported."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return {'success': False, 'error': 'Only HTTP/HTTPS supported'}
        
        # JS-heavy sites need copy-paste
        js_sites = ['chat.openai.com', 'chatgpt.com', 'notion.so', 'claude.ai']
        for site in js_sites:
            if site in parsed.netloc.lower():
                return {'success': False, 'error': f'{site} requires JS. Copy-paste content instead.'}
        
        resp = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        for el in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            el.decompose()
        
        title = clean_text(soup.title.string) if soup.title else 'Imported'
        
        # Find main content
        content = ''
        for sel in ['main', 'article', '.content', '#content']:
            el = soup.select_one(sel)
            if el:
                content = clean_text(el.get_text('\n'))
                if len(content) > 100:
                    break
        
        if not content and soup.body:
            content = clean_text(soup.body.get_text('\n'))
        
        if len(content) < 50:
            return {'success': False, 'error': 'No meaningful content found'}
        
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH] + '\n[truncated]'
        
        return {'success': True, 'title': title[:200], 'content': content, 'source_url': url}
        
    except Exception as e:
        return {'success': False, 'error': str(e)[:100]}
